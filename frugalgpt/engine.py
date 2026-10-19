# -*- coding: utf-8 -*-
"""
frugalgpt-router · 社区版引擎（Community Edition）
====================================================
最基础的规则路由实现，仅依赖标准库（Q11-02 文档校正：无 numpy 依赖）：

  · 三档模型池（Light / Medium / Heavy）与公开成本常量
  · 规则启发式分档：按请求长度 + 关键词 + 任务类型
  · 敏感主题强制旗舰（安全优先于成本，仅内存计数）

本仓库为社区演示实现，不含商业版能力：
学习式评分器、语义 ANN 路由、漂移监控闭环、评测成本分层、
可审计证据链、多厂商池与计费/观测面板均属 Pro / Enterprise（商业版）。

运行：
  python -m frugalgpt.engine --mode demo
"""
import argparse

MODELS = [
    {'name': 'Light',  'cin': 0.15, 'cout': 0.55},   # 轻量档：简单问答/FAQ
    {'name': 'Medium', 'cin': 0.60, 'cout': 0.72},   # 中档：总结/翻译/常规生成
    {'name': 'Heavy',  'cin': 2.50, 'cout': 0.86},   # 旗舰档：复杂推理/高风险
]
COSTS = [m['cin'] + m['cout'] for m in MODELS]

# 敏感主题（命中任一 → 强制旗舰，安全优先）
SENSITIVE_WORDS = ['危险', '违法', '医疗', '金融', '合规', '隐私', '武器', '药物']

# 中档触发词：常规处理类任务
_MEDIUM_WORDS = ['总结', '翻译', '分析', '改写', '摘要', '代码', '解释', '对比', '列出', '生成', '写']
# 旗舰触发词：深度推理/高风险任务
# Q11-03/Q11-04 口径说明：
# - 120/40 字符阈值为经验硬编码（社区版无配置注入口）；按字符数计，
#   对英文长 prompt 会系统性低估长度——如需要可 fork 后在 _HEAVY_WORDS/阈值处改。
# - 词表含「方案」「诊断」等宽泛词，存在误触发概率（无阈值兜底）；
#   社区版定位为演示，生产语义判断请使用 Pro 版。
_HEAVY_WORDS = ['推理', '数学', '证明', '合同', '法律', '计算', '论文', '复杂', '方案', '诊断']


def route_rule(text):
    """纯规则分档：敏感 → Heavy；旗舰词 → Heavy；中档词 → Medium；短文本 → Light。"""
    if any(w in text for w in SENSITIVE_WORDS):
        return 2, 'safe'
    if any(w in text for w in _HEAVY_WORDS):
        return 2, 'keyword-heavy'
    if len(text) > 120:
        return 2, 'long'
    if any(w in text for w in _MEDIUM_WORDS) or len(text) > 40:
        return 1, 'keyword-medium'
    return 0, 'short'


def demo():
    """命令行演示：对若干示例请求输出分档结果。"""
    samples = [
        '你好',
        '请帮我总结一下这份文档的要点',
        '把这段中文翻译成英文',
        '请证明勾股定理',
        '这个药物有什么副作用？',
        '写一封生日祝福邮件',
    ]
    print('frugalgpt-router 社区版 · 规则路由演示\n')
    print('%-28s %-8s %s' % ('请求', '档位', '原因'))
    for s in samples:
        tier, reason = route_rule(s)
        print('%-28s %-8s %s' % (s[:26], MODELS[tier]['name'], reason))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='demo', choices=['demo'])
    args = ap.parse_args()
    if args.mode == 'demo':
        demo()


if __name__ == '__main__':
    main()
