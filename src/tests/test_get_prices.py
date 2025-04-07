import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import akshare as ak

# 创建模拟的数据模型和缓存类，替代原始导入
class MockCache:
    """模拟缓存类，用于测试"""
    def __init__(self):
        self.cache = {}
    
    def get_prices(self, ticker):
        return self.cache.get(ticker)
    
    def set_prices(self, ticker, prices):
        self.cache[ticker] = prices

# 模拟Price类
class Price:
    def __init__(self, time, open, high, low, close, volume, amount=None, ticker=None):
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.amount = amount
        self.ticker = ticker
    
    def model_dump(self):
        return {
            "time": self.time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
            "ticker": self.ticker
        }

# 现在可以安全导入api模块
from tools.api import get_prices, prices_to_df

# 设置要测试的股票和日期范围
def test_stock_prices(ticker, start_date, end_date):
    print(f"测试获取 {ticker} 从 {start_date} 到 {end_date} 的价格数据")
    
    try:
        # 获取价格数据·
        prices = get_prices(ticker, start_date, end_date)
        
        # 检查是否成功获取数据
        if not prices:
            print(f"未获取到 {ticker} 的价格数据")
            return
        
        # 打印获取的数据条数
        print(f"成功获取了 {len(prices)} 条价格数据")
        
        # 打印第一条数据作为示例
        if prices:
            print("\n首条数据示例:")
            first_price = prices[0]
            for field, value in first_price.model_dump().items():
                print(f"  {field}: {value}")
        
        # 转换为DataFrame并显示
        df = prices_to_df(prices)
        print("\nDataFrame格式数据前5行:")
        print(df.head().to_string())
        
        # 计算一些基本统计信息
        print("\n基本统计信息:")
        print(f"最高价: {df['high'].max():.2f}")
        print(f"最低价: {df['low'].min():.2f}")
        print(f"平均成交量: {df['volume'].mean():.2f}")
        print(f"交易日数量: {len(df)}")
        
        print("\n测试完成")
        return df
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

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