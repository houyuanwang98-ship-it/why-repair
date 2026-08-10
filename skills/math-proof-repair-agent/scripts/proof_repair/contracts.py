"""Shared constants, schemas, and result helpers."""

import re


__all__ = [
    "STOPWORDS",
    "NODE_CACHE_SCHEMA_VERSION",
    "NODE_ADJUDICATION_KINDS",
    "SESSION_SCHEMA_VERSION",
    "AMBIENT_BATCH_RESULT_ID",
    "PRIMARY_DIAGNOSIS_BUNDLE_KINDS",
    "TOPIC_ALIASES",
    "DOMAIN_FAMILIES",
    "GRAPH_BUILDER_SCHEMA",
    "AMBIENT_FACT_KINDS",
    "AMBIENT_FACT_DERIVATION_RULES",
    "DETERMINISTIC_SAFE_RULE_KINDS",
    "AMBIENT_FACT_ADJUDICATION_SCHEMA",
    "MODEL_ADJUDICATION_SCHEMA",
    "CALCULATION_ADJUDICATION_SCHEMA",
    "DIAGNOSIS_ADJUDICATION_SCHEMA",
    "THEOREM_VERIFICATION_SCHEMA",
    "STRUCTURE_AXIOMS",
    "CAUSE_EFFECT_WORDS",
    "CONDITION_WORDS",
    "CONJUNCTIONS",
    "LOGICAL_WORDS",
    "EXPLICIT_SUBQUESTION_PATTERN",
    "closed",
    "logical_classification",
]


STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "then",
    "this",
    "from",
    "into",
    "under",
    "because",
    "therefore",
    "thus",
    "have",
    "show",
    "prove",
    "let",
    "are",
    "is",
    "in",
    "of",
    "to",
    "a",
    "an",
}

NODE_CACHE_SCHEMA_VERSION = 1

NODE_ADJUDICATION_KINDS = (
    "ambient", "graph", "calculation", "proof", "diagnosis", "theorem"
)

SESSION_SCHEMA_VERSION = 1

AMBIENT_BATCH_RESULT_ID = "__ambient_facts__"

PRIMARY_DIAGNOSIS_BUNDLE_KINDS = {
    "calculation_diagnosis": "calculation",
    "proof_diagnosis": "proof",
}

TOPIC_ALIASES = {
    "field axioms": {"field axioms", "fields", "rings", "groups"},
    "group theory": {"group theory", "groups"},
    "ring theory": {"ring theory", "rings", "ideals"},
    "linear algebra": {"linear algebra", "linear maps", "vector spaces"},
}

DOMAIN_FAMILIES = {
    "algebra": {"algebra", "abstract algebra", "linear algebra"},
    "analysis": {"real analysis", "complex analysis"},
    "real analysis": {"real analysis", "analysis"},
    "abstract algebra": {"abstract algebra", "algebra"},
    "linear algebra": {"linear algebra", "algebra"},
}

GRAPH_BUILDER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "node_id": {"type": "integer", "minimum": 1},
                    "depends_on": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 1},
                    },
                    "self_contained_claim": {"type": "string"},
                },
                "required": ["node_id", "depends_on", "self_contained_claim"],
            },
        },
    },
    "required": ["nodes"],
}

AMBIENT_FACT_KINDS = {
    "euclidean_space",
    "extended_real_expression",
    "finite_dimensional",
    "metric",
    "metric_space",
    "normed_space",
    "positive_integer",
    "real_numbers",
    "real_sequence",
    "subset",
    "topological_space",
}

AMBIENT_FACT_DERIVATION_RULES = {
    "explicit_statement",
    "standard_notation",
    "type_declaration",
}

DETERMINISTIC_SAFE_RULE_KINDS = {
    "interior_is_open",
    "monotone_bounded_sequence_converges",
    "rational_power_is_separable",
}

AMBIENT_FACT_ADJUDICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "result_id": {"type": "string"},
                    "facts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "kind": {
                                    "type": "string",
                                    "enum": sorted(AMBIENT_FACT_KINDS),
                                },
                                "subject": {"type": "string"},
                                "object": {"type": ["string", "null"]},
                                "source_text": {"type": "string"},
                                "derivation_rule": {
                                    "type": "string",
                                    "enum": sorted(AMBIENT_FACT_DERIVATION_RULES),
                                },
                                "reasoning": {"type": "string"},
                            },
                            "required": [
                                "kind",
                                "subject",
                                "object",
                                "source_text",
                                "derivation_rule",
                                "reasoning",
                            ],
                        },
                    },
                    "abstained_conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["result_id", "facts", "abstained_conditions"],
            },
        },
    },
    "required": ["results"],
}

