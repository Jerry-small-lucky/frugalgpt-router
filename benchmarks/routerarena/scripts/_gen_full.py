# -*- coding: utf-8 -*-
"""
RouterArena 提交包：完整复现官方 prep_datasets.py 逻辑
======================================================
1. 用官方 40 个 eval_config 模板 + LCB release_v2（is_stdin）
   生成 router_data.json（full 8400）/ router_data_10.json（sub_10 809）
   / router_robustness.json（420）
2. 用产品三档规则 rule_decide 生成真实预测：
   - frugalgpt-router.json（full：8400 regular + 1618 optimality）
   - frugalgpt-router.json.sub10 副本（本地验证用 2427）
   - frugalgpt-router-robustness.json（420，无 optimality）
3. 官方语义自检（prompt 逐字、条数、模型∈config、global index 对齐）

Q11-17 已知冲突：官方数据集经 huggingface.co 联网下载，与提交包
「离线可复现」目标存在张力——本文件即该冲突的缓解（下载一次后本地
落盘 datasets/data，后续复现不联网）。
"""
import io, json, os, re
import pyarrow.parquet as pq

# Q11-28：PKG 由脚本位置相对推导（datasets/ 的上一级 = 提交包根），不再机器绑定
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(PKG, 'datasets', 'data')
REF = os.path.join(PKG, 'datasets', '_check_ref')
CFG_DIR = os.path.join(REF, 'eval_config')
LCB_HUB = os.path.join(REF, 'lcb_v2', 'hub', 'release_v2')
OUT = io.open(os.path.join(PKG, 'datasets', '_gen_full.log'), 'w', encoding='utf-8')
def log(*a):
    OUT.write(' '.join(str(x) for x in a) + '\n'); OUT.flush()

TIER_TO_ARENA = {
    'Light':   'gemini-2.0-flash-001',
    'Medium':  'gpt-4o-mini',
    'Heavy':   'gpt-4o',
}
MODELS = list(TIER_TO_ARENA.values())

def rule_decide(text):
    """V2 优化档阈值（与 config/frugalgpt-router-v2.json 配套）：
    Light ≤250 字符 且 ≤10 数字；Medium 251–700 字符 或 11–35 数字；Heavy >700 或 >35。
    V0 正式档（Medium=claude-3-haiku、阈值 450/25）见合规声明_Compliance.md 对照表。"""
    n_digit = len(re.findall(r'\d', text or ''))
    n_chars = len(text or '')
    if n_chars > 700 or n_digit > 35:
        return 'Heavy'
    if n_chars > 250 or n_digit > 10:
        return 'Medium'
    return 'Light'

# ---------- 1) LCB maps ----------
def escape_format_braces(text):
    return text.replace('{', '{{').replace('}', '}}')

def safe_format_prompt(template, **kwargs):
    esc = {k: (escape_format_braces(v) if isinstance(v, str) else v) for k, v in kwargs.items()}
    return template.format(**esc)

index_map, prefix_map = {}, {}
total = 0
for i in range(4):
    tab = pq.read_table(os.path.join(LCB_HUB, 'test-%05d-of-00004.parquet' % i),
                        columns=['question_content', 'public_test_cases'])
    rows = tab.to_pylist()
    for j, r in enumerate(rows):
        idx = str(total + j)
        content = r.get('question_content') or ''
        try:
            tests = json.loads(r.get('public_test_cases') or '[]')
        except Exception:
            tests = []
        is_stdin = any((t or {}).get('testtype') == 'stdin' for t in tests)
        index_map[idx] = is_stdin
        if content:
            prefix_map.setdefault(content[:120], is_stdin)
    total += len(rows)
log('LCB rows=%d' % total)

# ---------- 2) configs ----------
cfg_names = [os.path.splitext(f)[0] for f in os.listdir(CFG_DIR) if f.endswith('.json')]
configs = {}
for n in cfg_names:
    with open(os.path.join(CFG_DIR, n + '.json'), encoding='utf-8') as f:
        configs[n] = json.load(f).get('eval_params', {})
