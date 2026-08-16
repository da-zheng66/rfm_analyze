![部分截图](./assets/report_preview.png)

# 电商客户价值分层与 RFM 分析

> 从 54 万条原始交易明细，到可执行的客户分层、召回名单与经营仪表盘。
> 本项目的目标不是“跑通一个模型”，而是完整展示本人如何把业务问题转化为清洗、分析、洞察和行动方案。

## 项目定位

本项目基于英国 Online Retail 电商交易数据，构建一套客户价值分析闭环：

```text
业务问题
  → 数据获取与探查
  → 数据清洗
  → RFM 特征计算
  → 客户价值分层
  → 高价值沉睡用户识别
  → 可视化经营报告
```

最终输出可以直接支撑用户运营和营销资源分配决策。

## 数据集

[`Online_Retail.csv`](https://www.kaggle.com/datasets/tunguz/online-retail)：

```text
InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country
536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,12/1/10 8:26,2.55,17850,United Kingdom
...
```

该数据集存在以下问题：

- `InvoiceDate` 以 `12/1/10 8:26` 等字符串形式存储，需要解析为日期时间类型。
- `CustomerID` 缺失 135,080 行，约占原始数据的 24.9%，这些记录无法归因到具体客户。
- 5,268 行完全重复，需要去重。
- `InvoiceNo` 以 `C` 开头表示取消订单，共 9,288 行；另有 3 行 `A` 开头调账记录，不能作为正常成交数据。
- `Quantity` 存在 10,624 条负值，代表退货；`UnitPrice` 存在 2 条负值和 2,515 条 0 值。
- 部分 `StockCode` 是非商品代码，例如 `POST`、`DOT`、`M`，需要在分析前识别并剔除。
- `Description` 存在 1,454 条缺失，且文本格式不统一。

## 核心成果

[点击此处预览完整的可视化报告](https://html-preview.github.io/?url=https://github.com/da-zheng66/rfm_analyze/blob/main/outputs/rfm_report.html)

项目输出包括：

- 8 类客户价值群体。
- 高价值沉睡客户召回名单。
- 收入集中度 Pareto 分析。
- RFM 分布和关键统计摘要。
- Top 客户明细与差异化策略建议。

## 项目架构

```text
.
├── main.py                   # 端到端流程入口
├── app_config.toml           # 所有可调参数
├── data/
│   ├── raw/                  # 原始 CSV
│   ├── interim/              # 清洗后的 Parquet
│   └── processed/            # RFM、分层和沉睡客户结果
├── outputs/
│   └── rfm_report.html       # 自包含可视化报告
└── src/
    ├── config.py             # 惰性配置加载与单例
    ├── fetch.py              # 下载原始数据
    ├── clean.py              # pandas 数据清洗与质量报告
    ├── analyze.py            # DuckDB RFM 计算与客户分层
    └── report.py             # HTML 分析报告
```

## 配置化设计

所有路径、文件名、数据集参数、清洗规则、RFM 阈值和报告参数均集中在：

```text
app_config.toml
```

典型配置结构：

```toml
[paths]
raw_dir = "data/raw"
interim_dir = "data/interim"
processed_dir = "data/processed"
output_dir = "outputs"

[rfm]
tiles = 6
base_date = "2011-12-10"
r_threshold = 4
f_threshold = 4
m_threshold = 6
dormant_recency_days = 90
dormant_monetary_percentile = 0.05
```

通过 `src/config.py` 中的 `cfg()` 获取全局惰性单例，各模块不再散落硬编码参数。

## 运行方式

安装依赖：

```bash
uv sync
```

一键运行完整流程：

```bash
uv run python main.py
```

该命令会依次执行：

```text
run_fetch -> run_clean -> run_analyze -> run_report
```

也可以单独运行某个阶段：

```bash
uv run python -m src.fetch
uv run python -m src.clean
uv run python -m src.analyze
uv run python -m src.report
```

最终报告位于：

```text
outputs/rfm_report.html
```

## 分析流程

### 1. 数据获取

`fetch.py` 使用 `kagglehub` 下载 Online Retail 数据，并保存到 `data/raw/`。

### 2. 数据探查与清洗

`clean.py` 使用 pandas 完成：

- 日期、金额、客户 ID 等字段类型转换。
- 重复记录、取消订单、退货记录识别与处理。
- 缺失客户 ID、异常价格和异常商品代码处理。
- 计算辅助列用于后续分析。
- 记录每一步的数据量变化，输出数据质量报告。

清洗结果保存为：

```text
data/interim/cleaned_online_retail.parquet
```

### 3. RFM 特征计算

`analyze.py` 使用 DuckDB SQL 完成：

- `Recency`：客户距离最后一次交易的沉睡天数。
- `Frequency`：客户的历史订单数量。
- `Monetary`：客户的历史消费金额。
- 使用 `NTILE()` 生成 RFM 分数。
- 使用 `PERCENT_RANK()` 识别金额排名前 5% 的客户。

### 4. 客户分层与业务解释

根据配置中的 R、F、M 阈值，将客户划分为 8 类群体，并赋予业务含义和运营策略。

### 5. 高价值沉睡客户识别

使用配置中的沉睡天数和金额百分位阈值筛选高价值沉睡客户，并根据客户特征动态生成召回动作。

### 6. 可视化报告

`report.py` 生成自包含 HTML 经营报告，包含：

- 管理层摘要和核心 KPI。
- RFM 分布直方图。
- 客户价值分层环形图。
- 收入集中度 Pareto 曲线。
- RFM 关键统计摘要。
- 高价值沉睡客户召回名单。
- Top 10 高价值客户明细。

## 技术栈

| 工具 | 用途 |
| --- | --- |
| Python | 数据处理、流程编排和报告生成 |
| pandas | 数据探查、清洗、类型转换和结果汇总 |
| DuckDB | SQL 连接、分组聚合和窗口函数 |
| PyArrow | Parquet 中间结果读写 |
| kagglehub | 数据集获取 |
| TOML / tomllib | 项目配置管理 |
| HTML / CSS / SVG | 自包含可视化报告 |
