from __future__ import annotations

from datetime import datetime
from html import escape
from math import log10, sqrt
from pathlib import Path

import numpy as np
import pandas as pd


PROCESSED_DIR = Path("data/processed")
OUTPUT_PATH = Path("outputs/rfm_report.html")

SEGMENT_ORDER = [
    "重要价值用户",
    "重要发展用户",
    "重要保持用户",
    "重要挽留用户",
    "一般价值用户",
    "一般发展用户",
    "一般保持用户",
    "一般挽留用户",
]

SEGMENT_BY_CODE = {
    0b111: "重要价值用户",
    0b101: "重要发展用户",
    0b011: "重要保持用户",
    0b001: "重要挽留用户",
    0b110: "一般价值用户",
    0b100: "一般发展用户",
    0b010: "一般保持用户",
    0b000: "一般挽留用户",
}

SEGMENT_META = {
    "重要价值用户": {
        "tone": "emerald",
        "priority": "核心资产",
        "strategy": "保持高价值权益，提供专属客服、新品首发和会员升级路径。",
    },
    "重要发展用户": {
        "tone": "blue",
        "priority": "高频潜力",
        "strategy": "通过交叉销售和品类组合，提升购买频次与客单价。",
    },
    "重要保持用户": {
        "tone": "cyan",
        "priority": "复购维护",
        "strategy": "关注购买周期，通过会员日和定期触达维持活跃度。",
    },
    "重要挽留用户": {
        "tone": "amber",
        "priority": "高价值唤醒",
        "strategy": "使用专属召回券、电话回访和限时权益推动沉睡客户回流。",
    },
    "一般价值用户": {
        "tone": "lime",
        "priority": "价值升级",
        "strategy": "以小额满减和搭配推荐，尝试提升客单价。",
    },
    "一般发展用户": {
        "tone": "sky",
        "priority": "潜力培育",
        "strategy": "通过内容触达和首单激励，建立稳定购买习惯。",
    },
    "一般保持用户": {
        "tone": "slate",
        "priority": "轻量维系",
        "strategy": "使用低成本自动化营销维持曝光，不必投入高额权益。",
    },
    "一般挽留用户": {
        "tone": "rose",
        "priority": "选择性唤醒",
        "strategy": "控制营销成本，仅在关键节点进行批量唤醒。",
    },
}


