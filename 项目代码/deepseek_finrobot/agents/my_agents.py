import autogen
from typing import Dict, List, Optional, Union, Any
import os
import json
import torch
import asyncio
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from .data import AsyncDataCollector
from ..utils import get_current_date, get_llm_config_for_autogen


def extract_analysis_result_from_conversation(user_proxy, analyst) -> Optional[str]:
    """
    从AutoGen对话中提取分析结果

    Args:
        user_proxy: AutoGen UserProxyAgent实例
        analyst: AutoGen AssistantAgent实例

    Returns:
        提取的分析结果文本，如果未找到则返回None
    """
    try:
        result = None
        all_messages = []

        # 收集所有消息
        if hasattr(user_proxy, '_oai_messages'):
            all_messages.extend(user_proxy._oai_messages.get(analyst, []))
        if hasattr(analyst, '_oai_messages'):
            all_messages.extend(analyst._oai_messages.get(user_proxy, []))

        # 从最新消息中提取助手回复
        for msg in reversed(all_messages):
            if isinstance(msg, dict) and msg.get("role") == "assistant" and "content" in msg:
                result = msg["content"]
                break

        return result
    except Exception as e:
        print(f"提取分析结果时出错: {str(e)}")
        return None


class FundamentalAnalysisAgent:
    """
    基本面分析Agent - 专注于单股票分析，支持手动导出
    """

    def __init__(self, llm_config: Dict[str, Any], log_callback=None):
        self.llm_config = get_llm_config_for_autogen(**llm_config)
        self.log_callback = log_callback

        # 初始化AutoGen agents
        self.user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            code_execution_config={"work_dir": ".", "use_docker": False},
        )
        self.analyst = autogen.AssistantAgent(
            name="FundamentalAnalyst",
            llm_config=self.llm_config,
            system_message="""你是一位专业的基本面分析师，擅长综合分析股票、公司财务和行业趋势。
你需要基于提供的股票数据、财务指标、行业数据等基本面信息，给出全面的基本面分析。
你的分析应包括：
1. 个股技术与基本面分析
2. 公司财务状况与行业对比
3. 行业趋势、竞争格局与投资机会
4. 风险提示
请确保分析逻辑清晰，结论有理有据。"""
        )

        # 分析结果存储
        self.current_result = None
        self.current_data = None

    def analyze_fundamental(self, symbol: str, collected_data: Dict[str, Any], log_callback=None) -> str:
        if log_callback is None:
            log_callback = self.log_callback
        if log_callback:
            log_callback(f"开始基本面分析: {symbol}")
        try:
            # 检查数据有效性
            if "error" in collected_data:
                return f"提供的数据存在错误: {collected_data['error']}"

            # 重置对话状态
            self.reset()

            # 格式化分析请求
            basic_info = collected_data["basic_info"]
            price_history = collected_data["price_history"]
            financial_data = collected_data["financial_data"]
            industry_data = collected_data["industry_analysis"]
            research_data = collected_data["research_reports"]

            analysis_request = f"""
    请对以下公司及其行业进行全面的基本面分析（不涉及新闻和市场情绪）：

    【公司信息】
    股票代码: {basic_info['symbol']}
    股票名称: {basic_info['company_name']}
    所属行业: {basic_info['industry_name']}
    当前价格: {basic_info['current_price']}
    市盈率: {basic_info['pe_ratio']}
    市净率: {basic_info['pb_ratio']}
    总市值: {basic_info['total_market_cap']}
    流通市值: {basic_info['circulating_market_cap']}

    【最近30天价格走势】
    {price_history['recent_data'][['收盘', '成交量']].to_string() if price_history['has_data'] else "无行情数据"}

    【主要财务指标】
    {financial_data['indicators'].to_string() if financial_data['has_data'] else "无财务数据"}

    【行业成分股表现】
    {industry_data['top_performers'][['代码', '名称', '最新价', '涨跌幅', '市盈率']].to_string() if industry_data.get('has_data', False) else "无行业成分股数据"}

    【行业整体表现】
    {f"平均涨跌幅: {industry_data['industry_statistics']['average_change_pct']:.2f}%, 平均市盈率: {industry_data['industry_statistics']['average_pe']:.2f}, 平均市净率: {industry_data['industry_statistics']['average_pb']:.2f}" if industry_data.get('has_data', False) else "无行业数据"}

    【研究报告】
    {research_data['recent_reports'][['title', 'author']].to_string() if research_data['has_data'] else "无研究报告"}
    
    请基于以上所有基本面数据，完成以下分析：
    1. 个股技术面与基本面分析（不涉及新闻和市场情绪）
    2. 公司财务状况与行业对比
    3. 行业趋势、竞争格局与投资机会
    4. 风险提示
    请结构化、专业地给出你的分析结论。
    """

            # 发起分析对话
            print("开始进行基本面分析...")
            self.user_proxy.initiate_chat(
                self.analyst,
                message=analysis_request,
                max_turns=1
            )

            # 提取分析结果
            result = extract_analysis_result_from_conversation(self.user_proxy, self.analyst)

            # 更新状态并返回结果
            if result and result.strip():
                self.current_result = result
                if log_callback:
                    log_callback(f"完成基本面分析: {symbol}")
                return result
            else:
                return f"无法获取分析结果：对话未成功完成，请检查API连接或重试"

        except Exception as e:
            if log_callback:
                log_callback(f"基本面分析出错: {symbol} - {str(e)}")
            return f"分析时出错: {str(e)}"

    def reset(self):
        """重置AutoGen Agent状态（保留分析结果）"""
        self.current_result = None
        self.user_proxy.reset()
        self.analyst.reset()



