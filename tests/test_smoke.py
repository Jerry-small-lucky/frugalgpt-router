# -*- coding: utf-8 -*-
"""社区版冒烟测试：规则路由 / 安全优先 / API 管线（约 5 秒）。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frugalgpt.engine import MODELS, route_rule
from frugalgpt.api import route_and_generate


def test_rule_basic():
    # 短文本 → Light
    t, r = route_rule('你好')
    assert t == 0 and r == 'short', (t, r)
    # 中档词 → Medium
    t, r = route_rule('请帮我总结一下这份文档的要点')
    assert t == 1 and r == 'keyword-medium', (t, r)
    # 旗舰词 → Heavy
    t, r = route_rule('请证明勾股定理')
    assert t == 2 and r == 'keyword-heavy', (t, r)
    print('[ok] rule: short/medium/heavy 分档正确')


def test_safety_first():
    t, r = route_rule('这个药物有什么副作用？')
    assert t == 2 and r == 'safe', (t, r)          # 敏感词 → 强制旗舰
    t, r = route_rule('说一下金融风险提示')
    assert t == 2 and r == 'safe', (t, r)
    print('[ok] safety: 敏感主题强制旗舰（安全优先于成本）')


def test_api_pipeline():
    r = route_and_generate('把这段中文翻译成英文')
    assert r['tier'] == 'Medium' and r['reason'] == 'keyword-medium'
    assert r['decision_us'] >= 0 and r['content']
    r2 = route_and_generate('这个药物有什么副作用？')
    assert r2['tier'] == 'Heavy' and r2['reason'] == 'safe'
    print('[ok] api: 管线分档 + 敏感兜底正确')


def test_rule_boundary():
    """Q11-08：边界用例——空串/超长串/纯数字/纯标点不崩溃且档位符合预期。"""
    # 空串 → Light（无关键词、长度 0）
    t, r = route_rule('')
    assert t == 0 and r == 'short', (t, r)
    # 纯标点 → Light
    t, r = route_rule('！！！？？？')
    assert t == 0, (t, r)
    # 纯数字（无关键词，短）→ Light
    t, r = route_rule('12345')
    assert t == 0 and r == 'short', (t, r)
    # 超长串（>120）→ Heavy
    t, r = route_rule('这是一段用于测试超长输入是否会触发 long 分支的文本内容。' * 20)
    assert t == 2 and r == 'long', (t, r)
    # 长度 >40 无中档词 → Medium（'甲'*45 = 45 字符，无关键词命中）
    t, r = route_rule('甲' * 45)
    assert t == 1 and r == 'keyword-medium', (t, r)
    print('[ok] rule: 空串/纯数字/超长/长度分档边界正确')


if __name__ == '__main__':
    test_rule_basic()
    test_safety_first()
    test_api_pipeline()
    test_rule_boundary()
    print('ALL COMMUNITY SMOKE TESTS PASSED')
