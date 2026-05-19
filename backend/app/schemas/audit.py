import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: int
    admin_id: Optional[int]
    user_id: Optional[uuid.UUID]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    old_values: Optional[dict]
    new_values: Optional[dict]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    status: str
    error_message: Optional[str]
    checksum: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditChainVerification(BaseModel):
    total_logs: int
    verified_logs: int
    tampered_logs: int
    is_valid: bool
    tampered_ids: list[int] = []
    message: str