MODEL_ADJUDICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["derivable", "counterexample", "undetermined"],
        },
        "reasoning_summary": {"type": "string"},
        "proof_outline": {"type": "array", "items": {"type": "string"}},
        "completion_assessment": {
            "type": "string",
            "enum": [
                "directly_justified",
                "omitted_intermediate_steps",
                "not_applicable",
            ],
        },
        "original_step_requires_completion": {"type": "boolean"},
        "bridge_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "claim": {"type": "string"},
                    "justification": {"type": "string"},
                    "depends_on_context": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["claim", "justification", "depends_on_context"],
            },
        },
        "bridge_length": {"type": "integer", "minimum": 0},
        "counterexample_description": {"type": ["string", "null"]},
        "counterexample_verification": {"type": ["string", "null"]},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "decision",
        "reasoning_summary",
        "proof_outline",
        "completion_assessment",
        "original_step_requires_completion",
        "bridge_steps",
        "bridge_length",
        "counterexample_description",
        "counterexample_verification",
        "confidence",
    ],
}

CALCULATION_ADJUDICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "decision": {
            "type": "string",
            "enum": [
                "valid_transformation",
                "repairable_gap",
                "missing_precondition",
                "invalid_transformation",
                "context_mismatch",
                "undetermined",
            ],
        },
        "source_expression": {"type": "string"},
        "target_expression": {"type": "string"},
        "atomic_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "expression": {"type": "string"},
                    "rule": {"type": "string"},
                    "required_conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["expression", "rule", "required_conditions"],
            },
        },
        "used_axioms": {"type": "array", "items": {"type": "string"}},
        "introduced_assumptions": {"type": "array", "items": {"type": "string"}},
        "missing_conditions": {"type": "array", "items": {"type": "string"}},
        "reasoning_summary": {"type": "string"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "decision",
        "source_expression",
        "target_expression",
        "atomic_steps",
        "used_axioms",
        "introduced_assumptions",
        "missing_conditions",
        "reasoning_summary",
        "confidence",
    ],
}

DIAGNOSIS_ADJUDICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "diagnosis_review": {
            "type": "string",
            "enum": ["confirmed", "false_positive", "uncertain"],
        },
        "error_category": {
            "type": "string",
            "enum": [
                "directly_justified",
                "missing_bridge_lemma",
                "missing_assumption",
                "theorem_misuse",
                "algebraic_invalidity",
                "false_local_claim",
                "false_theorem",
                "target_mismatch",
                "ocr_uncertain",
                "undetermined",
            ],
        },
        "failed_inference": {"type": "string"},
        "violated_obligation": {"type": "string"},
        "error_scope": {
            "type": "string",
            "enum": ["none", "local_node", "original_theorem", "source_text"],
        },
        "evidence": {"type": "array", "items": {"type": "string"}},
        "counterexample_or_witness": {"type": ["string", "null"]},
        "claim_globally_derivable": {"type": ["boolean", "null"]},
        "repairability": {
            "type": "string",
            "enum": [
                "none",
                "insert_bridge",
                "establish_premise",
                "replace_step",
                "change_target",
                "change_assumption",
                "cannot_repair",
                "manual_review",
            ],
        },
        "minimal_repair": {"type": ["string", "null"]},
        "theorem_dependency": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "statement": {"type": "string"},
                "conditions": {"type": "array", "items": {"type": "string"}},
                "conclusion": {"type": "string"},
                "why_required": {"type": "string"},
                "search_query": {"type": "string"},
                "student_explicitly_invokes_theorem": {"type": "boolean"},
            },
            "required": [
                "name", "statement", "conditions", "conclusion",
                "why_required", "search_query",
                "student_explicitly_invokes_theorem",
            ],
        },
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "diagnosis_review",
        "error_category",
        "failed_inference",
        "violated_obligation",
        "error_scope",
        "evidence",
        "counterexample_or_witness",
        "claim_globally_derivable",
        "repairability",
        "minimal_repair",
        "theorem_dependency",
        "confidence",
    ],
}

THEOREM_VERIFICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "verification_status": {
            "type": "string",
            "enum": ["local_verified", "web_verified", "not_found"],
        },
        "theorem_name": {"type": "string"},
        "statement": {"type": "string"},
        "conditions": {"type": "array", "items": {"type": "string"}},
        "conclusion": {"type": "string"},
        "source_id": {"type": ["string", "null"]},
        "source_url": {"type": ["string", "null"]},
        "source_title": {"type": ["string", "null"]},
        "search_query": {"type": "string"},
        "search_attempted": {
            "type": "string",
            "enum": ["local_only", "local_and_web"],
        },
        "supports_claim": {"type": "boolean"},
        "premises_satisfied": {"type": "array", "items": {"type": "string"}},
        "missing_premises": {"type": "array", "items": {"type": "string"}},
        "is_foundational": {"type": ["boolean", "null"]},
        "direct_use_assessment": {
            "type": "string",
            "enum": ["direct_use_acceptable", "omission_is_gap", "not_applicable"],
        },
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "verification_status", "theorem_name", "statement", "conditions",
        "conclusion", "source_id", "source_url", "source_title",
        "search_query", "search_attempted", "supports_claim",
        "premises_satisfied", "missing_premises", "is_foundational",
        "direct_use_assessment", "evidence", "confidence",
    ],
}

