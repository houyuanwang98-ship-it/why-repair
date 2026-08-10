"""Ambient facts, theorem retrieval, and applicability checks."""

import re


from .contracts import (
    AMBIENT_BATCH_RESULT_ID,
    AMBIENT_FACT_DERIVATION_RULES,
    AMBIENT_FACT_KINDS,
    DETERMINISTIC_SAFE_RULE_KINDS,
    DOMAIN_FAMILIES,
    TOPIC_ALIASES,
)
from .text import contains_any, normalized_key, tokens


__all__ = [
    "infer_ambient_facts",
    "render_typed_ambient_fact",
    "ambient_source_text",
    "ambient_facts_from_adjudication",
    "build_ambient_adjudication_entry",
    "entry_text",
    "candidate_entries",
    "overlap_fields",
    "retrieve_rules",
    "search_required_theorem",
    "condition_satisfied",
    "conclusion_matches_goal",
    "assess_rule_applicability",
    "deterministic_safe_goal_matches",
    "deterministic_safe_evidence",
    "best_applicability_evidence",
]


def infer_ambient_facts(item):
    source = normalized_key(" ".join([
        str(item.get("theorem", "")),
        str(item.get("problem_text", "")),
        *[str(value) for value in item.get("assumptions", [])],
    ]))
    facts = []
    metric_context = (
        "metric space" in source
        or bool(re.search(r"\bmetric\s+d\b|\bd\s+is\s+(?:a\s+)?metric\b", source))
    )
    if metric_context:
        facts.extend([
            "The problem is set in a metric space.",
            "Every set under discussion is a subset of the stated metric space.",
            "d is the stated metric.",
        ])
    euclidean_context = contains_any(
        source,
        ["r^k", "r k", "euclidean space", "finite dimensional euclidean"],
    )
    if euclidean_context:
        facts.extend([
            "The ambient space is finite-dimensional Euclidean space.",
            "The Euclidean distance is a metric.",
        ])
    if contains_any(source, ["real numbers", "subset of r", " in r "]):
        facts.append("The objects under discussion lie in the real numbers.")
    return list(dict.fromkeys(facts))


def render_typed_ambient_fact(fact):
    kind = fact["kind"]
    subject = fact["subject"].strip()
    object_value = fact.get("object")
    object_value = object_value.strip() if isinstance(object_value, str) else None
    unary_templates = {
        "euclidean_space": "{subject} is a finite-dimensional Euclidean space.",
        "extended_real_expression": "{subject} is a defined extended-real expression.",
        "finite_dimensional": "{subject} is finite dimensional.",
        "metric_space": "{subject} is a metric space.",
        "normed_space": "{subject} is a normed space.",
        "positive_integer": "{subject} is a positive integer.",
        "real_numbers": "{subject} lies in the real numbers.",
        "real_sequence": "{subject} is a real sequence.",
        "topological_space": "{subject} is a topological space.",
    }
    if kind in unary_templates:
        if object_value is not None:
            return None
        return unary_templates[kind].format(subject=subject)
    if kind == "metric":
        if not object_value:
            return None
        return f"{subject} is a metric on {object_value}."
    if kind == "subset":
        if not object_value:
            return None
        return f"{subject} is a subset of {object_value}."
    return None


def ambient_source_text(item):
    return " ".join([
        str(item.get("theorem", "")),
        str(item.get("problem_text", "")),
        *[str(value) for value in item.get("assumptions", [])],
    ]).strip()