log('eval_configs=%d' % len(configs))

# ---------- 3) prompt_formatted 复刻 ----------
def build_formatted(path):
    tab = pq.read_table(path)
    rows = tab.to_pylist()
    out = []
    for row in rows:
        gidx = row.get('Global Index') or row.get('global_index') or row.get('global index')
        dname = row.get('Dataset name')
        if not dname:
            parts = str(gidx).split('_')
            if parts[0] == 'Ethics' and len(parts) >= 2:
                dname = parts[0] + '_' + parts[1]
            elif parts[0] == 'ChessInstruct' and len(parts) >= 2:
                dname = parts[0] + '_' + parts[1]
            else:
                dname = parts[0]
        options_list = row.get('Options') or []
        has_options = len(options_list) > 0
        if 'Ethics' in str(dname):
            base = str(dname)
        elif 'ChessInstruct' in str(dname):
            base = 'ChessInstruct_mcq' if has_options else 'ChessInstruct'
        else:
            base = str(dname).split('_', 1)[0]
        eval_params = configs.get(base, {})
        options_str = ''
        if options_list:
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            options_str = ''.join('%s. %s\n' % (letters[i] if i < len(letters) else '-', o)
                                  for i, o in enumerate(options_list))
        question = row.get('Question', '') or ''
        context_val = row.get('Context', '') or ''
        context_for_prompt = context_val if context_val != '' else 'None'
        if base == 'LiveCodeBench':
            idx = str(gidx).split('_')[-1]
            is_stdin = index_map.get(idx, prefix_map.get(question[:120]))
            if is_stdin is None:
                raise AssertionError('LCB row not found: %s' % gidx)
            prompt_formatted = safe_format_prompt(
                eval_params.get('is_stdin_prompt') if is_stdin else eval_params.get('not_is_stdin_prompt', '{Question}'),
                Question=question)
        elif base == 'SuperGLUE-RC':
            prompt_formatted = safe_format_prompt(
                eval_params.get('prompt', '{Question}'), Question=question, Answer='')
        elif base == 'SuperGLUE-Wic':
            prompt_formatted = safe_format_prompt(
                eval_params.get('prompt', '{Question}'), Question=question, Context=context_val)
        elif not has_options:
            prompt_formatted = safe_format_prompt(
                eval_params.get('prompt', '{Question}'), Context=context_for_prompt, Question=question)
        else:
            prompt_formatted = safe_format_prompt(
                eval_params.get('prompt', '{Question}'), Context=context_for_prompt,
                Question=question, Options=options_str)
        if len(prompt_formatted) > 10000:
            prompt_formatted = prompt_formatted[:5000] + '...' + prompt_formatted[-5000:]
        if not prompt_formatted:
            raise AssertionError('empty prompt for %s' % gidx)
        out.append({'prompt_formatted': prompt_formatted, 'global index': gidx})
    return out

ds_full = build_formatted(os.path.join(DATA, 'full-00000-of-00001.parquet'))
ds_sub = build_formatted(os.path.join(DATA, 'sub_10-00000-of-00001.parquet'))
# robustness: prompt = Question 原样
tab = pq.read_table(os.path.join(DATA, 'robustness-00000-of-00001.parquet'))
ds_rob = [{'prompt_formatted': (r.get('Question') or ''), 'global index': r.get('Global Index')}
          for r in tab.to_pylist()]
log('datasets: full=%d sub=%d rob=%d' % (len(ds_full), len(ds_sub), len(ds_rob)))