CSS = """
:root {
  --ink: #132238;
  --muted: #64748b;
  --line: #dce5e9;
  --panel: #ffffff;
  --bg: #f5f7f6;
  --navy: #132238;
  --mint: #18a978;
  --mint-soft: #dff7ed;
  --amber: #e49a21;
  --amber-soft: #fff2d9;
  --rose: #d95757;
  --rose-soft: #fde7e7;
  --blue: #2d7ff9;
  --blue-soft: #e2efff;
  --shadow: 0 18px 48px rgba(19, 34, 56, 0.08);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  color: var(--ink);
  background:
    radial-gradient(circle at 12% -4%, rgba(45, 127, 249, 0.12), transparent 27rem),
    radial-gradient(circle at 88% 4%, rgba(24, 169, 120, 0.14), transparent 26rem),
    var(--bg);
  font-family: "Segoe UI", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, sans-serif;
}

.report {
  width: min(1240px, calc(100% - 32px));
  margin: 0 auto;
  padding: 42px 0 60px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  margin-bottom: 26px;
  animation: rise 0.45s ease-out both;
}

.eyebrow {
  margin: 0 0 9px;
  color: var(--mint);
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.17em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: clamp(2.2rem, 5vw, 4rem);
  line-height: 0.98;
  letter-spacing: -0.055em;
}

.hero p {
  max-width: 620px;
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 1.02rem;
  line-height: 1.7;
}

.hero-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  color: var(--muted);
  font-size: 0.8rem;
  white-space: nowrap;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 13px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.75);
  color: var(--navy);
  font-weight: 800;
  box-shadow: 0 8px 22px rgba(19, 34, 56, 0.06);
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--mint);
  box-shadow: 0 0 0 5px rgba(24, 169, 120, 0.14);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.metric-card {
  min-height: 138px;
  padding: 20px;
  border-radius: 22px;
  background: var(--panel);
  box-shadow: var(--shadow);
  animation: rise 0.5s ease-out both;
}

.metric-label {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.metric-value {
  margin-top: 16px;
  font-size: 2rem;
  font-weight: 900;
  letter-spacing: -0.05em;
}

.metric-sub {
  margin-top: 7px;
  color: var(--muted);
  font-size: 0.82rem;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 18px;
  margin-bottom: 18px;
}

.panel {
  padding: 25px;
  border: 1px solid rgba(220, 229, 233, 0.9);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow);
  animation: rise 0.55s ease-out both;
}

main > section.panel {
  margin-bottom: 18px;
}

main > section.panel:last-of-type {
  margin-bottom: 0;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.section-kicker {
  margin: 0 0 7px;
  color: var(--mint);
  font-size: 0.73rem;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  font-size: 1.35rem;
  letter-spacing: -0.025em;
}

.panel-note {
  color: var(--muted);
  font-size: 0.8rem;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

th, td {
  padding: 13px 11px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: middle;
}

th {
  color: var(--muted);
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}

td.num, th.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.segment-name {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  white-space: nowrap;
}

.segment-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.share-bar {
  display: inline-block;
  width: 54px;
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #e9eff1;
  vertical-align: middle;
}

.share-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #33c6a0, #18a978);
}

.strategy-list {
  display: grid;
  gap: 12px;
}

.strategy-card {
  display: grid;
  grid-template-columns: 12px 1fr;
  gap: 12px;
  padding: 14px 15px;
  border-radius: 16px;
  background: #f7faf9;
}

.strategy-title {
  margin: 0 0 4px;
  font-weight: 900;
}

.strategy-copy {
  margin: 0;
  color: var(--muted);
  font-size: 0.87rem;
  line-height: 1.5;
}

.callout {
  padding: 20px 22px;
  border-left: 5px solid var(--blue);
  border-radius: 16px;
  background: var(--blue-soft);
  margin-bottom: 18px;
}

.callout h3 {
  margin: 0 0 7px;
  font-size: 1rem;
}

.callout p {
  margin: 0;
  color: #41536b;
  line-height: 1.65;
}

.scatter {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 18px;
}

.histogram {
  display: flex;
  align-items: flex-end;
  gap: 7px;
  height: 220px;
  padding-top: 10px;
}

.hist-col {
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  min-width: 0;
  height: 100%;
}

.hist-value {
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 0.65rem;
  font-weight: 800;
}

.hist-bar {
  width: min(100%, 34px);
  min-height: 4px;
  border-radius: 8px 8px 3px 3px;
  animation: grow 0.6s ease-out both;
}

.hist-label {
  margin-top: 8px;
  color: var(--muted);
  font-size: 0.63rem;
  line-height: 1.25;
  text-align: center;
}

.composition-grid {
  display: grid;
  grid-template-columns: 0.75fr 1.25fr;
  gap: 18px;
  margin-bottom: 18px;
}

.donut-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.donut {
  width: 190px;
  height: 190px;
  flex: 0 0 190px;
  border-radius: 50%;
  position: relative;
  box-shadow: inset 0 0 0 1px rgba(19, 34, 56, 0.04);
}

.donut::after {
  position: absolute;
  inset: 34px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--panel);
  content: attr(data-label);
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 800;
  text-align: center;
}

.legend {
  display: grid;
  gap: 9px;
}

.legend-item {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 0.8rem;
}

.legend-swatch {
  width: 9px;
  height: 9px;
  border-radius: 3px;
}

.legend-share {
  font-weight: 900;
  color: var(--ink);
}

.pareto {
  display: block;
  width: 100%;
  height: auto;
}

.stat-summary {
  overflow-x: auto;
}

.mini-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.mini-stat {
  padding: 15px;
  border-radius: 17px;
  background: #f7faf9;
}

.mini-stat-label {
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 800;
}

.mini-stat-value {
  margin-top: 8px;
  font-size: 1.45rem;
  font-weight: 900;
  letter-spacing: -0.04em;
}

footer {
  margin-top: 24px;
  color: var(--muted);
  font-size: 0.78rem;
  text-align: center;
}

@keyframes rise {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes grow {
  from { transform: scaleY(0); transform-origin: bottom; }
  to { transform: scaleY(1); transform-origin: bottom; }
}

@media (max-width: 960px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .grid-2 { grid-template-columns: 1fr; }
  .chart-grid { grid-template-columns: 1fr; }
  .composition-grid { grid-template-columns: 1fr; }
  .mini-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero { flex-direction: column; align-items: flex-start; }
  .hero-meta { align-items: flex-start; }
}

@media (max-width: 620px) {
  .metric-grid { grid-template-columns: 1fr 1fr; }
  .panel { padding: 19px; }
}

@media (max-width: 420px) {
  .metric-grid { grid-template-columns: 1fr; }
  .mini-stat-grid { grid-template-columns: 1fr; }
  .donut-wrap { flex-direction: column; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
"""


