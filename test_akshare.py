import sys
import pandas as pd
from datetime import datetime, timedelta
import akshare as ak
import json

def test_ak_stock_price(ticker, start_date, end_date):
    """测试使用akshare获取股票价格数据"""
    print(f"测试获取 {ticker} 从 {start_date} 到 {end_date} 的价格数据")
    
    try:
        # 转换为akshare接受的格式
        if not (ticker.startswith('sh') or ticker.startswith('sz')):
            # 简单判断沪深市场 (6开头是上证，其他是深证)
            if ticker.startswith('6'):
                ak_ticker = f"sh{ticker}"
            else:
                ak_ticker = f"sz{ticker}"
        else:
            ak_ticker = ticker
        
        print(f"转换后的股票代码: {ak_ticker}")
        
        # 获取A股历史行情数据
        df = ak.stock_zh_a_hist(symbol=ak_ticker, 
                              start_date=start_date.replace('-', ''), 
                              end_date=end_date.replace('-', ''), 
                              adjust="qfq")
        
        # 打印数据基本信息
        print(f"\n成功获取了 {len(df)} 条价格数据")
        print("\n数据前5行:")
        print(df.head().to_string())
        
        # 计算基本统计信息
        if not df.empty:
            print("\n基本统计信息:")
            print(f"最高价: {df['最高'].max():.2f}")
            print(f"最低价: {df['最低'].min():.2f}")
            print(f"平均成交量: {df['成交量'].mean():.2f}")
            print(f"交易日数量: {len(df)}")
        
        return df
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_ak_financial_indicator(ticker):
    """测试获取财务指标数据"""
    print(f"\n测试获取 {ticker} 的财务指标数据")
    
    try:
        # 移除市场前缀
        pure_ticker = ticker.replace('sh', '').replace('sz', '')
        print(f"处理后的股票代码: {pure_ticker}")
        
        # 获取财务指标
        df = ak.stock_financial_analysis_indicator(symbol=pure_ticker)
        
        if df.empty:
            print("未获取到财务指标数据")
            return None
            
        print(f"成功获取财务指标，共有 {len(df)} 条记录，{len(df.columns)} 个指标")
        print("\n数据列名:")
        print(df.columns.tolist())
        
        # 打印前几行
        print("\n数据前5行样例:")
        print(df.head().to_string())
        
        return df
    
    except Exception as e:
        print(f"获取财务指标时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_ak_balance_sheet(ticker):
    """测试获取资产负债表"""
    print(f"\n测试获取 {ticker} 的资产负债表")
    
    try:
        # 移除市场前缀
        pure_ticker = ticker.replace('sh', '').replace('sz', '')
        
        # 获取akshare的API帮助文档
        help_text = str(help(ak.stock_financial_report_sina))
        print("API帮助文档:")
        print(help_text[:500] + "..." if len(help_text) > 500 else help_text)
        
        # 获取资产负债表
        # 根据akshare最新API调整参数
        try:
            df = ak.stock_financial_report_sina(symbol=pure_ticker, stock_type="资产负债表")
        except:
            try:
                # 尝试不同的参数名称
                df = ak.stock_financial_report_sina(symbol=pure_ticker, financial_type="资产负债表")
            except:
                # 如果以上都不行，尝试简单调用
                df = ak.stock_financial_report_sina(symbol=pure_ticker)
        
        if df.empty:
            print("未获取到资产负债表数据")
            return None
            
        print(f"成功获取资产负债表，共有 {len(df)} 条记录")
        print(f"报告期: {df.columns[1:].tolist()}")
        
        # 打印部分数据项
        items = ["资产总计", "负债合计", "所有者权益(或股东权益)合计"]
        print("\n关键财务数据:")
        for item in items:
            row = df[df.iloc[:, 0] == item]
            if not row.empty:
                print(f"{item}:")
                for col in df.columns[1:4]:  # 只打印前3个期间的数据
                    print(f"  {col}: {row[col].values[0]}")
        
        return df
    
    except Exception as e:
        print(f"获取资产负债表时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_ak_insider_trades(ticker):
    """测试获取内部交易数据"""
    print(f"\n测试获取 {ticker} 的内部交易数据")
    
    try:
        # 移除市场前缀
        pure_ticker = ticker.replace('sh', '').replace('sz', '')
        
        # 获取高管增减持数据
        df = ak.stock_em_executive_change(symbol=pure_ticker)
        
        if df.empty:
            print("未获取到内部交易数据")
            return None
            
        print(f"成功获取内部交易数据，共有 {len(df)} 条记录")
        print("\n数据前5行:")
        print(df.head().to_string())
        
        return df
    
    except Exception as e:
        print(f"获取内部交易数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 可以通过命令行参数传入股票代码，也可以使用默认值
    ticker = sys.argv[1] if len(sys.argv) > 1 else "600000"  # 默认测试浦发银行
    
    # 设置日期范围: 默认为最近30天(与当前时间对应)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 如果提供了日期参数，则使用提供的参数
    if len(sys.argv) > 3:
        start_date = sys.argv[2]
        end_date = sys.argv[3]
    
    # 运行测试
    print("=" * 50)
    print(f"开始测试 akshare 获取 A股 {ticker} 数据")
    print("=" * 50)
    
    # 测试获取股票价格数据
    price_df = test_ak_stock_price(ticker, start_date, end_date)
    
    # 测试获取财务指标
    indicator_df = test_ak_financial_indicator(ticker)
    
    # 测试获取资产负债表
    balance_df = test_ak_balance_sheet(ticker)
    
    # 测试获取内部交易数据
    insider_df = test_ak_insider_trades(ticker)
    
    print("\n所有测试完成") 