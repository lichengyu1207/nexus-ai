"""
数据跨境流动审计智能体
Data Cross-Border Audit Agent

负责监控数据是否被传输到境外，并检查是否符合跨境合规要求。
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


class TransferType(Enum):
    API_CALL = "api_call"
    DATA_STORAGE = "data_storage"
    THIRD_PARTY_SERVICE = "third_party_service"
    EMPLOYEE_ACCESS = "employee_access"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_ASSESSMENT = "pending_assessment"
    EXEMPT = "exempt"


class RiskLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CrossBorderTransfer:
    transfer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    transfer_type: str = TransferType.API_CALL.value
    source_location: str = "CN"
    destination_location: str = ""
    destination_country: str = ""
    
    data_types: List[str] = field(default_factory=list)
    data_volume: int = 0
    data_subjects_count: int = 0
    
    purpose: str = ""
    recipient: str = ""
    recipient_type: str = ""
    
    compliance_status: str = ComplianceStatus.PENDING_ASSESSMENT.value
    security_assessment_passed: bool = False
    standard_contract_signed: bool = False
    user_consent_obtained: bool = False
    
    is_exempt: bool = False
    exemption_reason: str = ""
    
    risk_level: str = RiskLevel.MEDIUM.value
    blocked: bool = False
    block_reason: str = ""


@dataclass
class CountryDataProtection:
    country_code: str = ""
    country_name: str = ""
    protection_level: str = ""
    adequacy_decision: bool = False
    notes: str = ""
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class DataCrossBorderAuditAgent:
    """
    数据跨境流动审计智能体
    
    功能：
    1. 监控范围：API调用、数据存储、第三方服务、员工访问
    2. 合规要求检查：安全评估、用户同意、标准合同、豁免情形
    3. 告警机制：未经批准的跨境传输立即告警，可配置阻断
    4. 审计记录：记录所有跨境数据传输日志
    5. 知识库：维护各国数据保护水平清单
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "DataCrossBorderAuditAgent"
        self.description = "监控数据跨境传输并检查合规要求"
        self.config = config or {}
        
        self.transfers: Dict[str, CrossBorderTransfer] = {}
        self.country_protection_levels: Dict[str, CountryDataProtection] = {}
        
        self.block_non_compliant = self.config.get("block_non_compliant", True)
        
        self._init_country_protection_levels()
        
        self.stats = {
            "total_transfers": 0,
            "transfers_by_type": defaultdict(int),
            "transfers_by_destination": defaultdict(int),
            "compliant_transfers": 0,
            "non_compliant_transfers": 0,
            "blocked_transfers": 0,
            "transfers_by_risk": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_country_protection_levels(self):
        countries = [
            CountryDataProtection(
                country_code="EU",
                country_name="欧盟",
                protection_level="adequate",
                adequacy_decision=True,
                notes="GDPR保护水平，中国已认定",
            ),
            CountryDataProtection(
                country_code="US",
                country_name="美国",
                protection_level="partial",
                adequacy_decision=False,
                notes="需签订标准合同",
            ),
            CountryDataProtection(
                country_code="JP",
                country_name="日本",
                protection_level="adequate",
                adequacy_decision=True,
                notes="APPI保护水平",
            ),
            CountryDataProtection(
                country_code="KR",
                country_name="韩国",
                protection_level="adequate",
                adequacy_decision=True,
                notes="PIPA保护水平",
            ),
            CountryDataProtection(
                country_code="SG",
                country_name="新加坡",
                protection_level="adequate",
                adequacy_decision=True,
                notes="PDPA保护水平",
            ),
            CountryDataProtection(
                country_code="HK",
                country_name="香港",
                protection_level="adequate",
                adequacy_decision=True,
                notes="PDPO保护水平",
            ),
            CountryDataProtection(
                country_code="OTHER",
                country_name="其他",
                protection_level="unknown",
                adequacy_decision=False,
                notes="需要安全评估",
            ),
        ]
        
        for country in countries:
            self.country_protection_levels[country.country_code] = country
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def record_transfer(
        self,
        transfer_type: str,
        destination_country: str,
        data_types: List[str],
        data_volume: int = 0,
        data_subjects_count: int = 0,
        purpose: str = "",
        recipient: str = "",
        recipient_type: str = "",
    ) -> CrossBorderTransfer:
        transfer = CrossBorderTransfer(
            transfer_type=transfer_type,
            destination_country=destination_country,
            destination_location=destination_country,
            data_types=data_types,
            data_volume=data_volume,
            data_subjects_count=data_subjects_count,
            purpose=purpose,
            recipient=recipient,
            recipient_type=recipient_type,
        )
        
        await self._assess_compliance(transfer)
        
        if transfer.compliance_status == ComplianceStatus.NON_COMPLIANT.value and self.block_non_compliant:
            transfer.blocked = True
            transfer.block_reason = "跨境传输不符合合规要求"
            self.stats["blocked_transfers"] += 1
        
        self.transfers[transfer.transfer_id] = transfer
        
        self.stats["total_transfers"] += 1
        self.stats["transfers_by_type"][transfer_type] += 1
        self.stats["transfers_by_destination"][destination_country] += 1
        self.stats["transfers_by_risk"][transfer.risk_level] += 1
        
        if transfer.compliance_status == ComplianceStatus.COMPLIANT.value:
            self.stats["compliant_transfers"] += 1
        elif transfer.compliance_status == ComplianceStatus.NON_COMPLIANT.value:
            self.stats["non_compliant_transfers"] += 1
        
        return transfer
    
    async def _assess_compliance(self, transfer: CrossBorderTransfer):
        country_info = self.country_protection_levels.get(
            transfer.destination_country,
            self.country_protection_levels.get("OTHER")
        )
        
        if transfer.is_exempt:
            transfer.compliance_status = ComplianceStatus.EXEMPT.value
            transfer.risk_level = RiskLevel.LOW.value
            return
        
        if country_info and country_info.adequacy_decision:
            transfer.risk_level = RiskLevel.LOW.value
            if transfer.user_consent_obtained:
                transfer.compliance_status = ComplianceStatus.COMPLIANT.value
                return
        
        if transfer.data_subjects_count >= 100000:
            transfer.risk_level = RiskLevel.HIGH.value
            if not transfer.security_assessment_passed:
                transfer.compliance_status = ComplianceStatus.NON_COMPLIANT.value
                return
        
        if transfer.security_assessment_passed:
            transfer.compliance_status = ComplianceStatus.COMPLIANT.value
            transfer.risk_level = RiskLevel.LOW.value
            return
        
        if transfer.standard_contract_signed and transfer.user_consent_obtained:
            transfer.compliance_status = ComplianceStatus.COMPLIANT.value
            transfer.risk_level = RiskLevel.MEDIUM.value
            return
        
        if transfer.standard_contract_signed:
            transfer.compliance_status = ComplianceStatus.PENDING_ASSESSMENT.value
            transfer.risk_level = RiskLevel.MEDIUM.value
            return
        
        transfer.compliance_status = ComplianceStatus.NON_COMPLIANT.value
        transfer.risk_level = RiskLevel.HIGH.value
    
    async def check_exemption(
        self,
        transfer: CrossBorderTransfer,
        exemption_type: str,
    ) -> bool:
        exemptions = {
            "contract_necessary": lambda t: t.purpose == "履行合同必要",
            "legal_obligation": lambda t: t.purpose == "法定义务",
            "vital_interests": lambda t: t.purpose == "保护生命",
            "public_interest": lambda t: t.purpose == "公共利益",
        }
        
        checker = exemptions.get(exemption_type)
        if checker and checker(transfer):
            transfer.is_exempt = True
            transfer.exemption_reason = exemption_type
            return True
        
        return False
    
    async def record_security_assessment(
        self,
        transfer_id: str,
        passed: bool,
        assessment_report: Optional[Dict] = None,
    ) -> bool:
        transfer = self.transfers.get(transfer_id)
        if not transfer:
            return False
        
        transfer.security_assessment_passed = passed
        
        if passed:
            await self._assess_compliance(transfer)
        
        return True
    
    async def record_standard_contract(
        self,
        transfer_id: str,
        signed: bool,
        contract_details: Optional[Dict] = None,
    ) -> bool:
        transfer = self.transfers.get(transfer_id)
        if not transfer:
            return False
        
        transfer.standard_contract_signed = signed
        
        if signed:
            await self._assess_compliance(transfer)
        
        return True
    
    async def record_user_consent(
        self,
        transfer_id: str,
        consent_obtained: bool,
    ) -> bool:
        transfer = self.transfers.get(transfer_id)
        if not transfer:
            return False
        
        transfer.user_consent_obtained = consent_obtained
        
        if consent_obtained:
            await self._assess_compliance(transfer)
        
        return True
    
    async def get_non_compliant_transfers(self) -> List[Dict]:
        return [
            {
                "transfer_id": t.transfer_id,
                "timestamp": t.timestamp,
                "transfer_type": t.transfer_type,
                "destination_country": t.destination_country,
                "data_types": t.data_types,
                "compliance_status": t.compliance_status,
                "risk_level": t.risk_level,
                "blocked": t.blocked,
                "security_assessment_passed": t.security_assessment_passed,
                "standard_contract_signed": t.standard_contract_signed,
                "user_consent_obtained": t.user_consent_obtained,
            }
            for t in self.transfers.values()
            if t.compliance_status == ComplianceStatus.NON_COMPLIANT.value
        ]
    
    async def get_transfers_by_destination(
        self,
        country_code: str,
    ) -> List[Dict]:
        return [
            {
                "transfer_id": t.transfer_id,
                "timestamp": t.timestamp,
                "transfer_type": t.transfer_type,
                "data_types": t.data_types,
                "data_volume": t.data_volume,
                "compliance_status": t.compliance_status,
            }
            for t in self.transfers.values()
            if t.destination_country == country_code
        ]
    
    async def get_country_protection_level(
        self,
        country_code: str,
    ) -> Optional[Dict]:
        country = self.country_protection_levels.get(country_code)
        if not country:
            return None
        
        return {
            "country_code": country.country_code,
            "country_name": country.country_name,
            "protection_level": country.protection_level,
            "adequacy_decision": country.adequacy_decision,
            "notes": country.notes,
        }
    
    async def generate_cross_border_report(
        self,
        time_range: Optional[tuple] = None,
    ) -> Dict:
        if time_range:
            transfers = [
                t for t in self.transfers.values()
                if time_range[0] <= t.timestamp <= time_range[1]
            ]
        else:
            now = datetime.utcnow()
            start = (now - timedelta(days=30)).isoformat()
            transfers = [t for t in self.transfers.values() if t.timestamp >= start]
        
        report = {
            "time_range": time_range or {
                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "total_transfers": len(transfers),
            "transfers_by_destination": defaultdict(int),
            "transfers_by_type": defaultdict(int),
            "compliance_summary": {
                "compliant": 0,
                "non_compliant": 0,
                "pending": 0,
                "exempt": 0,
            },
            "total_data_volume": 0,
            "total_data_subjects": 0,
            "blocked_count": 0,
        }
        
        for transfer in transfers:
            report["transfers_by_destination"][transfer.destination_country] += 1
            report["transfers_by_type"][transfer.transfer_type] += 1
            report["total_data_volume"] += transfer.data_volume
            report["total_data_subjects"] += transfer.data_subjects_count
            
            if transfer.compliance_status == ComplianceStatus.COMPLIANT.value:
                report["compliance_summary"]["compliant"] += 1
            elif transfer.compliance_status == ComplianceStatus.NON_COMPLIANT.value:
                report["compliance_summary"]["non_compliant"] += 1
            elif transfer.compliance_status == ComplianceStatus.EXEMPT.value:
                report["compliance_summary"]["exempt"] += 1
            else:
                report["compliance_summary"]["pending"] += 1
            
            if transfer.blocked:
                report["blocked_count"] += 1
        
        report["transfers_by_destination"] = dict(report["transfers_by_destination"])
        report["transfers_by_type"] = dict(report["transfers_by_type"])
        
        return report
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_transfers": self.stats["total_transfers"],
            "transfers_by_type": dict(self.stats["transfers_by_type"]),
            "transfers_by_destination": dict(self.stats["transfers_by_destination"]),
            "compliant_transfers": self.stats["compliant_transfers"],
            "non_compliant_transfers": self.stats["non_compliant_transfers"],
            "blocked_transfers": self.stats["blocked_transfers"],
            "transfers_by_risk": dict(self.stats["transfers_by_risk"]),
        }
