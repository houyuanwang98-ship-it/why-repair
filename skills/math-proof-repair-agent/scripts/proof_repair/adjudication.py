"""Host-adjudication templates, prompts, and provider adapters."""

import json


from .contracts import (
    CALCULATION_ADJUDICATION_SCHEMA,
    DIAGNOSIS_ADJUDICATION_SCHEMA,
    GRAPH_BUILDER_SCHEMA,
    MODEL_ADJUDICATION_SCHEMA,
)
from .graph import build_graph_adjudication_entry
from .io_session import stable_digest
from .text import normalized_key


__all__ = [
    "diagnosis_adjudication_input",
    "calculation_adjudication_endpoint_mismatch",
    "node_adjudication_candidate",
    "unresolved_ancestor_ids",
    "dependency_frontier",
    "externalize_retrieved_rules",
    "build_host_adjudication_template",
    "build_model_adjudication_prompt",
    "make_openai_adjudicator",
    "build_diagnosis_adjudication_prompt",
    "make_openai_diagnosis_adjudicator",
    "make_openai_graph_builder",
    "build_calculation_adjudication_prompt",
    "make_openai_calculation_adjudicator",
]


def diagnosis_adjudication_input(result, node):
    return {
        "theorem": result["theorem"],
        "assumptions": result["assumptions"],
        "original_claim": node["claim"],
        "self_contained_claim": node["self_contained_claim"],
        "depends_on": node["depends_on"],
        "local_context": node["local_context"],
        "ambient_facts": node.get("ambient_facts", []),
        "retrieved_rules": node["retrieved_rules"],
        "preliminary_status": node["status"],
        "preliminary_error_type": node["error_type"],
        "preliminary_diagnosis": node["diagnosis"],
        "source_reliability": node["source_reliability"],
        "deterministic_evidence": {
            "satisfied_conditions": node["satisfied_conditions"],
            "missing_conditions": node["missing_conditions"],
            "matched_conclusion": node["matched_conclusion"],
            "operation_check": node["operation_check"],
            "counterexample": node["counterexample"],
        },
    }


def calculation_adjudication_endpoint_mismatch(node):
    calculation = node.get("calculation_adjudication")
    if not isinstance(calculation, dict):
        return False
    source_expression = calculation.get("source_expression")
    target_expression = calculation.get("target_expression")
    if not isinstance(source_expression, str) or not isinstance(
        target_expression, str
    ):
        return True
    return (
        normalized_key(source_expression)
        != normalized_key(node.get("calculation_source_expression", ""))
        or normalized_key(target_expression)
        != normalized_key(node.get("claim", ""))
    )