STRUCTURE_AXIOMS = {
    "field": {
        "additive_associativity", "additive_commutativity", "additive_identity",
        "additive_inverse", "multiplicative_associativity",
        "multiplicative_commutativity", "multiplicative_identity",
        "multiplicative_inverse", "distributivity", "equality_substitution",
    },
    "commutative_ring": {
        "additive_associativity", "additive_commutativity", "additive_identity",
        "additive_inverse", "multiplicative_associativity",
        "multiplicative_commutativity", "multiplicative_identity",
        "distributivity", "equality_substitution",
    },
    "ring": {
        "additive_associativity", "additive_commutativity", "additive_identity",
        "additive_inverse", "multiplicative_associativity",
        "multiplicative_identity", "distributivity", "equality_substitution",
    },
    "abelian_group": {
        "associativity", "identity", "inverse", "commutativity",
        "equality_substitution",
    },
    "group": {"associativity", "identity", "inverse", "equality_substitution"},
    "vector_space": {
        "vector_addition", "scalar_multiplication", "distributivity",
        "scalar_associativity", "additive_inverse", "equality_substitution",
    },
    "real_numbers": {
        "additive_associativity", "additive_commutativity", "additive_identity",
        "additive_inverse", "multiplicative_associativity",
        "multiplicative_commutativity", "multiplicative_identity",
        "multiplicative_inverse", "distributivity", "ordered_field",
        "equality_substitution",
    },
    "unknown": {"equality_substitution"},
}

CAUSE_EFFECT_WORDS = [
    "therefore", "thus", "consequently", "hence", "accordingly",
    "as a result", "as a consequence", "for this reason",
    "because", "since", "so", "thereby",
    "lead to", "result in", "give rise to", "contribute to",
    "stem from", "arise from", "due to", "owing to",
]

CONDITION_WORDS = [
    "if", "unless", "provided that", "providing that",
    "as long as", "so long as", "on condition that",
    "in case", "in the event that", "suppose that",
    "supposing that", "otherwise", "or else",
    "whether",
]

CONJUNCTIONS = sorted(set(
    CAUSE_EFFECT_WORDS + [
        "but", "however", "nevertheless", "nonetheless",
        "on the other hand", "whereas", "while", "although",
        "though", "even though", "yet", "still",
        "moreover", "furthermore", "in addition", "additionally",
        "besides", "also", "then",
        "first", "firstly", "second", "secondly", "third", "thirdly",
        "next", "finally", "lastly", "after", "afterwards", "later",
        "subsequently", "meanwhile", "simultaneously", "eventually",
        "in conclusion", "in summary", "overall", "in short",
        "for example", "for instance", "in particular", "namely",
        "in fact", "actually", "indeed", "obviously", "clearly",
        "in other words", "that is", "i.e.",
    ]
), key=lambda w: (-len(w), w))

LOGICAL_WORDS = sorted(set(
    CAUSE_EFFECT_WORDS + CONDITION_WORDS + CONJUNCTIONS
), key=lambda w: (-len(w), w))

EXPLICIT_SUBQUESTION_PATTERN = re.compile(
    r"(?im)^\s*(?:"
    r"\((?P<paren>[0-9]+|[a-z])\)"
    r"|(?P<plain>[0-9]+|[a-z])[.)]"
    r"|(?P<named>(?:part|question|problem)\s+(?:\([0-9a-z]+\)|[0-9a-z]+))"
    r")\s*[:.-]?\s+"
)


def closed(diagnosis):
    return {
        "status": "closed",
        "gap_type": None,
        "error_type": None,
        "diagnosis": diagnosis,
        "repair_action": None,
        "minimal_repair": None,
    }


def logical_classification(status):
    mapping = {
        "closed": ("no_error", "none"),
        "valid_with_gap": ("repairable_gap", "insert_local_justification"),
        "missing_bridge_lemma": ("repairable_gap", "insert_local_justification"),
        "missing_assumption": ("unsupported_inference", "establish_or_add_premise"),
        "theorem_misuse": ("unsupported_inference", "replace_local_step"),
        "algebraic_invalidity": ("unsupported_inference", "replace_local_step"),
        "false_local_claim": ("false_claim", "replace_local_step"),
        "false_theorem": ("false_claim", "change_theorem_or_give_counterexample"),
        "target_mismatch": ("unsupported_inference", "replace_local_step"),
        "downstream_invalid": ("downstream_dependency", "repair_predecessor"),
        "undetermined": ("indeterminate", "manual_review"),
    }
    return mapping[status]
