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
    
    def get_financial_metrics(self, ticker):
        return self.cache.get(ticker)
    
    def set_financial_metrics(self, ticker, metrics):
        self.cache[ticker] = metrics

# 模拟FinancialMetrics类
class FinancialMetrics:
    def __init__(self, ticker, report_period, revenue=None, gross_profit=None, 
                 operating_income=None, net_income=None, eps_basic=None, 
                 eps_diluted=None, dividend_per_share=None, total_assets=None, 
                 total_equity=None, free_cash_flow=None, operating_cash_flow=None, 
                 pe_ratio=None, market_cap=None):
        self.ticker = ticker
        self.report_period = report_period
        self.revenue = revenue
        self.gross_profit = gross_profit
        self.operating_income = operating_income
        self.net_income = net_income
        self.eps_basic = eps_basic
        self.eps_diluted = eps_diluted
        self.dividend_per_share = dividend_per_share
        self.total_assets = total_assets
        self.total_equity = total_equity
        self.free_cash_flow = free_cash_flow
        self.operating_cash_flow = operating_cash_flow
        self.pe_ratio = pe_ratio
        self.market_cap = market_cap
    
    def model_dump(self):
        return {
            "ticker": self.ticker,
            "report_period": self.report_period,
            "revenue": self.revenue,
            "gross_profit": self.gross_profit,
            "operating_income": self.operating_income,
            "net_income": self.net_income,
            "eps_basic": self.eps_basic,
            "eps_diluted": self.eps_diluted,
            "dividend_per_share": self.dividend_per_share,
            "total_assets": self.total_assets,
            "total_equity": self.total_equity,
            "free_cash_flow": self.free_cash_flow,
            "operating_cash_flow": self.operating_cash_flow,
            "pe_ratio": self.pe_ratio,
            "market_cap": self.market_cap
        }

# 模块级别的缓存实例
_mock_cache = MockCache()

# 模拟get_cache函数
def get_cache():
    return _mock_cache

# 修改sys.modules以注入模拟模块
import types
data_module = types.ModuleType('data')
data_module.cache = types.ModuleType('data.cache')
data_module.cache.get_cache = get_cache
data_module.models = types.ModuleType('data.models')

# 添加所有需要的模型类
model_classes = [
    "CompanyNews", "CompanyNewsResponse", "FinancialMetrics", 
    "FinancialMetricsResponse", "Price", "PriceResponse", 
    "LineItem", "LineItemResponse", "InsiderTrade", "InsiderTradeResponse"
]

for model_name in model_classes:
    if model_name == "FinancialMetrics":
        setattr(data_module.models, model_name, FinancialMetrics)
    else:
        # 创建简单的基类，足够让导入不报错
        setattr(data_module.models, model_name, type(model_name, (), {"model_dump": lambda self: {}}))

# 注册模块
sys.modules['data'] = data_module
sys.modules['data.cache'] = data_module.cache
sys.modules['data.models'] = data_module.models

print("已准备模拟模块: data.cache 和 data.models")

# 现在可以安全导入api模块
try:
    from tools.api import get_financial_metrics
    print("成功从 tools.api 导入 get_financial_metrics 函数")
except ImportError as e:
    print(f"无法导入 tools.api: {e}")
    sys.exit(1)

def test_financial_metrics(ticker, end_date, period="ttm", limit=1):
    """测试获取财务指标数据"""
    print(f"测试获取 {ticker} 截至 {end_date} 的财务指标数据")
    print(f"参数: period={period}, limit={limit}")
    
    try:
        # 获取财务指标数据
        metrics = get_financial_metrics(ticker, end_date, period, limit)
        
        # 检查是否成功获取数据
        if not metrics:
            print(f"未获取到 {ticker} 的财务指标数据")
            return None
        
        # 打印获取的数据条数
        print(f"成功获取了 {len(metrics)} 条财务指标数据")
        
        # 打印各报告期
        report_periods = [m.report_period for m in metrics]
        print(f"\n报告期列表: {report_periods}")
        
        # 打印第一个报告期的详细数据
        if metrics:
            first_metric = metrics[0]
            print(f"\n最新报告期 ({first_metric.report_period}) 财务数据:")
            
            data = first_metric.model_dump()
            # 跳过ticker和report_period字段
            metric_data = {k: v for k, v in data.items() if k not in ['ticker', 'report_period']}
            
            # 格式化输出
            for key, value in metric_data.items():
                if value is not None:
                    # 对金额数据进行格式化 (大数显示为百万/亿)
                    if key in ['revenue', 'gross_profit', 'operating_income', 'net_income', 
                               'total_assets', 'total_equity', 'free_cash_flow', 
                               'operating_cash_flow', 'market_cap'] and value > 10000:
                        if value > 100000000:  # 亿元级别
                            formatted_value = f"{value/100000000:.2f}亿元"
                        else:  # 万元级别
                            formatted_value = f"{value/10000:.2f}万元"
                        print(f"  {key}: {formatted_value} ({value})")
                    elif key in ['pe_ratio', 'eps_basic', 'eps_diluted']:
                        print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
        
        # 分析财务趋势
        if len(metrics) > 1:
            print("\n财务趋势分析:")
            
            # 收入趋势
            revenues = [m.revenue for m in metrics if m.revenue is not None]
            if len(revenues) > 1:
                revenue_growth = (revenues[0] / revenues[-1] - 1) * 100
                print(f"  收入增长率: {revenue_growth:.2f}% (比较最新vs最早期间)")
            
            # 净利润趋势
            net_incomes = [m.net_income for m in metrics if m.net_income is not None]
            if len(net_incomes) > 1:
                profit_growth = (net_incomes[0] / net_incomes[-1] - 1) * 100
                print(f"  净利润增长率: {profit_growth:.2f}% (比较最新vs最早期间)")
            
            # 利润率趋势
            profit_margins = []
            for m in metrics:
                if m.revenue is not None and m.revenue > 0 and m.net_income is not None:
                    profit_margins.append(m.net_income / m.revenue * 100)
            
            if profit_margins:
                print(f"  利润率: 最新 {profit_margins[0]:.2f}%, 平均 {sum(profit_margins)/len(profit_margins):.2f}%")
        
        return metrics
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