def node_adjudication_candidate(result, node, bundle_primary=True):
    calculation = node.get("calculation_adjudication")
    if calculation and (
        calculation.get("decision") == "undetermined"
        or calculation_adjudication_endpoint_mismatch(node)
    ):
        primary_input = {
            "source_expression": node["calculation_source_expression"],
            "target_expression": node["claim"],
            "calculation_context": node["calculation_context"],
        }
        if bundle_primary:
            return {
                "result_id": result["id"],
                "node_id": node["node_id"],
                "kind": "calculation_diagnosis",
                "input": {
                    "primary_kind": "calculation",
                    "primary_input": primary_input,
                    "diagnosis_if_nonclosed": diagnosis_adjudication_input(result, node),
                    "instructions": (
                        "Fill primary_response using CALCULATION_ADJUDICATION_SCHEMA. "
                        "Leave diagnosis_response null when the primary closes the "
                        "node or is a structurally valid high-confidence repairable "
                        "gap. Otherwise fill diagnosis_response using "
                        "DIAGNOSIS_ADJUDICATION_SCHEMA."
                    ),
                },
                "response_schema": "PRIMARY_DIAGNOSIS_BUNDLE_SCHEMA",
                "response": None,
            }
        return {
            "result_id": result["id"],
            "node_id": node["node_id"],
            "kind": "calculation",
            "input": primary_input,
            "response_schema": "CALCULATION_ADJUDICATION_SCHEMA",
            "response": None,
        }
    proof = node.get("model_adjudication")
    if proof and proof.get("decision") == "undetermined":
        primary_input = {
            "local_context": node["local_context"],
            "ambient_facts": node.get("ambient_facts", []),
            "claim": node["claim"],
            "retrieved_rules": node["retrieved_rules"],
        }
        if bundle_primary:
            return {
                "result_id": result["id"],
                "node_id": node["node_id"],
                "kind": "proof_diagnosis",
                "input": {
                    "primary_kind": "proof",
                    "primary_input": primary_input,
                    "diagnosis_if_nonclosed": diagnosis_adjudication_input(result, node),
                    "instructions": (
                        "Fill primary_response using MODEL_ADJUDICATION_SCHEMA. "
                        "Leave diagnosis_response null when the primary closes the "
                        "node or proves a structurally valid high-confidence omitted "
                        "bridge. Otherwise fill diagnosis_response using "
                        "DIAGNOSIS_ADJUDICATION_SCHEMA."
                    ),
                },
                "response_schema": "PRIMARY_DIAGNOSIS_BUNDLE_SCHEMA",
                "response": None,
            }
        return {
            "result_id": result["id"],
            "node_id": node["node_id"],
            "kind": "proof",
            "input": primary_input,
            "response_schema": "MODEL_ADJUDICATION_SCHEMA",
            "response": None,
        }
    diagnosis = node.get("diagnosis_adjudication")
    theorem_dependency = diagnosis.get("theorem_dependency") if diagnosis else None
    if theorem_dependency and node.get("theorem_verification") is None:
        return {
            "result_id": result["id"],
            "node_id": node["node_id"],
            "kind": "theorem",
            "input": {
                "theorem": result["theorem"],
                "assumptions": result["assumptions"],
                "claim": node["self_contained_claim"],
                "local_context": node["local_context"],
                "required_theorem": theorem_dependency,
                "local_candidates": node["theorem_candidates"],
                "instructions": (
                    "Check local_candidates first. If none exactly verifies the "
                    "required theorem, search the web using the supplied query and "
                    "prefer an authoritative mathematical source. Then verify the "
                    "theorem statement, all premises, whether it supports this exact "
                    "claim, whether it is foundational, and whether omitting it is an "
                    "acceptable direct use or a proof gap. Return not_found only after "
                    "both local and web search fail."
                ),
            },
            "response_schema": "THEOREM_VERIFICATION_SCHEMA",
            "response": None,
        }
    if (
        node["status"] not in {"closed", "downstream_invalid", "undetermined"}
        and node.get("diagnosis_adjudication") is None
    ):
        return {
            "result_id": result["id"],
            "node_id": node["node_id"],
            "kind": "diagnosis",
            "input": diagnosis_adjudication_input(result, node),
            "response_schema": "DIAGNOSIS_ADJUDICATION_SCHEMA",
            "response": None,
        }
    return None


def unresolved_ancestor_ids(node_id, nodes_by_id, memo):
    if node_id in memo:
        return memo[node_id]
    ancestors = set()
    for predecessor_id in nodes_by_id[node_id].get("depends_on", []):
        ancestors.add(predecessor_id)
        ancestors.update(unresolved_ancestor_ids(predecessor_id, nodes_by_id, memo))
    memo[node_id] = ancestors
    return ancestors


def dependency_frontier(result, candidates):
    if not candidates:
        return []
    nodes = result["proof_graph"]
    if any(node.get("dependency_source") == "heuristic_fallback" for node in nodes):
        return candidates[:1]
    nodes_by_id = {node["node_id"]: node for node in nodes}
    candidate_ids = {entry["node_id"] for entry in candidates}
    memo = {}
    frontier = []
    for entry in candidates:
        node_id = entry["node_id"]
        if unresolved_ancestor_ids(node_id, nodes_by_id, memo) & candidate_ids:
            continue
        if entry["kind"] in {"calculation", "calculation_diagnosis"}:
            context_barrier = any(
                earlier["node_id"] < node_id
                and nodes_by_id[earlier["node_id"]]
                    .get("calculation_context", {})
                    .get("context_changed")
                for earlier in candidates
            )
            if context_barrier:
                continue
        frontier.append(entry)
    return frontier


def externalize_retrieved_rules(value, rule_dictionary):
    if isinstance(value, list):
        return [externalize_retrieved_rules(item, rule_dictionary) for item in value]
    if not isinstance(value, dict):
        return value
    compact = {}
    for key, item in value.items():
        if key != "retrieved_rules":
            compact[key] = externalize_retrieved_rules(item, rule_dictionary)
            continue
        references = []
        for rule in item:
            rule_id = str(rule.get("id", "rule")) if isinstance(rule, dict) else "rule"
            reference = f"{rule_id}@{stable_digest(rule)[:12]}"
            rule_dictionary.setdefault(reference, rule)
            references.append(reference)
        compact["retrieved_rule_refs"] = references
    return compact