class RFMReport:
    def __init__(self, processed_dir: Path = PROCESSED_DIR) -> None:
        self.processed_dir = processed_dir
        self.rfm = self._read("rfm.csv")
        self.stats = self._read("rfm_stats.csv")
        self.dormant = self._read("top5_dormant.csv")
        self.generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self._prepare()

    def _read(self, filename: str) -> pd.DataFrame:
        path = self.processed_dir / filename
        frame = pd.read_csv(path)
        return frame.drop(columns=["Unnamed: 0"], errors="ignore")

    def _prepare(self) -> None:
        self.rfm["customer_id"] = pd.to_numeric(
            self.rfm["customer_id"], errors="coerce"
        ).astype("Int64")
        self.rfm["segment"] = self.rfm.apply(self._segment_for_row, axis=1)
        self.dormant["customer_id"] = pd.to_numeric(
            self.dormant["customer_id"], errors="coerce"
        ).astype("Int64")

        self.stats = self.stats.set_index("customer_type")
        self.stats["segment_revenue"] = (
            self.stats["customers"] * self.stats["average_monetary"]
        )
        self.stats["customer_share"] = (
            self.stats["customers"] / self.stats["customers"].sum()
        )
        self.stats["revenue_share"] = (
            self.stats["segment_revenue"] / self.stats["segment_revenue"].sum()
        )

        self.total_customers = int(len(self.rfm))
        self.total_monetary = float(self.rfm["monetary"].sum())
        self.average_monetary = float(self.rfm["monetary"].mean())
        self.median_monetary = float(self.rfm["monetary"].median())
        self.average_recency = float(self.rfm["recency_days"].mean())
        self.average_frequency = float(self.rfm["frequency"].mean())

        dormant = self.rfm[
            (self.rfm["recency_days"] > 90) & (self.rfm["m_rank"] <= 0.05)
        ]
        self.dormant_count = int(len(dormant))
        self.dormant_revenue = float(dormant["monetary"].sum())
        self.top20_share = self._top_share(0.2)
        self.top50_share = self._top_share(0.5)

    @staticmethod
    def _segment_for_row(row: pd.Series) -> str:
        code = (
            4 * (int(row["r_score"]) - 1)
            + 2 * (int(row["f_score"]) - 1)
            + (int(row["m_score"]) - 1)
        )
        return SEGMENT_BY_CODE.get(code, "未分类")

    def _top_share(self, ratio: float) -> float:
        values = self.rfm["monetary"].sort_values(ascending=False)
        n = max(int(len(values) * ratio), 1)
        return float(values.head(n).sum() / values.sum())

    def render(self) -> str:
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RFM 客户价值分层分析报告</title>
<style>{CSS}</style>
</head>
<body>
<main class="report">
{self._render_hero()}
{self._render_metrics()}
{self._render_executive_callout()}
<section class="grid-2">
{self._render_segment_table()}
{self._render_strategies()}
</section>
{self._render_scatter_panel()}
{self._render_distribution_panel()}
{self._render_composition_panel()}
{self._render_pareto_panel()}
{self._render_dormant_profile()}
{self._render_dormant_table()}
{self._render_top_customers()}
<footer>Generated by RFMReport · {escape(self.generated_at)}</footer>
</main>
</body>
</html>
"""

    def save(self, output_path: Path = OUTPUT_PATH) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(), encoding="utf-8")
        return output_path

    def _render_hero(self) -> str:
        return f"""
