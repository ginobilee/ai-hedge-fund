# 写一下测试 akshare 的版本号的代码
import akshare as ak

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



# stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol="600004", start_year="2020")
# print(stock_financial_analysis_indicator_df)

stock_financial_report_sina_df = ak.stock_financial_report_sina(stock="sh600600", symbol="资产负债表")
print(stock_financial_report_sina_df)
# print(f"成功获取数据: {len(df)} 条记录")


stock_balance_sheet_by_report_em_df = ak.stock_balance_sheet_by_report_em(symbol="sh600600")
print(stock_balance_sheet_by_report_em_df)