def build_host_adjudication_template(
    results, *, use_frontier=True, bundle_primary=True, workflow_mode="grading"
):
    entries = []
    for result in results:
        candidates = [
            candidate
            for node in result["proof_graph"]
            if (candidate := node_adjudication_candidate(
                result, node, bundle_primary=bundle_primary
            )) is not None
        ]
        entries.extend(
            dependency_frontier(result, candidates)
            if use_frontier
            else candidates[:1]
        )
    rule_dictionary = {}
    for entry in entries:
        entry["input"] = externalize_retrieved_rules(
            entry["input"], rule_dictionary
        )
    return {
        "workflow_mode": workflow_mode,
        "rule_dictionary": rule_dictionary,
        "instructions": (
            "The active host agent fills every response in this dependency frontier "
            "using the skill references, then reruns the checker. Bundled primary "
            "entries include diagnosis in the same response when the primary decision "
            "does not close the node. For theorem entries, inspect local candidates "
            "first and browse authoritative web sources only when no local candidate "
            "verifies the required theorem. "
            "Resolve every retrieved_rule_refs entry through the shared top-level "
            "rule_dictionary. "
            + (
                "This is grading mode: do not load the iterative repair reference or "
                "generate repair artifacts."
                if workflow_mode == "grading"
                else "This is repair mode: finish all checker obligations before "
                "loading and applying the iterative repair reference."
            )
        ),
        "adjudications": entries,
    }


def build_model_adjudication_prompt(item, claim, local_context, retrieved_rules):
    return """You are adjudicating one local mathematical proposition.

Decide exactly one of:
- derivable: give a short valid proof from only the supplied context;
- counterexample: give explicit values or a structure satisfying every context
  assumption while making the claim false, and verify both parts;
- undetermined: use this when neither a proof nor a checked counterexample is
  available. Failure to find a counterexample is not evidence of derivability.

Apply this intermediate-step completion standard when decision=derivable:
1. Use only supplied context and rules whose preconditions are satisfied.
2. The first inference must start from the supplied context, and the final
   bridge claim must exactly establish the requested claim.
3. Each bridge step must be atomic and cite a definition, rule, assumption, or
   earlier bridge step in its justification.
4. Do not introduce a new assumption, strengthen the context, change the goal,
   or hide another inference inside phrases such as "clearly" or "obviously".
5. Return the shortest complete chain. Do not split a direct one-rule inference
   into cosmetic language fragments.
6. Set directly_justified and bridge_length=0 when one explicit rule application
   already connects context to claim. Set omitted_intermediate_steps only when
   at least one mathematical intermediate claim is genuinely absent from the
   student's step; then bridge_length must equal the number of bridge_steps.
7. If no complete chain satisfies these requirements, return undetermined.

Treat retrieved rules only as hints. Return the required structured JSON.

Domain: {domain}
Topic: {topic}
Original theorem: {theorem}
Local context:
{context}
Claim:
{claim}
Retrieved rule hints:
{rules}
""".format(
        domain=item.get("domain", ""),
        topic=item.get("topic", ""),
        theorem=item.get("theorem", ""),
        context=json.dumps(local_context, ensure_ascii=False, indent=2),
        claim=claim,
        rules=json.dumps(retrieved_rules, ensure_ascii=False, indent=2),
    )


def make_openai_adjudicator(model, max_output_tokens):
    client_holder = {}

    def adjudicate(item, claim, local_context, retrieved_rules):
        if "client" not in client_holder:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "Model adjudication requires the openai package. Install requirements.txt."
                ) from exc
            client_holder["client"] = OpenAI()
        response = client_holder["client"].responses.create(
            model=model,
            input=build_model_adjudication_prompt(
                item, claim, local_context, retrieved_rules
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "obligation_adjudication",
                    "strict": True,
                    "schema": MODEL_ADJUDICATION_SCHEMA,
                }
            },
            temperature=0,
            max_output_tokens=max_output_tokens,
            store=False,
        )
        return json.loads(response.output_text)

    return adjudicate


