import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import akshare as ak
import datetime

# 设置中文字体和解决负号显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认中文字体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题

def get_stock_data(stock_code, start_date, end_date):
    if stock_code.startswith(('sh', 'sz')):  # 沪深指数
        df = ak.stock_zh_index_daily(symbol=stock_code)
    else:  # A股个股
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")

    column_mapping = {
        '日期': 'date',
        '收盘': 'close',
        'open': 'open',
        'high': 'high',
        'low': 'low'
    }
    df.rename(columns=column_mapping, inplace=True)

    if 'date' not in df.columns or 'close' not in df.columns:
        raise ValueError(f"缺失必要列，当前列：{df.columns.tolist()}")
        
    df.index = pd.to_datetime(df['date'])
    
    # --- 新增的筛选逻辑 ---
    # 统一在此处对所有数据源进行日期筛选
    df = df.loc[start_date:end_date]
    
    return df[['close']].rename(columns={'close': stock_code})


# 计算每日收益率
def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    returns = prices.pct_change().dropna()
    return returns

# 年化收益率
def annualized_return(returns, periods_per_year=252):
    return (1 + returns).prod() ** (periods_per_year / len(returns)) - 1

# 年化波动率
def annualized_volatility(returns, periods_per_year=252):
    return returns.std() * np.sqrt(periods_per_year)

# 夏普比率
def sharpe_ratio(returns, risk_free_rate=0.03, periods_per_year=252):
    excess_return = returns.mean() * periods_per_year - risk_free_rate
    vol = annualized_volatility(returns, periods_per_year)
    return excess_return / vol if vol != 0 else np.nan

def sortino_ratio(returns, risk_free_rate=0.03, periods_per_year=252):
    # 计算年化超额收益
    excess_return = returns.mean() * periods_per_year - risk_free_rate
    # 只保留负收益部分计算下行波动率
    downside_returns = returns[returns < 0]
    downside_deviation = downside_returns.std() * np.sqrt(periods_per_year)
    # 防止除以零
    if downside_deviation == 0:
        return np.nan
    return excess_return / downside_deviation

# 最大回撤
def max_drawdown(returns):
    wealth_index = (1 + returns).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks) / previous_peaks
    return drawdowns.min()

# 信息比率
def information_ratio(portfolio_returns, benchmark_returns, periods_per_year=252):
    excess_returns = portfolio_returns - benchmark_returns
    ann_excess_return = annualized_return(excess_returns, periods_per_year)
    ann_tracking_error = annualized_volatility(excess_returns, periods_per_year)
    return ann_excess_return / ann_tracking_error if ann_tracking_error != 0 else np.nan

# 超额收益最大回撤
def max_excess_drawdown(portfolio_returns, benchmark_returns):
    excess_returns = portfolio_returns - benchmark_returns
    wealth_index = (1 + excess_returns).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks) / previous_peaks
    return drawdowns.min()

# 相对基准月胜率
def monthly_win_rate(portfolio_returns, benchmark_returns):
    # 按月聚合
    port_monthly = portfolio_returns.resample('ME').sum()
    bench_monthly = benchmark_returns.resample('ME').sum()
    combined = pd.concat([port_monthly, bench_monthly], axis=1).dropna()
    wins = (combined.iloc[:, 0] > combined.iloc[:, 1]).sum()
    total = len(combined)
    return wins / total if total > 0 else np.nan

# 投资组合收益
def portfolio_return(weights, returns):
    return (returns * weights).sum(axis=1)

