import akshare as ak
import pandas as pd

# stock_individual_info_em_df = ak.stock_individual_info_em(symbol="000001")
# print(stock_individual_info_em_df)

# # market_cap= ak.stock_individual_info_em(symbol="000001")["value"][5]
# info= ak.stock_individual_info_em(symbol="000001")
# market_cap=info[info["item"]=="总市值"]["value"].values[0]

def test_stock_info():
    """测试获取股票基本信息"""
    try:
        stock_info = ak.stock_individual_info_em(symbol="000001")
        print("股票基本信息:")
        print(stock_info)
        
        # 获取总市值
        market_cap = stock_info[stock_info["item"]=="总市值"]["value"].values[0]
        print(f"总市值: {market_cap}")
    except Exception as e:
        print(f"获取股票基本信息失败: {e}")
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

def test_financial_indicators():
    """测试获取财务指标"""
    try:
        # 获取2024年的财务指标
        fin_indicator = ak.stock_financial_analysis_indicator(symbol="000001", start_year="2024")
        print("\n财务指标数据:")
        print(fin_indicator)
        
        # 打印日期列的信息
        print("\n日期列信息:")
        print("日期列类型:", fin_indicator['日期'].dtype)
        print("日期列唯一值:", fin_indicator['日期'].unique())
        print("日期列示例值:", fin_indicator['日期'].iloc[0])
        
        # 获取每股收益
        eps_basic = safe_get_value(fin_indicator, '每股收益_调整后(元)', '2024-12-31', '日期')
        print(f"\n每股收益_调整后(元): {eps_basic}")
        
        # 测试其他财务指标
        roe = safe_get_value(fin_indicator, '净资产收益率(%)', '2024-12-31', '日期')
        print(f"净资产收益率(%): {roe}")

        eps_basic_kc = safe_get_value(fin_indicator, '扣除非经常性损益后的每股收益(元)', '2024-12-31', '日期')
        print(f"\n eps_basic_kc: {eps_basic_kc}")
        
    except Exception as e:
        print(f"获取财务指标失败: {e}")

def test_income_statement():
    """测试获取利润表数据"""
    try:
        # 获取平安银行(000001)的利润表数据
        income_stmt = ak.stock_financial_report_sina(stock="600519", symbol="利润表")
        print("\n利润表数据:")
        print(income_stmt)
        
        # 打印列名信息
        print("\n利润表字段:")
        print("列名:", income_stmt.columns.tolist())
        
        # 打印数据基本信息
        print("\n数据基本信息:")
        print("数据形状:", income_stmt.shape)
        print("数据类型:\n", income_stmt.dtypes)
        
        # 打印前几行数据示例
        print("\n数据示例:")
        print(income_stmt.head())
        
    except Exception as e:
        print(f"获取利润表数据失败: {e}")

def test_balance_sheet():
    """测试获取资产负债表数据"""
    try:
        # 获取平安银行(000001)的资产负债表数据
        balance_sheet = ak.stock_financial_report_sina(stock="000001", symbol="资产负债表")
        print("\n资产负债表数据:")
        print(balance_sheet)
        
        # 打印列名信息
        print("\n资产负债表字段:")
        print("列名:", balance_sheet.columns.tolist())
        
        # 打印数据基本信息
        print("\n数据基本信息:")
        print("数据形状:", balance_sheet.shape)
        print("数据类型:\n", balance_sheet.dtypes)
        
        # 打印前几行数据示例
        print("\n数据示例:")
        print(balance_sheet.head())
        
    except Exception as e:
        print(f"获取资产负债表数据失败: {e}")

def test_ps_ratio():
    """测试获取市销率(PS)数据"""
    try:
        # 获取平安银行(000001)的市销率数据
        stock_a_indicator_lg_df = ak.stock_a_indicator_lg(symbol="600519")
        print("\n市销率(PS)数据:")
        print(stock_a_indicator_lg_df)
        
        # 打印列名信息
        print("\n市销率字段:")
        print("列名:", stock_a_indicator_lg_df.columns.tolist())
        
        # 打印数据基本信息
        print("\n数据基本信息:")
        print("数据形状:", stock_a_indicator_lg_df.shape)
        print("数据类型:\n", stock_a_indicator_lg_df.dtypes)
        
        # 打印前几行数据示例
        print("\n数据示例:")
        print(stock_a_indicator_lg_df.head())
        
        # 获取最新的PS_TTM值
        if not stock_a_indicator_lg_df.empty:
            latest_ps = stock_a_indicator_lg_df['ps_ttm'].iloc[0]
            latest_pb = stock_a_indicator_lg_df['pb'].iloc[0]
            latest_pe = stock_a_indicator_lg_df['pe_ttm'].iloc[0]
            latest_total_mv = stock_a_indicator_lg_df['total_mv'].iloc[0]
            print(f"\n最新市销率(PS_TTM): {latest_ps}, 市净率(PB): {latest_pb}, 市盈率(PE_TTM): {latest_pe}, 总市值(total_mv): {latest_total_mv}")
        
    except Exception as e:
        print(f"获取市销率数据失败: {e}")

