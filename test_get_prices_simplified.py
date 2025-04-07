import sys
import pandas as pd
from datetime import datetime, timedelta
import akshare as ak

class MockCache:
    """模拟缓存类，用于测试"""
    def __init__(self):
        self.cache = {}
    
    def get_prices(self, ticker):
        return self.cache.get(ticker)
    
    def set_prices(self, ticker, prices):
        self.cache[ticker] = prices

# 创建模拟的Price类
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

# 创建模拟的get_cache函数
def get_cache():
    return MockCache()

# 添加直接测试akshare的函数
def test_akshare_direct(ticker, start_date, end_date):
    """直接测试akshare的API"""
    print(f"直接测试 akshare API 获取 {ticker} 股票数据")
    
    try:
        # 简单判断沪深市场 (6开头是上证，其他是深证)
        # if ticker.startswith('6'):
        #     ak_ticker = f"sh{ticker}"
        # else:
        #     ak_ticker = f"sz{ticker}"
        
        ak_ticker = ticker
        print(f"使用股票代码: {ak_ticker}")
        print(f"查询日期范围: {start_date.replace('-', '')} 到 {end_date.replace('-', '')}")
        
        # 查看API文档
        print("\nakshare.stock_zh_a_hist 参数说明:")
        print(str(ak.stock_zh_a_hist.__doc__))
        
        # 获取A股历史行情数据
        df = ak.stock_zh_a_hist(symbol=ak_ticker, 
                                period="daily", 
                               start_date=start_date.replace('-', ''), 
                               end_date=end_date.replace('-', ''), 
                               adjust="qfq")
        
        if df.empty:
            print("数据查询结果为空")
            return None
        
        print(f"成功获取数据: {len(df)} 条记录")
        print("\n数据前5行:")
        print(df.head().to_string())
        return df
    
    except Exception as e:
        print(f"akshare API 调用出错: {e}")
        import traceback
        traceback.print_exc()
        return None

# 从api.py中复制的get_prices函数，但去除了依赖
def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data for A-shares using akshare."""
    # 创建模拟缓存实例
    _cache = get_cache()
    
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by date range and convert to Price objects
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # # 补充前缀，A股需要带市场代码如 sh.600000 或 sz.000001
    # if not (ticker.startswith('sh.') or ticker.startswith('sz.')):
    #     # 简单判断沪深市场 (6开头是上证，其他是深证，不完全准确但一般适用)
    #     if ticker.startswith('6'):
    #         a_ticker = f"sh.{ticker}"
    #     else:
    #         a_ticker = f"sz.{ticker}"
    # else:
    a_ticker = ticker
    
    print(f"get_prices: 处理后的股票代码为 {a_ticker}")
    
    # 使用akshare获取A股历史行情数据
    try:
        # 转换为akshare接受的格式
        ak_ticker = a_ticker.replace('sh.', 'sh').replace('sz.', 'sz')
        
        print(f"get_prices: 转换为akshare格式的股票代码为 {ak_ticker}")
        print(f"get_prices: 查询日期范围: {start_date.replace('-', '')} 到 {end_date.replace('-', '')}")
        
        # 获取A股历史行情数据
        df = ak.stock_zh_a_hist(symbol=ak_ticker, 
                                period="daily", start_date=start_date.replace('-', ''), 
                               end_date=end_date.replace('-', ''), adjust="qfq")
        
        print(f"get_prices: 查询结果DataFrame大小: {df.shape}")
        
        # 处理可能的空数据
        if df.empty:
            print("get_prices: 查询结果为空")
            return []
            
        # 转换为API预期的格式
        prices = []
        for _, row in df.iterrows():
            # 将日期转为ISO格式字符串
            date_str = row['日期'].strftime('%Y-%m-%d') if isinstance(row['日期'], datetime) else row['日期']
            
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
        import traceback
        traceback.print_exc()
        return []

# 测试函数
def test_get_prices(ticker, start_date, end_date):
    print(f"测试获取 {ticker} 从 {start_date} 到 {end_date} 的价格数据")
    
    try:
        # 获取价格数据
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
        
        # 计算一些基本统计信息
        high_values = [p.high for p in prices]
        low_values = [p.low for p in prices]
        volume_values = [p.volume for p in prices]
        
        print("\n基本统计信息:")
        print(f"最高价: {max(high_values):.2f}")
        print(f"最低价: {min(low_values):.2f}")
        print(f"平均成交量: {sum(volume_values)/len(volume_values):.2f}")
        print(f"交易日数量: {len(prices)}")
        
        print("\n测试完成")
        return prices
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 可以通过命令行参数传入股票代码，也可以使用默认值
    ticker = sys.argv[1] if len(sys.argv) > 1 else "600734"  # 默认测试浦发银行
    
    # 设置日期范围: 默认为2022年
    end_date = "2005-05-20"
    # end_date = "2005-05-20"
    start_date = "2005-05-01"
    # start_date="2005-05-01", 
    
    # 如果提供了日期参数，则使用提供的参数
    if len(sys.argv) > 3:
        start_date = sys.argv[2]
        end_date = sys.argv[3]
    
    print("=" * 50)
    print(f"开始测试获取 A股 {ticker} 数据")
    print("=" * 50)
    
    # 首先直接调用akshare测试
    print("\n测试1: 直接调用akshare")
    df = test_akshare_direct(ticker, start_date, end_date)
    
    print("\n测试2: 通过封装的get_prices函数")
    # 运行封装的测试函数
    test_get_prices(ticker, start_date, end_date) 