<header class="hero">
  <div>
    <p class="eyebrow">RFM Intelligence</p>
    <h1>客户价值分层分析报告</h1>
    <p>基于 Online Retail 交易数据，通过 Recency、Frequency、Monetary 三个维度评估客户价值，识别高价值沉睡客户并输出业务策略。</p>
  </div>
  <div class="hero-meta">
    <div class="pill"><span class="dot"></span>Business Review</div>
    <span>报告生成：{escape(self.generated_at)}</span>
  </div>
</header>
"""

    def _render_metrics(self) -> str:
        metrics = [
            ("客户总数", self._fmt_int(self.total_customers), "完成 RFM 打分的唯一客户"),
            ("总消费金额", self._fmt_money(self.total_monetary), f"中位数 {self._fmt_money(self.median_monetary)}"),
            ("平均购买频次", self._fmt_decimal(self.average_frequency, 1), "订单 / 客户"),
            ("平均沉睡天数", self._fmt_int(int(self.average_recency)), "距最后一次交易"),
            ("高价值沉睡客户", self._fmt_int(self.dormant_count), f"沉睡收入 {self._fmt_money(self.dormant_revenue)}"),
        ]
        cards = "".join(
            f"""
<div class="metric-card">
  <div class="metric-label">{escape(label)}</div>
  <div class="metric-value">{value}</div>
  <div class="metric-sub">{escape(sub)}</div>
</div>
"""
            for label, value, sub in metrics
        )
        return f'<section class="metric-grid">{cards}</section>'

    def _render_executive_callout(self) -> str:
        return f"""
<section class="callout">
  <h3>管理层摘要</h3>
  <p>前 20% 客户贡献了 {self.top20_share:.1%} 的消费金额，前 50% 客户贡献了 {self.top50_share:.1%}。高价值沉睡客户共 {self.dormant_count} 人，累计历史消费 {self._fmt_money(self.dormant_revenue)}，是近期召回动作的第一优先级。</p>
</section>
"""

    def _render_segment_table(self) -> str:
        rows = []
        for segment in SEGMENT_ORDER:
            if segment not in self.stats.index:
                continue
            row = self.stats.loc[segment]
            tone = SEGMENT_META.get(segment, {}).get("tone", "slate")
            color = self._tone_color(tone)
            rows.append(
                f"""
<tr>
  <td><span class="segment-name"><span class="segment-dot" style="background:{color}"></span>{escape(segment)}</span></td>
  <td class="num">{self._fmt_int(int(row["customers"]))}</td>
  <td class="num">{row["customer_share"]:.1%}</td>
  <td class="num">{self._fmt_int(int(row["average_recency_days"]))}</td>
  <td class="num">{self._fmt_decimal(row["average_frequency"], 1)}</td>
  <td class="num">{self._fmt_money(row["average_monetary"])}</td>
  <td class="num">{row["revenue_share"]:.1%}</td>
  <td><span class="share-bar"><span style="width:{row["revenue_share"] * 100:.1f}%"></span></span></td>
</tr>
"""
            )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Segment Overview</p>
      <h2>客户价值分层</h2>
    </div>
    <span class="panel-note">按客户数、平均 RFM 与收入贡献排序</span>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>客户类型</th>
          <th class="num">客户数</th>
          <th class="num">客户占比</th>
          <th class="num">平均 R</th>
          <th class="num">平均 F</th>
          <th class="num">平均 M</th>
          <th class="num">收入占比</th>
          <th>贡献度</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""

    def _render_strategies(self) -> str:
        cards = []
        for segment in ["重要价值用户", "重要发展用户", "重要保持用户", "重要挽留用户"]:
            meta = SEGMENT_META.get(segment, {})
            color = self._tone_color(meta.get("tone", "slate"))
            cards.append(
                f"""
<div class="strategy-card">
  <span class="segment-dot" style="background:{color}; margin-top:4px"></span>
  <div>
    <p class="strategy-title">{escape(segment)} · {escape(meta.get("priority", "待定义"))}</p>
    <p class="strategy-copy">{escape(meta.get("strategy", "根据业务目标持续观察。"))}</p>
  </div>
