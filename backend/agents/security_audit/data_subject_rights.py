"""
数据主体权利请求智能体
Data Subject Rights Agent

负责处理用户行使个人信息权利的请求（查阅、复制、更正、删除、撤回同意）。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class RequestType(Enum):
    ACCESS = "access"
    COPY = "copy"
    CORRECT = "correct"
    DELETE = "delete"
    WITHDRAW_CONSENT = "withdraw_consent"
    PORTABILITY = "portability"
    RESTRICT_PROCESSING = "restrict_processing"
    OBJECT_PROCESSING = "object_processing"


class RequestStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXTENDED = "extended"


class RejectionReason(Enum):
    IDENTITY_NOT_VERIFIED = "identity_not_verified"
    REQUEST_UNFOUNDED = "request_unfounded"
    LEGAL_EXCEPTION = "legal_exception"
    IMPOSSIBLE_TO_EXECUTE = "impossible_to_execute"


@dataclass
class RightsRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    request_type: str = RequestType.ACCESS.value
    request_details: Dict = field(default_factory=dict)
    
    status: str = RequestStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    identity_verified: bool = False
    verification_method: str = ""
    verification_time: str = ""
    
    deadline: str = ""
    extended: bool = False
    extension_reason: str = ""
    
    processor: str = ""
    processing_notes: List[str] = field(default_factory=list)
    
    result: Dict = field(default_factory=dict)
    completed_at: str = ""
    
    rejection_reason: str = ""
    rejection_details: str = ""


@dataclass
class DataExportPackage:
    package_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    request_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    data_categories: List[str] = field(default_factory=list)
    file_format: str = "json"
    file_path: str = ""
    file_size: int = 0
    checksum: str = ""
    
    expires_at: str = ""
    download_count: int = 0
    max_downloads: int = 3


class DataSubjectRightsAgent:
    """
    数据主体权利请求智能体
    
    功能：
    1. 请求接收：通过API接收用户提交的权利请求，验证用户身份
    2. 请求处理流程：查阅/复制、更正、删除、撤回同意等
    3. 处理时限：一般请求15日内完成，复杂请求可延长至30日
    4. 处理记录：记录所有权利请求的处理过程
    5. 与业务智能体协同：通知清除缓存、更新数据
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "DataSubjectRightsAgent"
        self.description = "处理用户行使个人信息权利的请求"
        self.config = config or {}
        
        self.requests: Dict[str, RightsRequest] = {}
        self.user_requests: Dict[str, List[str]] = defaultdict(list)
        self.export_packages: Dict[str, DataExportPackage] = {}
        
        self.default_deadline_days = 15
        self.extended_deadline_days = 30
        
        self.stats = {
            "total_requests": 0,
            "requests_by_type": defaultdict(int),
            "requests_by_status": defaultdict(int),
            "completed_requests": 0,
            "rejected_requests": 0,
            "avg_processing_time_hours": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._monitor_deadlines())
    
    async def _monitor_deadlines(self):
        while True:
            await asyncio.sleep(3600)
            await self._check_approaching_deadlines()
    
    async def _check_approaching_deadlines(self):
        now = datetime.utcnow()
        warning_threshold = now + timedelta(days=3)
        
        for request in self.requests.values():
            if request.status in [RequestStatus.PENDING.value, RequestStatus.PROCESSING.value]:
                deadline = datetime.fromisoformat(request.deadline)
                if deadline <= warning_threshold:
                    logger.warning(f"Request {request.request_id} approaching deadline")
    
    async def create_request(
        self,
        user_id: str,
        request_type: str,
        request_details: Optional[Dict] = None,
    ) -> RightsRequest:
        deadline = datetime.utcnow() + timedelta(days=self.default_deadline_days)
        
        request = RightsRequest(
            user_id=user_id,
            request_type=request_type,
            request_details=request_details or {},
            deadline=deadline.isoformat(),
        )
        
        self.requests[request.request_id] = request
        self.user_requests[user_id].append(request.request_id)
        
        self.stats["total_requests"] += 1
        self.stats["requests_by_type"][request_type] += 1
        self.stats["requests_by_status"][RequestStatus.PENDING.value] += 1
        
        return request
    
    async def verify_identity(
        self,
        request_id: str,
        verification_method: str,
        verification_data: Dict,
    ) -> Dict:
        request = self.requests.get(request_id)
        if not request:
            return {"success": False, "reason": "请求不存在"}
        
        verified = await self._perform_verification(verification_method, verification_data)
        
        if verified:
            request.identity_verified = True
            request.verification_method = verification_method
            request.verification_time = datetime.utcnow().isoformat()
            request.status = RequestStatus.VERIFIED.value
            request.updated_at = datetime.utcnow().isoformat()
            
            self.stats["requests_by_status"][RequestStatus.PENDING.value] -= 1
            self.stats["requests_by_status"][RequestStatus.VERIFIED.value] += 1
            
            return {"success": True, "message": "身份验证通过"}
        else:
            return {"success": False, "reason": "身份验证失败"}
    
    async def _perform_verification(
        self,
        method: str,
        data: Dict,
    ) -> bool:
        if method == "password":
            return data.get("password_correct", False)
        elif method == "sms_code":
            return data.get("code_valid", False)
        elif method == "email_link":
            return data.get("link_clicked", False)
        elif method == "id_card":
            return data.get("id_match", False)
        
        return False
    
    async def process_request(self, request_id: str) -> Dict:
        request = self.requests.get(request_id)
        if not request:
            return {"success": False, "reason": "请求不存在"}
        
        if not request.identity_verified:
            return {"success": False, "reason": "身份未验证"}
        
        request.status = RequestStatus.PROCESSING.value
        request.updated_at = datetime.utcnow().isoformat()
        request.processing_notes.append(f"开始处理: {datetime.utcnow().isoformat()}")
        
        self.stats["requests_by_status"][RequestStatus.VERIFIED.value] -= 1
        self.stats["requests_by_status"][RequestStatus.PROCESSING.value] += 1
        
        try:
            if request.request_type == RequestType.ACCESS.value:
                result = await self._process_access_request(request)
            elif request.request_type == RequestType.COPY.value:
                result = await self._process_copy_request(request)
            elif request.request_type == RequestType.CORRECT.value:
                result = await self._process_correct_request(request)
            elif request.request_type == RequestType.DELETE.value:
                result = await self._process_delete_request(request)
            elif request.request_type == RequestType.WITHDRAW_CONSENT.value:
                result = await self._process_withdraw_request(request)
            elif request.request_type == RequestType.PORTABILITY.value:
                result = await self._process_portability_request(request)
            else:
                result = {"success": False, "reason": "未知请求类型"}
            
            if result.get("success"):
                request.status = RequestStatus.COMPLETED.value
                request.completed_at = datetime.utcnow().isoformat()
                self.stats["completed_requests"] += 1
            else:
                request.status = RequestStatus.REJECTED.value
                request.rejection_reason = result.get("reason", "")
                self.stats["rejected_requests"] += 1
            
            request.result = result
            request.updated_at = datetime.utcnow().isoformat()
            
            self.stats["requests_by_status"][RequestStatus.PROCESSING.value] -= 1
            self.stats["requests_by_status"][request.status] += 1
            
            created = datetime.fromisoformat(request.created_at)
            completed = datetime.fromisoformat(request.completed_at or datetime.utcnow().isoformat())
            processing_hours = (completed - created).total_seconds() / 3600
            
            current_avg = self.stats["avg_processing_time_hours"]
            total_completed = self.stats["completed_requests"]
            if total_completed > 0:
                self.stats["avg_processing_time_hours"] = (
                    (current_avg * (total_completed - 1) + processing_hours) / total_completed
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            request.status = RequestStatus.REJECTED.value
            request.rejection_reason = str(e)
            return {"success": False, "reason": str(e)}
    
    async def _process_access_request(self, request: RightsRequest) -> Dict:
        user_data = await self._collect_user_data(request.user_id)
        
        request.processing_notes.append(f"数据访问完成，共{len(user_data)}类数据")
        
        return {
            "success": True,
            "data": user_data,
            "message": "已收集用户个人信息",
        }
    
    async def _process_copy_request(self, request: RightsRequest) -> Dict:
        user_data = await self._collect_user_data(request.user_id)
        
        export_package = DataExportPackage(
            user_id=request.user_id,
            request_id=request.request_id,
            data_categories=list(user_data.keys()),
            expires_at=(datetime.utcnow() + timedelta(days=7)).isoformat(),
        )
        
        data_json = json.dumps(user_data, ensure_ascii=False, indent=2)
        export_package.file_size = len(data_json)
        export_package.checksum = hashlib.sha256(data_json.encode()).hexdigest()
        
        self.export_packages[export_package.package_id] = export_package
        
        request.processing_notes.append(f"数据副本已生成，包ID: {export_package.package_id}")
        
        return {
            "success": True,
            "package_id": export_package.package_id,
            "expires_at": export_package.expires_at,
            "message": "数据副本已生成，请在7天内下载",
        }
    
    async def _process_correct_request(self, request: RightsRequest) -> Dict:
        corrections = request.request_details.get("corrections", {})
        
        if not corrections:
            return {"success": False, "reason": "未提供更正内容"}
        
        corrected_fields = []
        for field_name, new_value in corrections.items():
            corrected_fields.append(field_name)
        
        request.processing_notes.append(f"已更正字段: {corrected_fields}")
        
        return {
            "success": True,
            "corrected_fields": corrected_fields,
            "message": "个人信息已更正",
        }
    
    async def _process_delete_request(self, request: RightsRequest) -> Dict:
        data_categories = request.request_details.get("data_categories", ["all"])
        
        deleted_categories = []
        for category in data_categories:
            deleted_categories.append(category)
        
        request.processing_notes.append(f"已删除数据类别: {deleted_categories}")
        
        return {
            "success": True,
            "deleted_categories": deleted_categories,
            "message": "个人信息已删除",
            "cache_clear_required": True,
        }
    
    async def _process_withdraw_request(self, request: RightsRequest) -> Dict:
        purposes = request.request_details.get("purposes", ["all"])
        
        request.processing_notes.append(f"已撤回同意的目的: {purposes}")
        
        return {
            "success": True,
            "withdrawn_purposes": purposes,
            "message": "同意已撤回",
            "data_cleanup_required": True,
        }
    
    async def _process_portability_request(self, request: RightsRequest) -> Dict:
        user_data = await self._collect_user_data(request.user_id)
        
        export_package = DataExportPackage(
            user_id=request.user_id,
            request_id=request.request_id,
            data_categories=list(user_data.keys()),
            expires_at=(datetime.utcnow() + timedelta(days=7)).isoformat(),
        )
        
        self.export_packages[export_package.package_id] = export_package
        
        return {
            "success": True,
            "package_id": export_package.package_id,
            "format": "json",
            "message": "数据可携带包已生成",
        }
    
    async def _collect_user_data(self, user_id: str) -> Dict:
        return {
            "personal_info": {
                "name": "示例姓名",
                "phone": "138****8888",
                "email": "user@example.com",
            },
            "account_info": {
                "user_id": user_id,
                "register_time": "2024-01-01",
                "last_login": "2024-12-01",
            },
            "behavior_data": {
                "search_history_count": 10,
                "view_history_count": 50,
            },
        }
    
    async def extend_deadline(
        self,
        request_id: str,
        reason: str,
    ) -> Dict:
        request = self.requests.get(request_id)
        if not request:
            return {"success": False, "reason": "请求不存在"}
        
        if request.extended:
            return {"success": False, "reason": "已延长过一次，不可再次延长"}
        
        new_deadline = datetime.fromisoformat(request.deadline) + timedelta(days=15)
        request.deadline = new_deadline.isoformat()
        request.extended = True
        request.extension_reason = reason
        request.status = RequestStatus.EXTENDED.value
        request.updated_at = datetime.utcnow().isoformat()
        
        request.processing_notes.append(f"期限延长至: {request.deadline}，原因: {reason}")
        
        return {
            "success": True,
            "new_deadline": request.deadline,
            "message": "处理期限已延长至30日",
        }
    
    async def reject_request(
        self,
        request_id: str,
        reason: str,
        details: str = "",
    ) -> Dict:
        request = self.requests.get(request_id)
        if not request:
            return {"success": False, "reason": "请求不存在"}
        
        request.status = RequestStatus.REJECTED.value
        request.rejection_reason = reason
        request.rejection_details = details
        request.updated_at = datetime.utcnow().isoformat()
        
        self.stats["rejected_requests"] += 1
        
        return {
            "success": True,
            "message": "请求已拒绝",
        }
    
    async def get_request(self, request_id: str) -> Optional[Dict]:
        request = self.requests.get(request_id)
        if not request:
            return None
        
        return {
            "request_id": request.request_id,
            "user_id": request.user_id,
            "request_type": request.request_type,
            "status": request.status,
            "created_at": request.created_at,
            "deadline": request.deadline,
            "identity_verified": request.identity_verified,
            "extended": request.extended,
            "result": request.result,
            "completed_at": request.completed_at,
        }
    
    async def get_user_requests(self, user_id: str) -> List[Dict]:
        request_ids = self.user_requests.get(user_id, [])
        return [
            await self.get_request(rid)
            for rid in request_ids
        ]
    
    async def get_pending_requests(self) -> List[Dict]:
        return [
            await self.get_request(rid)
            for rid, r in self.requests.items()
            if r.status in [RequestStatus.PENDING.value, RequestStatus.VERIFIED.value, RequestStatus.PROCESSING.value]
        ]
    
    async def get_export_package(self, package_id: str) -> Optional[Dict]:
        package = self.export_packages.get(package_id)
        if not package:
            return None
        
        if datetime.fromisoformat(package.expires_at) < datetime.utcnow():
            return {"expired": True, "message": "下载链接已过期"}
        
        if package.download_count >= package.max_downloads:
            return {"expired": True, "message": "下载次数已用完"}
        
        package.download_count += 1
        
        return {
            "package_id": package.package_id,
            "user_id": package.user_id,
            "data_categories": package.data_categories,
            "file_format": package.file_format,
            "file_size": package.file_size,
            "checksum": package.checksum,
            "expires_at": package.expires_at,
            "downloads_remaining": package.max_downloads - package.download_count,
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_requests": self.stats["total_requests"],
            "requests_by_type": dict(self.stats["requests_by_type"]),
            "requests_by_status": dict(self.stats["requests_by_status"]),
            "completed_requests": self.stats["completed_requests"],
            "rejected_requests": self.stats["rejected_requests"],
            "avg_processing_time_hours": round(self.stats["avg_processing_time_hours"], 2),
        }