def ambient_facts_from_adjudication(response, items):
    if not isinstance(response, dict) or set(response) != {"results"}:
        return None
    results = response.get("results")
    if not isinstance(results, list) or len(results) != len(items):
        return None
    items_by_id = {str(item.get("id", "")): item for item in items}
    if len(items_by_id) != len(items):
        return None
    facts_by_result = {}
    for result in results:
        if not isinstance(result, dict) or set(result) != {
            "result_id", "facts", "abstained_conditions"
        }:
            return None
        result_id = result.get("result_id")
        if result_id not in items_by_id or result_id in facts_by_result:
            return None
        facts = result.get("facts")
        abstentions = result.get("abstained_conditions")
        if (
            not isinstance(facts, list)
            or len(facts) > 12
            or not isinstance(abstentions, list)
            or not all(
                isinstance(value, str) and value.strip()
                for value in abstentions
            )
        ):
            return None
        source = normalized_key(ambient_source_text(items_by_id[result_id]))
        rendered_facts = []
        for fact in facts:
            if not isinstance(fact, dict) or set(fact) != {
                "kind", "subject", "object", "source_text",
                "derivation_rule", "reasoning"
            }:
                return None
            if fact.get("kind") not in AMBIENT_FACT_KINDS:
                return None
            if fact.get("derivation_rule") not in AMBIENT_FACT_DERIVATION_RULES:
                return None
            if not isinstance(fact.get("subject"), str) or not fact["subject"].strip():
                return None
            if fact.get("object") is not None and (
                not isinstance(fact["object"], str) or not fact["object"].strip()
            ):
                return None
            if not isinstance(fact.get("source_text"), str) or not fact["source_text"].strip():
                return None
            if not isinstance(fact.get("reasoning"), str) or not fact["reasoning"].strip():
                return None
            if len(fact["reasoning"]) > 300:
                return None
            evidence = normalized_key(fact["source_text"])
            subject = normalized_key(fact["subject"])
            if not evidence or evidence not in source or subject not in evidence:
                return None
            rendered = render_typed_ambient_fact(fact)
            if rendered is None:
                return None
            rendered_facts.append(rendered)
        facts_by_result[result_id] = list(dict.fromkeys(rendered_facts))
    if set(facts_by_result) != set(items_by_id):
        return None
    return facts_by_result


def build_ambient_adjudication_entry(items):
    return {
        "result_id": AMBIENT_BATCH_RESULT_ID,
        "node_id": 0,
        "kind": "ambient",
        "input": {
            "proof_instances": [
                {
                    "result_id": str(item.get("id", "")),
                    "theorem": item.get("theorem", ""),
                    "assumptions": list(item.get("assumptions", [])),
                    "deterministic_facts": infer_ambient_facts(item),
                }
                for item in items
            ],
            "allowed_fact_kinds": sorted(AMBIENT_FACT_KINDS),
            "allowed_derivation_rules": sorted(AMBIENT_FACT_DERIVATION_RULES),
            "instructions": (
                "Use only a small amount of reasoning to record background "
                "conditions directly implied by each theorem, its assumptions, "
                "or standard notation appearing in them. Quote source_text from "
                "that proof instance. Do not infer from topic labels, student proof "
                "steps, neighboring exercises, or unstated chapter context. Do not "
                "record a fact that discharges a mathematical step the student must "
                "prove. Return an entry for every result_id. Put uncertain proposed "
                "conditions in abstained_conditions instead of facts."
            ),
        },
        "response_schema": "AMBIENT_FACT_ADJUDICATION_SCHEMA",
        "response": None,
    }


def entry_text(entry):
    parts = [
        entry.get("topic", ""),
        entry.get("name", ""),
        entry.get("statement", ""),
        entry.get("conclusion", ""),
    ]
    parts.extend(entry.get("conditions", []))
    parts.extend(entry.get("typical_uses", []))
    parts.extend(entry.get("common_misuses", []))
    parts.extend(entry.get("bridge_lemmas", []))
    parts.extend(entry.get("repair_templates", []))
    return " ".join(parts)