# 写 dataset JSON（供校验用，镜像官方 ./dataset 位置）
ds_dir = os.path.join(PKG, 'datasets', 'router_data')
os.makedirs(ds_dir, exist_ok=True)
json.dump(ds_full, open(os.path.join(ds_dir, 'router_data.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(ds_sub, open(os.path.join(ds_dir, 'router_data_10.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(ds_rob, open(os.path.join(ds_dir, 'router_robustness.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- 4) 生成 predictions（官方 generate_prediction_file 语义） ----------
def gen_predictions(dataset, split, with_optimality=True):
    preds = []
    sub10_indices = {e['global index'] for e in ds_sub}
    sub_selected = {}
    for entry in dataset:
        gi = entry['global index']
        prompt = entry['prompt_formatted']
        model = TIER_TO_ARENA[rule_decide(prompt)]
        preds.append({'global index': gi, 'prompt': prompt, 'prediction': model,
                      'generated_result': None, 'cost': None, 'accuracy': None,
                      'for_optimality': False})
        if with_optimality and gi in sub10_indices:
            sub_selected[gi] = (model, prompt)
    if with_optimality:
        for gi, (sel, prompt) in sub_selected.items():
            for other in [m for m in MODELS if m != sel]:
                preds.append({'global index': gi, 'prompt': prompt, 'prediction': other,
                              'generated_result': None, 'cost': None, 'accuracy': None,
                              'for_optimality': True})
    return preds

pred_full = gen_predictions(ds_full, 'full', True)
pred_sub = gen_predictions(ds_sub, 'sub_10', True)
pred_rob = gen_predictions(ds_rob, 'robustness', False)
log('predictions: full=%d (regular 8400 + opt %d) | sub=%d | rob=%d' % (
    len(pred_full), len(pred_full) - 8400, len(pred_sub), len(pred_rob)))

PRED_DIR = os.path.join(PKG, 'router_inference', 'predictions')
# Q11-29：输出文件名与仓库提交物一致（V2 档）；如需生成 V0 档，将 TIER_TO_ARENA/rule_decide 换回 V0 配置并改名为 frugalgpt-router.json
json.dump(pred_full, open(os.path.join(PRED_DIR, 'frugalgpt-router-v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(pred_rob, open(os.path.join(PRED_DIR, 'frugalgpt-router-v2-robustness.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(pred_sub, open(os.path.join(PRED_DIR, 'frugalgpt-router-v2.sub10.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- 5) 自检（官方语义） ----------
def check(preds, dataset, expect, name):
    dmap = {e['global index']: e['prompt_formatted'] for e in dataset}
    regular = [p for p in preds if not p.get('for_optimality', p.get('for_optimization'))]  # Q11-27：官方键名 for_optimality 优先，兼容旧笔误键
    errs = []
    if len(regular) != expect:
        errs.append('size %d != %d' % (len(regular), expect))
    for p in regular:
        gi = p.get('global index')
        if gi not in dmap:
            errs.append('gidx %s not in dataset' % gi); continue
        if p['prompt'] != dmap[gi]:
            errs.append('prompt mismatch %s' % gi)
        if p['prediction'] not in MODELS:
            errs.append('model %s not in pool' % p['prediction'])
    log('%s: regular=%d expect=%d errs=%d %s' % (name, len(regular), expect, len(errs), 'PASS' if not errs else ('FAIL ' + str(errs[:3]))))
    return not errs

ok = check(pred_full, ds_full, 8400, 'full')
ok &= check(pred_sub, ds_sub, 809, 'sub10')
ok &= check(pred_rob, ds_rob, 420, 'robustness')

# 档位分布统计（full regular）
# Q11-29：由 prediction 反查档位（生成时已 rule_decide 一次），不再对每条重复计算
T2T = {'gemini-2.0-flash-001': 'Light', 'claude-3-haiku-20240307': 'Medium', 'gpt-4o': 'Heavy'}
dist = {'Light': 0, 'Medium': 0, 'Heavy': 0}
for p in pred_full:
    if not p.get('for_optimality', p.get('for_optimization')):
        dist[T2T.get(p['prediction'], 'Heavy')] += 1
log('full regular 档位分布: %s' % dist)
log('ALL %s' % ('PASS' if ok else 'FAIL'))
OUT.close()
print('gen done ok=%s' % ok)