# 计算所有指标
def evaluate_portfolio(portfolio_weights: dict, start_date: str, end_date: str, benchmark_code='sh000300'):
    stocks = list(portfolio_weights.keys())
    weights = np.array(list(portfolio_weights.values()))
    
    # 获取每只股票的历史价格数据
    prices = {}
    for stock in stocks:
        data = get_stock_data(stock, start_date, end_date)
        prices[stock] = data
    
    # 合并价格数据
    price_df = pd.concat(prices.values(), axis=1).dropna()
    
    # 计算各资产收益率
    returns_df = calculate_returns(price_df)
    
    # 计算投资组合收益率
    portfolio_rets = portfolio_return(weights, returns_df)
    
    # 获取基准指数数据（沪深300）
    try:
        benchmark_price = ak.stock_zh_index_daily(symbol=benchmark_code)
        benchmark_price.index = pd.to_datetime(benchmark_price['date'])
        benchmark_price = benchmark_price.loc[start_date:end_date]
        benchmark_rets = benchmark_price['close'].pct_change().dropna()
        benchmark_rets = benchmark_rets.reindex(portfolio_rets.index, fill_value=0)
    except Exception as e:
        print(f"获取基准数据失败：{e}")
        benchmark_rets = pd.Series(np.zeros(len(portfolio_rets)), index=portfolio_rets.index)
    
    # 计算各项指标
    metrics = {
        '年化收益率': annualized_return(portfolio_rets),
        '年化波动率': annualized_volatility(portfolio_rets),
        '夏普比率': sharpe_ratio(portfolio_rets),
        '索提诺比率': sortino_ratio(portfolio_rets),
        '最大回撤': max_drawdown(portfolio_rets),
        '年化超额收益率': annualized_return(portfolio_rets - benchmark_rets),
        '超额收益年化波动率': annualized_volatility(portfolio_rets - benchmark_rets),
        '信息比率': information_ratio(portfolio_rets, benchmark_rets),
        '相对基准月胜率': monthly_win_rate(portfolio_rets, benchmark_rets),
        '超额收益最大回撤': max_excess_drawdown(portfolio_rets, benchmark_rets),
        '偏度': stats.skew(portfolio_rets),
        '峰度': stats.kurtosis(portfolio_rets),
        'VaR_5%': np.percentile(portfolio_rets, 5),
        'CVaR_5%': portfolio_rets[portfolio_rets <= np.percentile(portfolio_rets, 5)].mean(),
        '累计收益': (1 + portfolio_rets).prod() - 1,
        '年化累计收益': (1 + portfolio_rets.mean())**252 - 1
    }

    # 返回指标和原始收益序列供后续分析
    return pd.Series(metrics), portfolio_rets, benchmark_rets


# 可视化投资组合表现
def plot_portfolio_performance(portfolio_returns_dict, benchmark_rets, title="投资组合累计净值对比"):
    """
    可视化多个投资组合的累计净值曲线。

    Args:
        portfolio_returns_dict (dict): 包含投资组合名称和对应收益率Series的字典。
                                      例如：{"原始投资组合": portfolio_rets_original, "调整后投资组合": portfolio_rets_adjusted}
        benchmark_rets (pd.Series): 基准指数的收益率Series。
        title (str): 图表的标题。
    """
    plt.figure(figsize=(12, 6))
    
    for name, rets in portfolio_returns_dict.items():
        cumulative_rets = (1 + rets).cumprod()
        plt.plot(cumulative_rets, label=name)
    
    cumulative_bench = (1 + benchmark_rets).cumprod()
    plt.plot(cumulative_bench, label="沪深300基准", linestyle='--', color='gray') # 基准线设为灰色虚线

    plt.title(title)
    plt.xlabel("时间")
    plt.ylabel("累计净值")
    plt.legend()
    plt.grid(True)
    plt.show()

    # 收益分布直方图（可以考虑为每个组合单独绘制，或只绘制主要组合）
    # 这里为了简洁，仅绘制第一个组合的日收益率分布
    if portfolio_returns_dict:
        first_portfolio_name = list(portfolio_returns_dict.keys())[0]
        first_portfolio_rets = portfolio_returns_dict[first_portfolio_name]
        plt.figure(figsize=(10, 4))
        sns.histplot(first_portfolio_rets, bins=50, kde=True)
        plt.title(f"{first_portfolio_name} 日收益率分布")
        plt.xlabel("日收益率")
        plt.ylabel("频率")
        plt.grid(True)
        plt.show()


