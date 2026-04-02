import asyncio
import json
import os
import logging
from datetime import datetime
import autogen
from dataclasses import dataclass
import logging
from typing import Dict, List, Optional, Union, Any
import re
from .data import AsyncDataCollector
from .my_agents import *
from ..utils import get_current_date, format_financial_number, get_llm_config_for_autogen

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StockAnalysisReport:
    """股票分析报告数据结构"""
    stock_code: str
    stock_name: str
    fundamental_analysis: str
    news_sentiment: str
    timestamp: datetime

@dataclass
class TradingDecision:
    """交易决策数据结构"""
    stock_code: str
    action: str  # BUY, SELL, HOLD
    weight: float  # 投资组合权重
    confidence: float  # 置信度 0-1
    reasoning: str
    target_price: float
    stop_loss: float



def load_llm_config() -> Dict[str, Any]:
    """加载LLM配置"""
    return {
        "config_list": [
            {
                "model": "deepseek-chat",
                "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
                "base_url": "https://api.deepseek.com/v1",
            }
        ],
        "temperature": 0.7,
        "seed": 42,
    }

def export_analysis_to_markdown(content: str, symbol: str, output_dir: str,
                                filename: str = None, include_timestamp: bool = True) -> str:
    """
    导出分析结果到Markdown文件

    Args:
        content: 要导出的分析内容
        symbol: 股票代码
        output_dir: 输出目录
        filename: 文件名，如果为None则自动生成
        include_timestamp: 是否在文件名中包含时间戳

    Returns:
        导出文件的完整路径，如果失败则返回错误信息
    """
    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
            filename = f"{symbol}_{timestamp}.md" if timestamp else f"{symbol}.md"

        # 确保文件名有正确的扩展名
        if not filename.endswith('.md'):
            filename += '.md'

        full_path = os.path.join(output_dir, filename)

        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        abs_path = os.path.abspath(full_path)
        print(f"分析结果已导出至：{abs_path}")
        return abs_path

    except Exception as e:
        error_msg = f"导出失败：{str(e)}"
        print(error_msg)
        return error_msg