</div>
"""
            )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Action Plan</p>
      <h2>重点策略建议</h2>
    </div>
  </div>
  <div class="strategy-list">{''.join(cards)}</div>
</section>
"""

    def _render_scatter_panel(self) -> str:
        scatter = self._render_scatter_svg()
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">RFM Map</p>
      <h2>价值地图：沉睡天数与消费金额</h2>
    </div>
    <span class="panel-note">气泡大小表示购买频次，颜色表示客户价值分层</span>
  </div>
  {scatter}
</section>
"""

    def _render_scatter_svg(self) -> str:
        sample = self.rfm.sample(n=min(650, len(self.rfm)), random_state=42)
        width, height = 1000, 470
        left, right, top, bottom = 72, 28, 30, 62
        plot_w = width - left - right
        plot_h = height - top - bottom
        x_values = sample["recency_days"]
        y_values = sample["monetary"].clip(lower=1)
        log_y = y_values.map(lambda value: log10(value))
        freq_values = sample["frequency"]
        max_freq = max(freq_values.max(), 1)
        max_recency = max(x_values.max(), 1)
        min_log = log_y.min()
        max_log = log_y.max()

        points = []
        for _, row in sample.iterrows():
            x = left + (row["recency_days"] / max_recency) * plot_w
            y = top + (1 - ((log10(max(row["monetary"], 1)) - min_log) / (max_log - min_log or 1))) * plot_h
            radius = 3.5 + sqrt(row["frequency"] / max_freq) * 11
            segment = row["segment"]
            color = self._tone_color(SEGMENT_META.get(segment, {}).get("tone", "slate"))
            points.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}" opacity="0.58"/>'
            )

        grid_lines = []
        for i in range(1, 5):
            y = top + plot_h * i / 4
            grid_lines.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#dfe8e7" stroke-width="1"/>'
            )
        for i in range(1, 5):
            x = left + plot_w * i / 4
            grid_lines.append(
                f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height - bottom}" stroke="#dfe8e7" stroke-width="1"/>'
            )

        x_labels = "".join(
            f'<text x="{left + plot_w * i / 4:.1f}" y="{height - 24}" text-anchor="middle" class="axis-label">{int(max_recency * i / 4)}</text>'
            for i in range(5)
        )
        y_labels = "".join(
            f'<text x="{left - 14}" y="{top + plot_h - plot_h * i / 4:.1f}" text-anchor="end" class="axis-label">{10 ** (min_log + (max_log - min_log) * i / 4):,.0f}</text>'
            for i in range(5)
        )
        return f"""
