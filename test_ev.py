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


def safe_float(value):
    """安全地将值转换为浮点数，处理nan值"""
    try:
        if pd.isna(value):
            return 0.0
        if isinstance(value, str):
            return float(value.replace(',', ''))
        return float(value)
    except Exception as e:
        print(f"safe_float 转换为浮点数失败: {e}")
        return 0.0

def calculate_enterprise_value(market_cap: float, balance_sheet: pd.DataFrame, date: str) -> float:
    """计算企业价值(EV)
    
    EV = Market Cap + Total Debt - Cash & Equivalents + Minority Interest
    
    Args:
        market_cap: 市值（元）
        balance_sheet: 资产负债表数据
        date: 报告期
    """
    try:
        if pd.isna(market_cap) or market_cap is None:
            return None
        
        # 获取指定日期的数据
        data = balance_sheet[balance_sheet['报告日']==date]
        if data.empty:
            print(f"未找到日期 {date} 的数据")
            return None
            
        # 使用 .iloc[0] 获取第一个值
        total_debt = safe_float(data['负债合计'].iloc[0])
        cash = safe_float(data['货币资金'].iloc[0])
        trading_assets = safe_float(data['交易性金融资产'].iloc[0])
        minority_interest = safe_float(data['少数股东权益'].iloc[0])
        
        # 打印调试信息
        print(f"负债合计: {total_debt}")
        print(f"货币资金: {cash}")
        print(f"交易性金融资产: {trading_assets}")
        print(f"少数股东权益: {minority_interest}")
        
        # 计算企业价值
        ev = market_cap + total_debt - (cash + trading_assets) + minority_interest
        
        return ev
        
    except Exception as e:
        print(f"计算企业价值失败: {e}")
        import traceback
        traceback.print_exc()
        return None

market_cap = 100

ticker = "600519"

balance_sheet = ak.stock_financial_report_sina(stock=ticker, symbol="资产负债表")

ev = calculate_enterprise_value(market_cap, balance_sheet, "20240930")
print(ev)