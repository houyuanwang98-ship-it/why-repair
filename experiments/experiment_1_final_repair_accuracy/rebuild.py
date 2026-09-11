"""Rebuild the retrospective experiment from tracked evidence, without model calls."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GOLD = 'data/benchmarks/m2/gold/algebra_pilot_v1.jsonl'
REVIEWS = 'data/manual_validation/person_a_step06_patch_results.jsonl'
TOTAL = 'data/manual_validation/person_a_step06_completion_record.json'


def read(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    return [json.loads(x) for x in text.splitlines() if x.strip()] if path.endswith('.jsonl') else json.loads(text)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def interval(k, n):
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [max(0, c-h), min(1, c+h)]


def build():
    source_paths = {GOLD, REVIEWS, TOTAL}
    raw_gold = read(GOLD)
    gold = {r['proof_id']: r for r in raw_gold}
    require(len(gold) == len(raw_gold), 'Duplicate Gold IDs')
    reviews = read(REVIEWS)
    require(len({r['proof_id'] for r in reviews}) == len(reviews), 'Duplicate proof IDs')
    total = read(TOTAL)
    require(hashlib.sha256((ROOT / REVIEWS).read_bytes()).hexdigest() == total['results_sha256'], 'Review digest mismatch')
    cases = []
    for row in sorted(reviews, key=lambda r: r['proof_id']):
        pid = row['proof_id']
        require(pid in gold, f'Missing Gold: {pid}')
        require(row['human_sync_status'] == 'completed', f'Incomplete review: {pid}')
        paths = row['evidence_paths']
        for path in paths:
            resolved = (ROOT / path).resolve()
            require(resolved.is_relative_to(ROOT) and resolved.is_file(), f'Missing/unsafe evidence: {path}')
            source_paths.add(path)
        completions = [p for p in paths if p.endswith('.completion.json')]
        require(len(completions) == 1, f'Completion count: {pid}')
        completion = read(completions[0])
        require(completion['proof_id'] == pid, f'Completion ID mismatch: {pid}')
        outcome = row['machine_agent_whole_proof_result']
        require(outcome in {'repaired', 'not_repaired_irreparable'}, f'Unknown outcome: {pid}')
        expected = 'accepted' if outcome == 'repaired' else 'irreparable'
        require(completion['controller_stop_reason'] == row['controller_stop_reason'] == expected, f'Terminal mismatch: {pid}')
        cases.append(dict(proof_id=pid, gold_status=gold[pid]['gold_validity_status'],
                          error_type=gold[pid]['gold_error_type'], outcome=outcome,
                          run_id=completion['run_id'], repair_rounds=completion['repair_rounds'],
                          evidence_paths=paths, evidence_basis=row['basis']))
    counts = Counter(c['outcome'] for c in cases)
    require(len(cases) == total['completed_patches'], 'Summary count mismatch')
    require(dict(counts) == total['whole_proof_result_counts'], 'Summary outcome mismatch')
    def stats(subset):
        n = len(subset)
        before = sum(c['gold_status'] == 'valid' for c in subset)
        after = sum(c['outcome'] == 'repaired' for c in subset)
        return dict(n=n, before=before, after=after, before_wilson95=interval(before,n),
                    after_wilson95=interval(after,n), change_percentage_points=100*(after-before)/n if n else None)
    result = dict(evidence_level='retrospective_owner_confirmed_engineering_records',
                  new_model_calls=0, all_cases=stats(cases),
                  excluding_undetermined=stats([c for c in cases if c['gold_status'] != 'undetermined']),
                  invalid_only=stats([c for c in cases if c['gold_status'] == 'invalid']),
                  outcomes=dict(counts), cases=cases)
    manifest = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(source_paths)}
    output = {'results.json': json.dumps(result,ensure_ascii=False,indent=2)+'\n',
              'source_manifest.json': json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'}
    lines = ['# 自动复算结果', '', '本表由 `rebuild.py` 从 Gold、人工同步记录及 Controller completion 重新计算。', '',
             '| 子集 | 修复前严格接受 | 修复后记录为 repaired | 描述性变化 |', '|---|---:|---:|---:|']
    for name,key in [('全部21题','all_cases'),('排除未确定题','excluding_undetermined'),('仅原Gold为invalid','invalid_only')]:
        s=result[key]; n=s['n']
        lines.append(f"| {name} | {s['before']}/{n} | {s['after']}/{n}（{100*s['after']/n:.1f}%） | +{s['change_percentage_points']:.1f}个百分点 |")
    lines += ['', '统计单位为不同证明，不是补丁轮次。不可修退出不计为修复成功。',
              '这些比例以历史纳入队列为分母；没有独立冻结的可修性标签，不能将14个成功样本反过来定义成可修集合。',
              'Wilson区间见 results.json；由于回顾性选择和同源样本，区间仅供描述，不能建立总体泛化或方法优势。', '',
              '| Proof ID | 原Gold | 历史终态 | 轮数 | Completion证据 |', '|---|---|---|---:|---|']
    for c in cases:
        completion=next(p for p in c['evidence_paths'] if p.endswith('.completion.json'))
        lines.append(f"| {c['proof_id']} | {c['gold_status']} | {c['outcome']} | {c['repair_rounds']} | [记录](../../{completion}) |")
    output['RECOMPUTED_RESULTS.md']='\n'.join(lines)+'\n'
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='Verify saved artifacts without modifying them')
    args=parser.parse_args()
    for name,content in output.items():
        path=HERE/name
        if args.check:
            require(path.exists() and path.read_text(encoding='utf-8') == content, f'Artifact drift: {name}')
        else:
            path.write_text(content,encoding='utf-8',newline='\n')
    print(f"Validated {len(cases)} proofs, {len(manifest)} source files; repaired={counts['repaired']}, irreparable={counts['not_repaired_irreparable']}")


if __name__ == '__main__':
    build()