def export_analysis_to_json(content: str, output_dir: str,
                            filename: str = None,
                            include_timestamp: bool = True) -> str:
    """
    导出决策JSON内容到文件（借鉴解析函数的健壮性）

    Args:
        content: 包含JSON的原始文本
        output_dir: 输出目录路径
        filename: 自定义文件名
        include_timestamp: 是否在文件名添加时间戳

    Returns:
        导出文件绝对路径或错误信息
    """
    try:
        # 1. 从内容提取JSON字符串
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            return "❌ 未找到JSON内容"

        json_str = json_match.group()

        # 2. 解析JSON数据
        try:
            decision_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # 尝试修复常见问题
            try:
                # 移除JSON前后的干扰字符
                clean_str = json_str.strip().rstrip(';').rstrip(',')
                decision_data = json.loads(clean_str)
            except:
                logger.error(f"JSON解析失败: {e}")
                return f"❌ JSON解析失败: {str(e)}"

        # 3. 准备目录和文件名
        os.makedirs(output_dir, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
            filename = f"投资组合_{timestamp}.json"
        elif not filename.lower().endswith('.json'):
            filename += '.json'

        full_path = os.path.join(output_dir, filename)

        # 4. 写入格式化JSON
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(decision_data, f, indent=2, ensure_ascii=False)

        # 5. 返回完整路径
        abs_path = os.path.abspath(full_path)
        logger.info(f"导出成功: {abs_path}")
        return abs_path

    except Exception as e:
        logger.exception(f"导出失败")
        return f"❌ 系统错误: {str(e)}"
    

async def collect_stock_data(stock_list: List[str]) -> Dict[str, Dict[str, Any]]:
    """异步收集股票数据"""
    collector = AsyncDataCollector()
    try:
        await collector.initialize()
        logger.info(f"开始收集 {len(stock_list)} 只股票的数据...")
        return await collector.collect_data_for_stocks(stock_list)
    except Exception as e:
        logger.error(f"数据收集失败: {str(e)}")
        return {}
    finally:
        await collector.close()


def generate_analysis_reports(
        stock_data: Dict[str, Dict[str, Any]],
        llm_config: Dict[str, Any],
        log_callback=None
) -> List[StockAnalysisReport]:
    """生成股票分析报告"""
    reports = []
    fundamental_agent = FundamentalAnalysisAgent(llm_config)
    public_agent = PublicAnalysisAgent(llm_config)

    for symbol, data in stock_data.items():
        if "error" in data:
            logger.warning(f"股票 {symbol} 数据存在错误，跳过分析")
            continue

        try:
            # 基本面分析
            fundamental_analysis = fundamental_agent.analyze_fundamental(symbol, data)
            export_analysis_to_markdown(content=fundamental_analysis, symbol=symbol,
                                        output_dir=r'.\data\fudament_analysis')

            # 舆情分析
            news_sentiment = public_agent.analyze_public_sentiment(symbol, data)
            export_analysis_to_markdown(content=news_sentiment, symbol=symbol, output_dir=r'.\data\news_sentiment')

            # 创建分析报告
            report = StockAnalysisReport(
                stock_code=symbol,
                stock_name=data["basic_info"].get("company_name", symbol),
                fundamental_analysis=fundamental_analysis,
                news_sentiment=news_sentiment,
                timestamp=datetime.now()
            )
            reports.append(report)
            logger.info(f"股票 {symbol} 分析完成")
        except Exception as e:
            logger.error(f"股票 {symbol} 分析失败: {str(e)}")
            # 创建错误报告
            error_report = StockAnalysisReport(
                stock_code=symbol,
                stock_name=symbol,
                fundamental_analysis=f"分析失败: {str(e)}",
                news_sentiment=f"分析失败: {str(e)}",
                timestamp=datetime.now()
            )
            reports.append(error_report)

    return reports


def generate_risk_reports(
        stock_data: Dict[str, Dict[str, Any]],
        llm_config: Dict[str, Any],
        log_callback=None
) -> Dict[str, Dict[str, Any]]:
    """生成风险分析报告 - 确保始终返回字典"""
    risk_reports = {}
    risk_agent = RiskAnalysisAgent(llm_config)

    for symbol, data in stock_data.items():
        if "error" in data:
            risk_reports[symbol] = {"error": data["error"]}
            continue

        try:
            risk_report = risk_agent.analyze_risk(symbol, data, log_callback=log_callback)
            export_analysis_to_json(content=risk_report, output_dir=r'.\data\risk_reports', filename=symbol)

            # 确保风险报告是字典类型
            if isinstance(risk_report, dict):
                risk_reports[symbol] = risk_report
            else:
                # 如果返回的是字符串（错误消息），转换为字典格式
                risk_reports[symbol] = {"error": str(risk_report)}

            logger.info(f"股票 {symbol} 风险分析完成")
        except Exception as e:
            logger.error(f"股票 {symbol} 风险分析失败: {str(e)}")
            risk_reports[symbol] = {"error": str(e)}

    return risk_reports


class ManagerAgent:
    """
    增强的投资经理代理 - 支持初始决策和风险调整决策
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化投资经理代理

        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config

        # 创建用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False,
        )

        # 初始决策的系统提示词
        self.initial_system_message = """你是一位资深的投资经理，负责基于分析师团队的报告制定初步投资决策。

你需要综合考虑以下分析师的报告：
1. 市场预测分析师：市场走势和趋势预测
2. 财务分析师：公司财务状况和基本面分析
3. 新闻情绪分析师：市场情绪和舆论影响
4. 行业分析师：行业趋势和竞争格局
5. 技术分析师：技术指标和交易信号

你的职责是制定初步投资决策，包括：
1. 评估各分析师建议的一致性和分歧
2. 基于综合分析制定交易行动（BUY/SELL/HOLD）
3. 确定初步的投资组合权重分配
4. 设定初步的目标价位和止损位
5. 提供清晰的决策理由

请以JSON格式输出初步投资决策。"""

        # 风险调整的系统提示词
        self.risk_adjusted_system_message = """你是一位资深的投资经理，现在需要基于风险分析师的详细风险报告来优化你的初步投资决策。

你的职责是：
1. 仔细分析每只股票的风险等级和具体风险点
2. 根据风险评估调整投资行动（BUY/SELL/HOLD）
3. 基于风险水平重新分配投资组合权重
4. 调整目标价位和止损位以控制风险
5. 确保整体投资组合符合风险管理原则

风险调整原则：
- 高风险股票应降低权重或避免投资
- 中风险股票可适度投资但需设置严格止损
- 低风险股票可作为投资组合的稳定成分
- 整体投资组合应保持适当分散化
- 单一股票权重不应过度集中

请基于风险分析结果，对初步决策进行必要的调整，并以JSON格式输出最终优化的投资决策。"""

        # 创建投资经理代理（初始决策）
        self.initial_manager = autogen.AssistantAgent(
            name="InitialInvestmentManager",
            llm_config=self.llm_config,
            system_message=self.initial_system_message
        )

        # 创建投资经理代理（风险调整）
        self.risk_adjusted_manager = autogen.AssistantAgent(
            name="RiskAdjustedInvestmentManager",
            llm_config=self.llm_config,
            system_message=self.risk_adjusted_system_message
        )

        self.current_portfolio = {}
        self.risk_tolerance = 0.6

    def reset(self):
        """重置对话历史"""
        self.user_proxy.reset()
        self.initial_manager.reset()
        self.risk_adjusted_manager.reset()

    def make_initial_decision(self, analysis_reports: List[StockAnalysisReport], log_callback=None) -> List[TradingDecision]:
        """
        基于分析师报告制定初步投资决策

        Args:
            analysis_reports: 分析师报告列表

        Returns:
            初步投资决策列表
        """
        logger.info("投资经理制定初步投资决策")

        decision_request = f"""
请基于以下分析师团队的报告制定初步投资决策：

当前日期：{get_current_date()}
风险容忍度：{self.risk_tolerance}

=== 分析师报告汇总 ===
"""

        for report in analysis_reports:
            decision_request += f"""

股票代码: {report.stock_code} ({report.stock_name})
基本面分析: {report.fundamental_analysis}...
新闻情绪: {report.news_sentiment}...
分析时间: {report.timestamp}
"""

        decision_request += """

请综合所有分析师建议，制定初步投资决策。输出格式：
{
    "initial_decisions": [
        {
            "stock_code": "股票代码",
            "action": "BUY/SELL/HOLD",
            "weight": 权重(0-1),
            "confidence": 置信度(0-1),
            "reasoning": "决策理由",
            "target_price": 目标价,
            "stop_loss": 止损价
        }
    ],
    "portfolio_summary": {
        "total_stocks": 股票总数,
        "expected_return": "预期收益",
        "investment_strategy": "投资策略"
    }
}
"""

        # 重置并发起对话
        self.reset()

        self.log_callback = log_callback

        try:
            self.user_proxy.initiate_chat(
                self.initial_manager,
                message=decision_request,
                max_turns=1
            )

            content = extract_analysis_result_from_conversation(self.user_proxy, self.initial_manager)
            export_analysis_to_json(content=content, output_dir=r'.\data\initial_decisions')
            decisions = self._parse_decision_result(content)

            return decisions
        except Exception as e:
            logger.error(f"初步投资决策制定失败: {e}")
            return self._create_default_decisions(analysis_reports)

    def make_risk_adjusted_decision(self,
                                    initial_decisions: List[TradingDecision],
                                    risk_reports: Dict[str, Dict],
                                    risk_preference: str = "中等",
                                    investment_horizon: str = "长期",
                                    log_callback=None) -> List[TradingDecision]:
        """
        基于风险分析报告调整投资决策，并考虑用户的风险偏好和投资期限

        Args:
            initial_decisions: 初步投资决策
            risk_reports: 各股票的风险分析报告
            risk_preference: 用户风险偏好（保守/中等/激进）
            investment_horizon: 用户投资期限（短期/中期/长期）

        Returns:
            风险调整后的投资决策
        """
        logger.info(f"投资经理基于风险报告调整投资决策（风险偏好: {risk_preference}, 投资期限: {investment_horizon})")

        # 根据风险偏好和投资期限制定调整策略
        adjustment_strategy = self._get_adjustment_strategy(risk_preference, investment_horizon)

        adjustment_request = f"""
请基于风险分析报告对初步投资决策进行优化调整，并考虑以下用户偏好：
- 风险偏好: {risk_preference}
- 投资期限: {investment_horizon}

调整策略建议:
{adjustment_strategy}

=== 初步投资决策 ===
"""

        for decision in initial_decisions:
            adjustment_request += f"""
股票代码: {decision.stock_code}
初步行动: {decision.action}
初步权重: {decision.weight:.2%}
置信度: {decision.confidence}
初步理由: {decision.reasoning}
目标价: {decision.target_price}
止损价: {decision.stop_loss}

"""

        adjustment_request += "\n=== 风险分析报告 ===\n"

        for stock_code, risk_report in risk_reports.items():
            if "error" not in risk_report:
                adjustment_request += f"""
{stock_code} 风险分析:
- 风险等级: {risk_report.get('risk_level', '未知')}
- 风险评分: {risk_report.get('overall_risk_score', 'N/A')}/10
- 技术风险: {risk_report.get('technical_risks', {}).get('trend_risk', 'N/A')}
- 波动性风险: {risk_report.get('quantitative_risks', {}).get('volatility_risk', 'N/A')}
- 最大回撤: {risk_report.get('quantitative_risks', {}).get('max_drawdown', 0):.2%}
- 风险警告: {', '.join(risk_report.get('risk_warnings', []))}
- 管理建议: {', '.join(risk_report.get('risk_management_suggestions', []))}

"""
            else:
                adjustment_request += f"""
{stock_code} 风险分析: {risk_report.get('error', '分析失败')}

"""

        adjustment_request += f"""
请基于风险分析结果和用户偏好调整投资决策，考虑以下原则：
1. 高风险股票应降低权重或回避（尤其对于保守型投资者）
2. 中风险股票可适度投资但需严格止损
3. 低风险股票可增加配置（尤其对于长期投资者）
4. 整体投资组合风险要均衡分散
5. 根据风险调整目标价和止损价

特别考虑用户的风险偏好和投资期限：
- 风险偏好: {risk_preference}
- 投资期限: {investment_horizon}

{self._get_preference_guidelines(risk_preference, investment_horizon)}

输出格式：
{{
    "adjusted_decisions": [
        {{
            "stock_code": "股票代码",
            "action": "调整后行动",
            "weight": 调整后权重权重(0-1),
            "confidence": 调整后置信度(0-1),
            "reasoning": "调整理由（包含风险考虑和用户偏好）",
            "target_price": 调整后目标价,
            "stop_loss": 调整后止损价,
            "risk_adjustment": "具体风险调整说明"
        }}
    ],
    "risk_summary": {{
        "portfolio_risk_level": "整体组合风险等级",
        "risk_adjustments_made": "主要风险调整措施",
        "final_strategy": "最终投资策略"
    }}
}}
"""

        try:
            self.user_proxy.initiate_chat(
                self.risk_adjusted_manager,
                message=adjustment_request,
                max_turns=1
            )

            content = extract_analysis_result_from_conversation(self.user_proxy, self.risk_adjusted_manager)
            export_analysis_to_json(content=content, output_dir=r'.\data\adjusted_decisions')
            adjusted_decisions = self._parse_decision_result(content)

            return adjusted_decisions
        except Exception as e:
            logger.error(f"风险调整决策失败: {e}")
            return self._create_conservative_adjustments(
                initial_decisions,
                risk_reports,
                risk_preference,
                investment_horizon
            )

    def _get_adjustment_strategy(self, risk_preference: str, investment_horizon: str) -> str:
        """根据风险偏好和投资期限生成调整策略"""
        strategy = ""

        # 风险偏好策略
        if risk_preference == "保守":
            strategy += "保守型投资者策略:\n"
            strategy += "- 高风险股票权重减少40-60%\n"
            strategy += "- 中风险股票权重减少20-40%\n"
            strategy += "- 低风险股票权重增加10-20%\n"
            strategy += "- 整体组合波动率目标降低20-30%\n"
            strategy += "- 止损位设置更严格（比目标价更接近当前价）\n"
        elif risk_preference == "激进":
            strategy += "激进型投资者策略:\n"
            strategy += "- 高风险股票权重可增加20-40%\n"
            strategy += "- 中风险股票权重可增加10-20%\n"
            strategy += "- 低风险股票权重减少10-20%\n"
            strategy += "- 整体组合波动率目标提高30-50%\n"
            strategy += "- 止损位设置更宽松（比目标价更远离当前价）\n"
        else:  # 中等
            strategy += "中等风险偏好投资者策略:\n"
            strategy += "- 高风险股票权重减少20-30%\n"
            strategy += "- 中风险股票权重保持基本不变\n"
            strategy += "- 低风险股票权重增加10-15%\n"
            strategy += "- 整体组合波动率目标保持稳定\n"
            strategy += "- 止损位设置适中（介于保守和激进之间）\n"

        # 投资期限策略
        strategy += "\n投资期限策略:\n"
        if investment_horizon == "短期":
            strategy += "- 短期投资者（<1年）应关注技术面和市场情绪\n"
            strategy += "- 降低长期基本面因素权重\n"
            strategy += "- 止损位设置更严格以控制短期波动风险\n"
            strategy += "- 避免高波动性股票\n"
        elif investment_horizon == "中期":
            strategy += "- 中期投资者（1-3年）平衡技术和基本面因素\n"
            strategy += "- 适度配置高增长潜力股票\n"
            strategy += "- 止损位设置适中\n"
        else:  # 长期
            strategy += "- 长期投资者（>3年）应关注基本面和行业趋势\n"
            strategy += "- 可容忍短期波动，配置更多高增长潜力股票\n"
            strategy += "- 止损位设置更宽松以允许长期价值实现\n"
            strategy += "- 增加周期性行业和新兴技术行业的配置\n"

        return strategy

    def _get_preference_guidelines(self, risk_preference: str, investment_horizon: str) -> str:
        """生成用户偏好指导原则"""
        guidelines = f"### 用户偏好指导原则 ({risk_preference}风险, {investment_horizon}投资)\n"

        # 风险偏好指导
        if risk_preference == "保守":
            guidelines += "- 最大单只股票权重不超过5%\n"
            guidelines += "- 高风险股票总权重不超过10%\n"
            guidelines += "- 组合波动率目标低于市场平均水平20%\n"
            guidelines += "- 严格止损策略（亏损达5%即止损）\n"
        elif risk_preference == "激进":
            guidelines += "- 单只股票权重最高可达20%\n"
            guidelines += "- 高风险股票总权重可达40%\n"
            guidelines += "- 组合波动率目标可高于市场平均水平30%\n"
            guidelines += "- 宽松止损策略（亏损达15%才考虑止损）\n"
        else:  # 中等
            guidelines += "- 单只股票权重最高不超过10%\n"
            guidelines += "- 高风险股票总权重不超过25%\n"
            guidelines += "- 组合波动率目标与市场平均水平相当\n"
            guidelines += "- 适中止损策略（亏损达10%考虑止损）\n"

        # 投资期限指导
        if investment_horizon == "短期":
            guidelines += "\n短期投资指导:\n"
            guidelines += "- 优先选择技术面强劲的股票\n"
            guidelines += "- 关注即将发布的财报和事件驱动机会\n"
            guidelines += "- 避免长期基本面好但短期承压的股票\n"
            guidelines += "- 目标收益设定在15-30%范围内\n"
        elif investment_horizon == "中期":
            guidelines += "\n中期投资指导:\n"
            guidelines += "- 平衡技术面和基本面因素\n"
            guidelines += "- 关注行业周期和结构性变化\n"
            guidelines += "- 目标收益设定在30-50%范围内\n"
        else:  # 长期
            guidelines += "\n长期投资指导:\n"
            guidelines += "- 优先选择基本面强劲、有长期竞争优势的公司\n"
            guidelines += "- 关注行业领导者和创新者\n"
            guidelines += "- 容忍短期波动，关注长期价值\n"
            guidelines += "- 目标收益设定在50-100%范围内\n"

        return guidelines

    def _parse_decision_result(self, content) -> List[TradingDecision]:
        """解析投资决策结果"""
        try:

            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    decision_data = json.loads(json_match.group())

                    decisions = []
                    # 处理不同的JSON结构
                    decision_list = (decision_data.get("initial_decisions") or
                                     decision_data.get("adjusted_decisions") or
                                     decision_data.get("decisions", []))

                    for item in decision_list:
                        decision = TradingDecision(
                            stock_code=item.get("stock_code", ""),
                            action=item.get("action", "HOLD"),
                            weight=float(item.get("weight", 0)),
                            confidence=float(item.get("confidence", 0.5)),
                            reasoning=item.get("reasoning", ""),
                            target_price=float(item.get("target_price", 0)),
                            stop_loss=float(item.get("stop_loss", 0))
                        )
                        decisions.append(decision)

                    if decisions:
                        total_weight = sum(d.weight for d in decisions)
                        if total_weight == 0:
                            # 避免除零错误
                            normalized_decisions = [TradingDecision(
                                stock_code=d.stock_code,
                                action=d.action,
                                weight=1.0 / len(decisions),
                                confidence=d.confidence,
                                reasoning=d.reasoning + " (权重异常，均等分配)",
                                target_price=d.target_price,
                                stop_loss=d.stop_loss
                            ) for d in decisions]
                        else:
                            normalized_decisions = [TradingDecision(
                                stock_code=d.stock_code,
                                action=d.action,
                                weight=d.weight / total_weight,  # 归一化处理
                                confidence=d.confidence,
                                reasoning=d.reasoning,
                                target_price=d.target_price,
                                stop_loss=d.stop_loss
                            ) for d in decisions]
                        return normalized_decisions

                    return decisions
                except json.JSONDecodeError:
                    logger.error("JSON解析失败")

        except Exception as e:
            logger.error(f"解析投资决策失败: {e}")

        return []

    def _create_default_decisions(self, analysis_reports: List[StockAnalysisReport]) -> List[TradingDecision]:
        # 创建默认决策
        decisions = [TradingDecision(
            stock_code=report.stock_code,
            action="HOLD",
            weight=1.0 / len(analysis_reports),  # 确保权重总和为100%
            confidence=0.5,
            reasoning="分析师报告综合评估，采用中性策略",
            target_price=0.0,
            stop_loss=0.0
        ) for report in analysis_reports]

        # 添加归一化保障，防止浮点数误差
        total = sum(d.weight for d in decisions)
        if abs(total - 1.0) > 0.0001:  # 考虑浮点精度
            return [TradingDecision(
                stock_code=d.stock_code,
                action=d.action,
                weight=d.weight / total,
                confidence=d.confidence,
                reasoning=d.reasoning + " (权重归一化调整)",
                target_price=d.target_price,
                stop_loss=d.stop_loss
            ) for d in decisions]

        return decisions

    def _create_conservative_adjustments(self,
                                         initial_decisions: List[TradingDecision],
                                         risk_reports: Dict[str, Dict],
                                         risk_preference: str = "中等",
                                         investment_horizon: str = "长期") -> List[TradingDecision]:
        """创建保守的风险调整，考虑用户偏好"""
        adjusted_decisions = []

        for decision in initial_decisions:
            risk_report = risk_reports.get(decision.stock_code, {})

            # 根据风险偏好和投资期限确定调整因子
            if risk_preference == "保守":
                risk_factor = 0.7  # 保守型投资者更大幅度降低风险
                stop_loss_factor = 0.95  # 更严格的止损
            elif risk_preference == "激进":
                risk_factor = 1.2  # 激进型投资者可适度增加风险
                stop_loss_factor = 0.85  # 更宽松的止损
            else:  # 中等
                risk_factor = 1.0
                stop_loss_factor = 0.90

            # 根据投资期限调整
            if investment_horizon == "短期":
                risk_factor *= 0.8  # 短期投资更谨慎
            elif investment_horizon == "长期":
                risk_factor *= 1.1  # 长期投资可承担更多风险

            # 保守调整逻辑
            adjusted_weight = decision.weight
            adjusted_action = decision.action

            if "error" not in risk_report:
                risk_level = risk_report.get('risk_level', '中风险')

                if risk_level == "高风险":
                    adjusted_weight *= (0.5 * risk_factor)  # 根据风险偏好调整降低幅度
                    if decision.action == "BUY" and risk_preference != "激进":
                        adjusted_action = "HOLD"  # 高风险时将买入改为持有（激进投资者除外）
                elif risk_level == "低风险":
                    adjusted_weight *= (1.2 * risk_factor)  # 根据风险偏好调整增加幅度

            # 调整止损位
            if decision.stop_loss > 0:
                adjusted_stop_loss = decision.stop_loss * stop_loss_factor
            else:
                # 如果没有止损价，根据风险偏好设置默认止损
                if risk_preference == "保守":
                    adjusted_stop_loss = decision.target_price * 0.95
                elif risk_preference == "激进":
                    adjusted_stop_loss = decision.target_price * 0.80
                else:
                    adjusted_stop_loss = decision.target_price * 0.90

            adjusted_decision = TradingDecision(
                stock_code=decision.stock_code,
                action=adjusted_action,
                weight=min(adjusted_weight, self._get_max_weight(risk_preference)),  # 根据风险偏好设置最大权重
                confidence=decision.confidence * (0.9 if risk_preference == "保守" else 1.0),  # 保守投资者降低置信度
                reasoning=f"风险调整: {decision.reasoning} (偏好: {risk_preference}, 期限: {investment_horizon})",
                target_price=decision.target_price,
                stop_loss=adjusted_stop_loss
            )
            adjusted_decisions.append(adjusted_decision)

            total_weight = sum(d.weight for d in adjusted_decisions)
            if abs(total_weight - 1.0) > 0.0001:  # 考虑浮点精度
                normalized_decisions = [TradingDecision(
                    stock_code=d.stock_code,
                    action=d.action,
                    weight=d.weight / total_weight,
                    confidence=d.confidence,
                    reasoning=d.reasoning + " (权重归一化)",
                    target_price=d.target_price,
                    stop_loss=d.stop_loss
                ) for d in adjusted_decisions]
                return normalized_decisions

        return adjusted_decisions

    def _get_max_weight(self, risk_preference: str) -> float:
        """根据风险偏好获取最大单只股票权重"""
        if risk_preference == "保守":
            return 0.05  # 5%
        elif risk_preference == "激进":
            return 0.20  # 20%
        else:
            return 0.10  # 10%


def run_trading_cycle(
        stock_codes: List[str],
        risk_preference: str = "中等",
        investment_horizon: str = "长期",
        progress_callback=None,
        log_callback=None
) -> Dict[str, Any]:
    """运行完整的交易周期"""
    # 加载LLM配置
    llm_config = load_llm_config()

    # 1. 收集股票数据
    if progress_callback:
        progress_callback("分析师团队进行股票分析")
    stock_data = asyncio.run(collect_stock_data(stock_codes))
    if not stock_data:
        return {"success": False, "message": "股票数据收集失败"}

    # 2. 生成分析报告
    if progress_callback:
        progress_callback("投资经理制定初始投资建议")
    analysis_reports = []
    fundamental_files = []
    news_files = []
    for symbol, data in stock_data.items():
        if "error" in data:
            continue
        fundamental_analysis = FundamentalAnalysisAgent(llm_config).analyze_fundamental(symbol, data)
        f_path = export_analysis_to_markdown(content=fundamental_analysis, symbol=symbol, output_dir=r'.\data\fudament_analysis')
        fundamental_files.append(f_path)
        news_sentiment = PublicAnalysisAgent(llm_config).analyze_public_sentiment(symbol, data)
        n_path = export_analysis_to_markdown(content=news_sentiment, symbol=symbol, output_dir=r'.\data\news_sentiment')
        news_files.append(n_path)
        report = StockAnalysisReport(
            stock_code=symbol,
            stock_name=data["basic_info"].get("company_name", symbol),
            fundamental_analysis=fundamental_analysis,
            news_sentiment=news_sentiment,
            timestamp=datetime.now()
        )
        analysis_reports.append(report)
    if not analysis_reports:
        return {"success": False, "message": "分析报告生成失败"}

    # 3. 生成初始决策
    if progress_callback:
        progress_callback("风险分析师进行风险分析")
    manager = ManagerAgent(llm_config)
    initial_decisions = manager.make_initial_decision(analysis_reports, log_callback=log_callback)

    # 4. 生成风险报告
    if progress_callback:
        progress_callback("投资经理根据风险报告优化投资建议")
    risk_reports = generate_risk_reports(stock_data, llm_config, log_callback=log_callback)

    # 5. 生成最终决策（风险调整后）
    if progress_callback:
        progress_callback("生成投资组合预期调整方案")
    final_decisions = manager.make_risk_adjusted_decision(
        initial_decisions,
        risk_reports,
        risk_preference,
        investment_horizon,
        log_callback=log_callback
    )

    # 6. 生成预期调整方案
    adjustment_agent = ExpectAdjustmentAgent(llm_config)

    # 创建当前投资组合（基于最终决策）
    current_portfolio = {}
    for decision in final_decisions:
        if decision.action in ["BUY", "HOLD"]:
            current_portfolio[decision.stock_code] = decision.weight

    # 生成预期调整方案
    adjustment_suggestions = adjustment_agent.dynamic_portfolio_adjustment(
        current_portfolio=current_portfolio,
        collected_data=stock_data,
        risk_preference=risk_preference,
        investment_horizon=investment_horizon,
        log_callback=log_callback
    )

    ppo_path = export_analysis_to_markdown(adjustment_suggestions, '+'.join(stock_codes),'.\\data\\PPO')

    # 返回结果
    return {
        "success": True,
        "timestamp": datetime.now(),
        "analyzed_stocks": stock_codes,
        "analysis_reports": analysis_reports,
        "initial_decisions": initial_decisions,
        "risk_reports": risk_reports,
        "final_decisions": final_decisions,
        "adjustment_suggestions": adjustment_suggestions,
        "current_portfolio": current_portfolio,
        "download_files": {
            "fundamental": fundamental_files,
            "news": news_files,
            "ppo": ppo_path
        }
    }


def main():
    """主程序入口"""

    # 检查环境变量
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        print("示例: export DEEPSEEK_API_KEY='your_api_key_here'")
        return

    # 加载LLM配置
    llm_config = load_llm_config()

    # 验证配置
    api_key = llm_config["config_list"][0]["api_key"]
    if not api_key:
        print("错误: API密钥未设置，请检查环境变量 DEEPSEEK_API_KEY")
        return

    print(f"使用模型: {llm_config['config_list'][0]['model']}")
    print(f"API基础URL: {llm_config['config_list'][0]['base_url']}")


    while True:
        try:
            print("\n" + "=" * 60)
            print("多智能体量化交易系统")
            print("流程: 分析师报告 → 初始建议 → 风险分析 → 优化建议 → 预期调整方案")
            print("=" * 60)

            # 获取股票代码输入
            stock_input = input("请输入股票代码（用逗号分隔，如 000001,600519,002304），或输入 'quit' 退出: ").strip()

            if stock_input.lower() == 'quit':
                print("退出交易系统")
                break

            if not stock_input:
                print("请输入有效的股票代码")
                continue

            stock_codes = [code.strip() for code in stock_input.split(',') if code.strip()]

            if not stock_codes:
                print("请输入有效的股票代码")
                continue

            # 获取投资偏好
            print("\n请选择投资偏好:")
            print("1. 保守型")
            print("2. 中等型")
            print("3. 激进型")

            risk_choice = input("请输入选择（1-3，默认为2）: ").strip()
            risk_mapping = {"1": "保守", "2": "中等", "3": "激进"}
            risk_preference = risk_mapping.get(risk_choice, "中等")

            # 获取投资期限
            print("\n请选择投资期限:")
            print("1. 短期（1-3个月）")
            print("2. 中期（3-12个月）")
            print("3. 长期（1年以上）")

            horizon_choice = input("请输入选择（1-3，默认为3）: ").strip()
            horizon_mapping = {"1": "短期", "2": "中期", "3": "长期"}
            investment_horizon = horizon_mapping.get(horizon_choice, "长期")

            print(f"将分析以下股票: {stock_codes}")
            print(f"风险偏好: {risk_preference}")
            print(f"投资期限: {investment_horizon}")

            # 运行交易周期
            print("\n开始运行交易周期...")
            result =run_trading_cycle(
                stock_codes,
                risk_preference=risk_preference,
                investment_horizon=investment_horizon
            )

            # 显示结果
            if result["success"]:
                print(f"\n🎉 交易周期完成！")
            else:
                print(f"❌ 交易周期失败: {result['message']}")

        except KeyboardInterrupt:
            print("\n用户中断，退出交易系统")
            break
        except Exception as e:
            logger.error(f"运行时错误: {e}")
            print(f"发生错误: {e}")
            continue


if __name__ == "__main__":
    main()