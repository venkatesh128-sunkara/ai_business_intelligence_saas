from datetime import datetime

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    dataset_id: int
    conversation_id: str | None = None


class ChartSpec(BaseModel):
    type: str
    title: str
    x: str | None = None
    y: str | None = None
    color: str | None = None
    x_label: str = ""
    y_label: str = ""


class QueryResult(BaseModel):
    id: int | None = None
    question: str
    sql: str
    summary: str
    chart: dict
    columns: list[str]
    rows: list[list]
    row_count: int
    conversation_id: str
    suggested_followups: list[str] = []
    engine: str = "llm"


class QueryRecordOut(BaseModel):
    id: int
    dataset_id: int
    question: str
    sql: str
    summary: str
    chart_json: dict
    result_preview_json: dict
    conversation_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryHistory(BaseModel):
    items: list[QueryRecordOut]
    total: int


class InsightOut(BaseModel):
    title: str
    category: str  # trend | outlier | top_performer | anomaly | correlation | summary
    description: str
    severity: str  # info | low | medium | high
    data: dict = {}


class InsightsResponse(BaseModel):
    dataset_id: int
    insights: list[InsightOut]
