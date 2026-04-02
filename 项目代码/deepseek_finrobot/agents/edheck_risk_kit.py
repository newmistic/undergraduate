import pandas as pd
import numpy as np

def compound(r):
    """
    returns the result of compounding the set of returns in r
    
    """
    return np.expm1(np.log1p(r).sum())

def get_fff_returns():
    """
    Load the Fama-French Research Factor Monthly Dataset
    """
    rets = pd.read_csv("data/F-F_Research_Data_Factors_m.csv",
                       header=0, index_col=0, na_values=-99.99)/100
    rets.index = pd.to_datetime(rets.index, format="%Y%m").to_period('M')
    return rets

#import statsmodels.api as sm
#def regress(dependent_variable, explanatory_variables, alpha=True):
    """
    Runs a linear regression to decompose the dependent variable into the explanatory variables
    returns an object of type statsmodel's RegressionResults on which you can call
       .summary() to print a full summary
       .params for the coefficients
       .tvalues and .pvalues for the significance levels
       .rsquared_adj and .rsquared for quality of fit
    """
#    if alpha:
#        explanatory_variables = explanatory_variables.copy()
#        explanatory_variables["Alpha"] = 1
    
#    lm = sm.OLS(dependent_variable, explanatory_variables).fit()
#    return lm

#------------------------------------------------------------------------------
def annualized_return(r, periods_per_year):
    '''
    Annualizes a set of returns
    We should infer the periods per year
    but that is currently left as an exercise to the reader
    '''
    conpounded_growth = (1+r).prod()
    n_periods = r.shape[0]
    return conpounded_growth**(periods_per_year/n_periods) -1
    
def annualized_vol(r, periods_per_year):
    '''
    Annualizes a set of returns
    We should infer the periods per year
    but that is currently left as an exercise to the reader
    '''
    return r.std()*(periods_per_year**0.5)

def sharpe_ratio(r, riskfree_rate, periods_per_year): 
    """
    Computes the annulized sharpe ratio of a set of return
    """
    # convert the annual riskfree rate to the per period because of monthly returns you have now
    rf_per_period = (1+riskfree_rate)**(1/periods_per_year)-1
    excess_ret = r - rf_per_period
    ann_excess_ret = annualized_return(excess_ret, periods_per_year)
    ann_vol = annualized_vol(r, periods_per_year)
    return ann_excess_ret/ann_vol


def drawdown(return_series: pd.Series):
    '''
    Takes a time series of asset returns.
    Computes and returns a DataFrame with columns for the wealth index, 
    the previous peaks, 
    and the percentage drawdown
    '''
    wealth_index = 1000*(1+return_series).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index-previous_peaks)/previous_peaks
    return pd.DataFrame({
        "Wealth": wealth_index,
        "Peak": previous_peaks,
        "Drawdown": drawdowns  
    })


def get_ffmarket_returns():
    '''
    Load the Fama-French Dataset for the returns of the Top and Bottom Deciles by MarketCap
    '''
    market_m = pd.read_csv("data/Portfolios_Formed_on_ME_monthly_EW.csv", 
                     header=0, index_col=0, parse_dates=True, na_values=-99.99)
    rets = market_m[['Lo 10','Hi 10']]
    rets.columns = ['SmallCap','LargeCap']
    rets = rets/100
    rets.index = pd.to_datetime(rets.index, format="%Y%m").to_period('M')
    return rets

'''
Kenneth R. French: 
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
'''

def get_hfi_returns():
    '''
    Load and format the EDHEC Hedge Fund Index Returns
    '''
    hfi = pd.read_csv("data/edhec-hedgefundindices.csv", 
                     header=0, index_col=0, parse_dates=True)
    hfi = hfi/100
    hfi.index = hfi.index.to_period('M')
    return hfi

