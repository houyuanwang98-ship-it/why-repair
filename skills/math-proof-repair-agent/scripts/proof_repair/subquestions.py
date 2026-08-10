"""Explicit subquestion splitting and derived rules."""

import re


from .contracts import EXPLICIT_SUBQUESTION_PATTERN
from .parsing import split_proof_into_nodes


__all__ = [
    "normalized_subquestion_label",
    "labels_form_explicit_sequence",
    "split_explicit_sections",
    "split_item_into_subquestions",
    "rules_from_accepted_subquestion",
]


def normalized_subquestion_label(match):
    label = match.group("paren") or match.group("plain") or match.group("named")
    if match.group("named"):
        label_match = re.search(r"\(?([0-9a-z]+)\)?$", label, flags=re.IGNORECASE)
        label = label_match.group(1)
    return label.lower()


def labels_form_explicit_sequence(labels):
    if len(labels) < 2 or len(set(labels)) != len(labels):
        return False
    if all(label.isdigit() for label in labels):
        values = [int(label) for label in labels]
        return all(right == left + 1 for left, right in zip(values, values[1:]))
    if all(len(label) == 1 and label.isalpha() for label in labels):
        values = [ord(label) for label in labels]
        return all(right == left + 1 for left, right in zip(values, values[1:]))
    return False


def split_explicit_sections(text):
    matches = list(EXPLICIT_SUBQUESTION_PATTERN.finditer(text or ""))
    labels = [normalized_subquestion_label(match) for match in matches]
    if not labels_form_explicit_sequence(labels):
        return []
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        if not body:
            return []
        sections.append({"label": labels[index], "text": body})
    return sections


def split_item_into_subquestions(item):
    structured = item.get("explicit_subquestions")
    if structured:
        labels = [str(part.get("label", "")).lower() for part in structured]
        if not labels_form_explicit_sequence(labels):
            return [item]
        question_sections = [
            {"label": label, "text": str(part.get("theorem", "")).strip()}
            for label, part in zip(labels, structured)
        ]
        proof_by_label = {
            label: part.get("proof_steps", [])
            for label, part in zip(labels, structured)
        }
    else:
        problem_text = item.get("problem_text", item.get("theorem", ""))
        question_sections = split_explicit_sections(problem_text)
        if not question_sections:
            return [item]
        proof_text = item.get("proof_text", "\n".join(item.get("flawed_proof_steps", [])))
        proof_sections = split_explicit_sections(proof_text)
        proof_by_label = {
            section["label"]: split_proof_into_nodes(section["text"])
            for section in proof_sections
        }

    parent_id = item.get("id", "proof")
    subitems = []
    for section in question_sections:
        label = section["label"]
        proof_steps = proof_by_label.get(label, [])
        if isinstance(proof_steps, str):
            proof_steps = split_proof_into_nodes(proof_steps)
        subitem = dict(item)
        for field in ("problem_text", "proof_text", "explicit_subquestions"):
            subitem.pop(field, None)
        subitem.update({
            "id": f"{parent_id}_part_{label}",
            "parent_id": parent_id,
            "subquestion_label": label,
            "theorem": section["text"],
            "flawed_proof_steps": list(proof_steps),
        })
        subitems.append(subitem)
    return subitems


def rules_from_accepted_subquestion(result):
    accepted_statuses = {"closed", "valid_with_gap", "missing_bridge_lemma"}
    rules = []
    for node in result["proof_graph"]:
        if node["status"] not in accepted_statuses:
            continue
        rules.append({
            "id": f"prior_{result['id']}_node_{node['node_id']}",
            "source": f"Earlier subquestion {result['subquestion_label']}",
            "kind": "DerivedRule",
            "rule_role": "prior_subquestion",
            "domain": result["domain"],
            "topic": result["topic"],
            "name": f"Prior subquestion {result['subquestion_label']} node {node['node_id']}",
            "statement": node["claim"],
            "conditions": list(result["assumptions"]),
            "conclusion": node["claim"],
            "typical_uses": ["Use in a later explicitly numbered subquestion."],
            "common_misuses": ["Do not use before this subquestion has been established."],
            "priority": 6,
            "status": "derived_from_checked_subquestion",
        })
    return rules
