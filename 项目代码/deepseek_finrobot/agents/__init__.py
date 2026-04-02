"""
代理模块 - 提供各种专业金融代理
"""

from .my_agents import *
from .workflow import SingleAssistant, SingleAssistantShadow, MultiAgentWorkflow

__all__ = [
    'FundamentalAnalysisAgent',
    'PublicAnalysisAgent',
    'RiskAnalysisAgent',
    'ExpectAdjustmentAgent',
    'SingleAssistant',
    'SingleAssistantShadow',
    'MultiAgentWorkflow'
] 