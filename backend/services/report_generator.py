"""
审计报告生成服务
生成符合监管要求的PDF审计报告
"""
import io
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from ..database import get_db_connection

logger = logging.getLogger(__name__)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available, PDF generation disabled")


ACTION_TYPE_LABELS = {
    "LOGIN": "登录",
    "LOGOUT": "登出",
    "LOGIN_FAILED": "登录失败",
    "REGISTER": "注册",
    "PASSWORD_CHANGE": "修改密码",
    "PROFILE_UPDATE": "更新资料",
    "TASK_CREATE": "创建任务",
    "TASK_VIEW": "查看任务",
    "TASK_UPDATE": "更新任务",
    "TASK_DELETE": "删除任务",
    "TASK_ASSIGN": "分配任务",
    "REPORT_CREATE": "创建报告",
    "REPORT_VIEW": "查看报告",
    "REPORT_EXPORT": "导出报告",
    "REPORT_DELETE": "删除报告",
    "REPORT_SHARE": "分享报告",
    "TEAM_CREATE": "创建团队",
    "TEAM_JOIN": "加入团队",
    "TEAM_LEAVE": "离开团队",
    "TEAM_MEMBER_ADD": "添加成员",
    "TEAM_MEMBER_REMOVE": "移除成员",
    "TEAM_DELETE": "删除团队",
    "FEEDBACK_CREATE": "创建反馈",
    "FEEDBACK_REPLY": "回复反馈",
    "ADMIN_USER_VIEW": "查看用户",
    "ADMIN_USER_CREATE": "创建用户",
    "ADMIN_USER_UPDATE": "更新用户",
    "ADMIN_USER_DELETE": "删除用户",
    "ADMIN_SETTING_CHANGE": "修改设置",
    "ADMIN_ANNOUNCEMENT_CREATE": "创建公告",
    "ADMIN_ANNOUNCEMENT_PUBLISH": "发布公告",
    "DATA_EXPORT": "数据导出",
    "DATA_IMPORT": "数据导入",
    "API_ACCESS": "API访问",
    "FILE_UPLOAD": "文件上传",
    "FILE_DOWNLOAD": "文件下载",
    "PRIVACY_CONSENT": "隐私同意",
}