<svg class="scatter" viewBox="0 0 {width} {height}" role="img" aria-label="RFM scatter plot">
  <style>
    .axis-label {{ fill: #7b8794; font-size: 12px; font-weight: 700; }}
  </style>
  {''.join(grid_lines)}
  <text x="{(left + (width - right)) / 2:.1f}" y="{height - 3}" text-anchor="middle" class="axis-label">沉睡天数（R）</text>
  <text x="18" y="{(top + height - bottom) / 2:.1f}" text-anchor="middle" class="axis-label" transform="rotate(-90 18 {(top + height - bottom) / 2:.1f})">消费金额（M，对数刻度）</text>
  {''.join(points)}
  {x_labels}
  {y_labels}
</svg>
"""

    def _render_distribution_panel(self) -> str:
        return f"""
<section class="chart-grid">
{self._render_histogram_panel("recency_days", "Recency 分布", "沉睡天数", "blue")}
{self._render_histogram_panel("frequency_log", "Frequency 分布（对数）", "购买频次", "emerald")}
{self._render_histogram_panel("monetary_log", "Monetary 分布（对数）", "消费金额", "amber")}
</section>
"""

    def _render_histogram_panel(
        self, column: str, title: str, unit: str, tone: str
    ) -> str:
        if column == "monetary_log":
            values = np.log10(self.rfm["monetary"].clip(lower=1))
            counts, edges = np.histogram(values, bins=10)
            labels = [self._fmt_money(float(10 ** edge)) for edge in edges[:-1]]
        elif column == "frequency_log":
            values = np.log10(self.rfm["frequency"].clip(lower=1))
            counts, edges = np.histogram(values, bins=10)
            labels = [
                f"{int(round(10 ** edges[i])):,}-{int(round(10 ** edges[i + 1])):,}"
                for i in range(len(edges) - 1)
            ]
        else:
            values = self.rfm[column]
            counts, edges = np.histogram(values, bins=10)
            labels = [
                f"{int(edges[i]):,}-{int(edges[i + 1]):,}"
                for i in range(len(edges) - 1)
            ]

        max_count = max(int(counts.max()), 1)
        color = self._tone_color(tone)
        bars = "".join(
            f"""
<div class="hist-col">
  <div class="hist-value">{int(count):,}</div>
  <div class="hist-bar" style="height:{(count / max_count * 100):.1f}%; background:{color};"></div>
  <div class="hist-label">{escape(label)}</div>
</div>
"""
            for count, label in zip(counts, labels)
        )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Distribution</p>
      <h2>{escape(title)}</h2>
    </div>
    <span class="panel-note">单位：{escape(unit)}</span>
  </div>
  <div class="histogram">{bars}</div>
</section>
"""

    def _render_composition_panel(self) -> str:
        donut = self._render_segment_donut_panel()
        summary = self._render_stat_summary()
        return f"""
<section class="composition-grid">
{donut}
{summary}
</section>
"""

    def _render_segment_donut_panel(self) -> str:
        segments = self.stats.reindex(SEGMENT_ORDER).dropna(subset=["customers"])
        total = max(int(segments["customers"].sum()), 1)
        gradient_parts = []
        legend_items = []
        start = 0.0
        for segment, row in segments.iterrows():
            share = float(row["customers"]) / total
            end = start + share * 100
            color = self._tone_color(
                SEGMENT_META.get(segment, {}).get("tone", "slate")
            )
            gradient_parts.append(f"{color} {start:.2f}% {end:.2f}%")
            legend_items.append(
                f"""
<div class="legend-item">
  <span class="legend-swatch" style="background:{color}"></span>
  <span>{escape(segment)}</span>
  <span class="legend-share">{share:.1%}</span>
</div>
"""
            )
            start = end

        gradient = ", ".join(gradient_parts)
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Segment Mix</p>
      <h2>客户价值分层构成</h2>
    </div>
  </div>
  <div class="donut-wrap">
    <div class="donut" style="background: conic-gradient({gradient}); white-space: pre-line;" data-label="客户总数\n{self._fmt_int(total)}"></div>
    <div class="legend">{''.join(legend_items)}</div>
  </div>
</section>
"""

    def _render_pareto_panel(self) -> str:
        values = self.rfm["monetary"].sort_values(ascending=False).to_numpy()
        if len(values) == 0:
            return ""
        cumulative = np.cumsum(values) / values.sum()
        width, height = 1000, 420
        left, right, top, bottom = 72, 28, 34, 64
        plot_w = width - left - right
        plot_h = height - top - bottom
        n = len(values)
        step = max(1, n // 320)
        points = []
        for index in range(0, n, step):
            x = left + (index / max(n - 1, 1)) * plot_w
            y = top + (1 - cumulative[index]) * plot_h
            points.append(f"{x:.1f},{y:.1f}")
        if not points or n < 2:
            return ""
        points.append(f"{width - right:.1f},{top:.1f}")
        line_points = " ".join(points)
        area_points = (
            f"{left:.1f},{height - bottom:.1f} "
            + line_points
            + f" {width - right:.1f},{height - bottom:.1f}"
        )
        top20_x = left + 0.2 * plot_w
        top50_x = left + 0.5 * plot_w

        grid_lines = "".join(
            f'<line x1="{left}" y1="{top + plot_h * i / 4:.1f}" x2="{width - right}" y2="{top + plot_h * i / 4:.1f}" stroke="#dfe8e7" stroke-width="1"/>'
            for i in range(1, 5)
        )
        x_labels = "".join(
            f'<text x="{left + plot_w * i / 4:.1f}" y="{height - 22}" text-anchor="middle" class="axis-label">{int(i * 25)}%</text>'
            for i in range(5)
        )
        y_labels = "".join(
            f'<text x="{left - 13}" y="{top + plot_h - plot_h * i / 4:.1f}" text-anchor="end" class="axis-label">{int(i * 25)}%</text>'
            for i in range(5)
        )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Revenue Concentration</p>
      <h2>收入集中度 Pareto 曲线</h2>
    </div>
    <span class="panel-note">客户按消费金额降序排列</span>
  </div>
  <svg class="pareto" viewBox="0 0 {width} {height}" role="img" aria-label="Revenue Pareto curve">
    <style>
      .axis-label {{ fill: #7b8794; font-size: 12px; font-weight: 700; }}
      .marker {{ fill: #d95757; font-size: 12px; font-weight: 900; }}
    </style>
    {grid_lines}
    <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{top}" stroke="#cbd7d6" stroke-width="1" stroke-dasharray="6 6"/>
    <polygon points="{area_points}" fill="rgba(45, 127, 249, 0.12)"/>
    <polyline points="{line_points}" fill="none" stroke="#2d7ff9" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>
    <line x1="{top20_x:.1f}" y1="{top}" x2="{top20_x:.1f}" y2="{height - bottom}" stroke="#d95757" stroke-width="1.5" stroke-dasharray="5 5"/>
    <line x1="{top50_x:.1f}" y1="{top}" x2="{top50_x:.1f}" y2="{height - bottom}" stroke="#d95757" stroke-width="1.5" stroke-dasharray="5 5"/>
    <text x="{top20_x + 8:.1f}" y="{top + 20:.1f}" class="marker">Top 20%</text>
    <text x="{top50_x + 8:.1f}" y="{top + 20:.1f}" class="marker">Top 50%</text>
    <text x="{(left + width - right) / 2:.1f}" y="{height - 3}" text-anchor="middle" class="axis-label">客户累计占比</text>
    <text x="18" y="{(top + height - bottom) / 2:.1f}" text-anchor="middle" class="axis-label" transform="rotate(-90 18 {(top + height - bottom) / 2:.1f})">收入累计占比</text>
    {x_labels}
    {y_labels}
  </svg>
</section>
"""

    def _render_stat_summary(self) -> str:
        metrics = [
            ("recency_days", "Recency（沉睡天数）"),
            ("frequency", "Frequency（购买频次）"),
            ("monetary", "Monetary（消费金额）"),
        ]
        rows = []
        for column, label in metrics:
            series = self.rfm[column]
            desc = series.describe()

            def fmt(value: float) -> str:
                if column == "monetary":
                    return self._fmt_money(value)
                return self._fmt_decimal(value, 2)

            rows.append(
                f"""
<tr>
  <td><strong>{escape(label)}</strong></td>
  <td class="num">{fmt(desc["mean"])}</td>
  <td class="num">{fmt(desc["50%"])}</td>
  <td class="num">{fmt(desc["min"])}</td>
  <td class="num">{fmt(desc["25%"])}</td>
  <td class="num">{fmt(desc["75%"])}</td>
  <td class="num">{fmt(desc["max"])}</td>
</tr>
"""
            )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Statistical Summary</p>
      <h2>RFM 关键统计摘要</h2>
    </div>
  </div>
  <div class="stat-summary">
    <table>
      <thead>
        <tr>
          <th>指标</th>
          <th class="num">均值</th>
          <th class="num">中位数</th>
          <th class="num">最小值</th>
          <th class="num">Q1</th>
          <th class="num">Q3</th>
          <th class="num">最大值</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""

    def _render_dormant_profile(self) -> str:
        dormant = self.rfm[
            (self.rfm["recency_days"] > 90) & (self.rfm["m_rank"] <= 0.05)
        ]
        if dormant.empty:
            return ""
        avg_recency = float(dormant["recency_days"].mean())
        avg_frequency = float(dormant["frequency"].mean())
        total_revenue = float(dormant["monetary"].sum())
        revenue_share = total_revenue / self.total_monetary if self.total_monetary else 0.0
        top_segment = (
            str(dormant["segment"].value_counts().idxmax())
            if dormant["segment"].notna().any()
            else "未分类"
        )
        cards = [
            ("沉睡客户数", self._fmt_int(len(dormant)), "recency > 90 且 M 前 5%"),
            ("平均沉睡天数", self._fmt_int(int(avg_recency)), "从最近一次交易计算"),
            ("平均购买频次", self._fmt_decimal(avg_frequency, 1), "历史订单数"),
            ("沉睡客户收入", self._fmt_money(total_revenue), f"占总收入 {revenue_share:.1%}"),
        ]
        cards_html = "".join(
            f"""
<div class="mini-stat">
  <div class="mini-stat-label">{escape(label)}</div>
  <div class="mini-stat-value">{value}</div>
  <div class="metric-sub">{escape(sub)}</div>
</div>
"""
            for label, value, sub in cards
        )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Dormant Profile</p>
      <h2>高价值沉睡客户画像</h2>
    </div>
    <span class="panel-note">主要分层：{escape(top_segment)}</span>
  </div>
  <div class="mini-stat-grid">{cards_html}</div>
</section>
"""

    def _render_top_customers(self) -> str:
        top = self.rfm.nlargest(10, "monetary")[
            ["customer_id", "recency_days", "frequency", "monetary", "segment"]
        ]
        rows = []
        for _, row in top.iterrows():
            tone = SEGMENT_META.get(row["segment"], {}).get("tone", "slate")
            color = self._tone_color(tone)
            rows.append(
                f"""
<tr>
  <td><code>{escape(str(row["customer_id"]))}</code></td>
  <td class="num">{self._fmt_int(int(row["recency_days"]))}</td>
  <td class="num">{self._fmt_int(int(row["frequency"]))}</td>
  <td class="num">{self._fmt_money(row["monetary"])}</td>
  <td><span class="segment-name"><span class="segment-dot" style="background:{color}"></span>{escape(row["segment"])}</span></td>
</tr>
"""
            )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Top Customers</p>
      <h2>Top 10 高价值客户</h2>
    </div>
    <span class="panel-note">按历史消费金额排序</span>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>客户 ID</th>
          <th class="num">沉睡天数</th>
          <th class="num">购买频次</th>
          <th class="num">历史消费</th>
          <th>客户分层</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""

    def _render_dormant_table(self) -> str:
        rows = []
        for _, row in self.dormant.iterrows():
            action = self._dormant_action(row)
            rows.append(
                f"""
<tr>
  <td><code>{escape(str(row["customer_id"]))}</code></td>
  <td class="num">{self._fmt_int(int(row["recency_days"]))}</td>
  <td class="num">{self._fmt_int(int(row["frequency"]))}</td>
  <td class="num">{self._fmt_money(row["monetary"])}</td>
  <td>{escape(row["customer_type"])}</td>
  <td><span class="pill">{escape(action)}</span></td>
</tr>
"""
            )
        return f"""
<section class="panel">
  <div class="panel-header">
    <div>
      <p class="section-kicker">Win-back List</p>
      <h2>Top 5 高价值沉睡客户</h2>
    </div>
    <span class="panel-note">沉睡超过 90 天，且金额排名前 5%</span>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>客户 ID</th>
          <th class="num">沉睡天数</th>
          <th class="num">购买频次</th>
          <th class="num">历史消费</th>
          <th>客户类型</th>
          <th>建议动作</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""

    @staticmethod
    def _dormant_action(row: pd.Series) -> str:
        recency_days = int(row["recency_days"])
        frequency = int(row["frequency"])
        monetary = float(row["monetary"])
        customer_type = str(row["customer_type"])

        if recency_days >= 240 and frequency <= 2:
            return "专线回访 + 大额券"
        if monetary >= 30000:
            return "VIP 专属召回 + 权益礼包"
        if customer_type == "重要挽留用户":
            return "人工电话回访"
        if frequency >= 4:
            return "新品首发提醒"
        return "短信 + 邮件自动化召回"

    @staticmethod
    def _tone_color(tone: str) -> str:
        return {
            "emerald": "#18a978",
            "blue": "#2d7ff9",
            "cyan": "#2aa9c9",
            "amber": "#e49a21",
            "lime": "#7fb82f",
            "sky": "#57a6d8",
            "slate": "#6c7a89",
            "rose": "#d95757",
        }.get(tone, "#6c7a89")

    @staticmethod
    def _fmt_int(value: int) -> str:
        return f"{int(value):,}"

    @staticmethod
    def _fmt_decimal(value: float, digits: int = 2) -> str:
        return f"{value:,.{digits}f}"

    @staticmethod
    def _fmt_money(value: float) -> str:
        return f"¥{value:,.0f}"


def main() -> None:
    report = RFMReport()
    output = report.save()
    print(f"RFM report generated: {output.resolve()}")


if __name__ == "__main__":
    main()
