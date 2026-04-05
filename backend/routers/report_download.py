"""
报告下载接口 - 支持MD/ZIP下载
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from typing import Optional
import io
import zipfile
import os
from datetime import datetime

from ..auth import get_current_user
from ..database import get_db_connection
from ..services.md_report_generator import md_report_generator

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportDownloadRequest(BaseModel):
    report_id: str
    format: str = 'md'


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = 'md',
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """SELECT id, user_id, community_name, result, created_at 
               FROM analysis_tasks 
               WHERE id = ? AND user_id = ?""",
            (report_id, user_id)
        )
        task = await cursor.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        community_name = task[2] or "房产分析报告"
        user_name = current_user.get("username", "用户")
        
        md_content = md_report_generator.generate_report(
            community_name=community_name,
            user_name=user_name,
            persona="周瑜",
            data={"task_id": report_id}
        )
        
        css_content = load_css_template()
        csv_content = md_report_generator.generate_csv({"community_name": community_name})
        
        if format == 'md':
            return Response(
                content=md_content.encode('utf-8'),
                media_type='text/markdown',
                headers={
                    'Content-Disposition': f'attachment; filename="{community_name}_报告.md"'
                }
            )
        
        elif format == 'zip':
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f'{community_name}_报告.md', md_content.encode('utf-8'))
                zf.writestr('report.css', css_content.encode('utf-8'))
                zf.writestr(f'{community_name}_数据.csv', csv_content.encode('utf-8'))
                zf.writestr('README.txt', f"""房都督房产分析报告
==================

报告名称：{community_name}
生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
用户：{user_name}

文件说明：
- {community_name}_报告.md：Markdown格式报告（可用Typora、VS Code等打开）
- report.css：样式文件（用于打印预览）
- {community_name}_数据.csv：核心数据表格

转换指南：
1. PDF转换：用Typora打开MD文件，选择"文件" > "导出" > "PDF"
2. Word转换：用Pandoc命令：pandoc 报告.md -o 报告.docx
3. 在线转换：访问 https://dillinger.io/ 或 https://stackedit.io/

更多帮助请访问：https://fangdudu.com/help/report-conversion
""".encode('utf-8'))
            
            zip_buffer.seek(0)
            
            return Response(
                content=zip_buffer.getvalue(),
                media_type='application/zip',
                headers={
                    'Content-Disposition': f'attachment; filename="{community_name}_报告.zip"'
                }
            )
        
        elif format == 'csv':
            return Response(
                content=csv_content.encode('utf-8'),
                media_type='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename="{community_name}_数据.csv"'
                }
            )
        
        elif format == 'html':
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{community_name} - 房产分析报告</title>
    <link rel="stylesheet" href="/static/report.css">
    <style>
        body {{
            font-family: 'Inter', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        h1 {{ color: #0A1A2F; border-bottom: 3px solid #D4AF37; padding-bottom: 15px; }}
        h2 {{ color: #2C5530; margin-top: 40px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background-color: #0A1A2F; color: #fff; padding: 12px; }}
        td {{ border: 1px solid #e5e7eb; padding: 10px; }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="position: fixed; top: 20px; right: 20px; background: #D4AF37; padding: 10px 20px; border-radius: 8px;">
        <button onclick="window.print()" style="background: none; border: none; cursor: pointer; font-size: 16px;">
            🖨️ 打印为PDF
        </button>
    </div>
    {markdown_to_html(md_content)}
</body>
</html>"""
            
            return Response(
                content=html_content.encode('utf-8'),
                media_type='text/html',
                headers={
                    'Content-Disposition': f'inline; filename="{community_name}_报告.html"'
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="不支持的格式")
            
    finally:
        await conn.close()


def load_css_template() -> str:
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'report.css')
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return """body { font-family: 'Inter', sans-serif; line-height: 1.6; color: #333; }
h1 { color: #0A1A2F; border-bottom: 2px solid #D4AF37; }
h2 { color: #2C5530; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; }
th { background-color: #f2f2f2; }"""


def markdown_to_html(md_content: str) -> str:
    lines = md_content.split('\n')
    html_lines = []
    in_table = False
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('# '):
            html_lines.append(f'<h1>{stripped[2:]}</h1>')
        elif stripped.startswith('## '):
            html_lines.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith('### '):
            html_lines.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith('#### '):
            html_lines.append(f'<h4>{stripped[5:]}</h4>')
        elif stripped.startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{stripped[2:]}</li>')
        elif stripped.startswith('| '):
            if not in_table:
                html_lines.append('<table>')
                in_table = True
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if all(c.replace('-', '').replace(':', '') == '' for c in cells):
                continue
            cell_tag = 'th' if html_lines[-2].startswith('<table>') else 'td'
            row = '<tr>' + ''.join(f'<{cell_tag}>{c}</{cell_tag}>' for c in cells) + '</tr>'
            html_lines.append(row)
        elif stripped.startswith('---'):
            html_lines.append('<hr>')
        elif stripped == '':
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_table:
                html_lines.append('</table>')
                in_table = False
            html_lines.append('<br>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_table:
                html_lines.append('</table>')
                in_table = False
            html_lines.append(f'<p>{stripped}</p>')
    
    if in_list:
        html_lines.append('</ul>')
    if in_table:
        html_lines.append('</table>')
    
    return '\n'.join(html_lines)


@router.get("/{report_id}/preview")
async def preview_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    return await download_report(report_id, 'html', current_user)
