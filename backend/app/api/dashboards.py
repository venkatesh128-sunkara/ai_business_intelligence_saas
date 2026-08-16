from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_dataset_for_user, get_member_workspace
from app.db.session import get_db
from app.models import Dashboard, DashboardItem, QueryRecord, User
from app.models.user import utcnow
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardItemIn,
    DashboardItemOut,
    DashboardItemUpdate,
    DashboardOut,
)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("", response_model=list[DashboardOut])
def list_dashboards(
    workspace_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Dashboard)
    if workspace_id is not None:
        get_member_workspace(workspace_id, user, db)
        q = q.filter(Dashboard.workspace_id == workspace_id)
    elif user.role != "admin":
        q = q.filter(Dashboard.created_by == user.id)
    dashboards = q.order_by(Dashboard.updated_at.desc()).all()
    result = []
    for d in dashboards:
        result.append(_to_out(d, db))
    return result


@router.post("", response_model=DashboardOut, status_code=201)
def create_dashboard(
    payload: DashboardCreate,
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ws = get_member_workspace(workspace_id, user, db)
    if ws.owner_id != user.id and user.role != "admin":
        raise HTTPException(403, "Only workspace owner can create dashboards")
    d = Dashboard(
        workspace_id=workspace_id,
        name=payload.name,
        description=payload.description,
        created_by=user.id,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return _to_out(d, db)


@router.get("/{dashboard_id}", response_model=DashboardOut)
def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.get(Dashboard, dashboard_id)
    if d is None:
        raise HTTPException(404, "Dashboard not found")
    get_member_workspace(d.workspace_id, user, db)
    return _to_out(d, db)


@router.post("/{dashboard_id}/items", response_model=DashboardItemOut, status_code=201)
def add_item(
    dashboard_id: int,
    payload: DashboardItemIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.get(Dashboard, dashboard_id)
    if d is None:
        raise HTTPException(404, "Dashboard not found")
    get_member_workspace(d.workspace_id, user, db)
    q = db.get(QueryRecord, payload.query_id)
    if q is None:
        raise HTTPException(404, "Query not found")
    item = DashboardItem(
        dashboard_id=dashboard_id,
        query_id=q.id,
        title=payload.title or q.question,
        chart_json=q.chart_json,
        config_json=payload.config or {},
    )
    db.add(item)
    d.updated_at = utcnow()
    db.commit()
    db.refresh(item)
    return DashboardItemOut.model_validate(item)


@router.patch("/items/{item_id}", response_model=DashboardItemOut)
def update_item(
    item_id: int,
    payload: DashboardItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(DashboardItem, item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    d = db.get(Dashboard, item.dashboard_id)
    get_member_workspace(d.workspace_id, user, db)
    if payload.title is not None:
        item.title = payload.title
    if payload.config is not None:
        item.config_json = payload.config
    d.updated_at = utcnow()
    db.commit()
    db.refresh(item)
    return DashboardItemOut.model_validate(item)


@router.delete("/items/{item_id}", status_code=204)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(DashboardItem, item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    d = db.get(Dashboard, item.dashboard_id)
    get_member_workspace(d.workspace_id, user, db)
    db.delete(item)
    db.commit()


@router.delete("/{dashboard_id}", status_code=204)
def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.get(Dashboard, dashboard_id)
    if d is None:
        raise HTTPException(404, "Dashboard not found")
    get_member_workspace(d.workspace_id, user, db)
    db.query(DashboardItem).filter_by(dashboard_id=d.id).delete()
    db.delete(d)
    db.commit()


def _to_out(d: Dashboard, db: Session) -> DashboardOut:
    items = db.query(DashboardItem).filter_by(dashboard_id=d.id).all()
    out = DashboardOut(
        id=d.id,
        workspace_id=d.workspace_id,
        name=d.name,
        description=d.description,
        created_by=d.created_by,
        created_at=d.created_at,
        updated_at=d.updated_at,
        items=[DashboardItemOut.model_validate(i) for i in items],
    )
    return out

