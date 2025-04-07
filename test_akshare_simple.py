import akshare as ak
import pandas as pd

def test_basic_functionality():
    """测试akshare最基本的功能"""
    print(f"akshare版本: {ak.__version__}")
    
    # 测试获取上证指数
    print("\n测试获取上证指数行情:")
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        print(f"获取到 {len(df)} 条记录")
        print("数据示例:")
        print(df.head())
    except Exception as e:
        print(f"获取上证指数出错: {e}")
    
    # 测试获取贵州茅台股票实时行情
    print("\n测试获取贵州茅台实时行情:")
    try:
        df = ak.stock_zh_a_spot_em()
        # 过滤贵州茅台
        df_maotai = df[df['代码'] == '600519']
        if not df_maotai.empty:
            print("贵州茅台实时行情:")
            print(df_maotai)
        else:
            print("未找到贵州茅台的实时行情")
    except Exception as e:
        print(f"获取实时行情出错: {e}")
    
    # 测试获取股票列表
    print("\n测试获取股票列表:")
    try:
        stock_list = ak.stock_info_a_code_name()
        print(f"共获取到 {len(stock_list)} 只股票")
        print("前5只股票:")
        print(stock_list.head())
    except Exception as e:
        print(f"获取股票列表出错: {e}")

def test_stock_history():
    """测试股票历史数据获取"""
    print("\n测试获取贵州茅台历史行情:")
    
    # 测试不同的参数组合
    test_params = [
        {"symbol": "sh600519", "period": "daily", "adjust": "qfq"},
        {"symbol": "sh600519", "period": "daily", "adjust": ""},
        {"symbol": "600519", "period": "daily", "adjust": "qfq"},
        {"symbol": "sh600519", "period": "daily", "adjust": "qfq", "start_date": "20210101", "end_date": "20210110"},
    ]
    
    for i, params in enumerate(test_params):
        print(f"\n测试参数组合 {i+1}:")
        print(params)
        try:
            df = ak.stock_zh_a_hist(**params)
            print(f"查询结果: 获取到 {len(df)} 条记录")
            if not df.empty:
                print("数据示例:")
                print(df.head())
        except Exception as e:
            print(f"查询出错: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("测试 akshare 基本功能")
    print("=" * 50)
    
    # 测试基本功能
    test_basic_functionality()
    
    # 测试股票历史数据
    test_stock_history() 