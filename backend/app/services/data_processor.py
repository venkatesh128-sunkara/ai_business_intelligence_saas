"""CSV/Excel ingestion, cleaning and profiling.

Flow:
  1. Read file with pandas
  2. Clean: normalize column names, infer dtypes, parse dates, dedupe, trim
  3. Profile every column (dtype, missing, unique, samples, numeric stats)
  4. Persist to a SQL table named after the dataset
"""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import settings
from app.db.session import engine

VALID_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,126}$")


def clean_column_name(name: str, used: set[str]) -> str:
    n = name.strip()
    n = re.sub(r"[^a-zA-Z0-9_]+", "_", n)
    n = re.sub(r"_+", "_", n).strip("_")
    if not n:
        n = "column"
    if not re.match(r"^[a-zA-Z_]", n):
        n = "c_" + n
    base = n[:127]
    final = base
    i = 2
    while final in used:
        final = f"{base}_{i}"
        i += 1
    used.add(final)
    return final


def _coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Try to parse columns that look like dates into datetime objects."""
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(20)
            if len(sample) == 0:
                continue
            nonnull = sample.astype(str)
            looks_like_date = (
                nonnull.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}").mean() > 0.6
                or nonnull.str.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}").mean() > 0.6
                or nonnull.str.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s+\d{1,2}:\d{2}").mean() > 0.6
            )
            if looks_like_date:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().mean() > 0.7:
                    df[col] = parsed
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the DataFrame."""
    df = df.copy()
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.duplicated()]

    used: set[str] = set()
    df.columns = [clean_column_name(str(c), used) for c in df.columns]

    df = _coerce_dates(df)

    # Trim string whitespace
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(lambda v: v.strip() if isinstance(v, str) else v)

    # Deduplicate identical rows (keep first)
    df = df.drop_duplicates()

    # Coerce numeric-looking strings to numbers
    for col in df.columns:
        if df[col].dtype == object:
            coerced = pd.to_numeric(df[col], errors="coerce")
            if coerced.notna().mean() > 0.9:
                df[col] = coerced

    return df.reset_index(drop=True)


def _jsonable(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (pd.Timedelta,)):
        return str(value)
    if isinstance(value, (float, int)):
        if isinstance(value, float) and (value != value):  # NaN
            return None
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def build_profile(df: pd.DataFrame) -> dict[str, Any]:
    columns = []
    for col in df.columns:
        series = df[col]
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))
        samples = [_jsonable(v) for v in series.dropna().head(5).tolist()]
        stats: dict[str, Any] = {}
        if pd.api.types.is_numeric_dtype(series) and series.notna().any():
            s = series.dropna()
            stats = {
                "min": _jsonable(s.min()),
                "max": _jsonable(s.max()),
                "mean": round(float(s.mean()), 4),
                "median": _jsonable(s.median()),
                "std": round(float(s.std()), 4) if s.std() == s.std() else None,
            }
        elif pd.api.types.is_datetime64_any_dtype(series) and series.notna().any():
            s = series.dropna()
            stats = {
                "min": s.min().isoformat(),
                "max": s.max().isoformat(),
            }
        elif series.notna().any():
            s = series.dropna()
            top = s.value_counts().head(3)
            stats = {
                "top_values": [{"value": _jsonable(k), "count": int(v)} for k, v in top.items()],
            }
        columns.append(
            {
                "name": col,
                "dtype": str(series.dtype),
                "missing": missing,
                "unique": unique,
                "sample": samples,
                "stats": stats,
            }
        )
    return {"columns": columns, "row_count": int(len(df)), "column_count": int(len(df.columns))}


def load_to_sql(df: pd.DataFrame, table_name: str) -> None:
    """Persist the DataFrame into the analysis SQL database."""
    validate_sql_table(table_name)
    with engine.begin() as conn:
        conn.exec_driver_sql(f'DROP TABLE IF EXISTS "{table_name}"')
    df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)


def validate_sql_table(table_name: str) -> str:
    if VALID_NAME_RE.match(table_name):
        return table_name
    raise ValueError("invalid table name")


class DataProcessor:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _read(self, path: str, source_type: str) -> pd.DataFrame:
        if source_type == "excel":
            return pd.read_excel(path)
        return pd.read_csv(path)

    def process(
        self,
        file_bytes: bytes,
        filename: str,
        dataset_name: str,
        source_type: str = "csv",
    ) -> dict[str, Any]:
        ext = os.path.splitext(filename)[1].lower()
        if ext in (".xlsx", ".xls"):
            source_type = "excel"
        elif ext == ".csv":
            source_type = "csv"
        else:
            raise ValueError("Only .csv, .xlsx and .xls files are supported")

        if len(file_bytes) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise ValueError(f"File exceeds {settings.MAX_UPLOAD_MB}MB limit")

        stored_name = f"{uuid.uuid4().hex}{ext}"
        path = self.upload_dir / stored_name
        path.write_bytes(file_bytes)

        df = self._read(str(path), source_type)
        if df.empty:
            path.unlink(missing_ok=True)
            raise ValueError("The uploaded file contains no rows")

        df = clean_dataframe(df)
        if len(df) > settings.MAX_ROWS_PER_DATASET:
            path.unlink(missing_ok=True)
            raise ValueError(f"Dataset exceeds {settings.MAX_ROWS_PER_DATASET:,} row limit")

        table_name = "ds_" + re.sub(r"[^a-zA-Z0-9_]", "_", dataset_name.lower())[:48] + "_" + uuid.uuid4().hex[:6]
        load_to_sql(df, table_name)

        profile = build_profile(df)
        schema_json = json.loads(json.dumps(profile))

        return {
            "table_name": table_name,
            "storage_path": str(path),
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "file_size": len(file_bytes),
            "profile_json": schema_json,
            "schema_json": schema_json,
            "source_type": source_type,
        }
