from datetime import datetime

from pydantic import BaseModel


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    missing: int
    unique: int
    sample: list
    stats: dict = {}


class DatasetOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    filename: str
    source_type: str
    status: str
    row_count: int
    column_count: int
    file_size: int
    profile_json: dict
    schema: dict
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class DatasetList(BaseModel):
    items: list[DatasetOut]
    total: int


class DataPreview(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
