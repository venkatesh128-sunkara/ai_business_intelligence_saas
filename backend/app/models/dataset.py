from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.user import utcnow


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    table_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), default="csv")  # csv | excel
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing | ready | failed
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(500), default="")
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def schema(self) -> dict:
        return self.schema_json
