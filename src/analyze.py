import duckdb
import pandas as pd
import numpy as np
import os

INPUT_PATH = 'data/interim/cleaned_online_retail.parquet'
os.makedirs('data/processed')
con = duckdb.connect(database=INPUT_PATH)

# 计算 RFM
rfm = con.execute('''
WITH rfm AS (
    SELECT
        CustomerID AS customer_id,
        DATEDIFF('day', MAX(InvoiceDate), DATE '2011-12-10') AS recency_days,
        COUNT(DISTINCT InvoiceNo) AS frequency,
        ROUND(SUM(LineAmount), 2) AS monetary
    FROM
        cleaned_online_retail
    GROUP BY
        CustomerID
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    NTILE(2) OVER (ORDER BY recency_days DESC) AS r_score,
    NTILE(2) OVER (ORDER BY frequency ASC) AS f_score,
    NTILE(2) OVER (ORDER BY monetary ASC) AS m_score,
    PERCENT_RANK() OVER (ORDER BY recency_days ASC) AS r_rank,
    PERCENT_RANK() OVER (ORDER BY frequency DESC) AS f_rank,
    PERCENT_RANK() OVER (ORDER BY monetary DESC) AS m_rank
FROM
    rfm
ORDER BY
    r_rank ASC,
    f_rank ASC,
    m_rank ASC;
''').fetch_df()

rfm.to_csv('data/processed/rfm.csv')

# 用户分层
customer_types = {
    0b111: "重要价值用户",
    0b101: "重要发展用户",
    0b011: "重要保持用户",
    0b001: "重要挽留用户",
    0b110: "一般价值用户",
    0b100: "一般发展用户",
    0b010: "一般保持用户",
    0b000: "一般挽留用户",
}

bitflags = 4 * (rfm['r_score'] - 1) + 2 * (rfm['f_score'] - 1) + (rfm['m_score'] - 1)
rfm['customer_type'] = bitflags.map(customer_types)


rfm_stats = rfm.groupby('customer_type').agg(
    customers=('customer_id', 'count'),
    average_recency_days = ('recency_days', lambda x: np.ceil(x.mean()).astype('int32')),
    average_frequency=('frequency', lambda x: np.ceil(x.mean()).astype('int32')),
    average_monetary=('monetary', lambda x: round(x.mean(), 2)),
)
rfm_stats.to_csv('data/processed/rfm_stats.csv')

top5_dormant = rfm[(rfm['recency_days'] > 90) & (rfm['m_rank'] <= 0.05)].sort_values(by='monetary', ascending=False)
top5_dormant.to_csv('data/processed/top5_dormant.csv')
