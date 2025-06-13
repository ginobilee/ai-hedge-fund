import akshare as ak
import pandas as pd

def normalize_date(date_str):
    """标准化日期格式，移除所有分隔符和时间部分"""
    if isinstance(date_str, str):
        # 如果包含时间，只保留日期部分
        if " " in date_str:
            date_str = date_str.split(" ")[0]
        return date_str.replace("-", "").replace("/", "").replace(".", "")
    elif pd.isna(date_str):
        return None
    return str(date_str).split(" ")[0].replace("-", "").replace("/", "").replace(".", "")

pure_ticker = '600519'
stock_a_indicator = ak.stock_a_indicator_lg(pure_ticker)
stock_a_indicator['date'] = stock_a_indicator['trade_date'].apply(normalize_date)

def get_pe_pb_ps(indicator: pd.DataFrame, date: str):
    data = indicator[indicator['date']==date].iloc[0]
    print(data)
    price_to_sales_ratio = data['ps_ttm']
    price_to_book_ratio = data['pb']
    price_to_earnings_ratio = data['pe_ttm']
    print(price_to_book_ratio, price_to_sales_ratio,  price_to_earnings_ratio)
    return {
        'pe': price_to_earnings_ratio,
        'pb': price_to_book_ratio,
        'ps': price_to_sales_ratio
    }

d = get_pe_pb_ps(stock_a_indicator, '20210331')
print(d['pe'], d['pb'], d['ps'])