class PublicAnalysisAgent:
    """
    舆情分析Agent - 专注于单股票舆情分析
    """

    def __init__(self, llm_config: Dict[str, Any], log_callback=None):
        self.llm_config = get_llm_config_for_autogen(**llm_config)
        self.log_callback = log_callback

        # 初始化AutoGen agents
        self.user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            code_execution_config={"work_dir": ".", "use_docker": False},
        )
        self.news_analyst = autogen.AssistantAgent(
            name="PublicAnalyst",
            llm_config=self.llm_config,
            system_message="""你是一位专业的财经舆情分析师，擅长分析财经新闻、行业新闻和市场情绪对市场和个股的影响。
你需要分析提供的财经新闻、行业新闻、市场情绪指标、个股热度和个股情绪，给出对市场或个股的影响分析。
你的分析应该包括以下几个方面：
1. 新闻摘要：简要概括财经新闻和行业新闻内容
2. 影响分析：分析新闻、行业新闻和市场情绪对市场或个股的潜在影响
3. 情绪评估：评估新闻和行业新闻的市场情绪（积极/消极/中性）
4. 情感分析：分析公众对个股的情感倾向和关注度
请确保你的分析逻辑清晰，观点客观中立。不要分析公司财务、行业基本面等内容。"""
        )

        # 分析结果存储
        self.current_result = None
        self.current_data = None

    def analyze_public_sentiment(self, symbol: str, collected_data: Dict[str, Any], log_callback=None) -> str:
        if log_callback is None:
            log_callback = self.log_callback
        if log_callback:
            log_callback(f"开始舆情分析: {symbol}")
        try:
            # 检查数据有效性
            if "error" in collected_data:
                return f"提供的数据存在错误: {collected_data['error']}"

            # 保存当前状态
            self.current_data = collected_data

            # 重置对话状态
            self.reset()

            # 格式化分析请求
            basic_info = collected_data["basic_info"]
            financial_news = collected_data["financial_news"]
            industry_news = collected_data["industry_news"]
            market_sentiment = collected_data["market_sentiment"]
            hot_stocks = collected_data["hot_stocks"]
            industry_attention = collected_data["industry_attention"]
            stock_attention = collected_data["stock_attention"]
            stock_desire = collected_data["stock_desire"]

            # 处理热门股票数据
            hot_stocks_str = "无热门股票数据"
            if hot_stocks['has_data']:
                try:
                    available_columns = hot_stocks['hot_data'].columns.tolist()
                    hot_stocks_str = hot_stocks['hot_data'][available_columns].head(5).to_string()
                except Exception as e:
                    hot_stocks_str = "热门股票数据处理失败"

            # 处理行业关注度数据
            industry_attention_str = "无行业关注度数据"
            if industry_attention['has_data']:
                try:
                    industry_attention_str = industry_attention['attention_data'].describe().to_string()
                except Exception as e:
                    industry_attention_str = "行业关注度数据处理失败"

            analysis_request = f"""
请分析以下财经新闻、行业新闻和市场情绪，并给出对市场或相关个股的影响分析：

【最新财经新闻】
{financial_news['news_data'][['title', 'content']].to_string() if financial_news['has_data'] else "无相关新闻"}

【行业新闻】
{industry_news['news_data'][['title', 'content']].to_string() if industry_news['has_data'] else "无行业新闻"}

【市场情绪指标】
{json.dumps(market_sentiment['sentiment_data'], ensure_ascii=False, indent=2) if market_sentiment['has_data'] else "无市场情绪数据"}

【热门股票】
{hot_stocks_str}

【同行业市场机构参与度、关注指数总体情况】
{industry_attention_str}

【{basic_info['company_name']}一段时间内用户关注指数】
{stock_attention['attention_data'].to_string() if stock_attention['has_data'] else "无个股关注指数数据"}

【{basic_info['company_name']}一段时间内日度市场参与意愿】
{stock_desire['desire_data'].to_string() if stock_desire['has_data'] else "无个股参与意愿数据"}

请基于以上新闻、行业新闻、市场情绪和个股关注，分析其对市场或相关个股的潜在影响。你的分析应包括新闻摘要、影响分析、情绪评估和情感分析，不要分析公司财务或行业基本面。
"""

            # 发起分析对话
            self.user_proxy.initiate_chat(
                self.news_analyst,
                message=analysis_request,
                max_turns=1
            )

            # 提取分析结果
            result = extract_analysis_result_from_conversation(self.user_proxy, self.news_analyst)

            # 更新状态并返回结果
            if result and result.strip():
                self.current_result = result
                if log_callback:
                    log_callback(f"完成舆情分析: {symbol}")
                return result
            else:
                return f"无法获取分析结果：对话未成功完成，请检查API连接或重试"

        except Exception as e:
            if log_callback:
                log_callback(f"舆情分析出错: {symbol} - {str(e)}")
            return f"分析时出错: {str(e)}"

    def reset(self):
        """重置AutoGen Agent状态"""
        self.current_result = None
        self.user_proxy.reset()
        self.news_analyst.reset()