#--------------------------------------------------------------
def get_ind_returns():
    '''
    Load and format the Ken French 30 Industry Portfolios Value Weighted Monthly Returns
    '''
    ind = pd.read_csv("data/ind30_m_vw_rets.csv", header=0, index_col=0, parse_dates=True)/100
    ind.index = pd.to_datetime(ind.index, format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind

def get_ind_size():
    '''
    '''
    ind = pd.read_csv("data/ind30_m_size.csv", header=0, index_col=0, parse_dates=True)
    ind.index = pd.to_datetime(ind.index, format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind

def get_ind_nfirms():
    '''
    '''
    ind = pd.read_csv("data/ind30_m_nfirms.csv", header=0, index_col=0, parse_dates=True)
    ind.index = pd.to_datetime(ind.index, format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind
#----------------------------------------------------------------------------

def get_ind_file(filetype, weighting="vw", n_inds=30):
    """
    Load and format the Ken French Industry Portfolios files
    Variant is a tuple of (weighting, size) where:
        weighting is one of "ew", "vw"
        number of inds is 30 or 49
    """    
    if filetype=="returns":
        name = f"{weighting}_rets" 
        divisor = 100
    elif filetype=="nfirms":
        name = "nfirms"
        divisor = 1
    elif filetype=="size":
        name = "size"
        divisor = 1
    else:
        raise ValueError(f"filetype must be one of: returns, nfirms, size")
    
    ind = pd.read_csv(f"data/ind{n_inds}_m_{name}.csv", header=0, index_col=0, na_values=-99.99)/divisor
    ind.index = pd.to_datetime(ind.index, format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind

def get_ind_returns_w(weighting="vw", n_inds=30):
    """
    Load and format the Ken French Industry Portfolios Monthly Returns
    """
    return get_ind_file("returns", weighting=weighting, n_inds=n_inds)


def get_ind_nfirms_w(n_inds=30):
    """
    Load and format the Ken French 30 Industry Portfolios Average number of Firms
    """
    return get_ind_file("nfirms", n_inds=n_inds)

def get_ind_size_w(n_inds=30):
    """
    Load and format the Ken French 30 Industry Portfolios Average size (market cap)
    """
    return get_ind_file("size", n_inds=n_inds)


def get_ind_market_caps(n_inds=30, weights=False):
    """
    Load the industry portfolio data and derive the market caps
    """
    ind_nfirms = get_ind_nfirms_w(n_inds=n_inds)
    ind_size = get_ind_size_w(n_inds=n_inds)
    ind_mktcap = ind_nfirms * ind_size
    if weights:
        total_mktcap = ind_mktcap.sum(axis=1)
        ind_capweight = ind_mktcap.divide(total_mktcap, axis="rows")
        return ind_capweight
    #else
    return ind_mktcap

#---------------------------------------------------------------------------

def semideviation(r):
    '''
    Returns the semideviation aka negtive semideviation of r
    r must be a Series or a DataFrame
    '''
    is_negtive = r < 0
    return r[is_negtive].std(ddof=0)


def skewness(r):
    '''
    Alternative to scipy.stats.skew()
    Computes the skewness of the supplied Series or DataFrame
    Returns a float or Series
    '''
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0) # 自由度为 0，不需要做 n-1 的校正，如果数据足够多的时候，不减一也没关系
    exp = (demeaned_r**3).mean()
    return exp/sigma_r**3

def kurtosis(r):
    '''
    Alternative to scipy.stats.kurtosis()
    Computes the kurtosis of the supplied Series or DataFrame
    Returns a float or Series
    '''
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0) # 自由度为 0，不需要做 n-1 的校正，如果数据足够多的时候，不减一也没关系
    exp = (demeaned_r**4).mean()
    return exp/sigma_r**4


import scipy.stats
def is_normal(r, level=0.01):
    '''
    Applies the Jarque-Bera test to determine if a Series is nomal or not
    Test is applied at 1% level by default
    Returns True if the hypothesis of normality is accepted, False otherwise
    '''
    statistic, p_value = scipy.stats.jarque_bera(r)
    return p_value > level

import numpy as np
def var_historic(r, level=5):
    '''
    Returns the historic Value at Risk at a specified level
    i.e. returns the number such that "level" percent of the returns
    fall below that number, and the (100-level) percent are above
    '''
    if isinstance(r, pd.DataFrame): # python 中内置的函数
        return r.aggregate(var_historic, level=level) # 在每一列上调用var_historic()函数
    elif isinstance(r, pd.Series):
        return -np.percentile(r, level)
    else:
        raise TypeError('Expected r to be Series or DataFrame')


from scipy.stats import norm
def var_gaussian(r, level=5, modified=False):
    '''
    Returns the Parametric Gaussian VaR of a Series or DataFrame
    If 'modified' is True, then the modified VaR id returned,
    using the Cornish-Fisher modification
    '''
    #Compute the Z score assuming it was Gaussian
    z = norm.ppf(level/100) 
    #分位数函数
    if modified:
        # modify the Z score based on obverved skewness and kurtosis
        s = skewness(r)
        k = kurtosis(r)
        z = (z + (z**2-1)*s/6 + (z**3-3*z)*(k-3)/24 - (2*z**3-5*z)*(s**2)/36 )
     
    return -(r.mean() + z*r.std(ddof=0))


def cvar_historic(r, level=5):
    '''
    Computes the Conditional VaR of Seried or DataFrame at a specified level
    i.e. returns the number such that "level" percent of the returns
    fall below that number, and the (100-level) percent are above
    '''
    if isinstance(r, pd.Series): # python 中内置的函数
        is_beyound = r <= -var_historic(r, level=level)
        return -r[is_beyound].mean()
    elif isinstance(r, pd.DataFrame):
        return r.aggregate(cvar_historic, level=level) # 在每一列上调用cvar_historic()函数
    else:
        raise TypeError('Expected r to be Series or DataFrame')


def portfolio_return(weights, returns):
    """
    Weights --> Returns
    """
    return weights.T @ returns # matrix multiplication 

def portfolio_vol(weights, covmat):
    """
    Weights --> Vol
    """
    return (weights.T @ covmat @ weights)**0.5

def plot_ef2(n_points, er, cov, style=".-"):
    """
    Plots the 2-assets efficient frontier
    """
    if er.shape[0] != 2 or cov.shape[0] != 2:
        raise ValueError("plot_ef2 can only plot 2-asset frontiers")
    weights = [np.array([w, 1-w]) for w in np.linspace(0, 1, n_points)]
    rets = [portfolio_return(w, er) for w in weights]
    vols = [portfolio_vol(w, cov) for w in weights]
    ef = pd.DataFrame({"Returns": rets, "Volatility": vols})
    return ef.plot.line(x="Volatility", y="Returns", style=style)


from scipy.optimize import minimize
import numpy as np
def minimize_vol(target_return, er, cov):
    """
    rarget_ret -> W
    """
    #要实现从目标收益得到权重，首先要知道有多少资产
    n = er.shape[0]
    #然后，明确二次优化器的工作方式是，要给定一个目标函数，要给定一些约束，要给一个初步的猜想
    #从最简单的猜想开始，即所有的权重都放在一个资产上，这里考虑等权分配的情况
    ini_guess = np.repeat(1/n, n)
    #让偶给出第一个限制（约束条件）
    bounds = ((0.0, 1.0), )*n
    return_is_target = {
        'type': 'eq',
        'args': (er,),
        'fun': lambda weights, er: target_return - portfolio_return(weights, er)
    }
    weights_sum_to_1 = {
        'type': 'eq',
        'fun': lambda weights: np.sum(weights) - 1      
    }
    results = minimize(portfolio_vol, ini_guess,
                       args=(cov,), method="SLSQP",
                       options={'disp': False}, #不显示运行各种过程
                       constraints=(return_is_target, weights_sum_to_1),
                       bounds=bounds
                      )
    return results.x #把results变成一个 variable (用于收集minimize())里面的内容


def optimal_weights(n_points, er, cov):
    '''
    -> list of target returns to run the optimizer on to minimize the vol to get weights from target returns
    '''
    target_rs = np.linspace(er.min(), er.max(), n_points)
    weights = [minimize_vol(target_return, er, cov) for target_return in target_rs]
    return weights

# def plot_ef(n_points, er, cov, style=".-"):
#     """
#     Plots the multi-assets efficient frontier
#     """
#     weights = optimal_weights(n_points, er, cov)
#     rets = [portfolio_return(w, er) for w in weights]
#     vols = [portfolio_vol(w, cov) for w in weights]
#     ef = pd.DataFrame({"Returns": rets, "Volatility": vols})
#     return ef.plot.line(x="Volatility", y="Returns", style=style)#, weights


def msr(riskfree_rate, er, cov):
    """
    Return the weights of the portfolio that gives you the maximum sharpe ratio
    given the riskfree rate and expected returns and a covariance matrix
    """
    #要实现从目标收益得到权重，首先要知道有多少资产
    n = er.shape[0]
    #然后，明确二次优化器的工作方式是，要给定一个目标函数，要给定一些约束，要给一个初步的猜想
    #从最简单的猜想开始，即所有的权重都放在一个资产上，这里考虑等权分配的情况
    ini_guess = np.repeat(1/n, n)
    #让偶给出第一个限制（约束条件）
    bounds = ((0.0, 1.0), )*n
    weights_sum_to_1 = {
        'type': 'eq',
        'fun': lambda weights: np.sum(weights) - 1      
    }
    def neg_sharpe_ratio(weights, riskfree_rate, er, cov):
        '''
        Return the negtive of the Sharpe ratio, given weights
        '''
        r = portfolio_return(weights, er)
        vol = portfolio_vol(weights, cov)
        return -(r - riskfree_rate)/vol

    results = minimize(neg_sharpe_ratio, ini_guess,
                       args=(riskfree_rate, er, cov,), method="SLSQP",
                       options={'disp': False}, #不显示运行各种过程
                       constraints=(weights_sum_to_1),
                       bounds=bounds
                      )
    return results.x #把results变成一个 variable (用于收集minimize())里面的内容

def plot_ef(n_points, er, cov, style=".-", show_cml=False, riskfree_rate=0):
    """
    Plots the multi-assets efficient frontier
    """
    weights = optimal_weights(n_points, er, cov)
    rets = [portfolio_return(w, er) for w in weights]
    vols = [portfolio_vol(w, cov) for w in weights]
    ef = pd.DataFrame({"Returns": rets, "Volatility": vols})
    
    ax = ef.plot.line(x="Volatility", y="Returns", style=style)#, weights
    
    if show_cml:
        ax.set_xlim(left = 0)
        w_msr = msr(riskfree_rate, er, cov)
        r_msr = portfolio_return(w_msr, er)
        vol_msr = portfolio_vol(w_msr, cov)
        # Add CML
        cml_x = [0, vol_msr] 
        cml_y = [riskfree_rate, r_msr]
        ax.plot(cml_x, cml_y, color="green", marker="o", markersize=12, linestyle="--", linewidth=2)
   
    return ax

def gmv(cov):
    """
    Returns the weights of the Global Minimum Vol Portfolio
    given the covariance matrix
    """
    n = cov.shape[0]
    return msr(0, np.repeat(1, n), cov)

def plot_ef_naive(n_points, er, cov, style=".-", show_cml=False, riskfree_rate=0, show_ew=False, show_gmv=False):
    """
    Plots the multi-assets efficient frontier
    """
    weights = optimal_weights(n_points, er, cov)
    rets = [portfolio_return(w, er) for w in weights]
    vols = [portfolio_vol(w, cov) for w in weights]
    ef = pd.DataFrame({"Returns": rets, "Volatility": vols})
    
    ax = ef.plot.line(x="Volatility", y="Returns", style=style)#, weights

    if show_ew:
        n = er.shape[0]
        w_ew = np.repeat(1/n, n)
        r_ew = portfolio_return(w_ew, er)
        vol_ew = portfolio_vol(w_ew, cov)
        # Display EW
        ax.plot([vol_ew], [r_ew], color='goldenrod', marker='o', markersize=10)

    if show_gmv:
        w_gmv = gmv(cov)
        r_gmv = portfolio_return(w_gmv, er)
        vol_gmv = portfolio_vol(w_gmv, cov)
        # Display GMV
        ax.plot([vol_gmv], [r_gmv], color='midnightblue', marker='o', markersize=10)
   
    if show_cml:
        ax.set_xlim(left = 0)
        w_msr = msr(riskfree_rate, er, cov)
        r_msr = portfolio_return(w_msr, er)
        vol_msr = portfolio_vol(w_msr, cov)
        # Add CML
        cml_x = [0, vol_msr] 
        cml_y = [riskfree_rate, r_msr]
        ax.plot(cml_x, cml_y, color="green", marker="o", markersize=10, linestyle="--", linewidth=2)
   
    return ax

#--风格投资----------------------------------------------------------------------------------
def style_analysis(dependent_variable, explanatory_variables):
    """
    Returns the optimal weights that minimizes the Tracking error between
    a portfolio of the explanatory variables and the dependent variable
    """
    n = explanatory_variables.shape[1]
    init_guess = np.repeat(1/n, n)
    bounds = ((0.0, 1.0),) * n # an N-tuple of 2-tuples!
    # construct the constraints
    weights_sum_to_1 = {'type': 'eq',
                        'fun': lambda weights: np.sum(weights) - 1
    }
    solution = minimize(portfolio_tracking_error, init_guess,
                       args=(dependent_variable, explanatory_variables,), method='SLSQP',
                       options={'disp': False},
                       constraints=(weights_sum_to_1,),
                       bounds=bounds)
    weights = pd.Series(solution.x, index=explanatory_variables.columns)
    return weights

def portfolio_tracking_error(weights, ref_r, bb_r):
    """
    returns the tracking error between the reference returns
    and a portfolio of building block returns held with given weights
    """
    return tracking_error(ref_r, (weights*bb_r).sum(axis=1))

def tracking_error(r_a, r_b):
    """
    Returns the Tracking Error between the two return series
    """
    return np.sqrt(((r_a - r_b)**2).sum())


def summary_stats(r, riskfree_rate=0.03):
    """
    Return a DataFrame that contains aggregated summary stats for the returns in the columns of r
    """
    ann_r = r.aggregate(annualized_return, periods_per_year=12)
    ann_vol = r.aggregate(annualized_vol, periods_per_year=12)
    ann_sr = r.aggregate(sharpe_ratio, riskfree_rate=riskfree_rate, periods_per_year=12)
    dd = r.aggregate(lambda r: drawdown(r).Drawdown.min())
    skew = r.aggregate(skewness)
    kurt = r.aggregate(kurtosis)
    cf_var5 = r.aggregate(var_gaussian, modified=True)
    hist_cvar5 = r.aggregate(cvar_historic)
    return pd.DataFrame({
        "Annualized Return": ann_r,
        "Annualized Vol": ann_vol,
        "Skewness": skew,
        "Kurtosis": kurt,
        "Cornish-Fisher VaR (5%)": cf_var5,
        "Historic CVaR (5%)": hist_cvar5,
        "Sharpe Ratio": ann_sr,
        "Max Drawdown": dd
    })

def ic_regress(df):
    """
    iuput:
    df:Dataframe
    
    output:
        IC值
    """
    # 用于储存结果
    regression_list = []
    # 使用OneHotEncoder对行业代码进行one-hot编码
    industry_encoded = pd.get_dummies(df['Nnindcd'], prefix='Nnindcd')
    x_columns = ['Msmvosd'] + list(industry_encoded.columns)
    # 将编码后的行业标号拼接到因子作为新特征
    df_with_industry = pd.concat([df, industry_encoded], axis=1)
    # 使用groupby按照Trddt分组
    grouped = df_with_industry.groupby('Trddt')
    for trddt, group in grouped:     
        if group['value'].notna().any():
            if group['Msmvosd'].notna().any():
                group = preprocess(group, 'value')
                group = preprocess(group, 'Msmvosd')
                x = group[x_columns].values
                x = x.astype(float)
                y = pd.to_numeric(group['value'].values)                
                model = sm.OLS(y, x)
                results = model.fit()
                residuals = results.resid
                ic = np.corrcoef(group['EXMretwd_shifted'], residuals)[0, 1]
                regression_list.append({'Trddt': trddt, \
                                           'IC': ic})

    regression_results = pd.DataFrame(regression_list)
    
    return regression_results