def test_profit_sheet_em():
    """测试使用 stock_profit_sheet_by_report_em 获取利润表数据"""
    try:
        # 获取贵州茅台(600519)的利润表数据
        profit_sheet = ak.stock_profit_sheet_by_yearly_em(symbol="sh600519")
        # print("\n利润表数据:")
        # print(profit_sheet)
        
        # 打印列名信息
        print("\n利润表字段:")
        print("列名:", profit_sheet.columns.tolist())
        
        # 打印数据基本信息
        print("\n数据基本信息:")
        print("数据形状:", profit_sheet.shape)
        print("数据类型:\n", profit_sheet.dtypes)
        
        # 获取最新一期的数据
        if not profit_sheet.empty:
            latest_data = profit_sheet.iloc[0]
            print(f"latest_data: {latest_data}")
            
            # 计算各项指标
            operating_profit = safe_float(latest_data['OPERATE_PROFIT'])    # 营业利润
            net_profit_parent = safe_float(latest_data['PARENT_NETPROFIT']) # 归属于母公司股东的净利润
            net_profit_deducted = safe_float(latest_data['DEDUCT_PARENT_NETPROFIT']) # 扣除非经常性损益后的净利润
            financial_expense = safe_float(latest_data['FINANCE_EXPENSE']) # 财务费用
            
            ebitda = operating_profit - (net_profit_parent - net_profit_deducted) + financial_expense
            
            print("\n最新一期财务指标:")
            print(f"报告期: {latest_data.name}")
            print(f"营业利润: {operating_profit/100000000:.2f}亿")
            print(f"归属于母公司股东的净利润: {net_profit_parent/100000000:.2f}亿")
            print(f"扣除非经常性损益后的净利润: {net_profit_deducted/100000000:.2f}亿")
            print(f"财务费用: {financial_expense/100000000:.2f}亿")
            
            # 计算利润率
            if operating_profit and net_profit_parent:
                operating_margin = operating_profit / net_profit_parent * 100
                print(f"营业利润率: {operating_margin:.2f}%")
        
    except Exception as e:
        print(f"获取利润表数据失败: {e}")

def test_cash_flow_sheet():
    """测试获取现金流量表数据并计算固定资产和投资性房地产折旧"""
    try:
        # 获取贵州茅台(600519)的现金流量表数据
        cash_flow = ak.stock_cash_flow_sheet_by_yearly_em(symbol="sh600519")
        
        # 打印列名信息
        print("\n现金流量表字段:")
        print("列名:", cash_flow.columns.tolist())
        
        # 打印数据基本信息
        print("\n数据基本信息:")
        print("数据形状:", cash_flow.shape)
        print("数据类型:\n", cash_flow.dtypes)
        
        # 获取最新一期的数据
        if not cash_flow.empty:
            latest_data = cash_flow.iloc[0]
            print(f"\n最新一期数据:")
            print(f"报告期: {latest_data.name}")
            
            # 获取固定资产折旧、油气资产折耗、生产性生物资产折旧
            depreciation = safe_float(latest_data['FA_IR_DEPR']) # 固定资产折旧/投资性房地产折旧
            print(f"固定资产折旧、油气资产折耗、生产性生物资产折旧: {depreciation/100000000:.2f}亿")
            
            ir_depr = safe_float(latest_data['IR_DEPR']) # 无形资产摊销
            ia_amortize = safe_float(latest_data['IA_AMORTIZE']) # 长期待摊费用摊销
            defer_income_amortize = safe_float(latest_data['DEFER_INCOME_AMORTIZE']) # 递延收益摊销
            print(f"无形资产摊销: {ir_depr/100000000:.2f}亿, 长期待摊费用摊销: {ia_amortize/100000000:.2f}, 递延收益摊销: {defer_income_amortize/100000000:.2f}")

            # 计算总折旧
            total_depreciation = depreciation
            print(f"总折旧: {total_depreciation/100000000:.2f}亿")

            # 计算总摊销
            total_amortization = ir_depr + ia_amortize + defer_income_amortize
            print(f"总摊销: {total_amortization/100000000:.2f}亿")
            
    except Exception as e:
        print(f"获取现金流量表数据失败: {e}")

