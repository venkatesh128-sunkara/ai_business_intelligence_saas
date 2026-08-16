from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_member_workspace, get_dataset_for_user
from app.core.config import settings
from app.db.session import engine, get_db
from app.models import Dataset, QueryRecord, User, Workspace
from app.schemas.dataset import DatasetList, DatasetOut, DataPreview
from app.services.data_processor import DataProcessor

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _dataset_limit_ok(db: Session, user: User) -> bool:
    limit = settings.FREE_DATASETS if user.plan != "pro" else 200
    return db.query(Dataset).filter(Dataset.created_by == user.id).count() < limit


@router.get("", response_model=DatasetList)
def list_datasets(
    workspace_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Dataset)
    if workspace_id is not None:
        get_member_workspace(workspace_id, user, db)
        q = q.filter(Dataset.workspace_id == workspace_id)
    elif user.role != "admin":
        q = q.join(Workspace, Dataset.workspace_id == Workspace.id).filter(
            (Workspace.owner_id == user.id) | (Dataset.created_by == user.id)
        )
    items = q.order_by(Dataset.created_at.desc()).all()
    return DatasetList(items=[DatasetOut.model_validate(d) for d in items], total=len(items))


@router.post("", response_model=DatasetOut, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    workspace_id: int = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ws = get_member_workspace(workspace_id, user, db)
    if not _dataset_limit_ok(db, user):
        raise HTTPException(403, "Dataset limit reached for your plan")
    if ws.owner_id != user.id and user.role != "admin":
        raise HTTPException(403, "Only workspace owner can upload datasets")

    contents = await file.read()
    processor = DataProcessor()
    try:
        result = processor.process(
            contents, file.filename or "upload", name, source_type=file.content_type or "csv"
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    dataset = Dataset(
        workspace_id=workspace_id,
        name=name,
        filename=file.filename or name,
        table_name=result["table_name"],
        source_type=result["source_type"],
        status="ready",
        row_count=result["row_count"],
        column_count=result["column_count"],
        file_size=result["file_size"],
        storage_path=result["storage_path"],
        profile_json=result["profile_json"],
        schema_json=result["schema_json"],
        created_by=user.id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_dataset_for_user(dataset_id, user, db)


@router.get("/{dataset_id}/preview", response_model=DataPreview)
def preview_dataset(
    dataset_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = get_dataset_for_user(dataset_id, user, db)
    cols = [c["name"] for c in ds.schema_json.get("columns", [])]
    rows = []
    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f'SELECT * FROM "{ds.table_name}" LIMIT {int(min(limit, 200))}'
        )
        for row in result.mappings():
            rows.append([_json_safe(v) for v in row.values()])
    return DataPreview(columns=cols, rows=rows, row_count=len(rows))


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = get_dataset_for_user(dataset_id, user, db)
    if ds.created_by != user.id and user.role != "admin":
        raise HTTPException(403, "Only the uploader can delete this dataset")
    with engine.begin() as conn:
        conn.exec_driver_sql(f'DROP TABLE IF EXISTS "{ds.table_name}"')
    import os

    if ds.storage_path and os.path.exists(ds.storage_path):
        os.remove(ds.storage_path)
    db.query(QueryRecord).filter_by(dataset_id=ds.id).delete()
    db.delete(ds)
    db.commit()


def _json_safe(v):
    if v is None:
        return None
    try:
        from datetime import date, datetime

        if isinstance(v, (datetime, date)):
            return v.isoformat()
    except Exception:
        pass
    try:
        import math

        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
    except Exception:
        pass
    return v
