"""Materialize all 600 existing project proofs and audit available experiment evidence."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(path):
    text = (ROOT/path).read_text(encoding='utf-8')
    return [json.loads(x) for x in text.splitlines() if x.strip()] if path.endswith('.jsonl') else json.loads(text)


def save(name, obj):
    text = ''.join(json.dumps(x, ensure_ascii=False)+'\n' for x in obj) if name.endswith('.jsonl') else json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    (HERE/name).write_text(text,encoding='utf-8',newline='\n')


def main():
    specs=[('M2 Pilot', 'data/benchmarks/m2/source/pilot_50.jsonl',50),
           ('M2 B50','data/benchmarks/m2/source/pilot_B50.jsonl',50),
           ('OPC-250','data/benchmarks/m7/opc_250_v0_2/candidate.jsonl',250),
           ('ProofNet-250','data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl',250)]
    gold_path='data/benchmarks/m2/gold/algebra_pilot_v1.jsonl'
    opc_path='data/benchmarks/m7/opc_250_v0_2/seed_annotations.json'
    gold={r['proof_id']:r for r in load(gold_path)}
    opc={r['case_id']:r for r in load(opc_path)}
    manual_paths=[f'data/manual_validation/person_{role}_step05_case_results.jsonl' for role in ['a','b']]
    reviews={}
    for path in manual_paths:
        for r in load(path):
            reviews.setdefault(r['case_id'],[]).append({'path':path,'record':r})
    historical=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    history={r['proof_id']:r for r in historical['cases']}
    inputs=[]; labels=[]; results=[]; ids=set()
    for group,path,expected in specs:
        rows=load(path)
        if len(rows)!=expected: raise ValueError(f'Unexpected source count: {path}')
        for r in rows:
            pid=r.get('proof_id',r.get('case_id'))
            if not pid or pid in ids: raise ValueError(f'Duplicate/missing ID: {pid}')
            ids.add(pid)
            inputs.append({'case_id':pid,'group':group,'source_path':path,
                           'theorem':r.get('theorem',r.get('problem')),'assumptions':r.get('assumptions',[]),
                           'proof':r.get('proof') or '\n'.join(s['text'] for s in r['proof_steps'])})
            status=gold[pid]['gold_validity_status'] if pid in gold else ('valid' if opc[pid]['human_proof_verdict']=='correct' else 'invalid') if pid in opc else None
            labels.append({'case_id':pid,'original_verdict':status,'verdict_source':gold_path if pid in gold else opc_path if pid in opc else None,
                           'human_review_records':reviews.get(pid,[]),
                           'repairability':None,'note':'审核完成记录不自动提供可机读数学判定；原始标签不代表新修复输出正确。'})
            for method in ['direct_rewrite','self_refine','generator_critic','full_system']:
                results.append({'case_id':pid,'method':method,'status':'not_run','final_proof':None,
                                'human_verified_success':None,'historical_reference':history.get(pid) if method=='full_system' else None})
    save('dataset.jsonl',inputs);save('gold_index.jsonl',labels);save('comparison_results.jsonl',results)
    paths=[s[1] for s in specs]+[gold_path,opc_path]+manual_paths
    save('full_source_manifest.json',{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    summary={'sample_count':len(inputs),'group_counts':dict(Counter(r['group'] for r in inputs)),
             'readable_original_gold_count':sum(r['original_verdict'] is not None for r in labels),
             'human_review_record_coverage':sum(bool(r['human_review_records']) for r in labels),
             'original_gold_counts':dict(Counter(r['original_verdict'] or 'not_structured' for r in labels)),
             'planned_assignments':len(results),'new_completed_assignments':0,
             'historical_reference_count':len(history),'full_comparison_accuracy':None,
             'status':'full_dataset_rebuilt_execution_pending'}
    save('full_results.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