def test_ebitda():
    """测试计算ebitda"""
    # EBITDA=营业利润-非经常性损益+折旧+摊销+利息费用

    #     非经常性损益 = 归属于母公司股东的净利润	- 扣除非经常性损益后的净利润	
    #     折旧 = 固定资产和投资性房地产折旧	从 现金流量表 中取 
    #     摊销 = 无形资产摊销 + 长期待摊费用摊销 
    #     利息费用 = 财务费用	
    symbol = "sh600519"
    try:
        # 获取贵州茅台(600519)的利润表数据
        profit_sheet = ak.stock_profit_sheet_by_report_em(symbol)
        # print(f"利润表数据:\n{profit_sheet}")
        date = '2024-12-31'
        # print(f"报告期: {date}, type: {type(date)}")
        # latest_date = profit_sheet.iloc[0]['REPORT_DATE']
        # print(f"数据中的日期: {latest_date}, {normalize_date(latest_date)}")
        # profit_sheet['REPORT_DATE'] = profit_sheet['REPORT_DATE'].apply(normalize_date)
        # data = profit_sheet[profit_sheet['REPORT_DATE'] == normalize_date(date)] 
        # print(f"date after normal: {normalize_date(date)}")
        # print(f"profit data after normal: {profit_sheet}")
        # print(f"最新一期数据:\n{data}")
        
        cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol)
        ebitda = calculate_ebitda(profit_sheet, cash_flow, date)

    except Exception as e:
        print(f"计算EBITDA失败: {e}")

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
            
        def normalize_date(date_str):
            """标准化日期格式，移除所有分隔符"""
            if isinstance(date_str, str):
                # 如果是字符串，移除所有分隔符
                return date_str.replace("-", "").replace("/", "").replace(".", "")
            elif pd.isna(date_str):
                return None
            # 如果是其他类型（如datetime），转换为字符串并移除分隔符
            return str(date_str).replace("-", "").replace("/", "").replace(".", "")

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

def safe_float(value):
    """安全地将值转换为浮点数，处理nan值"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        return float(value.replace(',', ''))
    return float(value)
    
def calculate_ebitda(profit_sheet_dc: pd.DataFrame, cash_flow_dc: pd.DataFrame, date: str):
    # 计算 EBITDA
    try:
        print(f"api.py: calculate ebitda for {date} ")

        operating_profit = None
        net_profit_parent = None
        net_profit_deducted = None
        financial_expense = None

        date = normalize_date(date)
        
        # 获取对应date的数据
        date_field_name = 'REPORT_DATE'
        profit_sheet_dc[date_field_name] = profit_sheet_dc[date_field_name].apply(normalize_date)
        data_for_date = profit_sheet_dc[profit_sheet_dc[date_field_name] == date].iloc[0]
        print(f"profit sheet data: {data_for_date}")
        
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


def calculate_enterprise_value(ticker="600519"):
    """计算企业价值(EV)
    
    EV = Market Cap + Total Debt - Cash & Equivalents + Preferred Stock + Minority Interest
    
    Args:
        ticker: 股票代码
    """
    try:
        date = "20210331"
        # 1. 获取市值
        stock_info = ak.stock_individual_info_em(symbol=ticker)
        market_cap = stock_info[stock_info["item"]=="总市值"]["value"].values[0]
        print(f"market_cap: {market_cap}, type: {type(market_cap)}")
        
        # 2. 获取资产负债表数据
        balance_sheet = ak.stock_financial_report_sina(stock=ticker, symbol="资产负债表")
        
        # 获取最新一期的数据（第一行）
        latest_data = balance_sheet.iloc[0]
        
        # 3. 计算总债务
        total_debt = safe_float(latest_data['负债合计'])
        print(f"total_debt: {total_debt}")
        
        # 4. 获取现金及等价物 (货币资金 + 交易性金融资产)
        cash_equivalents = safe_float(latest_data['货币资金']) + safe_float(latest_data['交易性金融资产'])
        
        # 5. 获取少数股东权益
        minority_interest = safe_float(latest_data['少数股东权益'])
        
        # 6. 计算企业价值
        ev = market_cap + total_debt - cash_equivalents + minority_interest
        
        # 打印详细计算过程
        print(f"\n企业价值(EV)计算过程:")
        print(f"市值: {market_cap/100000000:.2f}亿")
        print(f"总债务: {total_debt/100000000:.2f}亿")
        print(f"现金及等价物: {cash_equivalents/100000000:.2f}亿")
        print(f"少数股东权益: {minority_interest/100000000:.2f}亿")
        print(f"企业价值(EV): {ev/100000000:.2f}亿")
        
        return ev
        
    except Exception as e:
        print(f"计算企业价值失败: {e}")
        return None

if __name__ == "__main__":
    # 运行测试
    # test_stock_info()
    # test_financial_indicators()
    # test_income_statement()
    # test_balance_sheet()
    # calculate_enterprise_value()
    # test_ps_ratio()
    # test_profit_sheet_em()
    # test_cash_flow_sheet()
    test_ebitda()