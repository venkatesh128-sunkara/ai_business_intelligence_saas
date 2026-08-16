from datetime import datetime

from pydantic import BaseModel


class DashboardCreate(BaseModel):
    name: str
    description: str = ""


class DashboardItemIn(BaseModel):
    query_id: int
    title: str = ""
    config: dict = {}


class DashboardItemOut(BaseModel):
    id: int
    query_id: int
    title: str
    chart_json: dict
    config_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    items: list[DashboardItemOut] = []

    model_config = {"from_attributes": True}


class DashboardItemUpdate(BaseModel):
    config: dict | None = None
    title: str | None = None
