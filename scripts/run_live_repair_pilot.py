"""Real Codex patch/review/node-revalidation calls with immutable checkpoints.

This is a fixed-diagnosis engineering pilot, not an end-to-end ablation.
Run one case per invocation; repeat the same invocation to replay saved calls.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from harness.codex_cli import build_codex_adapter, CodexCLIError
from harness.m5_person_a_review import canonical_digest, patch_edit_ids
from harness.m5_repair import RepairBudget
from harness.m5_sequential_repair import M5SequentialRepairController
from scripts.build_m5_runtime_controller_replay import _nodes

SCHEMAS = {
    'generate': 'm5_person_b_patch_proposal_v0_1.schema.json',
    'review': 'm5_person_a_patch_review_v0_1.schema.json',
    'revalidate': 'm5_controller_revalidation_v0_1.schema.json',
}
COMMON = ('Use only INPUT JSON and mathematical knowledge. Do not use tools, files or web. '
          'You are an AI, not a human reviewer. Preserve the exact theorem, assumptions and domain. ')
PROMPTS = {
    'generate': COMMON + 'Propose one minimal patch for the current error certificate. '
        'Use generator_id=live-generator. All references must use supplied current versions. '
        'An insert_before node uses a fresh ID and an order_key before the target. '
        'For replace retain the target ID. Do not copy global assumptions into the proof as new assumptions. '
        'If the theorem is false use mark_irreparable and explain a counterexample.',
    'review': COMMON + 'Independently review the proposed patch against context and current proof. '
        'Use reviewer_id=live-reviewer and exact context_id. Cover every edit_id in deletion_trials. '
        'Check local repair and problem preservation; downstream nodes will be revalidated separately. '
        'accepted must equal all checks true, no hidden assumptions, no introduced errors, '
        'all deletion trials removal_breaks_repair true, no rejection codes. '
        'When rejecting include the appropriate codes for every false check. '
        'Use evidence_used from context.allowed_evidence. Explain actual mathematics, never merely trust the generator.',
    'revalidate': COMMON + 'Independently judge only target_node using its supplied dependency '
        'ancestors and the original problem. The caller has applied a patch but supplies no earlier verdict. '
        'Use evaluator_id=live-reviewer, the exact target reference and evaluation_id. '
        'Return accepted, rejected or undetermined with a mathematical reason. '
        'Do not assume a node is correct because a previous patch was accepted.',
}


def write_once(path, value):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError(f'Existing evidence differs: {path}')
        return
    with path.open('xb') as stream:
        stream.write(data)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def ancestors(nodes, target):
    by_key = {(n['node_id'], n['version']): n for n in nodes}
    found = {}
    def visit(node):
        for ref in node.get('depends_on', []):
            key = (ref['node_id'], ref['version'])
            if key not in found:
                found[key] = by_key[key]
                visit(by_key[key])
    visit(target)
    return [deepcopy(n) for n in sorted(found.values(), key=lambda n: n['order_key'])]


class Calls:
    def __init__(self, output, model, command, execute, max_calls=12, max_tokens=60000):
        self.output, self.model, self.command = output, model, command
        self.execute, self.max_calls, self.max_tokens = execute, max_calls, max_tokens
        self.count, self.tokens = 0, 0
        self.adapter = None

    def call(self, phase, payload):
        if self.count >= self.max_calls or self.tokens >= self.max_tokens:
            raise RuntimeError('Pilot call/token budget exhausted; checkpoint retained')
        self.count += 1
        folder = self.output / f'call-{self.count:03d}-{phase}'
        schema = read(ROOT / 'schemas' / SCHEMAS[phase])
        request = {'phase': phase, 'model': self.model, 'input': payload,
                   'prompt': PROMPTS[phase], 'schema': schema, 'timeout_seconds': 180,
                   'max_output_tokens': 3500, 'reasoning_effort': 'high'}
        write_once(folder / 'request.json', request)
        if (folder / 'failure.json').exists():
            raise RuntimeError('Prior failed call retained; use a new run ID for a new attempt')
        if (folder / 'response.json').exists():
            raw = read(folder / 'response.json')
        else:
            if not self.execute:
                raise RuntimeError('Prepared first request; pass --execute to make model calls')
            if self.adapter is None:
                def isolated_process(command, **kwargs):
                    command = command[:-1] + ['--disable', 'shell_tool', '--disable', 'skill_search', '-']
                    kwargs.update(encoding='utf-8', errors='strict')
                    return subprocess.run(command, **kwargs)
                self.adapter = build_codex_adapter(codex_command=self.command, process_runner=isolated_process)
            try:
                raw = self.adapter(model=self.model, prompt=PROMPTS[phase], input_payload=payload,
                    max_output_tokens=3500, sampling={'reasoning_effort': 'high'},
                    output_schema=schema, timeout_seconds=180)
            except CodexCLIError as exc:
                write_once(folder / 'failure.json', {'error': str(exc), 'raw': exc.raw_response})
                raise
            write_once(folder / 'response.json', raw)
        self.tokens += raw['usage']['total_tokens']
        if self.tokens > self.max_tokens:
            raise RuntimeError('Pilot token budget exceeded; response preserved but not applied')
        forbidden = [e for e in raw['events'] if isinstance(e.get('item'), dict)
                     and e['item'].get('type') in {'command_execution', 'mcp_tool_call', 'web_search'}]
        if forbidden:
            raise RuntimeError('Tool activity detected; response cannot enter isolated pilot')
        value = json.loads(raw['output_text'])
        Draft202012Validator(schema).validate(value)
        write_once(folder / 'validated.json', value)
        print(f'{folder.name}: recorded; cumulative tokens={self.tokens}', flush=True)
        return value


def run_case(case_id, output, calls, rounds):
    source, nodes = _nodes(case_id)
    initial = read(ROOT / f'data/benchmarks/m5/provisional_codex_interactive_v1/{case_id}.input.json')
    certificate = deepcopy(initial['error_certificate'])
    controller = M5SequentialRepairController(proof_id=case_id, nodes=nodes,
        error_certificate=certificate, repair_generator_id='live-generator',
        evaluator_ids={'live-reviewer'}, budget=RepairBudget(max_rounds=rounds, max_new_nodes=2, max_total_edits=6))
    problem = {key: source[key] for key in ('theorem', 'assumptions', 'domain')}
    bound_paths = [Path(__file__), ROOT / 'harness/m5_repair.py', ROOT / 'harness/m5_sequential_repair.py',
                   ROOT / 'harness/m5_person_a_review.py', ROOT / 'harness/codex_cli.py']
    source_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in bound_paths}
    write_once(output / 'inputs.json', {'problem': problem, 'nodes': nodes, 'certificate': certificate,
        'source_sha256': source_hashes,
        'rounds': rounds, 'model': calls.model, 'max_calls': calls.max_calls, 'max_tokens': calls.max_tokens,
        'kind': 'fixed_historical_diagnosis_live_repair_pilot', 'human_review': False})
    step = 0
    try:
        while controller.snapshot()['stop_reason'] is None:
            state = controller.snapshot()
            if state['rounds'] >= rounds:
                break
            target_node = next(n for n in state['nodes'] if n['node_id'] == certificate['target']['node_id'])
            payload = {'problem': problem, 'repair_input': controller.generator_input(),
                       'dependency_ancestors': ancestors(state['nodes'], target_node)}
            patch = calls.call('generate', payload)
            controller.submit(patch)
            if controller.snapshot()['stop_reason'] is not None:
                break
            evidence = [canonical_digest(payload), canonical_digest(patch)]
            context = {'schema_version': '0.1', 'context_id': f'{case_id}-r{state["rounds"]+1}',
                'proof_id': case_id, 'target': patch['target'], 'theorem': source['theorem'],
                'global_assumptions': source['assumptions'], 'domain': source['domain'],
                'failed_inference': certificate['failed_inference'], 'allowed_evidence': evidence,
                'unrelated_branch_digests': {}, 'error_certificate_digest': canonical_digest(certificate),
                'patch_digest': canonical_digest(patch)}
            review = calls.call('review', {'context': context, 'patch': patch,
                'current_nodes': state['nodes'], 'edit_ids': patch_edit_ids(patch)})
            if review['reviewer_id'] != 'live-reviewer':
                raise RuntimeError('Unexpected reviewer identity')
            state = controller.review_and_apply(context, review)
            step += 1
            write_once(output / f'state-{step:03d}.json', state)
            while state['stop_reason'] is None:
                pending = next((q for q in state['revalidation_queue'] if q['status'] == 'pending_evaluation'), None)
                if pending is None:
                    break
                node = next(n for n in state['nodes'] if n['node_id'] == pending['target']['node_id'])
                record = calls.call('revalidate', {'problem': problem, 'target': pending['target'],
                    'target_node': node, 'dependency_ancestors': ancestors(state['nodes'], node),
                    'evaluation_id': f'{case_id}-evaluation-{calls.count+1}'})
                state = controller.record_revalidation(record)
                step += 1
                write_once(output / f'state-{step:03d}.json', state)
                if record['verdict'] != 'accepted':
                    certificate = {'certificate_id': f'{case_id}-followup-{step}',
                        'target': record['target'], 'failed_inference': record['reason'],
                        'repair_constraints': {'allowed_operations': ['insert_before', 'replace', 'delete'],
                            'max_new_nodes': 2, 'preserve_theorem': True, 'preserve_assumptions': True}}
                    controller.supply_followup_certificate(certificate)
                    break
        final = controller.snapshot()
        write_once(output / 'result.json', {'status': final['stop_reason'] or 'round_budget_exhausted',
            'calls': calls.count, 'reported_tokens': calls.tokens, 'human_verified': False,
            'scientific_claim_allowed': False, 'final_state': final, 'events': controller.events})
    except Exception as exc:
        write_once(output / 'interruption.json', {'error_type': type(exc).__name__, 'error': str(exc),
            'calls': calls.count, 'reported_tokens': calls.tokens, 'state': controller.snapshot()})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=['m2-011', 'm2-018', 'm2-034'])
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', default='gpt-5.6-terra')
    parser.add_argument('--codex-command', default='codex')
    parser.add_argument('--rounds', type=int, choices=[1, 3], default=3)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    calls = Calls(args.output_dir, args.model, args.codex_command, args.execute)
    run_case(args.case, args.output_dir, calls, args.rounds)


if __name__ == '__main__':
    main()
