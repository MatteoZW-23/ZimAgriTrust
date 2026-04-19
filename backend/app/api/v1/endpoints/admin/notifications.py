from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.notification_template import NotificationTemplate, TemplateChannel
from app.models.system_audit import SystemAudit

router = APIRouter()

@router.get("/templates")
def list_templates(
    db: Session = Depends(get_db),
    channel: TemplateChannel = None,
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 230: View all notification templates.
    """
    query = db.query(NotificationTemplate)
    if channel:
        query = query.filter(NotificationTemplate.channel == channel)
    return query.all()

@router.patch("/templates/{template_id}")
def update_template(
    template_id: int,
    content: str,
    is_active: bool = True,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 231/232: Edit SMS/WhatsApp templates.
    """
    template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    old_content = template.content
    template.content = content
    template.is_active = is_active
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="TEMPLATE_UPDATE",
        target_type="NOTIFICATION_TEMPLATE",
        target_id=None,
        note=f"Updated template {template.name}"
    )
    db.add(audit)
    db.commit()
    return template

@router.post("/broadcast")
async def send_broadcast(
    message: str,
    target_role: UserRole = UserRole.FARMER,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 234: Send broadcast to farmers (or other roles).
    """
    from app.services.whatsapp_service import whatsapp_service
    users = db.query(User).filter(User.role == target_role).all()
    
    count = 0
    for user in users:
        await whatsapp_service.send_whatsapp_message(user.phone_number, message)
        count += 1
        
    audit = SystemAudit(
        admin_id=admin.id,
        action="BROADCAST_SENT",
        target_type="ROLE",
        note=f"Broadcast to {target_role}: {message[:50]}..."
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "recipients": count}