# 示例调用
if __name__ == "__main__":
    def normalize_weights(weights):
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}

    # 原始权重
    original_weights = {
	'601398' : 0.08,  # 贵州茅台 1
    '600036' : 0.10,  # 工商银行
    '002142' : 0.07,  # 招商银行
    '600519' : 0.12,  # 恒瑞医药 1
    '600887' : 0.06,  # 迈瑞医疗
    '600276' : 0.10,  # 药明康德 
    '002415' : 0.07,  # 宁波银行 1
    '300760' : 0.09,  # 海康威视 1
    '601857' : 0.06,  # 三一重工 1
    '601088' : 0.03,  # 中国中车 1
    }

    risk_adjusted_weights = {
        '601398' : 0.09,  # 贵州茅台 1
        '600036' : 0.09,  # 工商银行
        '002142' : 0.06,  # 招商银行
        '600519' : 0.10,  # 恒瑞医药 1
        '600887' : 0.00,  # 迈瑞医疗
        '600276' : 0.08,  # 药明康德 
        '002415' : 0.05,  # 宁波银行 1
        '300760' : 0.08,  # 海康威视 1
        '601857' : 0.00,  # 三一重工 1
        '601088' : 0.03,  # 中国中车 1
        }
    # 调整后的投资组合（降低银行/医药权重，增加消费/公用事业）
    ppo_adjusted_weights = {
	'601398' : 0.11,  # 贵州茅台 1
    '600036' : 0.11,  # 工商银行
    '002142' : 0.07,  # 招商银行
    '600519' : 0.10,  # 恒瑞医药 1
    '600887' : 0.05,  # 迈瑞医疗
    '600276' : 0.13,  # 药明康德 
    '002415' : 0.11,  # 宁波银行 1
    '300760' : 0.12,  # 海康威视 1
    '601857' : 0.11,  # 三一重工 1
    '601088' : 0.07,  # 中国中车 1
    }

    # 归一化后权重
    risk_normalized_weights = normalize_weights(risk_adjusted_weights)
    ppo_normalized_weights = normalize_weights(ppo_adjusted_weights)
    end_date = datetime.datetime.today().strftime("%Y%m%d")
    start_date = (datetime.datetime.today() - datetime.timedelta(days=365*2)).strftime("%Y%m%d")

    # 评估原始投资组合
    metrics_original, portfolio_rets_original, benchmark_rets = evaluate_portfolio(original_weights, start_date, end_date)

    # 评估调整后的投资组合
    risk_metrics_adjusted, risk_portfolio_rets_adjusted, _ = evaluate_portfolio(risk_normalized_weights, start_date, end_date)

    ppo_metrics_adjusted, ppo_portfolio_rets_adjusted, _ = evaluate_portfolio(ppo_normalized_weights, start_date, end_date)
    # 获取沪深300基准收益数据（作为单独的投资组合）
    benchmark_weights = {"sh000300": 1.0}  # 沪深300作为单一资产
    metrics_benchmark, portfolio_rets_benchmark, _ = evaluate_portfolio(benchmark_weights, start_date, end_date)


    # 将两个投资组合的绩效指标整合到DataFrame中
    comparison_df = pd.DataFrame({
        "原始": metrics_original,
        "风险调整": risk_metrics_adjusted,
        "PPO调整":ppo_metrics_adjusted,
        "沪深300基准": metrics_benchmark  # 新增沪深300基准列
    }).T # 转置以便行是组合名称，列是指标

    # 格式化输出，保持两位小数，百分比显示
    formatted_comparison_df = comparison_df.copy()
    for col in ['年化收益率', '年化波动率', '最大回撤', '年化超额收益率', '超额收益年化波动率', '超额收益最大回撤', 'VaR_5%', 'CVaR_5%', '累计收益', '年化累计收益']:
        formatted_comparison_df[col] = formatted_comparison_df[col].apply(lambda x: f"{x:.2%}")
    for col in ['夏普比率', '信息比率', '偏度', '峰度', '相对基准月胜率']:
        formatted_comparison_df[col] = formatted_comparison_df[col].apply(lambda x: f"{x:.4f}")

    print("--- 投资组合绩效对比 ---")
    print(formatted_comparison_df)

    # 可视化两个投资组合的累计净值对比
    portfolio_to_plot = {
        "原始投资组合": portfolio_rets_original,
        "风险调整后投资组合":risk_portfolio_rets_adjusted,
        "PPO调整后投资组合": ppo_portfolio_rets_adjusted
    }
    plot_portfolio_performance(portfolio_to_plot, benchmark_rets, title="投资组合累计净值对比 (原始 vs 调整后)")
