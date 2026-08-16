import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_dataset_for_user
from app.core.config import settings
from app.db.session import engine, get_db
from app.models import Dataset, QueryRecord, UsageRecord, User
from app.schemas.query import AskRequest, QueryHistory, QueryRecordOut, QueryResult
from app.services.chart_engine import build_figure
from app.services.nl2sql import NL2SQLEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


def _consume_query(db: Session, user: User) -> None:
    ym = datetime.now(timezone.utc).strftime("%Y-%m")
    limit = settings.FREE_QUERIES_PER_MONTH if user.plan != "pro" else 10_000
    rec = db.query(UsageRecord).filter_by(user_id=user.id, year_month=ym).first()
    if rec is None:
        rec = UsageRecord(user_id=user.id, year_month=ym, query_count=0)
        db.add(rec)
        db.flush()
    if rec.query_count >= limit:
        raise HTTPException(429, "Monthly query limit reached. Upgrade your plan or wait for next month.")
    rec.query_count += 1
    rec.updated_at = datetime.now(timezone.utc)


def _execute(sql: str):
    rows, columns = [], []
    with engine.connect() as conn:
        result = conn.exec_driver_sql(sql)
        columns = list(result.keys())
        for row in result.mappings():
            rows.append([_json_safe(v) for v in row.values()])
            if len(rows) >= 1000:
                break
    return columns, rows


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


def _suggest_followups(question: str, schema_json: dict, rows: list) -> list[str]:
    suggestions = [
        "Show me this data grouped by the most common category",
        "What is the trend over time?",
        "Which values are the highest and lowest?",
        "Explain why the numbers changed",
    ]
    cols = [c["name"] for c in schema_json.get("columns", [])]
    if cols:
        suggestions.append(f"Compare {cols[-1]} across categories")
    return suggestions[:4]


@router.post("/ask", response_model=QueryResult)
def ask(
    payload: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = get_dataset_for_user(payload.dataset_id, user, db)
    _consume_query(db, user)
    db.commit()

    conversation_id = payload.conversation_id or uuid.uuid4().hex
    history = _load_history(db, conversation_id, payload.dataset_id)

    engine_nl = NL2SQLEngine()
    gen = engine_nl.generate(
        payload.question,
        ds.schema_json,
        ds.table_name,
        conversation=history,
    )

    sql = gen["sql"]
    try:
        columns, rows = _execute(sql)
    except Exception as exc:  # noqa: BLE001
        logger.error("SQL execution failed: %s\n%s", exc, sql)
        raise HTTPException(400, f"Could not execute generated SQL: {exc}")

    chart = build_figure(columns, rows, gen.get("chart"))
    summary = gen.get("summary") or _auto_summary(payload.question, columns, rows)

    record = QueryRecord(
        workspace_id=ds.workspace_id,
        dataset_id=ds.id,
        user_id=user.id,
        question=payload.question,
        sql=sql,
        chart_json=chart,
        summary=summary,
        result_preview_json={"columns": columns, "rows": rows[:50]},
        conversation_id=conversation_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return QueryResult(
        id=record.id,
        question=payload.question,
        sql=sql,
        summary=summary,
        chart=chart,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        conversation_id=conversation_id,
        suggested_followups=_suggest_followups(payload.question, ds.schema_json, rows),
        engine=gen.get("engine", "rule"),
    )


def _load_history(db: Session, conversation_id: str, dataset_id: int) -> list[dict]:
    if not conversation_id:
        return []
    records = (
        db.query(QueryRecord)
        .filter(QueryRecord.conversation_id == conversation_id, QueryRecord.dataset_id == dataset_id)
        .order_by(QueryRecord.created_at)
        .all()
    )
    return [{"question": r.question, "summary": r.summary} for r in records[-4:]]


def _auto_summary(question: str, columns: list[str], rows: list) -> str:
    if not rows:
        return f"Your question \"{question}\" returned no rows."
    if len(columns) == 1 and len(rows) == 1:
        return f"Your question \"{question}\" returned the value {rows[0][0]}."
    if len(columns) == 2:
        first = rows[0][0]
        second = rows[0][1]
        return f"Top result for \"{question}\": {first} = {second}. {len(rows)} rows in total."
    return f"Query for \"{question}\" returned {len(rows)} rows across {len(columns)} columns."


@router.get("/history", response_model=QueryHistory)
def history(
    dataset_id: int | None = None,
    conversation_id: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(QueryRecord).filter(QueryRecord.user_id == user.id)
    if dataset_id is not None:
        get_dataset_for_user(dataset_id, user, db)
        q = q.filter(QueryRecord.dataset_id == dataset_id)
    if conversation_id:
        q = q.filter(QueryRecord.conversation_id == conversation_id)
    items = q.order_by(QueryRecord.created_at.desc()).limit(min(limit, 500)).all()
    return QueryHistory(items=[QueryRecordOut.model_validate(r) for r in items], total=len(items))


@router.delete("/{query_id}", status_code=204)
def delete_query(
    query_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rec = db.get(QueryRecord, query_id)
    if rec is None or rec.user_id != user.id:
        raise HTTPException(404, "Query not found")
    db.delete(rec)
    db.commit()
