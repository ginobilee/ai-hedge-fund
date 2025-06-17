# 写一下测试 akshare 的版本号的代码
import akshare as ak
import pandas as pd

# print(ak.__version__)

# # 获取A股历史行情数据
# df = ak.stock_zh_a_hist(
#     symbol="600734", 
#     period="daily", 
#     start_date="20050501", 
#     end_date="20050520", 
#     adjust="hfq"
    
#     # symbol=ak_ticker, 
#     #                     start_date=start_date.replace('-', ''), 
#     #                     end_date=end_date.replace('-', ''), 
#     #                     adjust="qfq"
#     )

# if df.empty:
#     print("数据查询结果为空")



# stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol="600004", start_year="2023")
# stock_financial_analysis_indicator_df.to_excel('600004.xlsx', index=False)
# print(stock_financial_analysis_indicator_df.columns)

# stock_financial_report_sina_df = ak.stock_financial_report_sina(stock="sh600600", symbol="资产负债表")
# print(stock_financial_report_sina_df)
# print(f"成功获取数据: {len(df)} 条记录")

# stock_financial_report_sina_df = ak.stock_financial_report_sina(stock="sh600600", symbol="利润表")
# print(stock_financial_report_sina_df)

# 东财 利润表
# stock_profit_sheet_by_report_em = ak.stock_profit_sheet_by_report_em(symbol="SH600519")
# stock_profit_sheet_by_report_em.to_excel('SH600519.xlsx', index=False)
# stock_profit_sheet_by_report_em = ak.stock_cash_flow_sheet_by_report_em(symbol='SH600519')
# stock_profit_sheet_by_report_em.to_excel('SH600519.xlsx', index=False)
# print(stock_profit_sheet_by_report_em['REPORT_DATE']) #, 'OPERATE_PROFIT'])
# print(stock_profit_sheet_by_report_em.tail())
# stock_balance_sheet_by_report_em_df = ak.stock_balance_sheet_by_report_em(symbol="sh600600")
# print(stock_balance_sheet_by_report_em_df)


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

def get_report_date_list(fin_indicator: pd.DataFrame, limit: int):
    dates = []
    if not fin_indicator.empty:
        dates = fin_indicator[["日期"]]

    dates = dates["日期"].tolist()
    valid_dates = [d for d in dates if normalize_date(str(d)).endswith('1231')]
    valid_dates = valid_dates[-limit:]
    date_str_list = [d.strftime("%Y%m%d") for d in valid_dates]
    return date_str_list

fin_indicator = ak.stock_financial_analysis_indicator(symbol='600519', start_year='2020')
date_list = get_report_date_list(fin_indicator, 3)
print(f'date_list: {date_list}')