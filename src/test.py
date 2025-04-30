import sys

from tests.test_get_prices import test_stock_prices
from tests.test_financial_metrics import test_financial_metrics
# test_stock_prices("000001", "2024-01-01", "2024-01-31")




# if __name__ == "__main__":
#     # 可以通过命令行参数传入股票代码，也可以使用默认值
#     ticker = sys.argv[1] if len(sys.argv) > 1 else "600519"  # 默认测试贵州茅台
    
#     # 设置日期范围: 默认为2022年
#     end_date = "2022-12-31"
#     start_date = "2022-01-01"
    
#     # 如果提供了日期参数，则使用提供的参数
#     if len(sys.argv) > 3:
#         start_date = sys.argv[2]
#         end_date = sys.argv[3]
    
#     # 运行测试
#     test_stock_prices(ticker, start_date, end_date) 


if __name__ == "__main__":
    # 可以通过命令行参数传入股票代码，也可以使用默认值
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SH600519"  # 默认测试贵州茅台
    
    # 设置日期和其他参数
    end_date = "2022-12-31"
    period = "annual"  # 年度数据
    limit = 1  # 最近1个报告期
    
    # 如果提供了额外参数
    if len(sys.argv) > 2:
        end_date = sys.argv[2]
    if len(sys.argv) > 3:
        period = sys.argv[3]
    if len(sys.argv) > 4:
        limit = int(sys.argv[4])
    
    # 运行测试
    test_financial_metrics(ticker, end_date, period, limit) 