from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_dataset_for_user
from app.db.session import get_db
from app.models import User
from app.schemas.query import InsightsResponse, InsightOut
from app.services.insight_engine import InsightEngine

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("/generate", response_model=InsightsResponse)
def generate_insights(
    dataset_id: int,
    use_llm: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = get_dataset_for_user(dataset_id, user, db)
    engine = InsightEngine()
    insights = engine.analyze(ds.table_name, ds.schema_json)
    if use_llm:
        insights = engine.enrich(insights)
    return InsightsResponse(
        dataset_id=ds.id,
        insights=[InsightOut(**i) for i in insights],
    )
