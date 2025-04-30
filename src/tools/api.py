import os
import pandas as pd
import requests
import akshare as ak
from datetime import datetime, timedelta
import numpy as np

from data.cache import get_cache
from data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
)

# Global cache instance
_cache = get_cache()

# 获取价格数据。已测试通过
def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data for A-shares using akshare."""
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by date range and convert to Price objects
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

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
        
        # 缓存结果
        if prices:
            _cache.set_prices(ticker, [p.model_dump() for p in prices])
            
        return prices
        
    except Exception as e:
        print(f"Error fetching price data for {ticker} using akshare: {e}")
        return []


def calculate_start_year(end_date: str, limit: int) -> int:
    """
    计算end_date年份前推limit年的起始年份
    :param end_date: 字符串日期，支持常见格式如"2025-03-29"
    :param limit: 向前推算的年数
    :return: 起始年份
    """
    # 解析日期字符串（支持多种格式）
    dt = datetime.strptime(end_date, "%Y-%m-%d")  # [8,6](@ref)
    # 计算起始年份
    return str(dt.year - limit)  # [6,7](@ref)


    
def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics for A-shares using akshare."""
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        # Filter cached data by date and limit
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # 移除市场前缀，获取纯股票代码
    pure_ticker = ticker.replace('sh.', '').replace('sz.', '').replace('sh', '').replace('sz', '').replace('SH', '').replace('SZ', '').replace('SH.', '').replace('SZ.', '')
    
    start_year = calculate_start_year(end_date, limit)
    
    try:
        # 获取主要财务指标
        fin_indicator = ak.stock_financial_analysis_indicator(symbol=pure_ticker, start_year=start_year)
        
        # 尝试获取资产负债表
        try:
            balance_sheet = ak.stock_financial_report_sina(stock=ticker, symbol="资产负债表")
        except:
            try:
                balance_sheet = ak.stock_financial_report_sina(stock=ticker)
            except:
                balance_sheet = pd.DataFrame()
        
        # 尝试获取利润表
        try:
            income_stmt = ak.stock_financial_report_sina(stock=ticker, symbol="利润表")
        except:
            try:
                income_stmt = ak.stock_financial_report_sina(stock=ticker)
            except:
                income_stmt = pd.DataFrame()

        # 尝试获取现金流量表
        try:
            cash_flow = ak.stock_financial_report_sina(stock=ticker, symbol="现金流量表")
        except:
            try:
                cash_flow = ak.stock_financial_report_sina(stock=ticker)
            except:
                cash_flow = pd.DataFrame()

        # 获取实时行情以计算市值
        market_cap = None
        try:
            quote_df = ak.stock_zh_a_spot_em()
            for _, row in quote_df.iterrows():
                if row['代码'] == pure_ticker:
                    # 总市值（亿元）
                    market_cap = float(row['总市值']) * 100000000  # 转为元
                    break
        except:
            pass
                
        # 获取报告期 - 优先使用财务指标的报告期
        dates = []
        print(f"api.py: fin_indicator 获取的报告期: ")
        if not fin_indicator.empty:
            dates = fin_indicator[["日期"]]
        
        # 如果没有找到报告期，尝试使用其他表格的报告期
        # if not dates:
        #     print("1111")  
        #     all_dfs = [df for df in [balance_sheet, income_stmt, cash_flow] if not df.empty]
        #     for df in all_dfs:
        #         if len(df.columns) > 1:  # 确保有数据列
        #             # 第一列通常是项目名称，其他列是报告期
        #             dates = df[["日期"]]  # list(df.columns[1:])
        #             break

        dates = dates["日期"].tolist()
        # 只保留最近的limit个报告期且不晚于end_date
        valid_dates = [d for d in dates if str(d) <= end_date]
        valid_dates = valid_dates[:limit]
        # print(f"z222222222: {valid_dates}")        
        
        if not valid_dates:
            return []

        # print(f"income_stmt: {income_stmt}")
        # 构建结果
        metrics_list = []
        for date in valid_dates:
            net_income = safe_get_value(income_stmt, '净利润', date, date_field_name='报告日')
            print(f"api.py: date: {date}, net_income: {net_income}")

            # print(f"api.py: fin_indicator: {fin_indicator}")
            # todo: eps_basic 对应的原来的哪个字段，应该从新的接口里取哪个字段？
            eps_basic = safe_get_value(fin_indicator, '基本每股收益', date, '日期')
            print(f"api.py: date: {date}, eps_basic: {eps_basic}")
            # 创建财务指标对象，使用安全的获取方式
            try:
                metrics = FinancialMetrics(
                    ticker=ticker,
                    report_period=str(date),
                    revenue=safe_get_value(income_stmt, "营业收入", date),
                    gross_profit=safe_get_value(income_stmt, "营业利润", date),
                    operating_income=safe_get_value(income_stmt, "营业利润", date),
                    net_income=safe_get_value(income_stmt, "净利润", date),
                    eps_basic=safe_get_value(fin_indicator, "基本每股收益", date),
                    eps_diluted=safe_get_value(fin_indicator, "稀释每股收益", date),
                    dividend_per_share=safe_get_value(fin_indicator, "每股股利", date),
                    total_assets=safe_get_value(balance_sheet, "资产总计", date),
                    total_equity=safe_get_value(balance_sheet, "所有者权益(或股东权益)合计", date),
                    free_cash_flow=safe_get_value(cash_flow, "经营活动产生的现金流量净额", date),
                    operating_cash_flow=safe_get_value(cash_flow, "经营活动产生的现金流量净额", date),
                    pe_ratio=None,  # 将在下一步计算
                    market_cap=market_cap,
                )
                
                # 计算PE比率
                if metrics.net_income and metrics.net_income > 0 and market_cap:
                    metrics.pe_ratio = market_cap / metrics.net_income
                
                metrics_list.append(metrics)
            except Exception as e:
                print(f"Error creating metrics for {ticker} at {date}: {e}")
                continue
            
        # 缓存结果
        if metrics_list:
            _cache.set_financial_metrics(ticker, [m.model_dump() for m in metrics_list])
            
        return metrics_list
        
    except Exception as e:
        print(f"Error fetching financial metrics for {ticker}: {e}")
        return []


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """Fetch line items for A-shares using akshare."""
    # 移除市场前缀，获取纯股票代码
    pure_ticker = ticker.replace('sh.', '').replace('sz.', '').replace('sh', '').replace('sz', '')
    
    try:
        # 获取主要财务指标
        fin_indicator = ak.stock_financial_analysis_indicator(symbol=pure_ticker)
        
        # 尝试获取资产负债表
        try:
            balance_sheet = ak.stock_financial_report_sina(stock=ticker, symbol="资产负债表")
        except:
            try:
                balance_sheet = ak.stock_financial_report_sina(stock=ticker)
            except:
                balance_sheet = pd.DataFrame()
        
        # 尝试获取利润表
        try:
            income_stmt = ak.stock_financial_report_sina(stock=ticker, symbol="利润表")
        except:
            try:
                income_stmt = ak.stock_financial_report_sina(stock=ticker)
            except:
                income_stmt = pd.DataFrame()
        
        # 尝试获取现金流量表
        try:
            cash_flow = ak.stock_financial_report_sina(stock=ticker, symbol="现金流量表")
        except:
            try:
                cash_flow = ak.stock_financial_report_sina(stock=ticker)
            except:
                cash_flow = pd.DataFrame()
        
        # 获取报告期
        dates = []
        all_dfs = [df for df in [fin_indicator, balance_sheet, income_stmt, cash_flow] if not df.empty]
        for df in all_dfs:
            if len(df.columns) > 1:  # 确保有数据列
                # 第一列通常是项目名称，其他列是报告期
                dates.extend(list(df.columns[1:]))
        
        # 去重并排序
        dates = sorted(set(dates), reverse=True)
        
        # 只保留最近的limit个报告期且不晚于end_date
        valid_dates = [d for d in dates if str(d) <= end_date]
        valid_dates = valid_dates[:limit]
        
        if not valid_dates:
            return []
        
        # 设置财务项目与中文对照表
        item_map = {
            "revenue": "营业收入",
            "net_income": "净利润",
            "operating_income": "营业利润",
            "return_on_invested_capital": "净资产收益率加权",
            "gross_margin": "毛利率",
            "operating_margin": "营业利润率",
            "free_cash_flow": "经营活动产生的现金流量净额",
            "capital_expenditure": "购建固定资产、无形资产和其他长期资产支付的现金",
            "cash_and_equivalents": "货币资金",
            "total_debt": "短期借款+长期借款",
            "shareholders_equity": "所有者权益(或股东权益)合计",
            "outstanding_shares": "股本",
            "research_and_development": "研发费用",
            "goodwill_and_intangible_assets": "商誉+无形资产",
        }
        
        # 构建结果
        line_items_list = []
        for date in valid_dates:
            # 创建一个空的LineItem对象
            item = LineItem(ticker=ticker, report_period=str(date))
            
            # 逐个处理请求的财务项目
            for req_item in line_items:
                if req_item in item_map:
                    # 根据映射关系获取对应的中文项目名
                    cn_item = item_map[req_item]
                    
                    # 根据不同的财务项目类型，从不同的报表中获取数据
                    if req_item == "operating_margin":
                        # 计算营业利润率
                        op_income = safe_get_value(income_stmt, "营业利润", date)
                        revenue = safe_get_value(income_stmt, "营业收入", date, date_field_name="报告日")
                        if revenue and revenue > 0:
                            setattr(item, req_item, op_income / revenue)
                    elif req_item == "gross_margin":
                        # 计算毛利率
                        gross_profit = safe_get_value(income_stmt, "营业毛利", date) or safe_get_value(income_stmt, "毛利", date)
                        revenue = safe_get_value(income_stmt, "营业收入", date, date_field_name="报告日")
                        if revenue and revenue > 0:
                            setattr(item, req_item, gross_profit / revenue)
                    elif req_item == "total_debt":
                        # 计算总负债
                        short_debt = safe_get_value(balance_sheet, "短期借款", date) or 0
                        long_debt = safe_get_value(balance_sheet, "长期借款", date) or 0
                        setattr(item, req_item, short_debt + long_debt)
                    elif req_item == "goodwill_and_intangible_assets":
                        # 计算商誉和无形资产总和
                        goodwill = safe_get_value(balance_sheet, "商誉", date) or 0
                        intangible = safe_get_value(balance_sheet, "无形资产", date) or 0
                        setattr(item, req_item, goodwill + intangible)
                    elif req_item == "return_on_invested_capital":
                        # 从财务指标中获取ROIC
                        value = safe_get_value(fin_indicator, "净资产收益率加权", date)
                        if value:
                            setattr(item, req_item, value)
                    elif cn_item in ["营业收入", "净利润", "营业利润"]:
                        # 从利润表获取收入和利润相关数据
                        value = safe_get_value(income_stmt, cn_item, date, date_field_name="报告日")
                        if value is not None:
                            setattr(item, req_item, value)
                    elif "现金流量" in cn_item:
                        # 从现金流量表获取现金流相关数据
                        value = safe_get_value(cash_flow, cn_item, date)
                        if value is not None:
                            setattr(item, req_item, value)
                    elif "支付" in cn_item:
                        # 资本支出等通常为负值
                        value = safe_get_value(cash_flow, cn_item, date)
                        if value is not None:
                            setattr(item, req_item, -abs(value))
                    else:
                        # 默认从资产负债表获取其他项目
                        value = safe_get_value(balance_sheet, cn_item, date)
                        if value is not None:
                            setattr(item, req_item, value)
            
            line_items_list.append(item)
            
        return line_items_list
        
    except Exception as e:
        print(f"Error fetching line items for {ticker}: {e}")
        return []


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[InsiderTrade]:
    """Fetch insider trades for A-shares using akshare."""
    # Check cache first
    if cached_data := _cache.get_insider_trades(ticker):
        # Filter cached data by date range
        filtered_data = [InsiderTrade(**trade) for trade in cached_data 
                        if (start_date is None or (trade.get("transaction_date") or trade["filing_date"]) >= start_date)
                        and (trade.get("transaction_date") or trade["filing_date"]) <= end_date]
        filtered_data.sort(key=lambda x: x.transaction_date or x.filing_date, reverse=True)
        if filtered_data:
            return filtered_data

    # 移除市场前缀，获取纯股票代码
    pure_ticker = ticker.replace('sh.', '').replace('sz.', '').replace('sh', '').replace('sz', '')
    
    try:
        # 获取高管增减持数据
        df = ak.stock_em_executive_change(symbol=pure_ticker)
        
        if df.empty:
            return []
            
        # 转换为API预期的格式
        trades = []
        for _, row in df.iterrows():
            # 处理日期
            try:
                filing_date = str(row['变动日期'])
                if isinstance(filing_date, str):
                    # 确保日期格式统一
                    filing_date = filing_date.split(' ')[0]  # 移除可能的时间部分
                    
                # 过滤日期范围
                if start_date and filing_date < start_date:
                    continue
                if filing_date > end_date:
                    continue
                    
                # 转换交易类型
                transaction_type = "buy" if "增持" in str(row['变动方向']) else "sell"
                
                # 尝试转换数值数据
                try:
                    if isinstance(row['变动数量'], str):
                        shares = float(row['变动数量'].replace(',', ''))
                    else:
                        shares = float(row['变动数量'])
                except:
                    shares = 0
                    
                try:
                    if isinstance(row['变动后持股'], str):
                        shares_held = float(row['变动后持股'].replace(',', ''))
                    else:
                        shares_held = float(row['变动后持股'])
                except:
                    shares_held = 0
                
                # 处理价格
                price = None
                if '增减持价格' in row:
                    try:
                        price = float(row['增减持价格'])
                    except:
                        pass
                
                # 创建内部交易对象
                trade = InsiderTrade(
                    ticker=ticker,
                    insider_name=str(row['变动人']),
                    transaction_date=filing_date,
                    filing_date=filing_date,
                    transaction_type=transaction_type,
                    position=str(row.get('职务', "高管")),
                    shares_transacted=shares,
                    shares_held=shares_held,
                    transaction_price=price,
                )
                trades.append(trade)
                
                # 限制结果数量
                if len(trades) >= limit:
                    break
            except Exception as e:
                print(f"Error processing insider trade: {e}")
                continue
                
        # 缓存结果
        if trades:
            _cache.set_insider_trades(ticker, [t.model_dump() for t in trades])
            
        return trades
        
    except Exception as e:
        print(f"Error fetching insider trades for {ticker}: {e}")
        return []


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[CompanyNews]:
    """Fetch company news for A-shares using akshare."""
    # Check cache first
    if cached_data := _cache.get_company_news(ticker):
        # Filter cached data by date range
        filtered_data = [CompanyNews(**news) for news in cached_data 
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data

    # 移除市场前缀，获取纯股票代码
    pure_ticker = ticker.replace('sh.', '').replace('sz.', '').replace('sh', '').replace('sz', '')
    
    try:
        # 获取个股新闻
        df = ak.stock_news_em(symbol=pure_ticker)
        
        if df.empty:
            return []
            
        # 转换为API预期的格式
        news_list = []
        for _, row in df.iterrows():
            try:
                # 处理日期
                news_date = str(row['日期'])
                if isinstance(news_date, str):
                    news_date = news_date.split(' ')[0]  # 移除可能的时间部分
                    
                # 过滤日期范围
                if start_date and news_date < start_date:
                    continue
                if news_date > end_date:
                    continue
                    
                # 创建新闻对象
                news = CompanyNews(
                    ticker=ticker,
                    date=news_date,
                    headline=str(row['新闻标题']),
                    url=str(row['新闻链接']),
                    source=str(row.get('新闻来源', "东方财富")),
                    summary=str(row.get('内容简介', "")),
                )
                news_list.append(news)
                
                # 限制结果数量
                if len(news_list) >= limit:
                    break
            except Exception as e:
                print(f"Error processing news item: {e}")
                continue
                
        # 缓存结果
        if news_list:
            _cache.set_company_news(ticker, [n.model_dump() for n in news_list])
            
        return news_list
        
    except Exception as e:
        print(f"Error fetching company news for {ticker}: {e}")
        return []


def get_market_cap(
    ticker: str,
    end_date: str,
) -> float | None:
    """Fetch market cap for A-shares using akshare."""
    # 移除市场前缀，获取纯股票代码
    pure_ticker = ticker.replace('sh.', '').replace('sz.', '').replace('sh', '').replace('sz', '')
    
    try:
        # 获取实时行情以获取最新市值
        quote_df = ak.stock_zh_a_spot_em()
        for _, row in quote_df.iterrows():
            if row['代码'] == pure_ticker:
                # 总市值（亿元）转换为元
                return float(row['总市值']) * 100000000
                
        # 如果没有找到，尝试从财务指标获取
        metrics = get_financial_metrics(ticker, end_date, limit=1)
        if metrics and metrics[0].market_cap:
            return metrics[0].market_cap
            
        return None
        
    except Exception as e:
        print(f"Error fetching market cap for {ticker}: {e}")
        return None


# 辅助函数
def safe_get_value(df, item_name, date, date_field_name="日期"):
    """从DataFrame中安全地获取特定项目和日期的值"""
    try:
        if df.empty:
            return None
            
        # print(f"safe_get_value: {df.columns} ")
        # 检查DataFrame的结构
        if item_name in df.columns:
            # 宽表格式：项目名称是列名
            if date_field_name is not None:
                # 将输入日期转换为无分隔符的格式以进行比较
                date_str = str(date)
                if "-" in date_str:
                    # 如果输入日期格式为"YYYY-MM-DD"，转换为"YYYYMMDD"
                    date_str = date_str.replace("-", "")

                # 查找匹配日期的行
                matched_rows = df[date_field_name].astype(str) == date_str
                # print(f"safe_get_value: matched_rows: {matched_rows}")
                if matched_rows.any():
                    # print("matched_rows.any--------------------------------")
                    row = df.loc[matched_rows]
                    if not row.empty:
                        # print(f"not row.empty----{row[item_name].values[0]}, {row[date_field_name].values[0]}----------------------------")
                        return float(row[item_name].values[0])

            # else:
            #     # 如果没有指定日期字段，尝试使用第一列作为日期
            #     date_col = df.columns[0]
            #     date_str = str(date).replace("-", "")
            #     row = df[df[date_col].astype(str) == date_str]
            #     if not row.empty:
            #         return float(row[item_name].values[0])
        else:
            # 长表格式：项目名称在第一列
            row = df[df.iloc[:, 0] == item_name]
            if not row.empty:
                date_str = str(date)
                if date_str in row.columns:
                    value = row[date_str].values[0]
                    # 转换为浮点数
                    if isinstance(value, str):
                        value = value.replace(',', '')
                        return float(value)
                    elif pd.isna(value):
                        return None
                    else:
                        return float(value)
                    
        return None
    except Exception as e:
        print(f"safe_get_value error: {e}")
        return None


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
