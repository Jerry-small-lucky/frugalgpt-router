# -*- coding: utf-8 -*-
"""
frugalgpt-router · 社区版 OpenAI 兼容 API
==========================================
仅标准库实现的最小服务：

  POST /v1/chat/completions   路由 + 生成（OpenAI 兼容请求/响应）
  GET  /v1/models             模型池与路由配置
  GET  /healthz               健康检查

运行：
  python -m frugalgpt.api --port 8090            # mock 模式（模拟三档回复，零费用）
  python -m frugalgpt.api --port 8090 --mode real   # 开发验证模式（接单一厂商，需 DEEPSEEK_API_KEY）

社区版边界：不含多厂商池、计费报表、可观测面板、可审计证据链等商业能力；
生产接入与完整能力见 Pro / Enterprise（商业版）。
Q11-05 定位：绑定 127.0.0.1、无鉴权、无速率限制——仅演示/本地开发定位，
生产须上 Pro 版（文档已声明；社区版勿直接暴露公网）。
"""
import argparse, json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .engine import MODELS, route_rule, SENSITIVE_WORDS

# 开发验证模式（真实厂商，演示用；生产接入属商业版）
_BASE_URL = 'https://api.deepseek.com/chat/completions'
_PRICE = {
    'deepseek-flash':  {'in': 0.15e-6, 'out': 0.6e-6},
    'deepseek-v4-pro': {'in': 0.66e-6, 'out': 1.98e-6},
}
_TIER_MODEL = [('deepseek-flash', False), ('deepseek-flash', True), ('deepseek-v4-pro', True)]

MODE = 'mock'
_SAFE_HITS = {'n': 0}   # 敏感命中计数（内存统计，不落盘审计——可审计证据链属商业版）


