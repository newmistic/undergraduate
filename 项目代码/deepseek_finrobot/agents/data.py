import asyncio
import aiohttp
import akshare as ak
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import datetime
import json
import os
from . import edheck_risk_kit as erk
from ..data_source import akshare_utils, cn_news_utils


class AsyncDataCollector():
    """异步数据收集器"""

    def __init__(self):
        super().__init__()
        self.session = None

    async def initialize(self):
        """初始化异步会话"""
        self.session = aiohttp.ClientSession()

    async def close(self):
        """关闭异步会话"""
        if self.session:
            await self.session.close()

    async def collect_data_for_stocks(self, stock_list: List[str], period: str = "daily",
                                      days: int = 120, new_days: int = 30,
                                      news_limit: int = 10) -> Dict[str, Dict[str, Any]]:
        """
        异步收集多个股票的数据

        Args:
            stock_list: 股票代码列表
            period: 时间周期
            days: 历史数据天数
            new_days: 新闻时间范围
            news_limit: 新闻数量限制

        Returns:
            包含所有股票数据的字典，格式为 {symbol: collected_data}
        """
        # 创建任务列表
        tasks = []
        for symbol in stock_list:
            task = asyncio.create_task(
                self.collect_all_data(symbol, period, days, new_days, news_limit)
            )
            tasks.append(task)

        # 并行执行所有任务
        results = await asyncio.gather(*tasks)

        # 将结果整理成字典
        return {symbol: data for symbol, data in zip(stock_list, results)}

    async def collect_all_data(self, symbol: str, period: str = "daily", days: int = 120,
                               new_days: int = 30, news_limit: int = 10) -> Dict[str, Any]:
        """
        收集指定股票的所有基本面数据

        Args:
            symbol: 股票代码
            period: 时间周期
            days: 历史数据天数，默认120天
            new_days: 新闻时间范围（天数）
            news_limit: 新闻数量限制

        Returns:
            包含所有数据的字典
        """
        try:
            # 1. 获取股票基本信息
            stock_info = await self._get_stock_basic_info(symbol)
            if "error" in stock_info:
                return {"error": stock_info["error"]}

            company_name = stock_info.get("股票简称", symbol)
            industry_name = stock_info.get("行业", "")

            # 2. 获取历史行情数据
            stock_history = await self._get_stock_history_data(symbol, period, days)

            # 3. 获取财务指标
            financial_indicator = await self._get_financial_indicators(symbol)

            # 4. 获取行业数据
            industry_data = await self._get_industry_data(industry_name)

            # 5. 获取研究报告
            research_reports = await self._get_research_reports(symbol)

            # 6. 获取财经新闻
            financial_news = await self._get_financial_news(symbol, company_name, new_days, news_limit)

            # 7. 获取行业新闻
            industry_news = await self._get_industry_news(symbol, industry_name)

            # 8. 获取市场情绪数据
            market_sentiment = await self._get_market_sentiment()

            # 9. 获取热门股票排行
            hot_stocks = await self._get_hot_stocks()

            # 10. 获取同行业关注度数据
            industry_attention = await self._get_industry_attention(industry_name)

            # 11. 获取个股关注度数据
            stock_attention = await self._get_stock_attention(symbol)

            # 12. 获取个股参与意愿数据
            stock_desire = await self._get_stock_desire(symbol)

            # 13. 计算技术指标
            stock_history, risk_metrics = await self._calculate_technical_indicators(stock_history)


            # 整合所有数据
            collected_data = {
                "basic_info": {
                    "symbol": symbol,
                    "company_name": company_name,
                    "industry_name": industry_name,
                    "current_price": stock_info.get('最新价', 'N/A'),
                    "pe_ratio": stock_info.get('市盈率(动态)', 'N/A'),
                    "pb_ratio": stock_info.get('市净率', 'N/A'),
                    "total_market_cap": stock_info.get('总市值', 'N/A'),
                    "circulating_market_cap": stock_info.get('流通市值', 'N/A'),
                    "raw_stock_info": stock_info
                },
                "price_history": {
                    "recent_data": stock_history.tail(20) if not stock_history.empty else pd.DataFrame(),
                    "latest_data": stock_history.tail(1).iloc[0] if not stock_history.empty else None,
                    "full_data": stock_history,
                    "period": period,
                    "days": days,
                    "has_data": not stock_history.empty
                },
                "financial_data": {
                    "indicators": financial_indicator.head(5) if not financial_indicator.empty else pd.DataFrame(),
                    "full_indicators": financial_indicator,
                    "has_data": not financial_indicator.empty
                },
                "industry_analysis": industry_data,
                "research_reports": {
                    "recent_reports": research_reports.head(3) if not research_reports.empty else pd.DataFrame(),
                    "full_reports": research_reports,
                    "has_data": not research_reports.empty
                },
                "financial_news": {
                    "news_data": financial_news,
                    "has_data": not financial_news.empty if isinstance(financial_news, pd.DataFrame) else False
                },
                "industry_news": {
                    "news_data": industry_news,
                    "has_data": not industry_news.empty if isinstance(industry_news, pd.DataFrame) else False
                },
                "market_sentiment": {
                    "sentiment_data": market_sentiment,
                    "has_data": isinstance(market_sentiment, dict) and "error" not in market_sentiment
                },
                "hot_stocks": {
                    "hot_data": hot_stocks,
                    "has_data": not hot_stocks.empty if isinstance(hot_stocks, pd.DataFrame) else False
                },
                "industry_attention": {
                    "attention_data": industry_attention,
                    "has_data": not industry_attention.empty if isinstance(industry_attention, pd.DataFrame) else False
                },
                "stock_attention": {
                    "attention_data": stock_attention,
                    "has_data": not stock_attention.empty if isinstance(stock_attention, pd.DataFrame) else False
                },
                "stock_desire": {
                    "desire_data": stock_desire,
                    "has_data": not stock_desire.empty if isinstance(stock_desire, pd.DataFrame) else False
                },
                "risk_metrics": risk_metrics,
                "collection_timestamp": datetime.datetime.now()
            }

            return collected_data

        except Exception as e:
            return {"error": f"数据收集失败: {str(e)}"}

    async def _get_stock_basic_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None, akshare_utils.get_stock_info, symbol)
        except Exception as e:
            return {"error": f"获取股票基本信息失败: {str(e)}"}

    async def _get_stock_history_data(self, symbol: str, period: str, days: int) -> pd.DataFrame:
        """获取股票历史行情数据"""
        try:
            end_date = datetime.datetime.now().strftime("%Y%m%d")
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y%m%d")
            return await asyncio.get_event_loop().run_in_executor(None,
                                                                  akshare_utils.get_stock_history, symbol, period,
                                                                  start_date, end_date)
        except Exception as e:
            print(f"获取历史行情数据失败: {str(e)}")
            return pd.DataFrame()

    async def _get_financial_indicators(self, symbol: str) -> pd.DataFrame:
        """获取财务指标"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None, akshare_utils.get_stock_financial_indicator,
                                                                  symbol)
        except Exception as e:
            print(f"获取财务指标失败: {str(e)}")
            return pd.DataFrame()

    async def _get_industry_data(self, industry_name: str) -> Dict[str, Any]:
        """获取行业数据"""
        try:
            if not industry_name:
                return {"has_data": False, "error": "行业名称为空"}

            # 获取行业列表
            industry_list = await asyncio.get_event_loop().run_in_executor(None, akshare_utils.get_stock_industry_list)
            industry_code = None

            # 查找行业代码
            for _, row in industry_list.iterrows():
                if row["板块名称"] == industry_name:
                    industry_code = row["板块代码"]
                    break

            if not industry_code:
                return {"has_data": False, "error": f"未找到行业 {industry_name} 的代码"}

            # 获取行业成分股
            industry_stocks = await asyncio.get_event_loop().run_in_executor(None,
                                                                             akshare_utils.get_stock_industry_constituents,
                                                                             industry_code)

            if industry_stocks is None or industry_stocks.empty:
                return {"has_data": False, "error": "行业成分股数据为空"}

            # 分析行业表现
            top_stocks = industry_stocks.sort_values("涨跌幅", ascending=False).head(5)
            bottom_stocks = industry_stocks.sort_values("涨跌幅").head(5)

            # 计算行业统计指标
            industry_stats = {
                "average_change_pct": industry_stocks['涨跌幅'].mean(),
                "average_pe": industry_stocks['市盈率'].mean(),
                "average_pb": industry_stocks['市净率'].mean(),
                "stock_count": len(industry_stocks)
            }

            return {
                "has_data": True,
                "industry_code": industry_code,
                "industry_name": industry_name,
                "top_performers": top_stocks,
                "bottom_performers": bottom_stocks,
                "full_constituents": industry_stocks,
                "industry_statistics": industry_stats
            }

        except Exception as e:
            return {"has_data": False, "error": f"获取行业数据失败: {str(e)}"}

    async def _get_research_reports(self, symbol: str) -> pd.DataFrame:
        """获取研究报告"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None, akshare_utils.get_stock_research_report, symbol)
        except Exception as e:
            print(f"获取研究报告失败: {str(e)}")
            return pd.DataFrame()

    async def _get_financial_news(self, symbol: str, company_name: str, days: int, limit: int) -> pd.DataFrame:
        """获取财经新闻"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None,
                                                                  cn_news_utils.search_news, symbol, company_name, days,
                                                                  limit)
        except Exception as e:
            print(f"获取财经新闻失败: {str(e)}")
            return pd.DataFrame()

    async def _get_industry_news(self, symbol: str, industry_name: str) -> pd.DataFrame:
        """获取行业新闻"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None,
                                                                  cn_news_utils.get_stock_industry_news, symbol,
                                                                  industry_name, 5)
        except Exception as e:
            print(f"获取行业新闻失败: {str(e)}")
            return pd.DataFrame()

    async def _get_market_sentiment(self) -> Dict[str, Any]:
        """获取市场情绪数据"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None, cn_news_utils.get_stock_market_sentiment)
        except Exception as e:
            print(f"获取市场情绪时出错: {str(e)}")
            return {"error": str(e)}

    async def _get_hot_stocks(self) -> pd.DataFrame:
        """获取热门股票排行"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None, cn_news_utils.get_stock_hot_rank)
        except Exception as e:
            print(f"获取热门股票时出错: {str(e)}")
            return pd.DataFrame()

    async def _get_industry_attention(self, industry_name: str) -> pd.DataFrame:
        """获取同行业关注度数据"""
        try:
            # 获取行业股票
            industry_stocks = await asyncio.get_event_loop().run_in_executor(None,
                                                                             akshare_utils.get_industry_stocks,
                                                                             industry_name)

            # 获取关注度数据
            comment_data = await asyncio.get_event_loop().run_in_executor(None, ak.stock_comment_em)
            comment_filtered = comment_data[['代码', '名称', "机构参与度", "关注指数"]]

            # 合并数据
            merged_data = pd.merge(
                industry_stocks,
                comment_filtered,
                on='代码',
                how='inner',
                suffixes=('_行情', '_舆情')
            )

            merged_comment = merged_data[[
                '代码',
                '名称_行情',
                '机构参与度',
                '关注指数'
            ]].rename(columns={'名称_行情': '名称'})

            return merged_comment
        except Exception as e:
            print(f"获取行业关注度数据失败: {str(e)}")
            return pd.DataFrame()

    async def _get_stock_attention(self, symbol: str) -> pd.DataFrame:
        """获取个股关注指数"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None,
                                                                  ak.stock_comment_detail_scrd_focus_em, symbol)
        except Exception as e:
            print(f"获取个股关注指数失败: {str(e)}")
            return pd.DataFrame()

    async def _get_stock_desire(self, symbol: str) -> pd.DataFrame:
        """获取个股参与意愿"""
        try:
            return await asyncio.get_event_loop().run_in_executor(None,
                                                                  ak.stock_comment_detail_scrd_desire_daily_em, symbol)
        except Exception as e:
            print(f"获取个股参与意愿失败: {str(e)}")
            return pd.DataFrame()

    async def _calculate_technical_indicators(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        计算技术指标

        Args:
            df: 股票历史数据DataFrame，必须包含'收盘'列

        Returns:
            添加了技术指标的DataFrame和风险指标字典
        """
        if df.empty or '收盘' not in df.columns:
            return df, {}

        # 计算移动平均线
        df['MA5'] = df['收盘'].rolling(window=5).mean()
        df['MA10'] = df['收盘'].rolling(window=10).mean()
        df['MA20'] = df['收盘'].rolling(window=20).mean()
        df['MA60'] = df['收盘'].rolling(window=60).mean()

        # 计算MACD
        df['EMA12'] = df['收盘'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['收盘'].ewm(span=26, adjust=False).mean()
        df['DIF'] = df['EMA12'] - df['EMA26']
        df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
        df['MACD'] = 2 * (df['DIF'] - df['DEA'])

        # 计算RSI
        delta = df['收盘'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 计算KDJ
        low_min = df['最低'].rolling(window=9).min()
        high_max = df['最高'].rolling(window=9).max()
        df['RSV'] = 100 * ((df['收盘'] - low_min) / (high_max - low_min))
        df['K'] = df['RSV'].ewm(com=2).mean()
        df['D'] = df['K'].ewm(com=2).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']

        # 计算布林带
        df['BOLL_MIDDLE'] = df['收盘'].rolling(window=20).mean()
        df['BOLL_STD'] = df['收盘'].rolling(window=20).std()
        df['BOLL_UPPER'] = df['BOLL_MIDDLE'] + 2 * df['BOLL_STD']
        df['BOLL_LOWER'] = df['BOLL_MIDDLE'] - 2 * df['BOLL_STD']

        # 计算风险指标
        try:
            df_temp = erk.drawdown(df['涨跌幅'])
            df['Wealth'] = df_temp['Wealth']
            df['Peak'] = df_temp['Peak']
            df['drawdown'] = df_temp['Drawdown']

            risk_metrics = {
                'annualized_return': erk.annualized_return(df['涨跌幅'], 252),
                'annualized_vol': erk.annualized_vol(df['涨跌幅'], 252),
                'sharpe_ratio': erk.sharpe_ratio(df['涨跌幅'], 0.017, 252),
                'max_drawdown': erk.drawdown(df['涨跌幅'])['Drawdown'].min(),
                'compound': erk.compound(df['涨跌幅']),
                'semideviation': erk.semideviation(df['涨跌幅']),
                'skewness': erk.skewness(df['涨跌幅']),
                'kurtosis': erk.kurtosis(df['涨跌幅']),
                'var_historic': erk.var_historic(df['涨跌幅']),
                'var_gaussian': erk.var_gaussian(df['涨跌幅']),
                'cvar_historic': erk.cvar_historic(df['涨跌幅'])
            }
        except Exception as e:
            print(f"计算风险指标时出错: {e}")
            # 提供默认值
            df['Wealth'] = (1 + df['涨跌幅']).cumprod()
            df['Peak'] = df['Wealth'].cummax()
            df['drawdown'] = (df['Wealth'] - df['Peak']) / df['Peak']

            risk_metrics = {
                'annualized_return': df['涨跌幅'].mean() * 252,
                'annualized_vol': df['涨跌幅'].std() * np.sqrt(252),
                'sharpe_ratio': 0,
                'max_drawdown': df['drawdown'].min(),
                'compound': df['Wealth'].iloc[-1] - 1,
                'semideviation': df['涨跌幅'][df['涨跌幅'] < 0].std(),
                'skewness': df['涨跌幅'].skew(),
                'kurtosis': df['涨跌幅'].kurtosis(),
                'var_historic': df['涨跌幅'].quantile(0.05),
                'var_gaussian': 0,
                'cvar_historic': df['涨跌幅'][df['涨跌幅'] <= df['涨跌幅'].quantile(0.05)].mean()
            }

        return df, risk_metrics

    async def get_data_summary(self, data: Dict[str, Any]) -> str:
        """
        获取数据收集摘要

        Args:
            data: collect_all_data返回的数据字典

        Returns:
            数据摘要文本
        """
        if "error" in data:
            return f"数据收集失败: {data['error']}"

        risk_metrics = data["risk_metrics"]
        history_data = data["price_history"]

        summary = f"""
    数据收集摘要 - {data['basic_info']['company_name']} ({data['basic_info']['symbol']})
    =====================================
    收集时间: {data['collection_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

    数据模块状态:
    - 基本信息: ✓ 已获取
    - 价格历史: {'✓ 已获取' if data['price_history']['has_data'] else '✗ 缺失'}
    - 财务指标: {'✓ 已获取' if data['financial_data']['has_data'] else '✗ 缺失'}  
    - 行业分析: {'✓ 已获取' if data['industry_analysis'].get('has_data', False) else '✗ 缺失'}
    - 研究报告: {'✓ 已获取' if data['research_reports']['has_data'] else '✗ 缺失'}
    - 财经新闻: {'✓ 已获取' if data['financial_news']['has_data'] else '✗ 缺失'}
    - 行业新闻: {'✓ 已获取' if data['industry_news']['has_data'] else '✗ 缺失'}
    - 市场情绪: {'✓ 已获取' if data['market_sentiment']['has_data'] else '✗ 缺失'}
    - 热门股票: {'✓ 已获取' if data['hot_stocks']['has_data'] else '✗ 缺失'}
    - 行业关注度: {'✓ 已获取' if data['industry_attention']['has_data'] else '✗ 缺失'}
    - 个股关注度: {'✓ 已获取' if data['stock_attention']['has_data'] else '✗ 缺失'}
    - 个股参与意愿: {'✓ 已获取' if data['stock_desire']['has_data'] else '✗ 缺失'}

    - 技术指标: {'✓ 已计算' if 'MA5' in history_data['full_data'].columns else '✗ 缺失'}
    - 风险指标: {'✓ 已计算' if risk_metrics and 'annualized_vol' in risk_metrics else '✗ 缺失'}
    """
        return summary


async def main():
    # 需要收集数据的股票列表
    stocks_to_collect = [
        "600519",  # 贵州茅台
        "000001",  # 平安银行
        "000651"  # 格力电器
    ]

    # 创建异步数据收集器
    collector = AsyncDataCollector()

    try:
        # 初始化
        await collector.initialize()

        # 收集数据
        print(f"开始收集 {len(stocks_to_collect)} 只股票的数据...")
        all_data = await collector.collect_data_for_stocks(stocks_to_collect)

        for symbol, data in all_data.items():
            if "error" in data:
                print(f"股票 {symbol} 数据收集失败: {data['error']}")
                continue

            # 打印数据摘要
            summary = await collector.get_data_summary(data)
            print("\n" + "=" * 80)
            print(summary)
            print("=" * 80 + "\n")



    finally:
        # 清理资源
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())