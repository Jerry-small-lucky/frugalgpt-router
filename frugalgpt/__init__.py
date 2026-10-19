# -*- coding: utf-8 -*-
"""
frugalgpt — FrugalGPT 范式的多档 LLM 路由引擎 · 社区版

能力入口：
  from frugalgpt.engine import MODELS, COSTS, SENSITIVE_WORDS, route_rule
  from frugalgpt.api import route_and_generate

社区版边界：规则路由为最基础能力；学习式评分器、语义 ANN 路由、
漂移监控闭环、评测成本分层、可审计证据链、多厂商池与计费/观测面板
均属 Pro / Enterprise（商业版），不在本仓库发布。
"""
__version__ = '0.2.1'

# Q11-01：显式再导出最常用入口（兼容 `from frugalgpt import route_rule`），
# 不改变原有子模块路径引用
from .engine import MODELS, COSTS, SENSITIVE_WORDS, route_rule  # noqa: E402,F401
from .api import route_and_generate  # noqa: E402,F401

__all__ = ['MODELS', 'COSTS', 'SENSITIVE_WORDS', 'route_rule', 'route_and_generate']
