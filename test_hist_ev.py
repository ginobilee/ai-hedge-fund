import akshare as ak
import pandas as pd

# 1. 获取后复权历史行情
hist_df = ak.stock_zh_a_hist(
    symbol="600519", 
    period="daily", 
    adjust="hfq"  # 后复权
)
hist_df["日期"] = pd.to_datetime(hist_df["日期"])

# 2. 获取复权因子（关键步骤）
factor_df = ak.stock_zh_a_daily(symbol="sh600519", adjust="hfq-factor")
factor_df["日期"] = pd.to_datetime(factor_df["date"])
factor_df["hfq_factor"] = factor_df["hfq_factor"].astype("float64")
factor_df = factor_df.sort_values("日期")

# 3. 获取最新总股本
info_df = ak.stock_individual_info_em(symbol="600519")
total_share = info_df.loc[info_df["item"] == "总股本", "value"].iloc[0]  # 单位：股
# print(total_share)

# 4. 动态计算历史股本（需复权因子调整）
# 对于 hist_df 的数据，factor_df 中只有部分对应日期的数据
# 逻辑是：对于 hist_df 中的每一条数据 h，取 factor_df["日期"] 小于等于 h["日期"] 的 最大值，然后取 factor_df["hfq_factor"] 的值，作为 h["hfq_factor"] 的值
merge_asof = pd.merge_asof(
    hist_df,
    factor_df,
    on="日期",
    direction="backward"
)

merge_asof["历史股本"] = total_share / merge_asof["hfq_factor"]  # 动态调整股本
merge_asof["历史市值"] = merge_asof["收盘"] * merge_asof["历史股本"]

# # 输出结果
print(merge_asof[["日期", "收盘", "历史市值"]].tail())