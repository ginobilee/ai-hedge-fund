import akshare as ak
import pandas as pd

from src.data.models import (
    Price,
    PriceResponse,
)

# stock_individual_info_em_df = ak.stock_individual_info_em(symbol="600519")
# total_share_capital = stock_individual_info_em_df[stock_individual_info_em_df['item'] == "总股本"]["value"].values[0]
# print(total_share_capital)


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


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    if not prices:
        return pd.DataFrame()
        
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)

# 获取价格数据。已测试通过
def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data for A-shares using akshare."""

    ak_ticker = ticker.replace('.', '')
    
    # 处理日期格式
    start_date_fmt = start_date.replace('-', '')
    end_date_fmt = end_date.replace('-', '')
    
    try:
        # 获取A股历史行情数据
        df = ak.stock_zh_a_hist(
            symbol=ak_ticker, 
            period="daily",
            start_date=start_date_fmt, 
            end_date=end_date_fmt, 
            adjust="qfq"
        )
        
        # 处理可能的空数据
        if df.empty:
            return []
            
        # 转换为API预期的格式
        prices = []
        for _, row in df.iterrows():
            # 将日期转为ISO格式字符串
            if isinstance(row['日期'], str):
                date_str = row['日期']
                if len(date_str) == 8:  # 如果格式是YYYYMMDD
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                date_str = row['日期'].strftime('%Y-%m-%d')
            
            price = Price(
                time=date_str,
                date=normalize_date(date_str),
                open=float(row['开盘']),
                high=float(row['最高']),
                low=float(row['最低']),
                close=float(row['收盘']),
                volume=float(row['成交量']),
                amount=float(row.get('成交额', 0)),
                ticker=ticker
            )
            prices.append(price)
        
        # 按日期降序排序
        prices.sort(key=lambda x: x.time, reverse=True)
        
        # # 缓存结果
        # if prices:
        #     _cache.set_prices(ticker, [p.model_dump() for p in prices])
            
        print(prices)
        return prices
        
    except Exception as e:
        print(f"Error fetching price data for {ticker} using akshare: {e}")
        return []

# prices = get_prices("600519", "2021-05-04", "2023-05-03")

# prices = get_prices(ticker="600519", start_date="20250304", end_date='20250606')
prices = get_price_data(ticker="600519", start_date="20250304", end_date='20250606')
print(prices)