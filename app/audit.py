from app.models import AuditLog

def log_action(db, user_id, action, table_name=None, record_id=None, old_value=None, new_value=None):
    db.add(AuditLog(user_id=user_id, action=action, table_name=table_name,
                    record_id=str(record_id) if record_id is not None else None,
                    old_value=old_value, new_value=new_value))