def candidate_entries(retrieval_query, theorem_bank):
    query_topic = normalized_key(retrieval_query.get("topic", ""))
    accepted_topics = TOPIC_ALIASES.get(query_topic, {query_topic})
    topic_candidates = [
        entry
        for entry in theorem_bank
        if normalized_key(entry.get("topic", "")) in accepted_topics
    ]
    if topic_candidates:
        return topic_candidates, "topic"

    query_domain = normalized_key(retrieval_query.get("domain", ""))
    accepted_domains = DOMAIN_FAMILIES.get(query_domain, {query_domain})
    domain_candidates = [
        entry
        for entry in theorem_bank
        if normalized_key(entry.get("domain", "")) in accepted_domains
    ]
    if domain_candidates:
        return domain_candidates, "domain"

    return list(theorem_bank), "global"


def overlap_fields(query_tokens, entry, fields):
    matched_fields = []
    matched_tokens = set()
    for field in fields:
        value = entry.get(field, "")
        field_text = " ".join(value) if isinstance(value, list) else value
        overlap = query_tokens & tokens(field_text)
        if overlap:
            matched_fields.append(field)
            matched_tokens.update(overlap)
    return matched_tokens, matched_fields


def retrieve_rules(retrieval_query, theorem_bank, max_rules):
    candidates, retrieval_scope = candidate_entries(retrieval_query, theorem_bank)
    goal_tokens = tokens(retrieval_query.get("goal", ""))
    assumption_tokens = tokens(" ".join(retrieval_query.get("assumptions", [])))
    predecessor_tokens = tokens(" ".join(retrieval_query.get("predecessor_claims", [])))
    query_topic = normalized_key(retrieval_query.get("topic", ""))
    accepted_topics = TOPIC_ALIASES.get(query_topic, {query_topic})
    query_domain = normalized_key(retrieval_query.get("domain", ""))
    accepted_domains = DOMAIN_FAMILIES.get(query_domain, {query_domain})
    scored = []
    for entry in candidates:
        goal_overlap, goal_fields = overlap_fields(
            goal_tokens, entry, ("name", "statement", "conclusion")
        )
        predecessor_overlap, predecessor_fields = overlap_fields(
            predecessor_tokens,
            entry,
            ("statement", "conditions", "typical_uses", "bridge_lemmas"),
        )
        assumption_overlap, assumption_fields = overlap_fields(
            assumption_tokens, entry, ("conditions",)
        )

        entry_topic = normalized_key(entry.get("topic", ""))
        entry_domain = normalized_key(entry.get("domain", ""))
        topic_score = 3.0 if entry_topic == query_topic else (2.0 if entry_topic in accepted_topics else 0.0)
        domain_score = 1.0 if entry_domain == query_domain else (0.5 if entry_domain in accepted_domains else 0.0)
        topic_conflict = -2.0 if retrieval_scope != "topic" and query_topic and entry_topic not in accepted_topics else 0.0
        score_breakdown = {
            "goal": 4.0 * len(goal_overlap),
            "predecessors": 3.0 * len(predecessor_overlap),
            "assumptions": 2.0 * len(assumption_overlap),
            "topic": topic_score,
            "domain": domain_score,
            "topic_conflict": topic_conflict,
        }
        score = sum(score_breakdown.values())
        if score > 0:
            matched_query_fields = []
            if goal_overlap:
                matched_query_fields.append("goal")
            if predecessor_overlap:
                matched_query_fields.append("predecessors")
            if assumption_overlap:
                matched_query_fields.append("assumptions")
            if topic_score:
                matched_query_fields.append("topic")
            if domain_score:
                matched_query_fields.append("domain")
            matched_rule_fields = sorted(
                set(goal_fields + predecessor_fields + assumption_fields)
            )
            if topic_score:
                matched_rule_fields.append("topic")
            if domain_score:
                matched_rule_fields.append("domain")
            scored.append(
                (
                    score,
                    entry,
                    score_breakdown,
                    matched_query_fields,
                    sorted(set(matched_rule_fields)),
                )
            )
    scored.sort(key=lambda row: (-row[0], row[1].get("id", "")))
    rules = [
        {
            "id": entry.get("id", ""),
            "name": entry.get("name", ""),
            "score": score,
            "score_breakdown": score_breakdown,
            "matched_query_fields": matched_query_fields,
            "matched_rule_fields": matched_rule_fields,
            "matched_fields": matched_rule_fields,
        }
        for score, entry, score_breakdown, matched_query_fields, matched_rule_fields in scored[:max_rules]
    ]
    return rules, retrieval_scope, len(candidates)


