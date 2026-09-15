"""Run all 600 proofs with four prompted repair workflows and an independent blind judge."""
import argparse, concurrent.futures, hashlib, json, os, subprocess, tempfile, threading
from pathlib import Path

HERE=Path(__file__).resolve().parent
LOCK=threading.Lock()
METHODS=['direct_rewrite','self_refine','generator_critic','full_system']

def read_jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(tmp,path)

def call(prompt,schema,out,model,effort):
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists(): return json.loads(out.read_text(encoding='utf-8'))
    last=out.with_suffix('.last.txt'); events=out.with_suffix('.events.jsonl')
    cmd=['codex','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--disable','shell_tool','--disable','skill_search','-m',model,
         '-c',f'model_reasoning_effort="{effort}"','--output-schema',str(schema),'-o',str(last),'-C',tempfile.gettempdir(),'--json','-']
    proc=subprocess.run(cmd,input=prompt,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=600)
    events.write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
    if not last.exists(): raise RuntimeError(f'codex failed rc={proc.returncode}; no output payload')
    try:
        value=json.loads(last.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f'codex failed rc={proc.returncode}; invalid output payload') from exc
    write(out,value); return value

def generation_prompt(c):
    return '''You are running a controlled proof-repair experiment. Do not use tools or files. Analyze the same proof under four workflows and return four complete final proofs. Keep theorem, assumptions, and domain unchanged. direct_rewrite: one-pass rewrite. self_refine: draft, internally check, return revised proof. generator_critic: generator plus critic workflow. full_system: dependency-aware evaluator certificate, minimal local repair, independent-review style check, and descendant revalidation. Do not expose hidden reasoning; give a short reason. If the theorem cannot be preserved, outcome irreparable and final_proof must explain why with a counterexample. Return methods exactly once. INPUT='''+json.dumps(c,ensure_ascii=False)

def judgment_prompt(c,g):
    order=sorted(g['outputs'],key=lambda x:hashlib.sha256((c['case_id']+x['method']).encode()).hexdigest())
    candidates=[{'candidate_id':f'candidate-{i+1}','proof':x['final_proof'],'claimed_outcome':x['outcome']} for i,x in enumerate(order)]
    mapping={f'candidate-{i+1}':x['method'] for i,x in enumerate(order)}
    prompt='''Act as an independent mathematical proof judge. Do not use tools or files. Judge the original and every anonymized candidate against only the exact theorem, assumptions, and domain. valid requires a complete correct proof; a valid counterexample-based irreparable response is not a valid proof of the theorem, but may preserve the problem. rigorous requires no material gap or hidden assumption. Use undetermined when evidence is insufficient. Return candidates exactly once. INPUT='''+json.dumps({'case_id':c['case_id'],'theorem':c['theorem'],'assumptions':c['assumptions'],'original_proof':c['proof'],'candidates':candidates},ensure_ascii=False)
    return prompt,mapping

def one(c,args):
    folder=args.output_dir/c['case_id']; folder.mkdir(parents=True,exist_ok=True)
    try:
        g=call(generation_prompt(c),HERE/'generation.schema.json',folder/'generation.json',args.model,args.effort)
        if g['case_id']!=c['case_id'] or {x['method'] for x in g['outputs']}!=set(METHODS): raise ValueError('generation identity mismatch')
        p,m=judgment_prompt(c,g); j=call(p,HERE/'judgment.schema.json',folder/'judgment.json',args.judge_model,args.judge_effort)
        if j['case_id']!=c['case_id'] or {x['candidate_id'] for x in j['candidates']}!=set(m): raise ValueError('judgment identity mismatch')
        write(folder/'mapping.json',m)
        row={'case_id':c['case_id'],'status':'completed','model':args.model,'judge_model':args.judge_model}
    except Exception as e:
        row={'case_id':c['case_id'],'status':'failed','error_type':type(e).__name__,'error':str(e)}
    with LOCK:
        print(json.dumps(row,ensure_ascii=False),flush=True)
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=HERE/'runs/full600_v1');ap.add_argument('--model',default='gpt-5.6-luna');ap.add_argument('--judge-model',default='gpt-5.6-terra');ap.add_argument('--effort',default='low');ap.add_argument('--judge-effort',default='medium');ap.add_argument('--workers',type=int,default=6);ap.add_argument('--limit',type=int);a=ap.parse_args()
    cases=read_jsonl(HERE/'dataset.jsonl'); done={p.parent.name for p in a.output_dir.glob('*/judgment.json')}
    todo=[c for c in cases if c['case_id'] not in done]
    if a.limit is not None: todo=todo[:a.limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex: rows=list(ex.map(lambda c:one(c,a),todo))
    allrows=[]
    for c in cases:
        f=a.output_dir/c['case_id']/'judgment.json'; allrows.append({'case_id':c['case_id'],'status':'completed' if f.exists() else 'failed'})
    write(a.output_dir/'run_summary.json',{'assigned':len(cases),'completed':sum(r['status']=='completed' for r in allrows),'failed':sum(r['status']=='failed' for r in allrows),'new_attempts':len(rows),'models':{'generator':a.model,'judge':a.judge_model},'human_verified':False})

if __name__=='__main__': main()
