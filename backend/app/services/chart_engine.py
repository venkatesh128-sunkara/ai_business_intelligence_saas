"""Turn SQL result rows into Plotly figure JSON."""
from __future__ import annotations

from typing import Any

import pandas as pd

COLOR_PALETTE = [
    "#6366f1", "#8b5cf6", "#ec4899", "#ef4444", "#f59e0b",
    "#10b981", "#06b6d4", "#3b82f6", "#84cc16", "#a855f7",
]


def _rows_to_df(columns: list[str], rows: list[list]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=columns)
    for c in df.columns:
        if df[c].dtype == object:
            coerced = pd.to_numeric(df[c], errors="coerce")
            if coerced.notna().mean() > 0.95 and coerced.notna().any():
                df[c] = coerced
    return df


def infer_numeric_axis(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def _scale_numeric_colors(values) -> list[str]:
    try:
        vals = [float(v) for v in values]
    except (TypeError, ValueError):
        return [COLOR_PALETTE[0]] * len(values)
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    scaled = [(v - lo) / rng for v in vals]
    return [COLOR_PALETTE[min(int(s * (len(COLOR_PALETTE) - 1)), len(COLOR_PALETTE) - 1)] for s in scaled]


def build_figure(
    columns: list[str],
    rows: list[list],
    chart: dict[str, Any] | None,
) -> dict[str, Any]:
    """Produce a Plotly figure JSON. chart may be a {type,x,y,...} spec or None."""
    if not rows:
        return {"data": [], "layout": {"title": "No data"}}

    df = _rows_to_df(columns, rows)
    chart = chart or {}
    ctype = str(chart.get("type") or "bar").lower()
    title = str(chart.get("title") or "")
    x_col = chart.get("x") or (df.columns[0] if len(df.columns) >= 1 else None)
    y_col = chart.get("y") or infer_numeric_axis(df) or (df.columns[-1] if len(df.columns) > 1 else df.columns[0])

    if x_col not in df.columns:
        x_col = df.columns[0]
    if y_col not in df.columns:
        y_col = infer_numeric_axis(df) or df.columns[-1]

    x_label = chart.get("x_label") or str(x_col)
    y_label = chart.get("y_label") or str(y_col)
    x_values = df[x_col].tolist()
    y_values = df[y_col].tolist()

    layout: dict[str, Any] = {
        "title": {"text": title or f"{x_label} vs {y_label}", "font": {"size": 16}},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#e2e8f0"},
        "margin": {"l": 60, "r": 20, "t": 60, "b": 60},
        "xaxis": {"title": x_label, "color": "#94a3b8", "gridcolor": "rgba(148,163,184,0.15)"},
        "yaxis": {"title": y_label, "color": "#94a3b8", "gridcolor": "rgba(148,163,184,0.15)"},
        "hovermode": "closest",
    }

    if ctype in ("line", "area"):
        data = [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": x_values,
            "y": y_values,
            "line": {"color": COLOR_PALETTE[0], "width": 3, "shape": "spline"},
            "marker": {"size": 7, "color": COLOR_PALETTE[0]},
            "fill": "tozeroy" if ctype == "area" else None,
            "fillcolor": "rgba(99,102,241,0.15)",
            "hovertemplate": f"{x_label}: %{{x}}<br>{y_label}: %{{y:,.2f}}<extra></extra>",
        }]
    elif ctype == "pie":
        data = [{
            "type": "pie",
            "labels": x_values,
            "values": y_values,
            "hole": 0.4,
            "marker": {"colors": COLOR_PALETTE},
            "textinfo": "percent+label",
            "hovertemplate": "%{label}: %{value:,.2f} (%{percent})<extra></extra>",
        }]
        layout["xaxis"] = {"visible": False}
        layout["yaxis"] = {"visible": False}
    elif ctype == "scatter":
        data = [{
            "type": "scatter",
            "mode": "markers",
            "x": x_values,
            "y": y_values,
            "marker": {"size": 12, "color": COLOR_PALETTE[0], "opacity": 0.75},
            "hovertemplate": f"{x_label}: %{{x:,.2f}}<br>{y_label}: %{{y:,.2f}}<extra></extra>",
        }]
    elif ctype == "indicator" and len(df) == 1:
        data = [{
            "type": "indicator",
            "value": y_values[0],
            "number": {"prefix": "$" if _is_money(y_label) else "", "font": {"size": 44}},
            "title": {"text": title or y_label, "font": {"size": 18}},
        }]
        layout["xaxis"] = {"visible": False}
        layout["yaxis"] = {"visible": False}
    else:  # bar, column or default
        data = [{
            "type": "bar",
            "x": x_values,
            "y": y_values,
            "marker": {"color": _scale_numeric_colors(y_values) if y_values else COLOR_PALETTE[0]},
            "hovertemplate": f"{x_label}: %{{x}}<br>{y_label}: %{{y:,.2f}}<extra></extra>",
        }]
        layout["bargap"] = 0.35

    return {"data": data, "layout": layout}


def _is_money(label: str) -> bool:
    label = label.lower()
    return any(k in label for k in ("revenue", "sales", "amount", "price", "cost", "profit", "salary", "price"))


def render_table(columns: list[str], rows: list[list]) -> list[list]:
    return [[str(v) if v is not None else "" for v in row] for row in rows[:50]]
