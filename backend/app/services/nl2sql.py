"""Natural Language -> SQL.

Two modes:
  * LLM mode: schema + RAG context + conversation history sent to the LLM,
    which returns JSON {sql, chart, summary}.
  * Rule-based fallback: deterministic parser so the platform is fully
    functional even without an API key.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

from app.services.ai_provider import LLMUnavailableError, get_provider
from app.services.vector_store import build_aliases, build_schema_text, VectorStore

logger = logging.getLogger(__name__)

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
MONTH_SHORT = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

AGG_ALIASES = {
    "sum": "SUM", "total": "SUM", "totals": "SUM",
    "average": "AVG", "avg": "AVG", "mean": "AVG",
    "count": "COUNT", "how many": "COUNT", "number of": "COUNT", "count of": "COUNT",
    "max": "MAX", "maximum": "MAX",
    "min": "MIN", "minimum": "MIN",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().replace("?", "").replace(".", "").strip())


def _find_column(question: str, schema_json: dict, alias_map: dict[str, str]) -> list[str]:
    """Return canonical column names whose name/alias appears in the question."""
    found: list[str] = []
    q = _norm(question)
    for col in schema_json.get("columns", []):
        name = col["name"]
        nlow = name.lower()
        if re.search(rf"\b{re.escape(nlow)}\b", q) or nlow.replace("_", " ") in q:
            if name not in found:
                found.append(name)
        else:
            for alias, canon in alias_map.items():
                if canon == name and alias in q and name not in found:
                    found.append(name)
    return found


# Semantic business terms -> candidate numeric columns by substring match
SEMANTIC_MEASURES: list[tuple[list[str], list[str]]] = [
    (["sales", "revenue", "turnover"], ["revenue", "sales", "amount", "turnover"]),
    (["order value", "average order", "aov"], ["revenue", "amount", "price", "value", "total"]),
    (["profit"], ["profit", "income", "margin"]),
    (["orders", "transactions", "purchases", "buyers"], ["order", "transaction", "purchase", "quantity"]),
]


def _find_measure(question: str, numeric_cols: list[dict]) -> str | None:
    """Find a numeric measure column even when only a synonym is mentioned."""
    q = _norm(question)
    for terms, needles in SEMANTIC_MEASURES:
        if any(re.search(rf"\b{re.escape(t)}\b", q) for t in terms):
            # iterate needles by priority (outer) over columns
            for needle in needles:
                for col in numeric_cols:
                    name = col["name"].lower()
                    if needle in name:
                        return col["name"]
    return None


class RuleBasedEngine:
    """Deterministic NL -> SQL parser. Handles common analytic questions."""

    def generate(self, question: str, schema_json: dict, table_name: str) -> dict:
        cols = schema_json.get("columns", [])
        alias_map = build_aliases(schema_json)
        mentioned = _find_column(question, schema_json, alias_map)
        numeric_cols = [c for c in cols if "int" in str(c["dtype"]) or "float" in str(c["dtype"])]
        date_cols = [c["name"] for c in cols if "date" in str(c["dtype"]) or "datetime" in str(c["dtype"])]

        q = _norm(question)

        # ---- aggregation ----
        agg: str | None = None
        for alias, sql_agg in AGG_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", q) or alias in q:
                agg = sql_agg
                break

        # measure column = a mentioned numeric column
        measure = next((c["name"] for c in numeric_cols if c["name"] in mentioned), None)
        if measure is None:
            measure = _find_measure(question, numeric_cols)

        # "highest/lowest/best/worst X" implies SUM(X) ordered desc/asc
        superlative_high = bool(re.search(r"\b(?:highest|most|largest|biggest|best|top)\b", q))
        superlative_low = bool(re.search(r"\b(?:lowest|least|smallest|worst|bottom)\b", q))

        # ---- group by candidates (non-numeric mentioned columns) ----
        group_col: str | None = None
        non_numeric_names = [c["name"] for c in cols if c["name"] not in [n["name"] for n in numeric_cols]]
        for m in mentioned:
            if m in non_numeric_names:
                group_col = m
                break

        # explicit "by X" / "per X" / "for each X" (must be a categorical column)
        by_match = re.search(r"\bby\s+([a-z_ ]+?)(?:\s+(?:in|for|during|where|when)\b|\s*$)", q)
        if by_match:
            phrase = by_match.group(1).strip()
            best = self._match_phrase(phrase, cols, alias_map)
            if best and best in non_numeric_names:
                group_col = best
        per_match = re.search(r"\bper\s+([a-z_ ]+?)(?:\s+(?:in|for|during|where|when)\b|\s*$)", q)
        if per_match and not group_col:
            best = self._match_phrase(per_match.group(1).strip(), cols, alias_map)
            if best and best in non_numeric_names:
                group_col = best

        # ---- time grouping ----
        time_group: str | None = None
        time_unit: str | None = None
        for unit in ["year", "month", "day", "quarter"]:
            if unit in q or f"per {unit}" in q or f"by {unit}" in q or f"weekly" in q and unit == "day":
                time_unit = unit
                break
        if q in ("weekly",) or "weekly" in q:
            time_unit = "day"
        if date_cols and (time_unit or "trend" in q or "over time" in q or "monthly" in q or "daily" in q or "quarterly" in q or "yearly" in q or "annual" in q):
            time_group = date_cols[0]
            if not time_unit:
                time_unit = "month"

        # ---- filters ----
        filters: list[str] = []
        date_col = date_cols[0] if date_cols else None

        # "in Q2 2023" / "Q2"
        q_match = re.search(r"\bq([1-4])(?:\s+(\d{4}))?\b", q)
        if q_match and date_col:
            qnum = int(q_match.group(1))
            year = q_match.group(2)
            months = (qnum - 1) * 3 + 1
            m0, m1 = months, months + 2
            expr = f"CAST(strftime('%m', \"{date_col}\") AS INTEGER) BETWEEN {m0} AND {m1}"
            if year:
                expr += f" AND strftime('%Y', \"{date_col}\") = '{year}'"
            filters.append(expr)

        # "in <month> <year>" or "in <month>"
        m_match = re.search(r"\bin\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)(?:\s+(\d{4}))?\b", q)
        if m_match and date_col:
            mn = MONTH_NAMES.get(m_match.group(1)) or MONTH_SHORT.get(m_match.group(1))
            year = m_match.group(2)
            if year:
                filters.append(f"strftime('%Y', \"{date_col}\") = '{year}' AND CAST(strftime('%m', \"{date_col}\") AS INTEGER) = {mn}")
            else:
                filters.append(f"CAST(strftime('%m', \"{date_col}\") AS INTEGER) = {mn}")

        # year
        y_match = re.search(r"\b(19\d{2}|20\d{2})\b", q)
        if y_match and date_col and not q_match:
            filters.append(f"strftime('%Y', \"{date_col}\") = '{y_match.group(1)}'")

        # "greater than N" / "at least N" / "above N" / "more than N"
        comp_patterns = [
            (r"\b(?:greater than|more than|above|at least|over)\s+(\d[\d.,]*)", ">="),
            (r"\b(?:less than|below|under|at most|fewer than)\s+(\d[\d.,]*)", "<="),
        ]
        for pat, op in comp_patterns:
            m = re.search(pat, q)
            if m and measure:
                val = m.group(1).replace(",", "")
                filters.append(f"\"{measure}\" {op} {val}")

        # "in <value>" categorical, e.g. "in the US" or "in region" / "where X is Y"
        in_val = re.search(r"\bin\s+['\"]?([a-z][a-z0-9 ]*?)['\"]?(?:\s+(?:for|during|and|in|where)\b|\s*$)", q)
        if in_val and group_col and not q_match and not m_match:
            val = in_val.group(1).strip()
            if len(val) > 1 and val not in ("the", "total", "2023", "2022", "2024"):
                filters.append(f"LOWER(CAST(\"{group_col}\" AS TEXT)) = LOWER('{val}')")

        where_eq = re.search(r"\bwhere\s+(?:is\s+)?([a-z_ ]+?)\s+(?:is|equals|=|was)\s+['\"]?([a-z0-9_ .-]+)['\"]?", q)
        if where_eq:
            col = self._match_phrase(where_eq.group(1).strip(), cols, alias_map)
            if col:
                filters.append(f"LOWER(CAST(\"{col}\" AS TEXT)) = LOWER('{where_eq.group(2).strip()}')")

        # "after <date>" / "before <date>" / "since <date>"
        after = re.search(r"\b(?:after|since)\s+(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})\b", q)
        before = re.search(r"\b(?:before|until)\s+(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})\b", q)
        if date_col:
            if after:
                filters.append(f"\"{date_col}\" >= '{after.group(1)}'")
            if before:
                filters.append(f"\"{date_col}\" <= '{before.group(1)}'")

        # ---- order / limit ----
        top_match = re.search(r"\btop\s+(\d+)", q)
        bottom_match = re.search(r"\bbottom\s+(\d+)", q)
        limit: int | None = None
        order_desc = False
        order_col: str | None = None
        if top_match:
            limit = int(top_match.group(1))
            order_desc = True
            order_col = measure
        elif bottom_match:
            limit = int(bottom_match.group(1))
            order_desc = False
            order_col = measure
        elif re.search(r"\b(?:highest|most|largest|biggest)\b", q) and measure:
            order_col = measure
            order_desc = True
        elif re.search(r"\b(?:lowest|least|smallest)\b", q) and measure:
            order_col = measure
            order_desc = False

        # ---- build SQL ----
        select_parts: list[str]
        group_parts: list[str] = []
        order_parts: list[str] = []

        if time_group:
            expr = f"strftime('%Y', \"{time_group}\")"
            label = f"strftime('%Y', \"{time_group}\")"
            if time_unit == "year":
                expr = f"strftime('%Y', \"{time_group}\")"
                label = f"strftime('%Y', \"{time_group}\")"
            elif time_unit == "quarter":
                expr = f"strftime('%Y-', \"{time_group}\") || printf('Q%d', ((CAST(strftime('%m', \"{time_group}\") AS INTEGER) - 1) / 3) + 1)"
                label = expr
            elif time_unit == "month":
                expr = f"strftime('%Y-%m', \"{time_group}\")"
                label = f"strftime('%Y-%m', \"{time_group}\")"
            else:
                expr = f"date(\"{time_group}\")"
                label = f"date(\"{time_group}\")"
            select_parts = [f"{expr} AS \"{time_unit}\""]
            group_parts = [expr]
            order_parts = [f"{expr} ASC"]
        elif group_col:
            select_parts = [f"\"{group_col}\""]
            group_parts = [f"\"{group_col}\""]
        else:
            select_parts = []

        # Grouped questions over a measure default to SUM, e.g. "revenue by region"
        if agg is None and measure and (group_parts or time_group):
            agg = "SUM"

        if agg and measure and agg != "COUNT":
            select_parts.append(f"{agg}(\"{measure}\") AS \"{agg.lower()}_{measure[:40]}\"")
        elif agg == "COUNT":
            select_parts.append("COUNT(*) AS \"count\"")
        elif measure and not agg:
            select_parts.append(f"\"{measure}\"")
            order_parts = [f"\"{measure}\" DESC"] if order_desc else [f"\"{measure}\" ASC"]
        elif not measure and (group_parts or time_group):
            select_parts.append("COUNT(*) AS \"count\"")

        if not select_parts:
            sql = f'SELECT * FROM "{table_name}" LIMIT 50'
        else:
            sql = "SELECT " + ", ".join(select_parts)
            sql += f' FROM "{table_name}"'
            if filters:
                sql += " WHERE " + " AND ".join(filters)
            if group_parts:
                sql += " GROUP BY " + ", ".join(group_parts)
            if order_col:
                if measure and agg and not group_parts and not time_group:
                    sql += f" ORDER BY \"{measure}\" {'DESC' if order_desc else 'ASC'}"
                elif order_col and agg:
                    sql += f" ORDER BY {agg}(\"{order_col}\") {'DESC' if order_desc else 'ASC'}"
                elif order_col:
                    sql += f" ORDER BY \"{order_col}\" {'DESC' if order_desc else 'ASC'}"
            if limit:
                sql += f" LIMIT {limit}"

        chart_type = recommend_chart(select_parts, time_group, group_col, measure, agg, numeric_cols)
        return {
            "sql": sql,
            "chart_type": chart_type,
            "engine": "rule",
        }

    def _match_phrase(self, phrase: str, cols: list[dict], alias_map: dict[str, str]) -> str | None:
        phrase = phrase.strip()
        for col in cols:
            name = col["name"]
            if phrase == name.lower() or phrase == name.lower().replace("_", " "):
                return name
        for alias, canon in alias_map.items():
            if phrase == alias:
                return canon
        for col in cols:
            name = col["name"].lower()
            if name.replace("_", " ") in phrase or phrase in name.replace("_", " "):
                return col["name"]
        return None


def recommend_chart(
    select_parts: list[str],
    time_group: str | None,
    group_col: str | None,
    measure: str | None,
    agg: str | None,
    numeric_cols: list[dict],
) -> str:
    if time_group:
        return "line"
    if group_col and (agg or measure):
        return "bar"
    if not group_col and not time_group:
        # single aggregate value -> indicator; plain numeric pair -> scatter
        if measure and not agg:
            if len(numeric_cols) >= 2:
                return "scatter"
            return "indicator"
        if agg:
            return "indicator"
    return "bar"


def conversation_context(history: list[dict], question: str) -> str:
    if not history:
        return ""
    lines = ["Previous conversation:"]
    for h in history[-4:]:
        lines.append(f'Q: {h["question"]}')
        lines.append(f'A: {h["summary"][:200]}')
    lines.append(f"Current question: {question}")
    return "\n".join(lines)


class NL2SQLEngine:
    def generate(
        self,
        question: str,
        schema_json: dict,
        table_name: str,
        conversation: list[dict] | None = None,
    ) -> dict:
        vector_store = VectorStore(schema_json.get("columns", []))
        rag_context = vector_store.to_prompt(question, top_k=6)
        history = conversation_context(conversation or [], question)
        schema_text = build_schema_text(schema_json)
        rule = RuleBasedEngine()

        if get_provider().available:
            try:
                return self._llm_generate(question, schema_json, schema_text, rag_context, history, table_name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM NL2SQL failed (%s), falling back to rule engine", exc)
        fallback = rule.generate(question, schema_json, table_name)
        fallback["summary"] = self._fallback_summary(question, fallback["sql"], fallback["chart_type"])
        fallback["engine"] = "rule"
        return fallback

    def _llm_generate(self, question, schema_json, schema_text, rag_context, history, table_name) -> dict:
        provider = get_provider()
        system = (
            "You are a senior data analyst that converts natural-language questions into SQL. "
            "You are given a dataset schema, relevant columns retrieved from a knowledge base, "
            "and prior conversation. Answer with STRICT JSON only, no markdown fences:\n"
            '{"sql": "...", "chart": {"type": "bar|line|scatter|pie|indicator|table", '
            '"title": "...", "x": "...", "y": "...", "x_label": "...", "y_label": "..."}, '
            '"summary": "one or two sentence plain-English explanation of what the query does and what result means"}'
            "\nRules:\n"
            "- Table name is \"%s\". Always use exactly this table name.\n"
            "- Only reference columns that exist in the schema.\n"
            "- Use SQLite dialect.\n"
            "- If asked to show/see/list data, return a query with LIMIT 50.\n"
            "- For time aggregation use strftime() (SQLite) with proper year-month format.\n"
            "- Keep chart 'x' and 'y' as the SELECT aliases (not raw column names unless aliased).\n"
            "- Summaries must be insightful, mention concrete numbers from the data where possible.\n"
        ) % table_name
        user = (
            f"SCHEMA:\n{schema_text}\n\n"
            f"RETRIEVED COLUMN CONTEXT:\n{rag_context}\n\n"
            f"{history}\n\n"
            f"QUESTION: {question}"
        )
        payload = provider.complete_json(system, user, temperature=0.1)
        chart = payload.get("chart", {})
        if isinstance(chart, dict):
            chart.setdefault("type", "bar")
            chart.setdefault("title", question)
        return {
            "sql": payload.get("sql", ""),
            "chart": chart,
            "summary": payload.get("summary", ""),
            "engine": "llm",
        }

    def _fallback_summary(self, question: str, sql: str, chart_type: str) -> str:
        short = question.rstrip("?.")
        if "count" in _norm(question) or "how many" in _norm(question):
            return f"Counting rows/records for \"{short}\". The chart shows the result."
        if chart_type == "line":
            return f"Time trend for \"{short}\". Values are aggregated over time periods."
        if chart_type == "bar":
            return f"Breakdown for \"{short}\". Bars compare values across categories."
        return f"Results for \"{short}\" generated by the built-in SQL engine."
