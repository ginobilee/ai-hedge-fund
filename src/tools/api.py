import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)


import pandas as pd
import requests
import akshare as ak
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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
    # if cached_data := _cache.get_prices(ticker):
    #     # Filter cached data by date range and convert to Price objects
    #     filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
    #     if filtered_data:
    #         return filtered_data

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
        print(f"prices: {df}")
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

def calculate_start_date(end_date: str, limit: int) -> str:
    dt = datetime.strptime(end_date, "%Y-%m-%d")  # [8,6](@ref)

    years_ago = dt - relativedelta(years=limit)
    result = years_ago.strftime("%Y-%m-%d")
    return result

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

def calculate_ebitda(profit_sheet_dc: pd.DataFrame, cash_flow_dc: pd.DataFrame, date: str):
    # 计算 EBITDA
    try:
        date = normalize_date(date)
        print(f"api.py: calculate ebitda for {date} ")
        # print(f"calculate ebitda, profit_sheet_dc is : {profit_sheet_dc}")

        operating_profit = None
        net_profit_parent = None
        net_profit_deducted = None
        financial_expense = None

        # 获取对应date的数据
        date_field_name = 'REPORT_DATE'
        profit_sheet_dc[date_field_name] = profit_sheet_dc[date_field_name].apply(normalize_date)
        # print(f"profit_sheet_dc after apply normalize_date: {profit_sheet_dc}")
        data_for_date = profit_sheet_dc[profit_sheet_dc[date_field_name] == date].iloc[0]
        
        # 计算各项指标
        operating_profit = safe_float(data_for_date['OPERATE_PROFIT'])    # 营业利润
        net_profit_parent = safe_float(data_for_date['PARENT_NETPROFIT']) # 归属于母公司股东的净利润
        net_profit_deducted = safe_float(data_for_date['DEDUCT_PARENT_NETPROFIT']) # 扣除非经常性损益后的净利润
        financial_expense = safe_float(data_for_date['FINANCE_EXPENSE']) # 财务费用
        
        print("\n财务指标:")
        print(f"报告期: {data_for_date['REPORT_DATE']}")
        print(f"营业利润: {operating_profit/100000000:.2f}亿")
        print(f"归属于母公司股东的净利润: {net_profit_parent/100000000:.2f}亿")
        print(f"扣除非经常性损益后的净利润: {net_profit_deducted/100000000:.2f}亿")
        print(f"财务费用: {financial_expense/100000000:.2f}亿")
        
        
        depreciation = None
        ir_depr = None
        ia_amortize = None
        defer_income_amortize = None
        total_depreciation = None
        total_amortization = None

        cash_flow_dc[date_field_name] = cash_flow_dc[date_field_name].apply(normalize_date)
        cash_flow_data = cash_flow_dc[cash_flow_dc[date_field_name] == date].iloc[0] # 获取对应date的数据
        
        print(f"\n现金流量指标: \n报告期: {cash_flow_data['REPORT_DATE']}")
        # 获取固定资产折旧、油气资产折耗、生产性生物资产折旧
        depreciation = safe_float(cash_flow_data['FA_IR_DEPR']) # 固定资产折旧/投资性房地产折旧
        print(f"固定资产折旧、油气资产折耗、生产性生物资产折旧: {depreciation/100000000:.2f}亿")
        
        # 获取摊销
        ir_depr = safe_float(cash_flow_data['IR_DEPR']) # 无形资产摊销
        ia_amortize = safe_float(cash_flow_data['IA_AMORTIZE']) # 长期待摊费用摊销
        defer_income_amortize = safe_float(cash_flow_data['DEFER_INCOME_AMORTIZE']) # 递延收益摊销
        print(f"无形资产摊销: {ir_depr/100000000:.2f}亿, 长期待摊费用摊销: {ia_amortize/100000000:.2f}, 递延收益摊销: {defer_income_amortize/100000000:.2f}")

        # 计算总折旧
        total_depreciation = depreciation
        print(f"总折旧: {total_depreciation/100000000:.2f}亿")

        # 计算总摊销
        total_amortization = ir_depr + ia_amortize + defer_income_amortize
        print(f"总摊销: {total_amortization/100000000:.2f}亿")

        ebitda = operating_profit - (net_profit_parent - net_profit_deducted) + financial_expense + total_depreciation + total_amortization
        print(f"EBITDA: {ebitda/100000000:.2f}亿")

        return ebitda
    except Exception as e:
        print(f"Error calculating ebitda: {e}")
        return None

    
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
    start_date = calculate_start_date(end_date, limit)
    print(f"start date: {start_date}")
    
    try:
        # 获取主要财务指标
        fin_indicator = ak.stock_financial_analysis_indicator(symbol=pure_ticker, start_year=start_year)
        # print(f"api.py: fin_indicator: {fin_indicator}")

        # 尝试获取资产负债表
        try:
            balance_sheet = ak.stock_financial_report_sina(stock=ticker, symbol="资产负债表")
        except:
            try:
                balance_sheet = ak.stock_financial_report_sina(stock=ticker)
            except:
                balance_sheet = pd.DataFrame()
        # print(f"api.py: balance_sheet: {balance_sheet}")

        # 尝试获取利润表
        try:
            income_stmt = ak.stock_financial_report_sina(stock=ticker, symbol="利润表")
        except:
            try:
                income_stmt = ak.stock_financial_report_sina(stock=ticker)
            except:
                income_stmt = pd.DataFrame()
        # print(f"api.py: income_stmt: {income_stmt}")

        # 获取 东财 利润表数据
        profit_sheet_dc = None
        try:
            profit_sheet_dc = ak.stock_profit_sheet_by_report_em(symbol=ticker)
            # print(f"first get profit sheet from dc: {profit_sheet_dc}")
        except Exception as e:
            print(f"get profit_sheet_dc error: {e} ")
            profit_sheet_dc = pd.DataFrame()

        # 尝试获取现金流量表
        try:
            cash_flow = ak.stock_financial_report_sina(stock=ticker, symbol="现金流量表")
        except:
            try:
                cash_flow = ak.stock_financial_report_sina(stock=ticker)
            except:
                cash_flow = pd.DataFrame()
        # print(f"api.py: cash_flow: {cash_flow}")

        # 获取 东财 现金流量表数据
        try:
            cash_flow_dc = ak.stock_cash_flow_sheet_by_report_em(symbol=ticker)
        except:
            cash_flow_dc = pd.DataFrame()

        # 计算 市盈率 todo: 这些都是最新数据，其实下面的计算要的是历史数据
        price_to_earnings_ratio = None
        price_to_book_ratio = None
        try:
            stock_a_indicator_lg_df = ak.stock_a_indicator_lg(pure_ticker)

            price_to_sales_ratio = stock_a_indicator_lg_df['ps_ttm'].iloc[0]
            price_to_book_ratio = stock_a_indicator_lg_df['pb'].iloc[0]
            price_to_earnings_ratio = stock_a_indicator_lg_df['pe_ttm'].iloc[0]
        except:
            pass

        print('-- calculate market_cap ----------------------------------------------------------------------------------------------------------------')
        stock_individual_info_em_df = ak.stock_individual_info_em(symbol=pure_ticker)
        total_share_capital = stock_individual_info_em_df[stock_individual_info_em_df['item'] == "总股本"]["value"].values[0]
        # print(f"total_share_capital: {total_share_capital}")
        prices = get_price_data(ticker=pure_ticker, start_date=start_date, end_date=end_date)
        prices["market_cap"] = prices['close'] * total_share_capital
        # print(prices.tail())
        print('----------------------------------------------------------------------------------------------------------------')

        # 获取报告期 - 优先使用财务指标的报告期
        dates = []
        if not fin_indicator.empty:
            dates = fin_indicator[["日期"]]
        
        dates = dates["日期"].tolist()
        # 只保留最近的limit个报告期且不晚于end_date
        valid_dates = [d for d in dates if str(d) <= end_date]
        valid_dates = valid_dates[:limit]
        date_str_list = [d.strftime("%Y%m%d") for d in valid_dates]

        print(f"z222222222: {date_str_list}")        
        
        if not date_str_list:
            return []

        # 构建结果
        metrics_list = []
        for date in date_str_list:
            # 当天的市值 = 当天的价格[qfq] * 当前的股本数
            print('------------- for date in date_list, calculate metric ------------------------------------')
            # print(prices)
            market_cap = prices[prices['date']==date]['market_cap'].iloc[0]
            print(f"market_cap: {market_cap/100000000:.2f}亿")

            enterprise_value = calculate_enterprise_value(market_cap, balance_sheet, date)
            print(f"企业价值(EV): {enterprise_value/100000000:.2f}亿")

            print('------------- for date in date_list, calculate ebitda ------------------------------------')
            ebitda = calculate_ebitda(profit_sheet_dc, cash_flow_dc, date)
            enterprise_value_to_ebitda_ratio = enterprise_value / ebitda
            print(f"ebitda: {ebitda/100000000:.2f}亿; enterprise_value_to_ebitda_ratio: {enterprise_value_to_ebitda_ratio}")
            # 创建财务指标对象，使用安全的获取方式
            try:
                # 计算企业价值
                
                metrics = FinancialMetrics(
                    ticker=ticker,
                    report_period=str(date),
                    
                    market_cap=market_cap,
                    net_income=safe_get_value(income_stmt, '净利润', date, date_field_name='报告日'),
                    eps_basic=safe_get_value(fin_indicator, '每股收益_调整后(元)', date, '日期'),
                    
                    enterprise_value=enterprise_value,
                    # ---- 以上指标已OK ------
                    price_to_earnings_ratio=price_to_earnings_ratio,
                    price_to_book_ratio=price_to_book_ratio,
                    price_to_sales_ratio=price_to_sales_ratio,
                    # revenue=safe_get_value(income_stmt, "营业收入", date),
                    # gross_profit=safe_get_value(income_stmt, "营业利润", date),
                    # operating_income=safe_get_value(income_stmt, "营业利润", date),
                    # eps_diluted=safe_get_value(fin_indicator, "稀释每股收益", date),
                    # dividend_per_share=safe_get_value(fin_indicator, "每股股利", date),
                    # total_assets=safe_get_value(balance_sheet, "资产总计", date),
                    # total_equity=safe_get_value(balance_sheet, "所有者权益(或股东权益)合计", date),
                    # free_cash_flow=safe_get_value(cash_flow, "经营活动产生的现金流量净额", date),
                    # operating_cash_flow=safe_get_value(cash_flow, "经营活动产生的现金流量净额", date),
                    pe_ratio=None,  # 将在下一步计算
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
        import traceback
        traceback.print_exc()
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

# 辅助函数
def safe_get_value(df, item_name, date, date_field_name="日期"):
    """从DataFrame中安全地获取特定项目和日期的值
    
    Args:
        df: DataFrame 数据
        item_name: 要获取的指标名称
        date: 日期，支持多种格式 (YYYY-MM-DD, YYYYMMDD, YYYY/MM/DD)
        date_field_name: 日期字段的名称
    """
    try:
        if df.empty:
            print(f"警告: DataFrame为空")
            return None

        # 标准化输入的日期
        target_date = normalize_date(date)
        
        # 检查DataFrame的结构
        if item_name in df.columns:
            # 宽表格式：项目名称是列名
            if date_field_name is not None:
                # 标准化DataFrame中的日期列
                df[date_field_name] = df[date_field_name].apply(normalize_date)
                
                # 查找匹配日期的行
                matched_rows = df[date_field_name] == target_date
                if matched_rows.any():
                    row = df.loc[matched_rows]
                    if not row.empty:
                        value = row[item_name].values[0]
                        if pd.isna(value):
                            print(f"警告: 值为空")
                            return None
                        return float(value)
                    else:
                        print(f"警告: 未找到匹配的行")
                else:
                    print(f"警告: 未找到匹配的日期 {target_date}")
                    print(f"可用的日期: {df[date_field_name].unique()}")

        else:
            # 长表格式：项目名称在第一列
            row = df[df.iloc[:, 0] == item_name]
            if not row.empty:
                # 标准化列名（日期）
                normalized_columns = {col: normalize_date(col) for col in row.columns}
                row = row.rename(columns=normalized_columns)
                
                if target_date in normalized_columns.values():
                    # 找到对应的原始列名
                    original_col = next(col for col, norm_col in normalized_columns.items() 
                                     if norm_col == target_date)
                    value = row[original_col].values[0]
                    if pd.isna(value):
                        print(f"警告: 值为空")
                        return None
                    # 转换为浮点数
                    if isinstance(value, str):
                        value = value.replace(',', '')
                        return float(value)
                    else:
                        return float(value)
                else:
                    print(f"警告: 未找到日期列 {target_date}")
                    print(f"可用的日期: {list(normalized_columns.values())}")
            else:
                print(f"警告: 未找到项目 {item_name}")
                    
        return None
    except Exception as e:
        print(f"获取值失败: {e}")
        return None


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
        # print(f"负债合计: {total_debt}")
        # print(f"货币资金: {cash}")
        # print(f"交易性金融资产: {trading_assets}")
        # print(f"少数股东权益: {minority_interest}")
        
        # 计算企业价值
        ev = market_cap + total_debt - (cash + trading_assets) + minority_interest
        
        return ev
        
    except Exception as e:
        print(f"计算企业价值失败: {e}")
        import traceback
        traceback.print_exc()
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

def test_get_financial_metrics():
    """测试获取财务指标的功能"""
    print("\n=== 开始测试 get_financial_metrics ===")
    
    # 测试参数
    test_ticker = "SH600519"  # 贵州茅台
    test_end_date = "2024-03-20"
    test_period = "annual"
    test_limit = 3
    
    print(f"\n测试参数:")
    print(f"股票代码: {test_ticker}")
    print(f"结束日期: {test_end_date}")
    print(f"周期: {test_period}")
    print(f"限制数量: {test_limit}")
    
    try:
        # 调用被测试的函数
        metrics = get_financial_metrics(
            ticker=test_ticker,
            end_date=test_end_date,
            period=test_period,
            limit=test_limit
        )
        
        # 打印结果
        print(f"\n获取到 {len(metrics)} 条财务指标数据:")
        for i, metric in enumerate(metrics, 1):
            print(f"\n指标 {i}:")
            print(f"报告期: {metric.report_period}")
            print(f"市值: {metric.market_cap/100000000:.2f}亿" if metric.market_cap else "市值: 无数据")
            print(f"企业价值: {metric.enterprise_value/100000000:.2f}亿" if metric.enterprise_value else "企业价值: 无数据")
            print(f"市盈率: {metric.price_to_earnings_ratio:.2f}" if metric.price_to_earnings_ratio else "市盈率: 无数据")
            print(f"市净率: {metric.price_to_book_ratio:.2f}" if metric.price_to_book_ratio else "市净率: 无数据")
            print(f"市销率: {metric.price_to_sales_ratio:.2f}" if metric.price_to_sales_ratio else "市销率: 无数据")
            print(f"EV/EBITDA: {metric.enterprise_value_to_ebitda_ratio:.2f}" if metric.enterprise_value_to_ebitda_ratio else "EV/EBITDA: 无数据")
            
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 执行测试
    test_get_financial_metrics()