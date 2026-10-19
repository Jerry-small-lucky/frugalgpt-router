# -*- coding: utf-8 -*-
"""frugalgpt-router 社区版 · 快速开始示例（离线可跑，无需 API key）。

覆盖：
1. route_rule(text) -> (tier_idx, reason)：纯规则分档
2. route_and_generate(text) -> dict：分档 + 生成（mock 模式，零费用）
3. HTTP API 启动与调用（注释内给出 curl 示例）

运行：python examples/quickstart.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frugalgpt.engine import MODELS, COSTS, SENSITIVE_WORDS, route_rule
from frugalgpt.api import route_and_generate


def main():
    # ---- 1. 规则分档：返回 (档位索引, 原因) ----
    samples = [
        '你好',                                  # 短文本 -> Light
        '请帮我总结一下这份文档的要点',            # 触发「总结」-> Medium
        '把这段中文翻译成英文',                  # 触发「翻译」-> Medium
        '请证明勾股定理',                        # 触发「证明/数学」-> Heavy
        '这个药物有什么副作用？',                # 命中敏感词「药物」-> Heavy（安全优先）
        '写一封生日祝福邮件',                    # 触发「写」-> Medium
    ]

    print('===== 1. 规则分档 =====')
    print('%-26s %-8s %-16s' % ('请求', '档位', '原因'))
    for s in samples:
        tier_idx, reason = route_rule(s)
        print('%-26s %-8s %-16s' % (s[:24], MODELS[tier_idx]['name'], reason))

    # 档位索引含义：0=Light, 1=Medium, 2=Heavy
    print('\n档位索引: 0=Light 1=Medium 2=Heavy')
    print('模型池（$ per 1M tokens, in/out）:',
          ', '.join('%s %.2f/%.2f' % (m['name'], m['cin'], m['cout']) for m in MODELS))
    print('档位合计成本: %s' % ['%.2f' % c for c in COSTS])

    # ---- 2. 分档 + 生成（mock 模式，零费用） ----
    print('\n===== 2. 路由 + 生成（mock）=====')
    r = route_and_generate('请帮我总结一下这份文档的要点')
    for k, v in r.items():
        print('  %-12s %s' % (k, v))

    # 返回字段说明：
    #   tier         档位名（Light/Medium/Heavy）
    #   reason       分档原因（short/keyword-medium/keyword-heavy/long/safe）
    #   content      生成内容（mock 为模拟文本；real 模式为模型输出）
    #   cost         估算成本（USD；mock 为演示口径，非计费）
    #   in/out_tokens 输入/输出 token 数
    #   decision_us  路由决策耗时（微秒）

    # ---- 3. HTTP API（OpenAI 兼容） ----
    print('\n===== 3. HTTP API =====')
    print('启动:  python -m frugalgpt.api --port 8090          （mock，零费用）')
    print('       python -m frugalgpt.api --port 8090 --mode real  （需 DEEPSEEK_API_KEY）')
    print('调用:')
    print('  curl -X POST http://127.0.0.1:8090/v1/chat/completions \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"model":"frugalgpt-router","messages":[{"role":"user","content":"请帮我总结一下这份文档"}]}\'')
    print('路由决策通过响应头返回: X-Router-Tier / X-Router-Reason / X-Router-Cost-USD / X-Router-Decision-Us')


if __name__ == '__main__':
    main()
