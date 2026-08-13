import pandas as pd
import numpy as np
import os


class CleanReport:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.raw_len = len(df)
        self.curr_len = self.raw_len
        self.records = []

    def add_record(self, name):
        before, after = self.curr_len, len(self.df)
        self.curr_len = after
        self.records.append([name, before, after])

    def save(self, path):
        record_df = pd.DataFrame(
            self.records,
            columns=['步骤名', '处理前', '处理后'],
        )
        record_df['删除量'] = record_df['处理前'] - record_df['处理后']
        record_df['变化率'] = round(record_df['处理后'] / record_df['处理前'], 4)
        record_df['总变化率'] = round(record_df['处理后'] / self.raw_len, 4)
        record_df.to_csv(path)


df = pd.read_csv('data/raw/Online_Retail.csv', encoding='latin1')
clean_report = CleanReport(df)

# InvoiceDate 样例是 12/1/10 8:26，需要解析成 datetime
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'].str.strip(), format='%m/%d/%y %H:%M').dt.date
clean_report.add_record('Parse Datetime')

# 规范文本
df['StockCode'] = df['StockCode'].str.strip().str.upper()
df['Description'] = df['Description'].str.strip().str.title()
df['Country'] = df['Description'].str.strip().str.title()
clean_report.add_record('Format Texts')

# 取消单和调账单共 9,291 行，RFM 应该排除
df.loc[df['InvoiceNo'].str.match('^[AC]'), 'InvoiceNo'] = np.nan
df.dropna(subset='InvoiceNo', inplace=True)
clean_report.add_record('Drop A/C Invoice')

# 删除 `CustomerID` 缺失的记录
df.dropna(subset='CustomerID', inplace=True)
clean_report.add_record('Drop Null CustomerID')

# Quantity 有负数，表示退货；需要单独处理或排除。
df.loc[df['Quantity'] <= 0, 'Quantity'] = pd.NA
df.dropna(subset='Quantity', inplace=True)
clean_report.add_record('Drop Negative Quantity')

# UnitPrice 存在 0 和负数。
df.loc[df['UnitPrice'] <= 0, 'UnitPrice'] = pd.NA
df.dropna(subset='UnitPrice', inplace=True)
clean_report.add_record('Drop Negative Unit Price')

# 部分 StockCode 不是正常商品码，例如 POST、DOT、M，属于非商品记录。
df.loc[~df['StockCode'].str.match('^[0-9]+[A-Z]*$'), 'StockCode'] = pd.NA
df.dropna(subset='StockCode', inplace=True)
clean_report.add_record('Drop Error Stock Code')

# 去重
print(df.shape)
df.drop_duplicates(inplace=True)
print(df.shape)
clean_report.add_record('Drop Duplicates')


# 类型调整
df['InvoiceNo'] = df['InvoiceNo'].astype('int32')
# 设置多重索引
df.set_index(['InvoiceNo', 'StockCode'], inplace=True)
# 计算总额
df['LineAmount'] = round(df['Quantity'] * df['UnitPrice'], 2)

# debug: 抽样输出
print(df.sample(n=10))


os.makedirs('data/interim')
# 保存为 parquet
df.to_parquet('data/interim/cleaned_online_retail.parquet')
# 生成质量报告
clean_report.save('data/interim/数据质量报告.csv')