class RiskAnalysisAgent:
    """
    风险分析Agent - 专注于单股票风险分析
    """

    def __init__(self, llm_config: Dict[str, Any], log_callback=None):
        self.llm_config = get_llm_config_for_autogen(**llm_config)
        self.log_callback = log_callback

        # 创建用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        # 创建风险分析师代理
        self.risk_analyst = autogen.AssistantAgent(
            name="RiskAnalyst",
            llm_config=self.llm_config,
            system_message="""你是一位专业的风险分析师，擅长使用各种技术指标和量化方法评估股票投资风险。

你的分析职责包括：
1. 技术风险评估：基于MA5/MA20、RSI、KDJ、MACD、Wealth、Peak、drawdown等技术指标分析风险
2. 波动性风险：分析价格波动特征、年化波动率、最大回撤等
3. 市场风险：评估趋势风险、关键价位突破风险
4. 量化风险指标：VaR、CVaR、夏普比率、偏度、峰度等风险度量
5. 风险等级评定：综合评估给出风险等级（高风险/中风险/低风险）

你必须以标准化的JSON格式输出风险分析结果，格式如下：
{
    "stock_code": "股票代码",
    "risk_level": "高风险/中风险/低风险",
    "overall_risk_score": 风险评分(1-10),
    "technical_risks": {
        "trend_risk": "趋势风险描述",
        "support_resistance_risk": "关键价位风险",
        "technical_indicators_risk": "技术指标风险"
    },
    "quantitative_risks": {
        "volatility_risk": "波动性风险描述",
        "max_drawdown": 最大回撤百分比,
        "var_risk": "VaR风险值",
        "sharpe_ratio": 夏普比率
    },
    "risk_warnings": [
        "具体风险警告1",
        "具体风险警告2"
    ],
    "risk_management_suggestions": [
        "风险管理建议1",
        "风险管理建议2"
    ]
}

请确保你的分析客观、准确，基于数据而非主观判断。"""
        )

        # 分析结果存储
        self.current_result = None
        self.current_data = None

    def analyze_risk(self, symbol: str, collected_data: Dict[str, Any], log_callback=None) -> Dict[str, Any]:
        if log_callback is None:
            log_callback = self.log_callback
        if log_callback:
            log_callback(f"开始风险分析: {symbol}")
        try:
            # 检查数据有效性
            if "error" in collected_data:
                return {"error": f"提供的数据存在错误: {collected_data['error']}"}

            # 保存当前状态
            self.current_data = collected_data

            # 重置对话状态
            self.reset()

            # 提取数据
            basic_info = collected_data["basic_info"]
            history_data = collected_data["price_history"]
            risk_metrics = collected_data["risk_metrics"]
            latest_data = history_data["latest_data"]
            recent_data = history_data["recent_data"]

            # 格式化分析请求
            analysis_request = f"""
请对以下股票进行专业风险分析：

== 基本信息 ==
股票代码: {symbol}
股票名称: {basic_info['company_name']}
当前价格: {basic_info['current_price']}
分析周期: {history_data['period']} ({history_data['days']}天)

== 最新技术指标 ==
收盘价: {latest_data.get('收盘', 0)}
MA5: {latest_data.get('MA5', 0)}
MA20: {latest_data.get('MA20', 0)}
RSI: {latest_data.get('RSI', 0)}
KDJ_K: {latest_data.get('K', 0)}
KDJ_D: {latest_data.get('D', 0)}
MACD: {latest_data.get('MACD', 0)}
当前回撤: {latest_data.get('drawdown', 0)}

== 量化风险指标 ==
年化收益率: {risk_metrics.get('annualized_return', 0)}
年化波动率: {risk_metrics.get('annualized_vol', 0)}
夏普比率: {risk_metrics.get('sharpe_ratio', 0)}
最大回撤: {risk_metrics.get('max_drawdown', 0)}
VaR(5%): {risk_metrics.get('var_historic', 0)}
CVaR(5%): {risk_metrics.get('cvar_historic', 0)}
偏度: {risk_metrics.get('skewness', 0)}
峰度: {risk_metrics.get('kurtosis', 0)}

== 近期趋势数据 ==
{recent_data[['收盘', 'MA5', 'MA20', 'RSI', 'K', 'D', 'MACD', 'drawdown']].tail(5).to_string()}

请基于以上数据进行全面风险分析，必须严格按照以下JSON格式输出：

{{
    "stock_code": "{symbol}",
    "risk_level": "高风险/中风险/低风险",
    "overall_risk_score": 数字(1-10),
    "technical_risks": {{
        "trend_risk": "趋势风险描述",
        "support_resistance_risk": "关键价位风险",
        "technical_indicators_risk": "技术指标风险"
    }},
    "quantitative_risks": {{
        "volatility_risk": "波动性风险描述",
        "max_drawdown": {risk_metrics.get('max_drawdown', 0)},
        "var_risk": "VaR风险分析",
        "sharpe_ratio": {risk_metrics.get('sharpe_ratio', 0)}
    }},
    "risk_warnings": [
        "具体风险警告"
    ],
    "risk_management_suggestions": [
        "具体管理建议"
    ]
}}
"""

            # 发起分析对话
            self.user_proxy.initiate_chat(
                self.risk_analyst,
                message=analysis_request,
                max_turns=1
            )

            # 提取分析结果
            result = extract_analysis_result_from_conversation(self.user_proxy, self.risk_analyst)

            # 更新状态并返回结果
            if result:
                self.current_result = result
                if log_callback:
                    log_callback(f"完成风险分析: {symbol}")
                return result
            else:
                # 返回基础风险评估
                return self._create_basic_risk_assessment(symbol, risk_metrics)

        except Exception as e:
            if log_callback:
                log_callback(f"风险分析出错: {symbol} - {str(e)}")
            return {"error": f"分析时出错: {str(e)}"}

    def _create_basic_risk_assessment(self, symbol: str, risk_metrics: Dict) -> Dict[str, Any]:
        """创建基础风险评估"""

        # 基于量化指标评估风险等级
        volatility = risk_metrics.get('annualized_vol', 0)
        max_drawdown = abs(risk_metrics.get('max_drawdown', 0))
        sharpe_ratio = risk_metrics.get('sharpe_ratio', 0)

        # 风险评分逻辑
        risk_score = 5  # 基础分

        if volatility > 0.3:  # 年化波动率超过30%
            risk_score += 2
        elif volatility < 0.15:  # 年化波动率低于15%
            risk_score -= 1

        if max_drawdown > 0.2:  # 最大回撤超过20%
            risk_score += 2
        elif max_drawdown < 0.1:  # 最大回撤低于10%
            risk_score -= 1

        if sharpe_ratio < 0:  # 夏普比率为负
            risk_score += 1
        elif sharpe_ratio > 1:  # 夏普比率大于1
            risk_score -= 1

        # 确定风险等级
        if risk_score >= 7:
            risk_level = "高风险"
        elif risk_score <= 3:
            risk_level = "低风险"
        else:
            risk_level = "中风险"

        return {
            "stock_code": symbol,
            "risk_level": risk_level,
            "overall_risk_score": max(1, min(10, risk_score)),
            "technical_risks": {
                "trend_risk": "基于历史数据的趋势风险评估",
                "support_resistance_risk": "关键价位突破风险需持续监控",
                "technical_indicators_risk": "技术指标显示正常波动范围"
            },
            "quantitative_risks": {
                "volatility_risk": f"年化波动率{volatility:.2%}，属于{'高' if volatility > 0.25 else '中' if volatility > 0.15 else '低'}波动",
                "max_drawdown": max_drawdown,
                "var_risk": f"VaR风险值{risk_metrics.get('var_historic', 0):.2%}",
                "sharpe_ratio": sharpe_ratio
            },
            "risk_warnings": [
                f"最大回撤达到{max_drawdown:.2%}，需注意风险控制" if max_drawdown > 0.15 else "回撤风险相对可控",
                f"波动率{volatility:.2%}，属于{'高' if volatility > 0.25 else '正常'}波动水平"
            ],
            "risk_management_suggestions": [
                "建议设置合理止损位，控制单笔损失",
                "根据风险承受能力调整仓位大小",
                "定期评估和调整投资策略"
            ]
        }

    def reset(self):
        """重置聊天历史"""
        self.current_result = None
        self.user_proxy.reset()
        self.risk_analyst.reset()



