from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.user import utcnow


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DashboardItem(Base):
    __tablename__ = "dashboard_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True, nullable=False)
    query_id: Mapped[int] = mapped_column(ForeignKey("queries.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="")
    chart_json: Mapped[dict] = mapped_column(JSON, default=dict)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)  # {x,y,w,h}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
