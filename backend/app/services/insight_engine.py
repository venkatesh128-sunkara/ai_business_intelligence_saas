"""Automatic business insights from a dataset.

Produces deterministic statistical insights (trends, outliers, top/bottom
performers, missing data, correlations) and optionally enriches them with an
LLM-written narrative.
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.services.ai_provider import get_provider

logger = logging.getLogger(__name__)


def load_dataframe(table_name: str) -> pd.DataFrame:
    from app.db.session import engine

    df = pd.read_sql(f'SELECT * FROM "{table_name}" LIMIT 50000', engine)
    for col in df.columns:
        if df[col].dtype == object:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().mean() > 0.7:
                df[col] = parsed
    return df


class InsightEngine:
    def analyze(self, table_name: str, schema_json: dict) -> list[dict[str, Any]]:
        try:
            df = load_dataframe(table_name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Could not load %s: %s", table_name, exc)
            return []
        insights: list[dict[str, Any]] = []
        insights += self._missing_data(df)
        insights += self._top_bottom(df)
        insights += self._numeric_trend(df)
        insights += self._correlations(df)
        insights += self._outliers(df)
        insights += self._overview(df, schema_json)
        insights = sorted(insights, key=lambda i: {"high": 0, "medium": 1, "low": 2, "info": 3}[i["severity"]])
        return insights

    def enrich(self, insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Use the LLM to turn statistical facts into business narrative."""
        provider = get_provider()
        if not provider.available or not insights:
            return insights
        try:
            facts = "\n".join(
                f"- {i['title']}: {i['description']}" for i in insights[:8]
            )
            system = (
                "You are a business intelligence analyst. Rewrite each insight as an "
                "actionable business insight for a non-technical executive. Keep each "
                "under 2 sentences, concrete, mention numbers. Output STRICT JSON array "
                'like [{"title": "...", "description": "..."}] matching the input order.'
            )
            payload = provider.complete_json(system, f"INSIGHTS:\n{facts}")
            items = payload if isinstance(payload, list) else payload.get("insights", [])
            for i, item in enumerate(items[: len(insights)]):
                if isinstance(item, dict):
                    insights[i]["title"] = item.get("title", insights[i]["title"])
                    insights[i]["description"] = item.get("description", insights[i]["description"])
                    insights[i]["llm"] = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM insight enrichment failed: %s", exc)
        return insights

    # ---- individual analyzers ----

    def _overview(self, df: pd.DataFrame, schema_json: dict) -> list[dict[str, Any]]:
        numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric:
            return []
        col = numeric[0]
        s = df[col].dropna()
        return [{
            "title": f"{col} overview",
            "category": "summary",
            "description": (
                f"{col} has {len(s):,} values. Minimum {s.min():,.2f}, maximum "
                f"{s.max():,.2f}, average {s.mean():,.2f}, median {s.median():,.2f}."
            ),
            "severity": "info",
            "data": {
                "column": col,
                "min": float(s.min()), "max": float(s.max()),
                "mean": round(float(s.mean()), 2), "median": round(float(s.median()), 2),
            },
        }]

    def _missing_data(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        insights = []
        total = len(df)
        if total == 0:
            return insights
        for col in df.columns:
            missing = int(df[col].isna().sum())
            if missing == 0:
                continue
            pct = missing / total * 100
            severity = "high" if pct > 20 else ("medium" if pct > 5 else "low")
            insights.append({
                "title": f"Missing values in {col}",
                "category": "anomaly",
                "description": f"{missing:,} of {total:,} rows ({pct:.1f}%) are missing in column \"{col}\".",
                "severity": severity,
                "data": {"column": col, "missing": missing, "pct": round(pct, 1)},
            })
        return insights

    def _top_bottom(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        insights = []
        cat_cols = [c for c in df.columns if df[c].dtype == object]
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for cat in cat_cols[:3]:
            for num in num_cols[:2]:
                grp = df.groupby(cat)[num].sum().sort_values(ascending=False)
                if len(grp) < 2 or grp.sum() == 0:
                    continue
                top_name, top_val = grp.index[0], float(grp.iloc[0])
                share = top_val / float(grp.sum()) * 100 if grp.sum() else 0
                bottom_name = grp.index[-1]
                insights.append({
                    "title": f"{top_name} leads {num}",
                    "category": "top_performer",
                    "description": (
                        f"\"{top_name}\" contributes {top_val:,.2f} ({share:.1f}%) of total "
                        f"{num}. \"{bottom_name}\" is the lowest at {float(grp.iloc[-1]):,.2f}."
                    ),
                    "severity": "medium",
                    "data": {"group_col": cat, "value_col": num, "top": str(top_name), "top_value": top_val, "share": round(share, 1)},
                })
        return insights

    def _numeric_trend(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        insights = []
        for dc in date_cols[:1]:
            for nc in num_cols[:2]:
                tmp = df[[dc, nc]].dropna()
                if len(tmp) < 3:
                    continue
                tmp = tmp.sort_values(dc)
                monthly = tmp.set_index(dc).resample("ME")[nc].sum()
                monthly = monthly[monthly.notna()]
                if len(monthly) < 2:
                    continue
                first_half = monthly.iloc[: len(monthly) // 2].sum()
                second_half = monthly.iloc[len(monthly) // 2:].sum()
                if first_half == 0:
                    continue
                delta = (second_half - first_half) / first_half * 100
                direction = "up" if delta >= 0 else "down"
                severity = "high" if abs(delta) > 25 else ("medium" if abs(delta) > 8 else "low")
                insights.append({
                    "title": f"{nc} trending {direction}",
                    "category": "trend",
                    "description": (
                        f"{nc} changed by {delta:+.1f}% when comparing the second half of the "
                        f"period to the first half (first half: {first_half:,.2f}, second half: {second_half:,.2f})."
                    ),
                    "severity": severity,
                    "data": {"column": nc, "delta_pct": round(delta, 1), "first": float(first_half), "second": float(second_half)},
                })
        return insights

    def _correlations(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        insights = []
        if len(numeric) < 2:
            return insights
        corr = df[numeric].corr()
        seen = set()
        for a in numeric:
            for b in numeric:
                if a == b or (a, b) in seen or (b, a) in seen:
                    continue
                seen.add((a, b))
                r = float(corr.loc[a, b])
                if r != r or abs(r) < 0.6:
                    continue
                kind = "strong positive" if r > 0 else "strong negative"
                insights.append({
                    "title": f"{a} and {b} are correlated",
                    "category": "correlation",
                    "description": (
                        f"Correlation coefficient r = {r:+.2f} indicates a {kind} relationship "
                        f"between \"{a}\" and \"{b}\"."
                    ),
                    "severity": "low",
                    "data": {"a": a, "b": b, "r": round(r, 2)},
                })
        return insights

    def _outliers(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        insights = []
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            s = df[col].dropna()
            if len(s) < 10:
                continue
            mean, std = float(s.mean()), float(s.std())
            if std == 0 or std != std:
                continue
            out = s[(s - mean).abs() > 3 * std]
            if len(out) == 0:
                continue
            insights.append({
                "title": f"Outliers detected in {col}",
                "category": "outlier",
                "description": (
                    f"{len(out):,} of {len(s):,} values in \"{col}\" fall more than 3 standard "
                    f"deviations from the mean ({mean:,.2f}). Max outlier: {out.max():,.2f}."
                ),
                "severity": "medium",
                "data": {"column": col, "outliers": int(len(out)), "mean": round(mean, 2), "max": float(out.max())},
            })
        return insights
