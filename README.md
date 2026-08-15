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
[`Online_Retail.csv`](https://www.kaggle.com/datasets/tunguz/online-retail):
```
InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country
536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,12/1/10 8:26,2.55,17850,United Kingdom
536365,71053,WHITE METAL LANTERN,6,12/1/10 8:26,3.39,17850,United Kingdom
536365,84406B,CREAM CUPID HEARTS COAT HANGER,8,12/1/10 8:26,2.75,17850,United Kingdom
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
- `Country` 包含 38 个国家，其中存在 `Unspecified`，需要根据分析目标决定是否保留。


## 核心成果

[点击此处预览完整的可视化报告](https://html-preview.github.io/?url=https://github.com/da-zheng66/rfm_analyze/blob/main/outputs/rfm_report.html)

## 业务价值

- 将客户划分为 8 类价值群体，避免“所有客户同等对待”。
- 识别高价值沉睡客户，并输出差异化召回动作。
- 分析收入集中度，帮助业务负责人判断客户结构是否健康。
- 通过 RFM 分数和业务解释，把技术结果翻译成运营策略。
- 最终交付自包含 HTML 报告，便于非技术同事直接阅读。

## 分析流程

### 1. 数据获取

使用 `kagglehub` 下载 Online Retail 数据，统一保存到 `data/raw/`。

### 2. 数据探查与清洗

使用 pandas 完成：

- 日期、金额、客户 ID 等字段类型转换。
- 重复记录、取消订单、退货记录识别与处理。
- 缺失客户 ID、异常价格和异常商品代码处理。
- 生成 `LineAmount = Quantity * UnitPrice`。
- 记录每一步的数据量变化，输出数据质量报告。

清洗结果保存为 `data/interim/cleaned_online_retail.parquet`。

### 3. RFM 特征计算

使用 DuckDB SQL 完成：

- `Recency`：客户距离最后一次交易的沉睡天数。
- `Frequency`：客户的历史订单数量。
- `Monetary`：客户的历史消费金额。
- 使用 `NTILE()` 生成 RFM 分数。
- 使用 `PERCENT_RANK()` 识别金额排名前 5% 的客户。

### 4. 客户分层与业务解释

将 R、F、M 分数组合为 8 类客户群体，并赋予业务含义，例如：

- 重要价值用户
- 重要发展用户
- 重要保持用户
- 重要挽留用户
- 一般价值用户
- 一般发展用户
- 一般保持用户
- 一般挽留用户

### 5. 高价值沉睡客户识别

定义沉睡条件为：

```text
recency_days > 90
且 monetary 排名位于前 5%
```

针对筛选出的客户，根据沉睡时长、购买频次、历史消费和客户类型，动态生成召回动作。

### 6. 可视化报告

生成自包含 HTML 经营报告，包含：

- 管理层摘要和核心 KPI。
- RFM 分布直方图。
- 客户价值分层环形图。
- 收入集中度 Pareto 曲线。
- RFM 关键统计摘要。
- Top 5 高价值沉睡客户召回名单。
- Top 10 高价值客户明细。

## 技术栈

| 工具 | 用途 |
| --- | --- |
| Python | 数据处理、流程编排和报告生成 |
| pandas | 数据探查、清洗、类型转换和结果汇总 |
| DuckDB | SQL 连接、分组聚合和窗口函数 |
| PyArrow | Parquet 中间结果读写 |
| kagglehub | 数据集获取 |
| HTML / CSS / SVG | 自包含可视化报告 |

## 项目结构

```text
.
├── data/
│   ├── raw/                       # 原始数据
│   ├── interim/                   # 清洗后的 Parquet
│   └── processed/                 # RFM 和分层结果
├── outputs/
│   └── rfm_report.html            # 可视化经营报告
├── src/
│   ├── fetch.py                   # 下载原始数据
│   ├── clean.py                   # pandas 数据清洗与质量报告
│   ├── analyze.py                 # DuckDB RFM 计算与客户分层
│   └── report.py                  # HTML 分析报表
├── IMPLEMENTATION.md              # 详细实施步骤
├── pyproject.toml
└── README.md
```

## 快速复现

```bash
# 安装依赖
uv sync

# 下载原始数据
uv run python -m src.fetch

# 清洗数据
uv run python -m src.clean

# 计算 RFM 和客户分层
uv run python -m src.analyze

# 生成分析报告
uv run python -m src.report
```

最终报告位于：

```text
outputs/rfm_report.html
```

## 后续优化方向

- 为清洗和 RFM 逻辑补充单元测试。
- 增加配置化阈值，使沉睡客户和分段规则可灵活调整。
- 增加交互式筛选，例如按国家、时间和客户群体下钻。
- 引入 CI/CD，自动验证数据质量并生成最新报告。

## 数据来源

本项目使用 Online Retail / E-Commerce Data，来源于英国在线零售交易数据。分析仅用于展示数据能力，不包含个人敏感信息。
