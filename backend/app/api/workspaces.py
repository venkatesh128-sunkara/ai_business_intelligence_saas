from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_member_workspace
from app.core.config import settings
from app.db.session import get_db
from app.models import Dataset, User, UsageRecord, Workspace, WorkspaceMember
from app.schemas.auth import UsageOut, WorkspaceCreate, WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _usage_for_user(db: Session, user: User) -> UsageOut:
    from datetime import datetime, timezone

    ym = datetime.now(timezone.utc).strftime("%Y-%m")
    rec = db.query(UsageRecord).filter_by(user_id=user.id, year_month=ym).first()
    qc = rec.query_count if rec else 0
    storage = db.query(Dataset).filter(Dataset.created_by == user.id).with_entities(Dataset.file_size).all()
    storage_bytes = sum(s[0] for s in storage)
    datasets = db.query(Dataset).filter(Dataset.created_by == user.id).count()
    limit = settings.FREE_QUERIES_PER_MONTH
    storage_limit = settings.FREE_STORAGE_MB
    ds_limit = settings.FREE_DATASETS
    if user.plan == "pro":
        limit, storage_limit, ds_limit = 10_000, 1024, 200
    return UsageOut(
        year_month=ym,
        query_count=qc,
        query_limit=limit,
        storage_bytes=storage_bytes,
        storage_limit_mb=storage_limit,
        dataset_count=datasets,
        dataset_limit=ds_limit,
    )


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "admin":
        return db.query(Workspace).order_by(Workspace.id).all()
    owned = db.query(Workspace).filter_by(owner_id=user.id).all()
    member_ids = db.query(WorkspaceMember.workspace_id).filter_by(user_id=user.id).all()
    member_ids = [r[0] for r in member_ids]
    joined = db.query(Workspace).filter(Workspace.id.in_(member_ids)).all() if member_ids else []
    return list(owned) + [w for w in joined if w.id not in {o.id for o in owned}]


@router.post("", response_model=WorkspaceOut, status_code=201)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ws = Workspace(name=payload.name, description=payload.description, owner_id=user.id)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


@router.get("/{workspace_id}/usage", response_model=UsageOut)
def workspace_usage(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_member_workspace(workspace_id, user, db)
    return _usage_for_user(db, user)


@router.post("/{workspace_id}/members")
def add_member(
    workspace_id: int,
    email: str,
    role: str = "viewer",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ws = get_member_workspace(workspace_id, user, db)
    if ws.owner_id != user.id and user.role != "admin":
        raise HTTPException(403, "Only the owner can invite members")
    target = db.query(User).filter_by(email=email.lower()).first()
    if target is None:
        raise HTTPException(404, "No user with that email")
    existing = db.query(WorkspaceMember).filter_by(workspace_id=workspace_id, user_id=target.id).first()
    if existing:
        existing.role = role
    else:
        db.add(WorkspaceMember(workspace_id=workspace_id, user_id=target.id, role=role))
    db.commit()
    return {"detail": f"{target.email} added to {ws.name}"}