def build_diagnosis_adjudication_prompt(payload):
    return """You are reviewing a preliminary diagnosis of one proof node.

Locate the first failed inference edge between the supplied direct context and
the student's current claim. Do not merely say that the proof is incomplete or
needs detail. State the exact unavailable premise, misapplied rule, invalid
transformation, false assertion, or target mismatch, and cite concrete evidence
from the supplied claim or context.

Independently review the preliminary classification:
- confirmed: an error is real; independently choose the most accurate category,
  even when it differs from the preliminary category;
- false_positive: the student's original text already contains a direct valid
  justification; use directly_justified, repairability=none, and no repair;
- uncertain: OCR or missing context prevents a responsible decision; use
  ocr_uncertain or undetermined and repairability=manual_review.

Use false_local_claim when only the current node is refuted. Use false_theorem
only when a counterexample satisfies every original theorem assumption and
refutes the original theorem conclusion.

Set theorem_dependency only when resolving this dispute genuinely requires a
specific supporting theorem whose existence or applicability must be checked.
Do not request theorem verification for direct calculations, target mismatches,
explicit counterexamples, OCR uncertainty, or conclusions settled directly by
the supplied context. A theorem-dependent positive decision is provisional:
the host will search the local theorem bank first and authoritative web sources
only if local search fails. Report whether the current claim remains derivable
from the original problem conditions. Give the shortest repair that addresses
the exact failed obligation. Return only the required structured JSON.

Input:
""" + json.dumps(payload, ensure_ascii=False, indent=2)


def make_openai_diagnosis_adjudicator(model, max_output_tokens):
    client_holder = {}

    def adjudicate(payload):
        if "client" not in client_holder:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "Diagnosis adjudication requires the openai package. Install requirements.txt."
                ) from exc
            client_holder["client"] = OpenAI()
        response = client_holder["client"].responses.create(
            model=model,
            input=build_diagnosis_adjudication_prompt(payload),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "proof_error_diagnosis",
                    "strict": True,
                    "schema": DIAGNOSIS_ADJUDICATION_SCHEMA,
                }
            },
            temperature=0,
            max_output_tokens=max_output_tokens,
            store=False,
        )
        return json.loads(response.output_text)

    return adjudicate


def make_openai_graph_builder(model, max_output_tokens):
    client_holder = {"client": None}

    def build_graph(item, proof_steps):
        if client_holder["client"] is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "Graph building requires the openai package. Install requirements.txt."
                ) from exc
            client_holder["client"] = OpenAI()
        payload = build_graph_adjudication_entry(item, proof_steps)["input"]
        response = client_holder["client"].responses.create(
            model=model,
            input=json.dumps(payload, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "proof_dependency_graph",
                    "strict": True,
                    "schema": GRAPH_BUILDER_SCHEMA,
                }
            },
            max_output_tokens=max_output_tokens,
        )
        return json.loads(response.output_text)

    return build_graph


def build_calculation_adjudication_prompt(source_expression, target_expression, context):
    return """You are checking one mathematical calculation transition.

The program controls the active axiom system. You may use only axioms listed in
calculation_context. Expand the transition into the shortest sequence of atomic
calculation steps. Every step must name one allowed axiom and list its required
conditions. Do not introduce assumptions.

Return:
- valid_transformation when the written transition is already one justified
  atomic calculation;
- repairable_gap when two or more valid atomic steps are needed and the student
  omitted intermediate expressions;
- missing_precondition when a needed condition is absent;
- invalid_transformation when the target does not follow by valid calculation;
- context_mismatch when the calculation requires an axiom outside the active
  system; or
- undetermined when you cannot produce or refute a complete chain.

The source_expression and target_expression in the response must reproduce the
supplied endpoints. `used_axioms` must use exact names from the context.

source_expression:
{source}

target_expression:
{target}

calculation_context:
{context}
""".format(
        source=source_expression,
        target=target_expression,
        context=json.dumps(context, ensure_ascii=False, indent=2),
    )


def make_openai_calculation_adjudicator(model, max_output_tokens):
    client_holder = {}

    def adjudicate(source_expression, target_expression, context):
        if "client" not in client_holder:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "Calculation adjudication requires the openai package. Install requirements.txt."
                ) from exc
            client_holder["client"] = OpenAI()
        response = client_holder["client"].responses.create(
            model=model,
            input=build_calculation_adjudication_prompt(
                source_expression, target_expression, context
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "calculation_adjudication",
                    "strict": True,
                    "schema": CALCULATION_ADJUDICATION_SCHEMA,
                }
            },
            temperature=0,
            max_output_tokens=max_output_tokens,
            store=False,
        )
        return json.loads(response.output_text)

    return adjudicate
