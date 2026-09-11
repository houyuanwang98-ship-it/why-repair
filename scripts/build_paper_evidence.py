"""Rebuild descriptive paper tables and source-bound case cards; no model calls."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/paper/generated'


def build():
    sources = {}

    def read(path):
        raw = (ROOT / path).read_bytes()
        sources[path] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    report = read('data/benchmarks/m3/revalidation/full50_report_v0_2.json')
    counter = read('data/benchmarks/m4/integrated_acceptance_v1_1.json')
    review = read('data/benchmarks/m7/interactive_case_level_human_review_v0_2.json')
    smoke = read('data/benchmarks/m6/codex_ai_proxy_nine_method_smoke_20260821/run_summary.json')
    final_review = read('data/manual_validation/minimum_final_review_status_v0_1.json')
    live_results = [read(f'data/benchmarks/m5/live_repair_pilot_20260910/{case_id}/result.json')
                    for case_id in ('m2-011', 'm2-018')]
    assert report['sample_count'] == report['proof_validity']['count'] == 50
    assert len(review['rows']) == len({r['case_id'] for r in review['rows']}) == review['summary']['cases']
    for label in ('confirmed', 'corrected'):
        assert sum(r['verification'] == label for r in review['rows']) == review['summary'][label]
    metrics = [
        ('M3 proof validity accuracy', report['proof_validity']['accuracy'], '50 proofs'),
        ('M3 error type accuracy', report['error_type']['accuracy'], '50 proofs'),
        ('M3 first error overall accuracy', report['first_error_localization']['overall_accuracy'], '50 proofs, including absent errors'),
        ('M3 first error applicable accuracy', report['first_error_localization']['exact_accuracy'], '37 applicable proofs'),
        ('M3 dependency precision', report['dependency_edges']['precision'], '62 predicted edges'),
        ('M3 dependency recall', report['dependency_edges']['recall'], '58 reference edges'),
        ('M3 dependency F1', report['dependency_edges']['f1'], 'edge-level harmonic mean'),
        ('M3 invalid proof false acceptance', report['safety_rates']['proof_false_acceptance_rate'], '26 invalid proofs; lower is better'),
    ]
    lines = ['# 可重建结果总表', '',
             '由 `python scripts/build_paper_evidence.py` 从历史报告重建；没有重新运行模型。', '',
             '## 50 题工程集描述性结果', '',
             '| 指标 | 数值 | 分母/口径 |', '|---|---:|---|']
    lines += [f'| {name} | {value:.4f} | {scope} |' for name, value, scope in metrics]
    lines += ['', '## 其他证据（不能与准确率合并）', '',
              f"- M4：{counter['benchmark']['accepted_count']}/{counter['benchmark']['valid_counterexample_count']} 个已确认有效反例通过有界执行验证。",
              f"- M6：{smoke['completed_batches']} 个方法批次完成；每批 3 道相同题，共 27 个 assignment。不是 27 道不同题。",
              f"- M7：{review['summary']['cases']} 道历史案例复核，确认 {review['summary']['confirmed']}、修正 {review['summary']['corrected']}。",
              f"- 实时修复 Pilot：{sum(r['status'] == 'accepted' for r in live_results)}/2 道完成 AI 独立调用复核与控制器重验；两道均于 {final_review['human_tasks'][0]['confirmed_on']} 获项目所有者人工确认。",
              '- m2-034 在后代重验中被拒绝且后续生成超过题目预算，维持中断状态，不进入成功数。',
              '- M7 历史文件保留 user_person_a 与 person_b 两个分片角色；当前只要求 Person B 的安排不能改写过去的参与者记录。',
              '- 该历史复核明确为 AI 预填后纠错，不提供独立双盲或标注者一致性指标。',
              '- 没有正式基线差异、显著性、真实账单或新实验成功率。', '']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'results.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    source_path = 'data/benchmarks/m2/pilot_50.jsonl'
    raw = (ROOT / source_path).read_bytes()
    sources[source_path] = hashlib.sha256(raw).hexdigest()
    cases = {r['proof_id']: r for r in map(json.loads, raw.decode('utf-8').splitlines())}
    selected = ['m2-011', 'm2-018', 'm2-021', 'm2-026', 'm2-028', 'm2-032', 'm2-034', 'm2-038', 'm2-042', 'm2-044']
    cards = ['# 十个历史代表案例', '',
             '从既有工程集抽取，用于展示；不是新题、独立测试集或新增人工审核。保留原始文本与复核意见，不自动规范化争议标签。', '']
    reviews = {r['case_id']: r for r in review['rows']}
    for cid in selected:
        case = cases[cid]
        cards += [f'## {cid}', '', case['theorem'], '', '假设：' + '；'.join(case['assumptions']), '']
        cards += [f"- {step['node_id']}：{step['text']}" for step in case['proof_steps']]
        cards += ['', '历史案例复核记录：', '', '```json', json.dumps(reviews[cid], ensure_ascii=False, indent=2), '```', '']
        patch_dir = ROOT / 'data/benchmarks/m5/provisional_codex_interactive_v1'
        for patch in sorted(patch_dir.glob(cid + '.patch*.json')):
            relative = patch.relative_to(ROOT).as_posix()
            obj = read(relative)
            cards += ['补丁来源：`' + relative + '`', '', '```json', json.dumps(obj, ensure_ascii=False, indent=2), '```', '']
    (OUT / 'case_cards.md').write_text('\n'.join(cards), encoding='utf-8', newline='\n')
    sources['scripts/build_paper_evidence.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    outputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT / 'results.md', OUT / 'case_cards.md')}
    (OUT / 'manifest.json').write_text(json.dumps({'source_sha256': sources, 'output_sha256': outputs,
        'new_model_runs': 0, 'scientific_comparison': False}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Rebuilt {len(metrics)} metrics and {len(selected)} historical case cards at {OUT}')


if __name__ == '__main__':
    build()