def _call_real(tier_idx, user_msg, max_tokens=1024):
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return {'content': '[real 模式缺少 DEEPSEEK_API_KEY，退回 mock]', 'cost': 0.0,
                'in_tokens': 0, 'out_tokens': 0}
    model, thinking = _TIER_MODEL[tier_idx]
    body = {'model': model,
            'messages': [{'role': 'user', 'content': user_msg}],
            'max_tokens': max_tokens, 'stream': False,
            'thinking': {'type': 'enabled' if thinking else 'disabled'}}
    import urllib.request
    # Q11-06：单次 90s 超时在 ThreadingHTTPServer 下会占住线程；加入 1 次快速重试
    # （临时网络抖动场景），仍失败则抛出由上层按 500 处理——避免静默丢请求。
    last = None
    for attempt in range(2):
        req = urllib.request.Request(_BASE_URL, data=json.dumps(body).encode('utf-8'), headers={
            'Authorization': 'Bearer %s' % api_key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.loads(resp.read().decode('utf-8'))
            break
        except Exception as e:  # noqa: BLE001
            last = e
    else:
        raise last
    msg = d['choices'][0]['message']
    u = d['usage']
    cost = (u.get('prompt_cache_miss_tokens', u['prompt_tokens']) * _PRICE[model]['in']
            + u.get('prompt_cache_hit_tokens', 0) * 0.003e-6
            + u['completion_tokens'] * _PRICE[model]['out'])
    return {'content': msg.get('content', ''), 'cost': cost,
            'in_tokens': u['prompt_tokens'], 'out_tokens': u['completion_tokens']}


def route_and_generate(user_msg):
    """规则分档 → 生成。敏感请求强制旗舰（安全优先于成本）。"""
    t0 = time.perf_counter()
    tier_idx, reason = route_rule(user_msg)
    if tier_idx == 2 and reason == 'safe':
        _SAFE_HITS['n'] += 1
    if MODE == 'real':
        res = _call_real(tier_idx, user_msg)
        content, cost = res['content'], res['cost']
        in_tokens, out_tokens = res['in_tokens'], res['out_tokens']
    else:
        # Q11-07 口径说明：mock 模式 token 用 len//4 字符估算，对中文严重失真
        # （中文字符 ≈1-2 token 而非 0.25）；此处成本数字仅作演示示意，
        # 非计费口径（计费见 Pro/Enterprise 审计证据链）
        n_in = max(1, len(user_msg) // 4)
        out_tokens = max(8, n_in // 3) * (1 + tier_idx)
        in_tokens = n_in
        cost = (in_tokens * MODELS[tier_idx]['cin'] / 1e6
                + out_tokens * MODELS[tier_idx]['cout'] / 1e6)
        styles = {0: '[Light] 简洁回答：', 1: '[Medium] 逐步回答：', 2: '[Heavy] 深度回答：'}
        content = styles[tier_idx] + user_msg[:60] + '（档位 %s，模拟生成）' % MODELS[tier_idx]['name']
    decision_us = round((time.perf_counter() - t0) * 1e6, 1)
    return {'tier': MODELS[tier_idx]['name'], 'reason': reason, 'content': content,
            'cost': cost, 'in_tokens': in_tokens, 'out_tokens': out_tokens,
            'decision_us': decision_us}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj, headers=None):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        for k, val in (headers or {}).items():
            self.send_header(k, val)
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        n = int(self.headers.get('Content-Length', 0))
        if n <= 0:
            return {}
        return json.loads(self.rfile.read(n).decode('utf-8'))

    def do_GET(self):
        if self.path.startswith('/v1/models'):
            self._send(200, {'object': 'list', 'data': [
                {'id': 'frugalgpt-router', 'object': 'model', 'owned_by': 'frugalgpt',
                 'permission': [], 'routing': 'rule',
                 'tiers': [m['name'] for m in MODELS]}]})
        elif self.path.startswith('/healthz'):
            self._send(200, {'status': 'ok', 'mode': MODE,
                             'edition': 'community',
                             'tiers': [m['name'] for m in MODELS],
                             'safe_hits': _SAFE_HITS['n']})
        else:
            self._send(404, {'error': 'not found'})

    def do_POST(self):
        if not self.path.startswith('/v1/chat/completions'):
            self._send(404, {'error': 'not found'}); return
        try:
            req = self._read_body()
        except Exception:
            self._send(400, {'error': 'invalid json'}); return
        messages = req.get('messages', [])
        user_msg = next((m.get('content', '') for m in messages if m.get('role') == 'user'), '')
        if not user_msg:
            self._send(400, {'error': 'missing user message'}); return
        r = route_and_generate(user_msg)
        resp = {'id': 'chatcmpl-%d' % int(time.time() * 1000), 'object': 'chat.completion',
                'created': int(time.time()), 'model': req.get('model', 'frugalgpt-router'),
                'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': r['content']},
                             'finish_reason': 'stop'}],
                'usage': {'prompt_tokens': r['in_tokens'],
                          'completion_tokens': r['out_tokens'],
                          'total_tokens': r['in_tokens'] + r['out_tokens']}}
        self._send(200, resp, headers={
            'X-Router-Tier': r['tier'], 'X-Router-Reason': r['reason'],
            'X-Router-Cost-USD': '%.6f' % r['cost'],
            'X-Router-Decision-Us': str(r['decision_us'])})


def main():
    global MODE
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8090)
    ap.add_argument('--mode', default='mock', choices=['mock', 'real'])
    args = ap.parse_args()
    MODE = args.mode
    if MODE == 'real' and not os.environ.get('DEEPSEEK_API_KEY'):
        print('[api] 警告：real 模式未设置 DEEPSEEK_API_KEY，将退回 mock 生成', flush=True)
    srv = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print('[api] 社区版 OpenAI 兼容服务已启动：http://127.0.0.1:%d  mode=%s' % (args.port, MODE), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n[api] 已停止', flush=True)


if __name__ == '__main__':
    main()