class AuditReportGenerator:
    def __init__(self):
        if REPORTLAB_AVAILABLE:
            self.width, self.height = A4
            self.styles = getSampleStyleSheet()
            self._setup_styles()
        else:
            self.width, self.height = 595, 842
            self.styles = None
    
    def _setup_styles(self):
        if not REPORTLAB_AVAILABLE:
            return
        
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#1a56db'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6b7280'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f2937'),
            spaceBefore=20,
            spaceAfter=10,
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubSectionTitle',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#374151'),
            spaceBefore=15,
            spaceAfter=8,
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
        ))
    
    async def generate_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None,
        action_types: Optional[List[str]] = None,
        include_logs: bool = True,
        generated_by: Optional[str] = None,
    ) -> bytes:
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab library not installed")
        
        report_data = await self._collect_report_data(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            action_types=action_types,
        )
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        story = []
        
        story.extend(self._create_cover_page(
            start_date=start_date,
            end_date=end_date,
            generated_by=generated_by,
        ))
        story.append(PageBreak())
        
        story.extend(self._create_summary_section(report_data))
        story.append(PageBreak())
        
        story.extend(self._create_statistics_section(report_data))
        
        if include_logs and report_data.get("logs"):
            story.append(PageBreak())
            story.extend(self._create_logs_section(report_data["logs"]))
        
        story.append(PageBreak())
        story.extend(self._create_verification_section(report_data))
        
        story.extend(self._create_footer_section())
        
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    async def _collect_report_data(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        user_id: Optional[str],
        action_types: Optional[List[str]],
    ) -> Dict[str, Any]:
        conn = await get_db_connection()
        try:
            conditions = []
            params = []
            
            if start_date:
                conditions.append("DATE(timestamp) >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("DATE(timestamp) <= ?")
                params.append(end_date)
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            if action_types:
                placeholders = ",".join("?" * len(action_types))
                conditions.append(f"action_type IN ({placeholders})")
                params.extend(action_types)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            cursor = await conn.execute(f"""
                SELECT COUNT(*) as count FROM audit_logs {where_clause}
            """, params)
            total_logs = (await cursor.fetchone())["count"]
            
            cursor = await conn.execute(f"""
                SELECT action_type, COUNT(*) as count
                FROM audit_logs {where_clause}
                GROUP BY action_type
                ORDER BY count DESC
            """, params)
            action_distribution = [dict(row) for row in await cursor.fetchall()]
            
            cursor = await conn.execute(f"""
                SELECT user_id, username, COUNT(*) as count
                FROM audit_logs {where_clause}
                AND user_id IS NOT NULL
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 20
            """, params)
            user_distribution = [dict(row) for row in await cursor.fetchall()]
            
            cursor = await conn.execute(f"""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM audit_logs {where_clause}
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, params)
            daily_trend = [dict(row) for row in await cursor.fetchall()]
            
            cursor = await conn.execute(f"""
                SELECT status, COUNT(*) as count
                FROM audit_logs {where_clause}
                GROUP BY status
            """, params)
            status_distribution = {row["status"]: row["count"] for row in await cursor.fetchall()}
            
            cursor = await conn.execute(f"""
                SELECT * FROM audit_logs {where_clause}
                ORDER BY timestamp DESC
                LIMIT 100
            """, params)
            logs = [dict(row) for row in await cursor.fetchall()]
            
            cursor = await conn.execute("""
                SELECT * FROM audit_verifications
                ORDER BY verification_time DESC
                LIMIT 1
            """)
            last_verification = await cursor.fetchone()
            
            cursor = await conn.execute(f"""
                SELECT COUNT(*) as count FROM anomaly_alerts
                WHERE status = 'open'
            """)
            open_alerts = (await cursor.fetchone())["count"]
            
            return {
                "total_logs": total_logs,
                "action_distribution": action_distribution,
                "user_distribution": user_distribution,
                "daily_trend": daily_trend,
                "status_distribution": status_distribution,
                "logs": logs,
                "last_verification": dict(last_verification) if last_verification else None,
                "open_alerts": open_alerts,
            }
        finally:
            await conn.close()
    
    def _create_cover_page(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        generated_by: Optional[str],
    ) -> List:
        elements = []
        
        elements.append(Spacer(1, 3*inch))
        
        elements.append(Paragraph(
            "审计日志报告",
            self.styles['CoverTitle']
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph(
            "Audit Log Report",
            self.styles['CoverSubtitle']
        ))
        
        elements.append(Spacer(1, 1*inch))
        
        elements.append(HRFlowable(
            width="60%",
            thickness=2,
            color=colors.HexColor('#1a56db'),
            spaceBefore=10,
            spaceAfter=10,
        ))
        
        elements.append(Spacer(1, 1*inch))
        
        time_range = "全部时间"
        if start_date and end_date:
            time_range = f"{start_date} 至 {end_date}"
        elif start_date:
            time_range = f"{start_date} 至今"
        elif end_date:
            time_range = f"至 {end_date}"
        
        cover_info = [
            ["报告生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["审计时间范围", time_range],
            ["生成人", generated_by or "系统管理员"],
            ["报告类型", "合规审计报告"],
        ]
        
        cover_table = Table(cover_info, colWidths=[3*cm, 8*cm])
        cover_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(cover_table)
        
        elements.append(Spacer(1, 2*inch))
        
        elements.append(Paragraph(
            "房都督AI - 智能房产分析平台",
            self.styles['CoverSubtitle']
        ))
        
        return elements
    
    def _create_summary_section(self, data: Dict) -> List:
        elements = []
        
        elements.append(Paragraph("一、统计摘要", self.styles['SectionTitle']))
        
        summary_data = [
            ["指标", "数值"],
            ["总日志数", f"{data['total_logs']:,}"],
            ["成功操作", f"{data['status_distribution'].get('success', 0):,}"],
            ["失败操作", f"{data['status_distribution'].get('failure', 0):,}"],
            ["独立用户数", f"{len(data['user_distribution']):,}"],
            ["操作类型数", f"{len(data['action_distribution']):,}"],
            ["待处理告警", f"{data['open_alerts']:,}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a56db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        
        return elements
    
    def _create_statistics_section(self, data: Dict) -> List:
        elements = []
        
        elements.append(Paragraph("二、操作类型分布", self.styles['SectionTitle']))
        
        if data['action_distribution']:
            action_data = [["操作类型", "次数", "占比"]]
            total = sum(item['count'] for item in data['action_distribution'])
            
            for item in data['action_distribution'][:15]:
                label = ACTION_TYPE_LABELS.get(item['action_type'], item['action_type'])
                percentage = f"{(item['count'] / total * 100):.1f}%" if total > 0 else "0%"
                action_data.append([label, f"{item['count']:,}", percentage])
            
            action_table = Table(action_data, colWidths=[5*cm, 3*cm, 2*cm])
            action_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(action_table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph("三、活跃用户 TOP 20", self.styles['SectionTitle']))
        
        if data['user_distribution']:
            user_data = [["用户", "操作次数"]]
            for item in data['user_distribution']:
                username = item.get('username') or item.get('user_id', '匿名')[:20]
                user_data.append([username, f"{item['count']:,}"])
            
            user_table = Table(user_data, colWidths=[6*cm, 4*cm])
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(user_table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph("四、每日趋势", self.styles['SectionTitle']))
        
        if data['daily_trend']:
            trend_data = [["日期", "日志数"]]
            for item in data['daily_trend'][-30:]:
                trend_data.append([item['date'], f"{item['count']:,}"])
            
            trend_table = Table(trend_data, colWidths=[4*cm, 3*cm])
            trend_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(trend_table)
        
        return elements
    
    def _create_logs_section(self, logs: List[Dict]) -> List:
        elements = []
        
        elements.append(Paragraph("五、日志明细（最近100条）", self.styles['SectionTitle']))
        
        log_data = [["时间", "用户", "操作", "资源", "状态"]]
        
        for log in logs:
            timestamp = log.get('timestamp', '')[:16] if log.get('timestamp') else '-'
            user = (log.get('username') or log.get('user_id') or '匿名')[:12]
            action = ACTION_TYPE_LABELS.get(log.get('action_type', ''), log.get('action_type', ''))[:10]
            resource = f"{log.get('resource_type', '')[:6]}:{(log.get('resource_id') or '')[:8]}" if log.get('resource_type') else '-'
            status = "成功" if log.get('status') == 'success' else "失败"
            
            log_data.append([timestamp, user, action, resource, status])
        
        log_table = Table(log_data, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 3*cm, 1.5*cm])
        log_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(log_table)
        
        return elements
    
    def _create_verification_section(self, data: Dict) -> List:
        elements = []
        
        elements.append(Paragraph("六、完整性验证", self.styles['SectionTitle']))
        
        verification = data.get('last_verification')
        
        if verification:
            status = verification.get('status', 'unknown')
            status_text = {
                'valid': '验证通过',
                'invalid': '验证失败',
                'warning': '存在警告',
            }.get(status, status)
            
            status_color = {
                'valid': colors.HexColor('#10b981'),
                'invalid': colors.HexColor('#ef4444'),
                'warning': colors.HexColor('#f59e0b'),
            }.get(status, colors.HexColor('#6b7280'))
            
            verify_data = [
                ["验证项目", "结果"],
                ["验证状态", status_text],
                ["验证时间", verification.get('verification_time', '-')[:19]],
                ["总日志数", f"{verification.get('total_logs', 0):,}"],
                ["验证通过数", f"{verification.get('verified_logs', 0):,}"],
                ["哈希错误", f"{verification.get('hash_errors', 0):,}"],
                ["链断裂", f"{verification.get('chain_errors', 0):,}"],
                ["完整性评分", f"{verification.get('integrity_score', 0):.1f}%"],
            ]
        else:
            verify_data = [
                ["验证项目", "结果"],
                ["验证状态", "暂无验证记录"],
                ["建议", "请执行日志完整性验证"],
            ]
        
        verify_table = Table(verify_data, colWidths=[5*cm, 8*cm])
        verify_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(verify_table)
        
        return elements
    
    def _create_footer_section(self) -> List:
        elements = []
        
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e5e7eb'),
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"房都督AI审计系统 | 本报告由系统自动生成",
            ParagraphStyle(
                name='Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#9ca3af'),
                alignment=TA_CENTER,
            )
        ))
        
        return elements


report_generator = AuditReportGenerator()