def search_required_theorem(theorem_dependency, theorem_bank, max_rules=5):
    query_text = " ".join([
        theorem_dependency["name"],
        theorem_dependency["statement"],
        " ".join(theorem_dependency["conditions"]),
        theorem_dependency["conclusion"],
        theorem_dependency["search_query"],
    ])
    query_tokens = tokens(query_text)
    query_name = normalized_key(theorem_dependency["name"])
    scored = []
    for entry in theorem_bank:
        entry_text = " ".join([
            str(entry.get("name", "")),
            str(entry.get("statement", "")),
            " ".join(entry.get("conditions", [])),
            str(entry.get("conclusion", "")),
            str(entry.get("topic", "")),
        ])
        overlap = query_tokens & tokens(entry_text)
        name_bonus = 10 if query_name and query_name == normalized_key(
            entry.get("name", "")
        ) else 0
        score = name_bonus + len(overlap)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda row: (-row[0], str(row[1].get("id", ""))))
    return [
        {
            "id": entry.get("id", ""),
            "name": entry.get("name", ""),
            "statement": entry.get("statement", ""),
            "conditions": list(entry.get("conditions", [])),
            "conclusion": entry.get("conclusion", ""),
            "source": entry.get("source", ""),
            "score": score,
        }
        for score, entry in scored[:max_rules]
    ]


def condition_satisfied(condition, proof_state):
    condition_key = normalized_key(condition)
    state_key = normalized_key(" ".join(proof_state))
    if condition_key and condition_key in state_key:
        return True

    condition_tokens = tokens(condition)
    state_tokens = tokens(state_key)
    if condition_tokens:
        coverage = len(condition_tokens & state_tokens) / len(condition_tokens)
        if coverage >= 0.6:
            return True

    predicate_aliases = {
        "nonzero": ("nonzero", "not equal 0", "not_equal 0", "invertible"),
        "field": ("field", "real numbers", "complex numbers"),
        "group": ("group",),
        "normal": ("normal", "kernel"),
        "homomorphism": ("homomorphism", "linear map", "linear"),
        "finite dimensional": ("finite dimensional",),
        "injective": ("injective", "kernel equal {0}", "ker(t) equal {0}"),
        "commutative": ("commutative", "abelian"),
        "integral domain": ("integral domain", "field"),
    }
    for predicate, aliases in predicate_aliases.items():
        if predicate in condition_key and any(alias in state_key for alias in aliases):
            return True
    if "subset of a metric space" in condition_key and contains_any(
        state_key,
        ["subset of the stated metric space", "problem is set in a metric space"],
    ):
        return True
    if contains_any(condition_key, ["d is a metric", "d is the metric"]) and contains_any(
        state_key,
        ["d is the stated metric", "euclidean distance is a metric"],
    ):
        return True
    if "finite dimensional euclidean space" in condition_key and contains_any(
        state_key,
        ["finite dimensional euclidean space", "ambient space is finite dimensional"],
    ):
        return True
    if contains_any(condition_key, [" is in f", " are in f"]) and contains_any(
        state_key, ["field", "real numbers", "complex numbers", "elements of r"]
    ):
        return True
    return False