class ExpectAdjustmentAgent:
    def __init__(self, llm_config, device="cpu"):
        self.device = device
        self.policy = None
        # 构建兼容两个版本API的llm_config
        self.llm_config = get_llm_config_for_autogen(**llm_config)

        # 创建用户代理
        self.user = autogen.UserProxyAgent(
            name="User",
            human_input_mode="TERMINATE",
            code_execution_config={"work_dir": ".", "use_docker": False},
        )

        # 创建投资组合管理代理
        self.portfolio_manager = autogen.AssistantAgent(
            name="PortfolioManager",
            llm_config=self.llm_config,
            system_message="""你是一位专业的投资组合管理师，擅长构建和优化投资组合。
你需要分析提供的股票数据、行业数据和市场情绪，给出投资组合建议。
你的分析应该包括以下几个方面：
1. 资产配置：不同资产类别（股票、债券、现金等）的配置比例
2. 行业配置：不同行业的配置比例
3. 个股选择：具体的股票选择和权重
4. 风险分析：投资组合的风险特征和分散化程度
5. 预期收益：投资组合的预期收益和风险调整后收益
6. 再平衡策略：投资组合的再平衡频率和触发条件

请确保你的分析逻辑清晰，建议符合投资者的风险偏好和投资目标。"""
        )

        self.analysis_generated = False
        self.full_analysis_content = None

    def dynamic_portfolio_adjustment(self,
                                     current_portfolio: Dict[str, float],
                                     collected_data: Dict[str, Dict[str, Any]],
                                     market_trend_prediction: str = None,
                                     risk_preference: str = "中等",
                                     investment_horizon: str = "长期") -> str:
        """基于PPO的动态投资组合调整，使用已收集的数据"""
        # 初始化默认值
        trend = "震荡"  # 默认趋势
        market_sentiment = {
            "market_trend": {
                "trend": trend,
                "sentiment": "中性"
            },
            "north_flow": {
                "value": 0
            }
        }

        try:
            # ====================== 0. 数据准备 ======================
            stocks = list(current_portfolio.keys())

            # 检查是否所有股票都有收集数据
            missing_stocks = [s for s in stocks if s not in collected_data]
            if missing_stocks:
                return f"错误：缺少以下股票的数据: {', '.join(missing_stocks)}"

            # 从收集的数据中提取股票信息
            self.stocks_info = {}
            self.stocks_history = {}
            for symbol in stocks:
                data = collected_data[symbol]
                self.stocks_info[symbol] = data['basic_info']
                self.stocks_history[symbol] = data['price_history']['full_data']

            # 使用收集数据中的市场情绪信息
            market_sentiment_data = next(iter(collected_data.values()))['market_sentiment']['sentiment_data']

            if isinstance(market_sentiment_data, dict) and 'error' not in market_sentiment_data:
                # 如果市场情绪数据可用
                trend = market_sentiment_data['market_trend']['trend']
                north_flow = market_sentiment_data['north_flow']['value']

                # 计算情绪
                if trend == "上涨" and north_flow > 0:
                    sentiment = "积极"
                elif trend == "下跌" and north_flow < 0:
                    sentiment = "消极"
                else:
                    sentiment = "中性"

                market_sentiment = {
                    "market_trend": {
                        "trend": trend,
                        "sentiment": sentiment
                    },
                    "north_flow": {
                        "value": north_flow
                    }
                }
            else:
                # 如果市场情绪数据不可用，使用默认值
                print("使用默认市场情绪数据")
                market_sentiment = {
                    "market_trend": {
                        "trend": "震荡",
                        "sentiment": "中性"
                    },
                    "north_flow": {
                        "value": 0
                    }
                }

            if market_trend_prediction is None:
                market_trend_prediction = trend

            # ====================== 构建PPO状态空间 ======================
            state, state_dim = self._build_ppo_state(current_portfolio, market_sentiment)
            action_dim = len(stocks)

            # ====================== PPO策略初始化与动作生成 ======================
            if not self.policy or self.policy.layers[0].in_features != state_dim:
                self._init_ppo_policy(state_dim, action_dim)

            with torch.no_grad():
                state_tensor = torch.from_numpy(state).float().unsqueeze(0).to(self.device)
                action = self.policy(state_tensor).squeeze().cpu().numpy()

            # ====================== 5. 应用动作并施加约束 ======================
            sector_adjustments = self.get_sector_adjustment(risk_preference, market_sentiment, investment_horizon)
            adjusted_portfolio = self._apply_ppo_action(current_portfolio, action, sector_adjustments)

            # ====================== 6. 奖励计算与模拟收益 ======================
            portfolio_values = self._simulate_portfolio_returns(adjusted_portfolio, self.stocks_history)
            reward = self.calculate_ppo_reward(
                np.array(list(current_portfolio.values())),
                np.array(list(adjusted_portfolio.values())),
                portfolio_values,
                market_trend_prediction
            )

            # ====================== 7. 生成LLM分析请求 ======================
            request = self._build_dynamic_request(
                adjusted_portfolio,
                reward,
                risk_preference,
                investment_horizon,
                market_trend_prediction
            )

            # 调用LLM生成建议
            return self._initiate_llm_analysis(request, current_portfolio)

        except Exception as e:
            return f"动态调整失败: {str(e)}"

    def _build_ppo_state(self, current_portfolio: Dict[str, float], market_sentiment: Dict[str, Any]):
        """构建PPO状态向量并返回维度"""
        state = []
        stocks = list(current_portfolio.keys())
        N = len(stocks)

        # 1. 持仓权重（N维）
        state.extend(current_portfolio.values())

        # 2. 个股年化收益+波动率（2N维）
        for symbol in stocks:
            history = self.stocks_history.get(symbol, pd.DataFrame())
            if not history.empty and '收盘' in history.columns:
                returns = history['收盘'].pct_change().dropna()
                state.extend([
                    returns.mean() * 252 if len(returns) > 0 else 0.0,
                    returns.std() * (252 ** 0.5) if len(returns) > 0 else 0.0
                ])
            else:
                state.extend([0.0, 0.0])

        # 3. 市场情绪（3维one-hot）
        sentiment = market_sentiment.get("market_trend", {}).get("sentiment", "中性")
        sentiment_mapping = {"积极": [1, 0, 0], "中性": [0, 1, 0], "消极": [0, 0, 1]}
        state.extend(sentiment_mapping.get(sentiment, [0, 1, 0]))  # 默认中性

        # 4. 行业分布（固定7维，不足补0）
        industry_dist = {}
        for symbol in stocks:
            industry = self.stocks_info.get(symbol, {}).get("industry_name", "未知")
            if industry not in industry_dist:
                industry_dist[industry] = 0.0
            industry_dist[industry] += current_portfolio[symbol]

        target_industries = ["银行", "必需消费", "医药", "公用事业", "白酒", "科技", "新能源"]
        state.extend([industry_dist.get(industry, 0.0) for industry in target_industries])

        return np.array(state, dtype=np.float32), len(state)

    def _init_ppo_policy(self, state_dim: int, action_dim: int):
        """初始化或重建PPO策略"""

        class PPOPolicy(torch.nn.Module):
            def __init__(self, state_dim: int, action_dim: int):
                super().__init__()
                self.layers = torch.nn.Sequential(
                    torch.nn.Linear(state_dim, 128),
                    torch.nn.ReLU(),
                    torch.nn.Linear(128, 64),
                    torch.nn.ReLU(),
                    torch.nn.Linear(64, action_dim),
                    torch.nn.Tanh()
                )

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                return self.layers(x)

        self.policy = PPOPolicy(state_dim, action_dim).to(self.device)
        if os.path.exists("ppo_policy.pth"):
            try:
                self.policy.load_state_dict(torch.load("ppo_policy.pth", map_location=self.device))
            except Exception as e:
                print(f"加载PPO策略失败，使用随机初始化: {e}")
        self.policy.eval()

    def _apply_ppo_action(self, current_portfolio: Dict[str, float], action: np.ndarray,
                          sector_adjustments: Dict[str, float]) -> Dict[str, float]:
        """应用PPO动作并施加约束"""
        delta_w = action * 0.2  # 动作缩放
        new_weights = np.array(list(current_portfolio.values())) + delta_w

        # 行业适配性约束
        for i, symbol in enumerate(current_portfolio.keys()):
            industry = self.stocks_info.get(symbol, {}).get("industry_name", "未知")
            new_weights[i] *= sector_adjustments.get(industry, 0.7)

        # 基础约束
        new_weights = np.clip(new_weights, 0.0, 0.3)  # 单资产≤30%
        new_weights /= max(new_weights.sum(), 1e-8)  # 归一化

        return {symbol: float(w) for symbol, w in zip(current_portfolio.keys(), new_weights)}

    def calculate_ppo_reward(self, old_weights: np.ndarray, new_weights: np.ndarray, portfolio_values: np.ndarray,
                             market_trend: str) -> float:
        """计算PPO奖励"""
        if len(portfolio_values) < 2:
            return 0.0

        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        if len(returns) == 0:
            return 0.0

        sharpe = returns.mean() / max(returns.std(), 1e-6) * np.sqrt(252)
        turnover = np.sum(np.abs(new_weights - old_weights))

        trend_reward = 20 if (market_trend == "上涨" and returns.mean() > 0) else \
            15 if (market_trend == "下跌" and returns.mean() < 0) else 0

        return sharpe * 100 - turnover * 50 + trend_reward

    def _simulate_portfolio_returns(self, portfolio: Dict[str, float],
                                    histories: Dict[str, pd.DataFrame]) -> np.ndarray:
        """模拟投资组合收益"""
        if not histories or all(df.empty for df in histories.values()):
            return np.array([1.0])

        # 找出共同日期
        common_dates = None
        for symbol, df in histories.items():
            if not df.empty and '日期' in df.columns:
                dates = set(df['日期'])
                common_dates = dates if common_dates is None else common_dates.intersection(dates)

        if not common_dates or len(common_dates) == 0:
            return np.array([1.0])

        sorted_dates = sorted(common_dates)

        # 模拟收益
        portfolio_values = np.zeros(len(sorted_dates) + 1)
        portfolio_values[0] = 1.0

        for i, date in enumerate(sorted_dates):
            daily_return = 0.0

            for symbol, weight in portfolio.items():
                if symbol in histories and not histories[symbol].empty:
                    stock_df = histories[symbol]
                    stock_data = stock_df[stock_df['日期'] == date]

                    if not stock_data.empty and '收盘' in stock_df.columns:
                        if i == 0:
                            prev_close = stock_df.iloc[0]['收盘']
                        else:
                            prev_data = stock_df[stock_df['日期'] == sorted_dates[i - 1]]
                            prev_close = prev_data.iloc[0]['收盘'] if not prev_data.empty else stock_df.iloc[0]['收盘']

                        current_close = stock_data.iloc[0]['收盘']

                        if prev_close > 0:
                            stock_return = (current_close / prev_close) - 1
                            daily_return += weight * stock_return

            portfolio_values[i + 1] = portfolio_values[i] * (1 + daily_return)

        return portfolio_values

    def get_sector_adjustment(self, risk_preference: str, market_sentiment: Dict[str, Any], investment_horizon: str) -> \
            Dict[str, float]:
        """获取行业适配性调整系数"""
        trend = market_sentiment.get("market_trend", {}).get("trend", "震荡")

        # 行业基准适配性
        base_adjustments = {
            "银行": 0.8, "必需消费": 0.9, "医药": 0.9,
            "公用事业": 0.7, "白酒": 1.0, "科技": 1.2, "新能源": 1.1
        }

        # 根据风险偏好调整
        if risk_preference == "保守":
            for sector in ["科技", "新能源"]:
                base_adjustments[sector] *= 0.8
            for sector in ["银行", "必需消费"]:
                base_adjustments[sector] *= 1.2
        elif risk_preference == "激进":
            for sector in ["科技", "新能源"]:
                base_adjustments[sector] *= 1.2
            for sector in ["银行", "公用事业"]:
                base_adjustments[sector] *= 0.8

        # 根据市场趋势调整
        if trend == "上涨":
            for sector in ["科技", "新能源", "白酒"]:
                base_adjustments[sector] *= 1.1
            for sector in ["银行", "公用事业"]:
                base_adjustments[sector] *= 0.9
        elif trend == "下跌":
            for sector in ["必需消费", "医药", "银行"]:
                base_adjustments[sector] *= 1.1
            for sector in ["科技", "新能源"]:
                base_adjustments[sector] *= 0.9

        return base_adjustments

    def _build_dynamic_request(self, adjusted_portfolio: Dict[str, float], reward: float, risk_preference: str,
                               investment_horizon: str, market_trend: str) -> str:
        """构建LLM分析请求"""
        return f"""
请分析以下PPO调整后的投资组合：
{json.dumps(adjusted_portfolio, indent=2, ensure_ascii=False)}

关键信息：
- 风险偏好：{risk_preference}
- 投资期限：{investment_horizon}
- 市场趋势：{market_trend}
- PPO奖励值：{reward:.2f}（越高表示组合越优）

分析要求：
1. 行业配置是否符合适配性规则？（附调整系数对比）
2. 个股调整幅度是否在合理范围内？（单资产≤30%）
3. 组合风险指标变化（波动率、夏普比率）
4. 给出再平衡操作的具体建议

输出格式：
1. 行业配置分析表格
2. 风险指标对比列表
3. 操作建议段落
"""

    def _initiate_llm_analysis(self, request, current_portfolio) -> str:
        try:
            # 重置聊天历史
            self.reset()
            self.user.initiate_chat(
                self.portfolio_manager,
                message=request,
                max_turns=1  # 限制对话最多进行1轮
            )

            # 从对话历史中获取分析结果
            analysis_result = extract_analysis_result_from_conversation(self.user, self.portfolio_manager)
            return analysis_result
        except Exception as e:
            return f"LLM分析过程出错: {str(e)}"

    def reset(self):
        """
        重置聊天历史
        """
        self.user.reset()
        self.portfolio_manager.reset()

