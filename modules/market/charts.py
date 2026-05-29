import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


COLORS = {
    "price_up": "#00aa44",
    "price_down": "#cc0000",
    "ma20": "#f0a500",
    "ma50": "#00aaff",
    "ma200": "#ff6600",
    "volume": "#444466",
    "bg": "#0e1117",
    "grid": "#1e2130",
    "text": "#e0e0e0",
}


def build_price_chart(df: pd.DataFrame, ticker: str, period_label: str) -> go.Figure:
    """Build candlestick price chart with volume and moving averages."""

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    is_up = df["Close"].iloc[-1] >= df["Open"].iloc[0]
    price_color = COLORS["price_up"] if is_up else COLORS["price_down"]

    # use simple line for intraday, candlestick for longer periods
    use_candle = period_label not in ["1D", "1W"]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25]
    )

    # ── Price trace ────────────────────────────────────────────────────────
    if use_candle:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color=COLORS["price_up"],
            decreasing_line_color=COLORS["price_down"],
            increasing_fillcolor=COLORS["price_up"],
            decreasing_fillcolor=COLORS["price_down"],
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Close"],
            name="Price",
            line=dict(color=price_color, width=1.5),
            fill="tozeroy",
            fillcolor=f"rgba({'0,170,68' if is_up else '204,0,0'},0.08)",
        ), row=1, col=1)

    # ── Moving averages ────────────────────────────────────────────────────
    if "MA20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA20"],
            name="MA20", line=dict(color=COLORS["ma20"], width=1, dash="dot"),
        ), row=1, col=1)

    if "MA50" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA50"],
            name="MA50", line=dict(color=COLORS["ma50"], width=1),
        ), row=1, col=1)

    if "MA200" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA200"],
            name="MA200", line=dict(color=COLORS["ma200"], width=1),
        ), row=1, col=1)

    # ── Volume bars ────────────────────────────────────────────────────────
    volume_colors = [
        COLORS["price_up"] if c >= o else COLORS["price_down"]
        for c, o in zip(df["Close"], df["Open"])
    ]

    fig.add_trace(go.Bar(
        x=df.index,
        y=df["Volume"],
        name="Volume",
        marker_color=volume_colors,
        opacity=0.6,
    ), row=2, col=1)

    # ── Layout ─────────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=f"{ticker} — {period_label}",
            x=0,
            y=0.98,
            font=dict(size=14)
        ),
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"], size=12),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=40, b=90),
        height=500,
    )


    # zoom y-axis to actual price range with 2% padding
    price_min = df["Low"].min()
    price_max = df["High"].max()
    padding = (price_max - price_min) * 0.02
    fig.update_yaxes(
        gridcolor=COLORS["grid"],
        showgrid=True,
        zeroline=False,
        range=[price_min - padding, price_max + padding],
        row=1, col=1
    )
    fig.update_yaxes(
        gridcolor=COLORS["grid"],
        showgrid=True,
        zeroline=False,
        row=2, col=1
    )

    return fig