def conclusion_matches_goal(conclusion, goal):
    normalized_conclusion = normalized_key(conclusion)
    normalized_goal = normalized_key(goal)
    simple_equality = r"\b[a-z]\s*equal\s*[a-z]\b"
    if re.search(simple_equality, normalized_conclusion) and re.search(simple_equality, normalized_goal):
        return True
    conclusion_tokens = tokens(conclusion)
    goal_tokens = tokens(goal)
    if not conclusion_tokens or not goal_tokens:
        return False
    overlap = conclusion_tokens & goal_tokens
    informative = overlap - {"equal", "implies", "multiply", "inverse"}
    return bool(informative) or len(overlap) >= 2


def assess_rule_applicability(retrieved_rules, theorem_bank_by_id, proof_state, goal):
    assessments = []
    for retrieved in retrieved_rules:
        entry = theorem_bank_by_id.get(retrieved["id"], {})
        conditions = list(entry.get("conditions", []))
        satisfied = [
            condition for condition in conditions if condition_satisfied(condition, proof_state)
        ]
        missing = [condition for condition in conditions if condition not in satisfied]
        conclusion = entry.get("conclusion", "") or entry.get("statement", "")
        safe_kind = entry.get("deterministic_safe_kind")
        deterministic_safe = (
            entry.get("deterministic_safe") is True
            and safe_kind in DETERMINISTIC_SAFE_RULE_KINDS
        )
        safe_goal_match = (
            deterministic_safe
            and deterministic_safe_goal_matches(safe_kind, goal)
        )
        assessments.append({
            "rule_id": retrieved["id"],
            "rule_name": retrieved["name"],
            "satisfied_conditions": satisfied,
            "missing_conditions": missing,
            "matched_conclusion": conclusion_matches_goal(conclusion, goal),
            "applicable": not missing and conclusion_matches_goal(conclusion, goal),
            "common_misuses": list(entry.get("common_misuses", [])),
            "retrieval_score": retrieved.get("score", 0),
            "matched_query_fields": list(retrieved.get("matched_query_fields", [])),
            "deterministic_safe": deterministic_safe,
            "deterministic_safe_kind": safe_kind if deterministic_safe else None,
            "deterministic_safe_goal_match": safe_goal_match,
        })
    return assessments


def deterministic_safe_goal_matches(kind, goal):
    """Recognize only checker-owned, one-theorem conclusion shapes.

    The theorem bank may opt a rule into this path, but it cannot supply an
    executable pattern.  Keeping the matcher in checker code makes a malformed
    or over-broad bank entry fail closed.
    """
    key = normalized_key(goal)
    if contains_any(key, ["not open", "is not open", "not separable", "diverges"]):
        return False
    if kind == "interior_is_open":
        interior_target = "interior" in key or re.search(r"\b[a-z][a-z0-9]*\s*\^\s*o\b", key)
        return bool(interior_target) and re.search(r"\bis open\b", key) is not None
    if kind == "rational_power_is_separable":
        return (
            (
                re.search(r"\br\s*\^\s*[a-z0-9]+\b", key) is not None
                or re.search(r"\br\s*(?:power|to the power)\s*[a-z0-9]+\b", key) is not None
            )
            and re.search(r"\bis separable\b", key) is not None
        )
    if kind == "monotone_bounded_sequence_converges":
        return "sequence" in key and contains_any(key, ["converges", "is convergent"])
    return False


def deterministic_safe_evidence(assessments, item):
    reliability = normalized_key(str(item.get("source_reliability", "")))
    if contains_any(reliability, ["uncertain", "unverified ocr", "illegible"]):
        return None
    candidates = [
        assessment for assessment in assessments
        if assessment["deterministic_safe"]
        and assessment["deterministic_safe_goal_match"]
        and not assessment["missing_conditions"]
    ]
    # Ambiguous multiple-rule closure is deliberately left to the host.
    return candidates[0] if len(candidates) == 1 else None


def best_applicability_evidence(assessments):
    if not assessments:
        return None
    return min(
        assessments,
        key=lambda item: (
            not item["matched_conclusion"],
            len(item["missing_conditions"]),
            -len(item["satisfied_conditions"]),
            item["rule_id"],
        ),
    )
