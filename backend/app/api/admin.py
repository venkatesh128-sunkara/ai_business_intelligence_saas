from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import Dashboard, Dataset, QueryRecord, User, Workspace

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def platform_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {
        "users": db.query(User).count(),
        "workspaces": db.query(Workspace).count(),
        "datasets": db.query(Dataset).count(),
        "queries": db.query(QueryRecord).count(),
        "dashboards": db.query(Dashboard).count(),
        "datasets_by_user": [
            {"name": u.name, "email": u.email, "datasets": c}
            for u, c in db.query(User, func.count(Dataset.id))
            .outerjoin(Dataset, Dataset.created_by == User.id)
            .group_by(User.id)
            .order_by(func.count(Dataset.id).desc())
            .limit(10)
            .all()
        ],
        "recent_queries": [
            {
                "question": q.question,
                "user": db.get(User, q.user_id).email if db.get(User, q.user_id) else "?",
                "created_at": q.created_at.isoformat(),
            }
            for q in db.query(QueryRecord).order_by(QueryRecord.created_at.desc()).limit(10).all()
        ],
    }
