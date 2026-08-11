"""Proof splitting and node classification."""

import re


from .calculation import is_complete_calculation_relation
from .contracts import CAUSE_EFFECT_WORDS, CONDITION_WORDS, CONJUNCTIONS, LOGICAL_WORDS
from .text import contains_any


__all__ = [
    "_match_at_start",
    "_find_after",
    "_find_any",
    "_comma_split_with_logical_words",
    "split_proof_into_nodes",
    "_has_subject_predicate",
    "_merge_incomplete_nodes",
    "_split_periods_if_complete",
    "classify_node_type",
    "retrieval_decision",
]


def _match_at_start(text, word_list):
    """Return the first matched phrase from word_list found at the start of text (case-insensitive)."""
    lower = text.lower().lstrip()
    for phrase in word_list:
        # Check exact start match with word boundary
        if lower.startswith(phrase):
            # Verify word boundary after the phrase
            rest = lower[len(phrase):]
            if not rest or not rest[0].isalpha():
                return phrase
        # Also check with common punctuation stripped
        stripped = lower.lstrip("(),;: ")
        if stripped.startswith(phrase):
            rest = stripped[len(phrase):]
            if not rest or not rest[0].isalpha():
                return phrase
    return None


def _find_after(text, word_list):
    """Find the earliest occurrence of any word from word_list in text (not at position 0). Uses word boundaries."""
    lower = text.lower()
    best_pos = len(lower) + 1
    best_phrase = None
    for phrase in word_list:
        pos = lower.find(phrase, 1)  # skip position 0
        while pos != -1:
            # Check word boundary before the phrase
            before = lower[pos - 1] if pos > 0 else ' '
            after_pos = pos + len(phrase)
            after = lower[after_pos] if after_pos < len(lower) else ' '
            # Valid boundary: before is non-alpha or start, after is non-alpha or end
            if (not before.isalpha() or not before.isascii()) and \
               (after_pos >= len(lower) or not lower[after_pos].isalpha()):
                if pos < best_pos:
                    best_pos = pos
                    best_phrase = phrase
                break
            pos = lower.find(phrase, pos + 1)
    return best_pos, best_phrase


def _find_any(text, word_list):
    """Find the earliest occurrence of any phrase in word_list anywhere in text."""
    lower = text.lower()
    best_pos = len(lower) + 1
    best_phrase = None
    for phrase in word_list:
        pos = lower.find(phrase)
        if pos != -1 and pos < best_pos:
            best_pos = pos
            best_phrase = phrase
    return best_pos, best_phrase


def _comma_split_with_logical_words(segments):
    """
    Comma rule: scan each segment left-to-right. For each comma NOT inside
    parentheses (math notation), check if the text between the last sentence
    boundary (or segment start) and this comma contains a logical connector
    word. If yes, split at this comma: the connector-through-comma text
    becomes one node.

    Example:
      "Then for each n in N, we do X."
      -> "Then" in "Then for each n in N" -> split at comma:
        ["Then for each n in N,", "we do X."]
    """
    STANDARD_SYMBOLS = re.compile(r'[.!?;]')
    result = []

    for seg in segments:
        # Find comma positions NOT inside parentheses
        depth = 0
        inside_paren = set()
        for i, ch in enumerate(seg):
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth = max(0, depth - 1)
            elif ch == ',' and depth > 0:
                inside_paren.add(i)

        commas = [m.start() for m in re.finditer(r',', seg)
                  if m.start() not in inside_paren]
        if not commas:
            result.append(seg)
            continue

        # Filter out commas that are part of number lists (e.g., "i = 1, 2, ..., N")
        filtered_commas = []
        for c_pos in commas:
            # Check if the comma is between two numbers or after a number before a \ldots/...
            after = seg[c_pos + 1:].lstrip()
            before = seg[:c_pos].rstrip()
            # Pattern: "1, 2" or "1, ..., N" - number before and number/... after
            if (before and before[-1].isdigit()) and \
               (after and (after[0].isdigit() or after.startswith('...') or after.startswith('\\ldots'))):
                continue
            # Also protect comma before "...," pattern
            if seg[c_pos:c_pos + 4] == ',...' or seg[max(0, c_pos - 4):c_pos + 1] == '...,':
                continue
            filtered_commas.append(c_pos)
        commas = filtered_commas

        # Left-to-right scan: split at commas that follow a logical connector
        pieces = []
        scan_start = 0  # where we're currently scanning from

        for comma_pos in commas:
            text_before = seg[scan_start:comma_pos]

            # Find last sentence boundary within text_before
            b_matches = list(STANDARD_SYMBOLS.finditer(text_before))
            if b_matches:
                bound_end = b_matches[-1].end()
                between = text_before[bound_end:].strip()
            else:
                between = text_before.strip()

            if not between:
                continue

            # Check if 'between' has a logical connector
            lower = between.lower()
            found = False
            for phrase in LOGICAL_WORDS:
                p = lower.find(phrase)
                while p != -1:
                    end_p = p + len(phrase)
                    after = lower[end_p] if end_p < len(lower) else ' '
                    before = lower[p - 1] if p > 0 else ' '
                    if (not before.isalpha() or not before.isascii()) and \
                       (not after.isalpha()):
                        found = True
                        break
                    p = lower.find(phrase, p + 1)
                if found:
                    break

            if found:
                # Split: connector-through-comma is one piece
                piece = seg[scan_start:comma_pos + 1].strip()
                if piece:
                    pieces.append(piece)
                scan_start = comma_pos + 1

        # Remaining text after last split
        remaining = seg[scan_start:].strip()
        if remaining:
            pieces.append(remaining)

        if pieces:
            result.extend(pieces)
        else:
            result.append(seg)

    return result


def split_proof_into_nodes(raw_text):
    """
    Split raw proof text into node-level statements.

    Base rule: split on sentence boundaries ('.', '!', '?', ';', newlines).

    Logical connector rules (derived from English_Logical_Connectors.pdf):
      1. Cause & Effect rule:
         If a Cause & Effect word appears mid-sentence (not at the very start),
         split a new node BEFORE that word.
      2. Condition rule:
         If a Condition word is found (at sentence start or mid-sentence),
         that word starts a new node. Continue collecting subsequent sentences
         until the next conjunction is encountered; split BEFORE that conjunction.
      3. Comma rule:
         If a comma exists and, between that comma and the nearest sentence-ending
         punctuation ('.', '!', '?', ';') before it, there is a logical connector
         word, split BEFORE that connector word so that "connector ... comma"
         forms its own node.

    Returns:
        list[str]: Ordered list of node claims.
    """
    # Phase 1: split into base segments
    # Split on sentence-ending punctuation + newlines
    segments = re.split(r'(?<=[.!?])\s+', raw_text.strip())
    # Further split on semicolons
    expanded = []
    for seg in segments:
        parts = re.split(r'\s*;\s*', seg)
        for p in parts:
            p = p.strip()
            if p:
                expanded.append(p)
    segments = expanded

    if not segments:
        return []

    # Phase 2: comma rule (logical-connector-driven comma splitting)
    # When a comma appears after a logical connector word (with only the
    # connector word between the preceding sentence boundary and the comma),
    # split the segment before the connector word so that "connector...comma"
    # becomes its own node.
    segments = _comma_split_with_logical_words(segments)

    # Phase 3: apply Cause & Effect mid-sentence splitting
    # For each segment, if a cause-effect word appears at a non-start position,
    # split before it.
    ce_split = []
    for seg in segments:
        pos, phrase = _find_after(seg, CAUSE_EFFECT_WORDS)
        if pos is not None and pos < len(seg):
            prefix = seg[:pos].rstrip()
            suffix = seg[pos:].lstrip()
            if prefix:
                ce_split.append(prefix)
            ce_split.append(suffix)
        else:
            ce_split.append(seg)

    # Phase 4: resolve Condition words
    # Walk through segments. When a Condition word starts a segment,
    # enter "condition mode":
    #   - If the same segment contains a conjunction (like "then") after the
    #     condition clause, split the segment at that conjunction.
    #   - Otherwise, merge subsequent segments until a conjunction appears.
    result = []
    i = 0
    while i < len(ce_split):
        seg = ce_split[i]
        cond_phrase = _match_at_start(seg, CONDITION_WORDS)
        if cond_phrase:
            # This segment starts with a Condition word
            # Check if this same segment contains a conjunction after
            # the condition word itself (e.g., "if X, then Y")
            conj_pos_in_seg, conj_phrase_in_seg = _find_after(
                seg, [w for w in CONJUNCTIONS if w not in CONDITION_WORDS]
            )
            if conj_phrase_in_seg:
                # Split within this segment at the conjunction
                cond_part = seg[:conj_pos_in_seg].rstrip()
                conj_part = seg[conj_pos_in_seg:].lstrip()
                if cond_part:
                    result.append(cond_part)
                result.append(conj_part)
                i += 1
                continue

            # No conjunction in the same segment - enter merge mode
            cond_node = seg
            i += 1
            while i < len(ce_split):
                next_seg = ce_split[i]
                conj_phrase = _match_at_start(next_seg, CONJUNCTIONS)
                if conj_phrase:
                    break
                cond_node += " " + next_seg
                i += 1
            result.append(cond_node)
        else:
            result.append(seg)
            i += 1

    # Phase 5: clean up empty nodes and consecutive duplicates
    result = [r.strip() for r in result if r.strip()]
    # Remove consecutive duplicate nodes
    deduped = []
    for r in result:
        if not deduped or r != deduped[-1]:
            deduped.append(r)
    result = deduped

    # Phase 6: merge nodes without subject + predicate
    result = _merge_incomplete_nodes(result)

    # Phase 7: split multi-sentence nodes at periods when safe
    result = _split_periods_if_complete(result)
    return result


def _has_subject_predicate(text):
    """
    Simple heuristic: check if a node has a plausible subject-verb structure.
    Returns True if the node is a complete-ish statement.
    """
    t = text.strip()
    if not t:
        return False
    words = t.split()
    # Very short nodes (1-2 words) are usually incomplete fragments
    # Exception: "No.", "Yes.", "Contradiction." etc.
    if len(words) <= 2:
        t_lower = t.lower().strip(".,;:!?")
        standalone_ok = {"no", "yes", "contradiction", "done", "qed"}
        if t_lower in standalone_ok:
            return True
        return False

    # Check for common verb keywords in math proofs
    common_verbs = {
        "absorb", "absorbed", "absorbing", "absorbs", "accelerate", "accelerated", "accelerates", "accelerating", "accept", "accepted", "accepting", "accepts", "accumulate", "accumulated", "accumulates", "accumulating", "ache", "ached", "aches", "achieve", "achieved", "achieves", "achieving", "aching",
        "act", "acted", "acting", "acts", "adapt", "adapted", "adapting", "adapts", "add", "added", "adding", "adds", "adjust", "adjusted", "adjusting", "adjusts", "admire", "admired", "admires", "admiring", "admit", "admited", "admiting", "admits",
        "admitted", "admitting", "advance", "advanced", "advances", "advancing", "advise", "advised", "advises", "advising", "affirm", "affirmed", "affirming", "affirms", "afford", "afforded", "affording", "affords", "aggregate", "aggregated", "aggregates", "aggregating", "agree", "agreed",
        "agrees", "agreing", "aim", "aimed", "aiming", "aims", "align", "aligned", "aligning", "aligns", "allocate", "allocated", "allocates", "allocating", "allow", "allowed", "allowing", "allows", "alter", "altered", "altering", "alterred", "alterring", "alters",
        "am", "amplified", "amplifies", "amplify", "analyze", "analyzed", "analyzes", "analyzing", "announce", "announced", "announces", "announcing", "answer", "answered", "answering", "answerred", "answerring", "answers", "apologise", "apologised", "apologises", "apologising", "appear", "appeared",
        "appearing", "appears", "append", "appended", "appending", "appends", "applaud", "applauded", "applauding", "applauds", "applied", "applies", "apply", "appreciate", "appreciated", "appreciates", "appreciating", "approve", "approved", "approves", "approving", "approximate", "approximated", "approximates",
        "approximating", "are", "argue", "argued", "argues", "arguing", "arise", "arisen", "arose", "arrange", "arranged", "arranges", "arranging", "arrive", "arrived", "arrives", "arriving", "ask", "asked", "asking", "asks", "assert", "asserted", "asserting",
        "asserts", "assess", "assessed", "assesses", "assessing", "assign", "assigned", "assigning", "assigns", "associate", "associated", "associates", "associating", "assume", "assumed", "assumes", "assuming", "ate", "attempt", "attempted", "attempting", "attempts", "attend", "attended",
        "attending", "attends", "attract", "attracted", "attracting", "attracts", "augment", "augmented", "augmenting", "augments", "average", "averaged", "averages", "averaging", "avoid", "avoided", "avoiding", "avoids", "bake", "baked", "bakes", "baking", "balance", "balanced",
        "balances", "balancing", "bang", "banged", "banging", "bangs", "bark", "barked", "barking", "barks", "base", "based", "bases", "basing", "bat", "bated", "bathe", "bathed", "bathes", "bathing", "bating", "bats", "batted", "batting",
        "battle", "battled", "battles", "battling", "be", "beam", "beamed", "beaming", "beams", "bear", "beat", "beaten", "became", "become", "been", "beg", "began", "beged", "begged", "begging", "begin", "beging", "begs", "begun",
        "behave", "behaved", "behaves", "behaving", "being", "belong", "belonged", "belonging", "belongs", "bend", "bended", "bending", "bends", "bent", "bet", "beted", "beting", "bets", "betted", "betting", "bind", "binded", "binding", "binds",
        "bit", "bite", "bited", "bites", "biting", "bitten", "bled", "bleed", "bleeded", "bleeding", "bleeds", "bless", "blessed", "blesses", "blessing", "blew", "blind", "blinded", "blinding", "blinds", "blink", "blinked", "blinking", "blinks",
        "block", "blocked", "blocking", "blocks", "blow", "blown", "blush", "blushed", "blushes", "blushing", "boast", "boasted", "boasting", "boasts", "boil", "boiled", "boiling", "boils", "bore", "born", "borrow", "borrowed", "borrowing", "borrows",
        "bought", "bounce", "bounced", "bounces", "bouncing", "bound", "bounded", "bounding", "bounds", "bow", "bowed", "bowing", "bows", "bracket", "bracketed", "bracketing", "brackets", "bracketted", "bracketting", "brake", "braked", "brakes", "braking", "branch",
        "branched", "branches", "branching", "break", "breaked", "breaking", "breaks", "breathe", "breathed", "breathes", "breathing", "bred", "breed", "breeded", "breeding", "breeds", "bring", "bringed", "bringing", "brings", "broadcast", "broadcasted", "broadcasting", "broadcasts",
        "broke", "broken", "brought", "brush", "brushed", "brushes", "brushing", "build", "builded", "building", "builds", "built", "bump", "bumped", "bumping", "bumps", "buried", "buries", "burn", "burned", "burning", "burns", "burnt", "burst",
        "bursted", "bursting", "bursts", "bury", "buy", "buzz", "buzzed", "buzzes", "buzzing", "calculate", "calculated", "calculates", "calculating", "call", "called", "calling", "calls", "came", "camp", "camped", "camping", "camps", "cancel", "canceled",
        "canceling", "cancelled", "cancelling", "cancels", "capture", "captured", "captures", "capturing", "care", "cared", "cares", "caring", "carried", "carries", "carry", "carve", "carved", "carves", "carving", "cash", "cashed", "cashes", "cashing", "cast",
        "casted", "casting", "casts", "catalogue", "catalogued", "catalogues", "cataloguing", "catch", "catched", "catches", "catching", "categorize", "categorized", "categorizes", "categorizing", "caught", "cause", "caused", "causes", "causing", "celebrate", "celebrated", "celebrates", "celebrating",
        "centre", "centred", "centres", "centring", "chain", "chained", "chaining", "chains", "challenge", "challenged", "challenges", "challenging", "change", "changed", "changes", "changing", "characterize", "characterized", "characterizes", "characterizing", "charge", "charged", "charges", "charging",
        "chase", "chased", "chases", "chasing", "cheat", "cheated", "cheating", "cheats", "check", "checked", "checking", "checks", "cheer", "cheered", "cheering", "cheers", "chew", "chewed", "chewing", "chews", "choose", "choosed", "chooses", "choosing",
        "chop", "choped", "choping", "chopped", "chopping", "chops", "chose", "chosen", "circle", "circled", "circles", "circling", "claim", "claimed", "claiming", "claims", "clap", "claped", "claping", "clapped", "clapping", "claps", "classified", "classifies",
        "classify", "clean", "cleaned", "cleaning", "cleans", "climb", "climbed", "climbing", "climbs", "cling", "clinged", "clinging", "clings", "clip", "cliped", "cliping", "clipped", "clipping", "clips", "close", "closed", "closes", "closing", "clung",
        "coach", "coached", "coaches", "coaching", "coast", "coasted", "coasting", "coasts", "cohere", "cohered", "coheres", "cohering", "coil", "coiled", "coiling", "coils", "collect", "collected", "collecting", "collects", "colour", "coloured", "colouring", "colours",
        "comb", "combed", "combine", "combined", "combines", "combing", "combining", "combs", "come", "command", "commanded", "commanding", "commands", "comment", "commented", "commenting", "comments", "communicate", "communicated", "communicates", "communicating", "commute", "commuted", "commutes",
        "commuting", "compare", "compared", "compares", "comparing", "compel", "compeled", "compeling", "compelled", "compelling", "compels", "compete", "competed", "competes", "competing", "complain", "complained", "complaining", "complains", "complement", "complemented", "complementing", "complements", "complete",
        "completed", "completes", "completing", "compose", "composed", "composes", "composing", "compound", "compounded", "compounding", "compounds", "compute", "computed", "computes", "computing", "concatenate", "concatenated", "concatenates", "concatenating", "concentrate", "concentrated", "concentrates", "concentrating", "conclude",
        "concluded", "concludes", "concluding", "concur", "concured", "concuring", "concurred", "concurring", "concurs", "conduct", "conducted", "conducting", "conducts", "confess", "confessed", "confesses", "confessing", "confirm", "confirmed", "confirming", "confirms", "conflate", "conflated", "conflates",
        "conflating", "conform", "conformed", "conforming", "conforms", "confuse", "confused", "confuses", "confusing", "conjoin", "conjoined", "conjoining", "conjoins", "connect", "connected", "connecting", "connects", "consent", "consented", "consenting", "consents", "conserve", "conserved", "conserves",
        "conserving", "consider", "considered", "considering", "considerred", "considerring", "considers", "consist", "consisted", "consisting", "consists", "consolidate", "consolidated", "consolidates", "consolidating", "constitute", "constituted", "constitutes", "constituting", "constrain", "constrained", "constraining", "constrains", "construct",
        "constructed", "constructing", "constructs", "contain", "contained", "containing", "contains", "contend", "contended", "contending", "contends", "continue", "continued", "continues", "continuing", "contract", "contracted", "contracting", "contracts", "contradict", "contradicted", "contradicting", "contradicts", "contrast",
        "contrasted", "contrasting", "contrasts", "contribute", "contributed", "contributes", "contributing", "converge", "converged", "converges", "converging", "converse", "conversed", "converses", "conversing", "convert", "converted", "converting", "converts", "convey", "conveyed", "conveying", "conveys", "cook",
        "cooked", "cooking", "cooks", "cool", "cooled", "cooling", "cools", "coordinate", "coordinated", "coordinates", "coordinating", "cope", "coped", "copes", "copied", "copies", "coping", "copy", "correct", "corrected", "correcting", "corrects", "correlate", "correlated",
        "correlates", "correlating", "correspond", "corresponded", "corresponding", "corresponds", "cost", "costing", "costs", "cough", "coughed", "coughing", "coughs", "count", "counted", "counting", "counts", "cover", "covered", "covering", "coverred", "coverring", "covers", "crack",
        "cracked", "cracking", "cracks", "crash", "crashed", "crashes", "crashing", "crawl", "crawled", "crawling", "crawls", "create", "created", "creates", "creating", "creep", "creeped", "creeping", "creeps", "crept", "cried", "cries", "cross", "crossed",
        "crosses", "crossing", "cry", "cumulate", "cumulated", "cumulates", "cumulating", "cure", "cured", "cures", "curing", "curl", "curled", "curling", "curls", "curse", "cursed", "curses", "cursing", "curve", "curved", "curves", "curving", "customize",
        "customized", "customizes", "customizing", "cut", "cuted", "cuting", "cuts", "cutted", "cutting", "cycle", "cycled", "cycles", "cycling", "damage", "damaged", "damages", "damaging", "dance", "danced", "dances", "dancing", "dare", "dared", "dares",
        "daring", "deal", "dealed", "dealing", "deals", "dealt", "debate", "debated", "debates", "debating", "debug", "debuged", "debugged", "debugging", "debuging", "debugs", "decay", "decayed", "decaying", "decays", "deceive", "deceived", "deceives", "deceiving",
        "decide", "decided", "decides", "deciding", "declare", "declared", "declares", "declaring", "decompose", "decomposed", "decomposes", "decomposing", "decorate", "decorated", "decorates", "decorating", "decrease", "decreased", "decreases", "decreasing", "deduce", "deduced", "deduces", "deducing",
        "defied", "defies", "define", "defined", "defines", "defining", "defy", "delay", "delayed", "delaying", "delays", "delegate", "delegated", "delegates", "delegating", "delete", "deleted", "deletes", "deleting", "delight", "delighted", "delighting", "delights", "delineate",
        "delineated", "delineates", "delineating", "deliver", "delivered", "delivering", "deliverred", "deliverring", "delivers", "demand", "demanded", "demanding", "demands", "demonstrate", "demonstrated", "demonstrates", "demonstrating", "denied", "denies", "denote", "denoted", "denotes", "denoting", "deny",
        "depart", "departed", "departing", "departs", "depend", "depended", "depending", "depends", "depict", "depicted", "depicting", "depicts", "deposit", "deposited", "depositing", "deposits", "depositted", "depositting", "derive", "derived", "derives", "deriving", "descend", "descended",
        "descending", "descends", "describe", "described", "describes", "describing", "desert", "deserted", "deserting", "deserts", "deserve", "deserved", "deserves", "deserving", "designate", "designated", "designates", "designating", "destroy", "destroyed", "destroying", "destroys", "detach", "detached",
        "detaches", "detaching", "detail", "detailed", "detailing", "details", "detect", "detected", "detecting", "detects", "determine", "determined", "determines", "determining", "develop", "developed", "developing", "developped", "developping", "develops", "deviate", "deviated", "deviates", "deviating",
        "devise", "devised", "devises", "devising", "diagnose", "diagnosed", "diagnoses", "diagnosing", "dictate", "dictated", "dictates", "dictating", "did", "differ", "differed", "differentiate", "differentiated", "differentiates", "differentiating", "differing", "differred", "differring", "differs", "dig",
        "diminish", "diminished", "diminishes", "diminishing", "direct", "directed", "directing", "directs", "disagree", "disagreed", "disagrees", "disagreing", "disappear", "disappeared", "disappearing", "disappears", "disapprove", "disapproved", "disapproves", "disapproving", "disclose", "disclosed", "discloses", "disclosing",
        "disconnect", "disconnected", "disconnecting", "disconnects", "discover", "discovered", "discovering", "discoverred", "discoverring", "discovers", "discriminate", "discriminated", "discriminates", "discriminating", "discuss", "discussed", "discusses", "discussing", "dish", "dished", "dishes", "dishing", "disjoint", "disjointed",
        "disjointing", "disjoints", "dismiss", "dismissed", "dismisses", "dismissing", "disobey", "disobeyed", "disobeying", "disobeys", "dispatch", "dispatched", "dispatches", "dispatching", "display", "displayed", "displaying", "displays", "disprove", "disproved", "disproves", "disproving", "dispute", "disputed",
        "disputes", "disputing", "dissect", "dissected", "dissecting", "dissects", "dissociate", "dissociated", "dissociates", "dissociating", "distinguish", "distinguished", "distinguishes", "distinguishing", "distribute", "distributed", "distributes", "distributing", "disturb", "disturbed", "disturbing", "disturbs", "dive", "dived",
        "diverge", "diverged", "diverges", "diverging", "dives", "divide", "divided", "divides", "dividing", "diving", "do", "document", "documented", "documenting", "documents", "done", "double", "doubled", "doubles", "doubling", "doubt", "doubted", "doubting", "doubts",
        "draft", "drafted", "drafting", "drafts", "drag", "draged", "dragged", "dragging", "draging", "drags", "drain", "drained", "draining", "drains", "drank", "draw", "drawed", "drawing", "drawn", "draws", "dream", "dreamed", "dreaming", "dreams",
        "dreamt", "dress", "dressed", "dresses", "dressing", "drew", "dried", "dries", "drink", "drip", "driped", "driping", "dripped", "dripping", "drips", "drive", "driven", "drop", "droped", "droping", "dropped", "dropping", "drops", "drove",
        "drown", "drowned", "drowning", "drowns", "drum", "drumed", "druming", "drummed", "drumming", "drums", "drunk", "dry", "dug", "duplicate", "duplicated", "duplicates", "duplicating", "dust", "dusted", "dusting", "dusts", "earn", "earned", "earning",
        "earns", "ease", "eased", "eases", "easing", "eat", "eaten", "edit", "edited", "editing", "edits", "editted", "editting", "educate", "educated", "educates", "educating", "effect", "effected", "effecting", "effects", "elicit", "elicited", "eliciting",
        "elicits", "elicitted", "elicitting", "eliminate", "eliminated", "eliminates", "eliminating", "embarrass", "embarrassed", "embarrasses", "embarrassing", "embed", "embedded", "embedding", "embeded", "embeding", "embeds", "embodied", "embodies", "embody", "emphasize", "emphasized", "emphasizes", "emphasizing",
        "employ", "employed", "employing", "employs", "emptied", "empties", "empty", "enable", "enabled", "enables", "enabling", "enclose", "enclosed", "encloses", "enclosing", "encompass", "encompassed", "encompasses", "encompassing", "encounter", "encountered", "encountering", "encounterred", "encounterring",
        "encounters", "encourage", "encouraged", "encourages", "encouraging", "end", "ended", "ending", "endorse", "endorsed", "endorses", "endorsing", "ends", "enforce", "enforced", "enforces", "enforcing", "engage", "engaged", "engages", "engaging", "engineer", "engineered", "engineering",
        "engineers", "enhance", "enhanced", "enhances", "enhancing", "enjoy", "enjoyed", "enjoying", "enjoys", "enlarge", "enlarged", "enlarges", "enlarging", "enter", "entered", "entering", "enterred", "enterring", "enters", "entertain", "entertained", "entertaining", "entertains", "enumerate",
        "enumerated", "enumerates", "enumerating", "equal", "equaled", "equaling", "equals", "equate", "equated", "equates", "equating", "escape", "escaped", "escapes", "escaping", "establish", "established", "establishes", "establishing", "estimate", "estimated", "estimates", "estimating", "evaluate",
        "evaluated", "evaluates", "evaluating", "evolve", "evolved", "evolves", "evolving", "examine", "examined", "examines", "examining", "exceed", "exceeded", "exceeding", "exceeds", "exchange", "exchanged", "exchanges", "exchanging", "excite", "excited", "excites", "exciting", "exclude",
        "excluded", "excludes", "excluding", "excuse", "excused", "excuses", "excusing", "execute", "executed", "executes", "executing", "exemplified", "exemplifies", "exemplify", "exercise", "exercised", "exercises", "exercising", "exhaust", "exhausted", "exhausting", "exhausts", "exhibit", "exhibited",
        "exhibiting", "exhibits", "exhibitted", "exhibitting", "exist", "existed", "existing", "exists", "expand", "expanded", "expanding", "expands", "expect", "expected", "expecting", "expects", "expedite", "expedited", "expedites", "expediting", "experiment", "experimented", "experimenting", "experiments",
        "explain", "explained", "explaining", "explains", "explode", "exploded", "explodes", "exploding", "exploit", "exploited", "exploiting", "exploits", "explore", "explored", "explores", "exploring", "exponentiate", "exponentiated", "exponentiates", "exponentiating", "export", "exported", "exporting", "exports",
        "expose", "exposed", "exposes", "exposing", "extend", "extended", "extending", "extends", "extract", "extracted", "extracting", "extracts", "extrapolate", "extrapolated", "extrapolates", "extrapolating", "fabricate", "fabricated", "fabricates", "fabricating", "facilitate", "facilitated", "facilitates", "facilitating",
        "factor", "factored", "factoring", "factorred", "factorring", "factors", "fade", "faded", "fades", "fading", "fail", "failed", "failing", "fails", "faint", "fainted", "fainting", "faints", "fall", "fallen", "fancied", "fancies", "fancy", "fasten",
        "fastened", "fastening", "fastenned", "fastenning", "fastens", "favour", "favoured", "favouring", "favours", "fax", "faxed", "faxes", "faxing", "fear", "feared", "fearing", "fears", "fed", "feed", "feeded", "feeding", "feeds", "feel", "feeled",
        "feeling", "feels", "fell", "felt", "fence", "fenced", "fences", "fencing", "fetch", "fetched", "fetches", "fetching", "fight", "fighted", "fighting", "fights", "figure", "figured", "figures", "figuring", "file", "filed", "files", "filing",
        "fill", "filled", "filling", "fills", "film", "filmed", "filming", "films", "filter", "filtered", "filtering", "filterred", "filterring", "filters", "finalize", "finalized", "finalizes", "finalizing", "find", "finded", "finding", "finds", "finish", "finished",
        "finishes", "finishing", "fire", "fired", "fires", "firing", "fit", "fited", "fiting", "fits", "fitted", "fitting", "fix", "fixed", "fixes", "fixing", "flap", "flaped", "flaping", "flapped", "flapping", "flaps", "flash", "flashed",
        "flashes", "flashing", "flatten", "flattened", "flattening", "flattenned", "flattenning", "flattens", "fled", "flee", "flew", "fling", "float", "floated", "floating", "floats", "flood", "flooded", "flooding", "floods", "flow", "flowed", "flowing", "flown",
        "flows", "flung", "flutter", "fluttered", "fluttering", "flutterred", "flutterring", "flutters", "fly", "focus", "focused", "focusing", "focuss", "focussed", "focussing", "fold", "folded", "folding", "folds", "follow", "followed", "following", "follows", "fool",
        "fooled", "fooling", "fools", "forbade", "forbid", "forbidded", "forbidden", "forbidding", "forbided", "forbiding", "forbids", "force", "forced", "forces", "forcing", "forecast", "forecasted", "forecasting", "forecasts", "foretell", "foretelled", "foretelling", "foretells", "forgave",
        "forget", "forgive", "forgived", "forgiven", "forgives", "forgiving", "forgot", "forgotten", "form", "formalize", "formalized", "formalizes", "formalizing", "formed", "forming", "forms", "formulate", "formulated", "formulates", "formulating", "fought", "found", "founded", "founding",
        "founds", "frame", "framed", "frames", "framing", "freeze", "fried", "fries", "frighten", "frightened", "frightening", "frightenned", "frightenning", "frightens", "froze", "frozen", "fry", "fulfil", "fulfiled", "fulfiling", "fulfilled", "fulfilling", "fulfils", "function",
        "functioned", "functioning", "functions", "fuse", "fused", "fuses", "fusing", "gain", "gained", "gaining", "gains", "gather", "gathered", "gathering", "gatherred", "gatherring", "gathers", "gauge", "gauged", "gauges", "gauging", "gave", "gaze", "gazed",
        "gazes", "gazing", "generalize", "generalized", "generalizes", "generalizing", "generate", "generated", "generates", "generating", "get", "give", "given", "glow", "glowed", "glowing", "glows", "glue", "glued", "glues", "gluing", "go", "gone", "got",
        "gotten", "govern", "governed", "governing", "governs", "grab", "grabbed", "grabbing", "grabed", "grabing", "grabs", "grade", "graded", "grades", "grading", "grant", "granted", "granting", "grants", "graph", "graphed", "graphing", "graphs", "grasp",
        "grasped", "grasping", "grasps", "grate", "grated", "grates", "grating", "grease", "greased", "greases", "greasing", "greet", "greeted", "greeting", "greets", "grew", "grind", "grinded", "grinding", "grinds", "grip", "griped", "griping", "gripped",
        "gripping", "grips", "groan", "groaned", "groaning", "groans", "ground", "group", "grouped", "grouping", "groups", "grow", "grown", "guarantee", "guaranteed", "guarantees", "guaranteing", "guard", "guarded", "guarding", "guards", "guess", "guessed", "guesses",
        "guessing", "guide", "guided", "guides", "guiding", "had", "halt", "halted", "halting", "halts", "hammer", "hammered", "hammering", "hammerred", "hammerring", "hammers", "hand", "handed", "handing", "handle", "handled", "handles", "handling", "hands",
        "hang", "happen", "happened", "happening", "happenned", "happenning", "happens", "harm", "harmed", "harming", "harms", "harness", "harnessed", "harnesses", "harnessing", "hate", "hated", "hates", "hating", "haunt", "haunted", "haunting", "haunts", "have",
        "heal", "healed", "healing", "heals", "heap", "heaped", "heaping", "heaps", "hear", "heard", "heared", "hearing", "hears", "heat", "heated", "heating", "heats", "held", "help", "helped", "helping", "helps", "herd", "herded",
        "herding", "herds", "hesitate", "hesitated", "hesitates", "hesitating", "hid", "hidden", "hide", "hided", "hides", "hiding", "hit", "hited", "hiting", "hits", "hitted", "hitting", "hold", "holded", "holding", "holds", "hook", "hooked",
        "hooking", "hooks", "hop", "hope", "hoped", "hopes", "hoping", "hopped", "hopping", "hops", "hover", "hovered", "hovering", "hoverred", "hoverring", "hovers", "hug", "huged", "hugged", "hugging", "huging", "hugs", "hum", "humed",
        "huming", "hummed", "humming", "hums", "hung", "hunt", "hunted", "hunting", "hunts", "hurried", "hurries", "hurry", "hurt", "hurted", "hurting", "hurts", "hypothesize", "hypothesized", "hypothesizes", "hypothesizing", "identified", "identifies", "identify", "ignore",
        "ignored", "ignores", "ignoring", "illustrate", "illustrated", "illustrates", "illustrating", "imagine", "imagined", "imagines", "imagining", "immerse", "immersed", "immerses", "immersing", "implement", "implemented", "implementing", "implements", "implied", "implies", "imply", "impose", "imposed",
        "imposes", "imposing", "impress", "impressed", "impresses", "impressing", "improve", "improved", "improves", "improving", "impute", "imputed", "imputes", "imputing", "include", "included", "includes", "including", "incorporate", "incorporated", "incorporates", "incorporating", "increase", "increased",
        "increases", "increasing", "incur", "incured", "incuring", "incurred", "incurring", "incurs", "indicate", "indicated", "indicates", "indicating", "induce", "induced", "induces", "inducing", "infect", "infected", "infecting", "infects", "infer", "infered", "infering", "inferred",
        "inferring", "infers", "inform", "informed", "informing", "informs", "initiate", "initiated", "initiates", "initiating", "inject", "injected", "injecting", "injects", "injure", "injured", "injures", "injuring", "input", "inputed", "inputing", "inputs", "inputted", "inputting",
        "insert", "inserted", "inserting", "inserts", "inspect", "inspected", "inspecting", "inspects", "install", "installed", "installing", "installs", "instantiate", "instantiated", "instantiates", "instantiating", "institute", "instituted", "institutes", "instituting", "instruct", "instructed", "instructing", "instructs",
        "insulate", "insulated", "insulates", "insulating", "insure", "insured", "insures", "insuring", "integrate", "integrated", "integrates", "integrating", "intend", "intended", "intending", "intends", "intensified", "intensifies", "intensify", "interact", "interacted", "interacting", "interacts", "intercept",
        "intercepted", "intercepting", "intercepts", "interconnect", "interconnected", "interconnecting", "interconnects", "interest", "interested", "interesting", "interests", "interfere", "interfered", "interferes", "interfering", "interject", "interjected", "interjecting", "interjects", "interpret", "interpreted", "interpreting", "interprets", "interpretted",
        "interpretting", "interrupt", "interrupted", "interrupting", "interrupts", "intersect", "intersected", "intersecting", "intersects", "intervene", "intervened", "intervenes", "intervening", "introduce", "introduced", "introduces", "introducing", "invent", "invented", "inventing", "invents", "invert", "inverted", "inverting",
        "inverts", "investigate", "investigated", "investigates", "investigating", "invite", "invited", "invites", "inviting", "invoke", "invoked", "invokes", "invoking", "involve", "involved", "involves", "involving", "irritate", "irritated", "irritates", "irritating", "is", "isolate", "isolated",
        "isolates", "isolating", "issue", "issued", "issues", "issuing", "iterate", "iterated", "iterates", "iterating", "jail", "jailed", "jailing", "jails", "jam", "jamed", "jaming", "jammed", "jamming", "jams", "jog", "joged", "jogged", "jogging",
        "joging", "jogs", "join", "joined", "joining", "joins", "joke", "joked", "jokes", "joking", "judge", "judged", "judges", "judging", "juggle", "juggled", "juggles", "juggling", "jump", "jumped", "jumping", "jumps", "justified", "justifies",
        "justify", "keep", "keeped", "keeping", "keeps", "kept", "key", "keyed", "keying", "keys", "kick", "kicked", "kicking", "kicks", "kidnap", "kidnaped", "kidnaping", "kidnapped", "kidnapping", "kidnaps", "kiss", "kissed", "kisses", "kissing",
        "kneel", "kneeled", "kneeling", "kneels", "knelt", "knew", "knit", "knited", "kniting", "knits", "knitted", "knitting", "knock", "knocked", "knocking", "knocks", "know", "knowed", "knowing", "known", "knows", "label", "labeled", "labeling",
        "labelled", "labelling", "labels", "lag", "laged", "lagged", "lagging", "laging", "lags", "laid", "lain", "land", "landed", "landing", "lands", "last", "lasted", "lasting", "lasts", "laugh", "laughed", "laughing", "laughs", "launch",
        "launched", "launches", "launching", "lay", "lead", "leaded", "leading", "leads", "lean", "leant", "leap", "leapt", "learn", "learned", "learning", "learns", "leave", "leaved", "leaves", "leaving", "led", "left", "lend", "lended",
        "lending", "lends", "lengthen", "lengthened", "lengthening", "lengthenned", "lengthenning", "lengthens", "lent", "lessen", "lessened", "lessening", "lessenned", "lessenning", "lessens", "let", "leted", "leting", "lets", "letted", "letting", "level", "leveled", "leveling",
        "levelled", "levelling", "levels", "lie", "lied", "lies", "lift", "lifted", "lifting", "lifts", "light", "lighted", "lighting", "lights", "liing", "like", "liked", "likes", "liking", "limit", "limited", "limiting", "limits", "limitted",
        "limitting", "linearize", "linearized", "linearizes", "linearizing", "link", "linked", "linking", "links", "list", "listed", "listen", "listened", "listening", "listenned", "listenning", "listens", "listing", "lists", "lit", "live", "lived", "lives", "living",
        "load", "loaded", "loading", "loads", "locate", "located", "locates", "locating", "lock", "locked", "locking", "locks", "log", "loged", "logged", "logging", "loging", "logs", "long", "longed", "longing", "longs", "look", "looked",
        "looking", "looks", "loop", "looped", "looping", "loops", "loosen", "loosened", "loosening", "loosenned", "loosenning", "loosens", "lose", "lost", "love", "loved", "loves", "loving", "lower", "lowered", "lowering", "lowerred", "lowerring", "lowers",
        "lug", "luged", "lugged", "lugging", "luging", "lugs", "lump", "lumped", "lumping", "lumps", "machine", "machined", "machines", "machining", "made", "magnified", "magnifies", "magnify", "mail", "mailed", "mailing", "mails", "maintain", "maintained",
        "maintaining", "maintains", "make", "manage", "managed", "manages", "managing", "manipulate", "manipulated", "manipulates", "manipulating", "map", "maped", "maping", "mapped", "mapping", "maps", "march", "marched", "marches", "marching", "mark", "marked", "marking",
        "marks", "match", "matched", "matches", "matching", "mate", "mated", "mates", "mating", "matter", "mattered", "mattering", "matterred", "matterring", "matters", "maximize", "maximized", "maximizes", "maximizing", "mean", "meaned", "meaning", "means", "meant",
        "measure", "measured", "measures", "measuring", "meddle", "meddled", "meddles", "meddling", "meet", "melt", "melted", "melting", "melts", "memorise", "memorised", "memorises", "memorising", "mend", "mended", "mending", "mends", "merge", "merged", "merges",
        "merging", "mess", "messed", "messes", "messing", "met", "migrate", "migrated", "migrates", "migrating", "milk", "milked", "milking", "milks", "mine", "mined", "mines", "minified", "minifies", "minify", "minimize", "minimized", "minimizes", "minimizing",
        "mining", "mirror", "mirrored", "mirroring", "mirrorred", "mirrorring", "mirrors", "miss", "missed", "misses", "missing", "mix", "mixed", "mixes", "mixing", "moan", "moaned", "moaning", "moans", "model", "modeled", "modeling", "modelled", "modelling",
        "models", "modified", "modifies", "modify", "modulate", "modulated", "modulates", "modulating", "monitor", "monitored", "monitoring", "monitorred", "monitorring", "monitors", "moor", "moored", "mooring", "moors", "motivate", "motivated", "motivates", "motivating", "mourn", "mourned",
        "mourning", "mourns", "move", "moved", "moves", "moving", "muddle", "muddled", "muddles", "muddling", "mug", "muged", "mugged", "mugging", "muging", "mugs", "multiplied", "multiplies", "multiply", "murder", "murdered", "murdering", "murderred", "murderring",
        "murders", "nail", "nailed", "nailing", "nails", "name", "named", "names", "naming", "navigate", "navigated", "navigates", "navigating", "need", "needed", "needing", "needs", "negate", "negated", "negates", "negating", "nest", "nested", "nesting",
        "nests", "nod", "nodded", "nodding", "noded", "noding", "nods", "normalize", "normalized", "normalizes", "normalizing", "note", "noted", "notes", "notice", "noticed", "notices", "noticing", "notified", "notifies", "notify", "noting", "number", "numbered",
        "numbering", "numberred", "numberring", "numbers", "obey", "obeyed", "obeying", "obeys", "object", "objected", "objecting", "objects", "observe", "observed", "observes", "observing", "obtain", "obtained", "obtaining", "obtains", "occupied", "occupies", "occupy", "occur",
        "occured", "occuring", "occurred", "occurring", "occurs", "offend", "offended", "offending", "offends", "offer", "offered", "offering", "offerred", "offerring", "offers", "ogle", "ogled", "ogles", "ogling", "oil", "oiled", "oiling", "oils", "omit",
        "omited", "omiting", "omits", "omitted", "omitting", "open", "opened", "opening", "openned", "openning", "opens", "operate", "operated", "operates", "operating", "oppose", "opposed", "opposes", "opposing", "optimize", "optimized", "optimizes", "optimizing", "order",
        "ordered", "ordering", "orderred", "orderring", "orders", "organize", "organized", "organizes", "organizing", "orient", "oriented", "orienting", "orients", "originate", "originated", "originates", "originating", "output", "outputed", "outputing", "outputs", "outputted", "outputting", "overcome",
        "overcomed", "overcomes", "overcoming", "overflow", "overflowed", "overflowing", "overflows", "overlap", "overlaped", "overlaping", "overlapped", "overlapping", "overlaps", "overload", "overloaded", "overloading", "overloads", "override", "overrided", "overrides", "overriding", "overrule", "overruled", "overrules",
        "overruling", "oversee", "overseed", "oversees", "overseing", "overturn", "overturned", "overturning", "overturns", "owe", "owed", "owes", "owing", "own", "owned", "owning", "owns", "pack", "packed", "packing", "packs", "paddle", "paddled", "paddles",
        "paddling", "paid", "paint", "painted", "painting", "paints", "pair", "paired", "pairing", "pairs", "parallel", "paralleled", "paralleling", "parallelled", "parallelling", "parallels", "parameterize", "parameterized", "parameterizes", "parameterizing", "park", "parked", "parking", "parks",
        "part", "parted", "participate", "participated", "participates", "participating", "parting", "partition", "partitioned", "partitioning", "partitions", "parts", "pass", "passed", "passes", "passing", "paste", "pasted", "pastes", "pasting", "pat", "pated", "pating", "pats",
        "patted", "pattern", "patterned", "patterning", "patterns", "patting", "pause", "paused", "pauses", "pausing", "pay", "peck", "pecked", "pecking", "pecks", "pedal", "pedaled", "pedaling", "pedalled", "pedalling", "pedals", "peel", "peeled", "peeling",
        "peels", "peep", "peeped", "peeping", "peeps", "penalize", "penalized", "penalizes", "penalizing", "perform", "performed", "performing", "performs", "permit", "permited", "permiting", "permits", "permitted", "permitting", "pertain", "pertained", "pertaining", "pertains", "phone",
        "phoned", "phones", "phoning", "pick", "picked", "picking", "picks", "pile", "piled", "piles", "piling", "pin", "pinch", "pinched", "pinches", "pinching", "pine", "pined", "pines", "pining", "pinned", "pinning", "pins", "pioneer",
        "pioneered", "pioneering", "pioneers", "place", "placed", "places", "placing", "plan", "planed", "planing", "planned", "planning", "plans", "plant", "planted", "planting", "plants", "play", "played", "playing", "plays", "plead", "pleaded", "pleading",
        "pleads", "please", "pleased", "pleases", "pleasing", "plot", "ploted", "ploting", "plots", "plotted", "plotting", "plug", "pluged", "plugged", "plugging", "pluging", "plugs", "point", "pointed", "pointing", "points", "poke", "poked", "pokes",
        "poking", "polish", "polished", "polishes", "polishing", "pop", "poped", "poping", "popped", "popping", "pops", "populate", "populated", "populates", "populating", "pose", "posed", "poses", "posing", "position", "positioned", "positioning", "positions", "possess",
        "possessed", "possesses", "possessing", "post", "posted", "posting", "postpose", "postposed", "postposes", "postposing", "posts", "pour", "poured", "pouring", "pours", "practise", "practised", "practises", "practising", "pray", "prayed", "praying", "prays", "preach",
        "preached", "preaches", "preaching", "precede", "preceded", "precedes", "preceding", "predict", "predicted", "predicting", "predicts", "preface", "prefaced", "prefaces", "prefacing", "prefer", "prefered", "prefering", "preferred", "preferring", "prefers", "prepare", "prepared", "prepares",
        "preparing", "prescribe", "prescribed", "prescribes", "prescribing", "present", "presented", "presenting", "presents", "preserve", "preserved", "preserves", "preserving", "press", "pressed", "presses", "pressing", "pretend", "pretended", "pretending", "pretends", "prevent", "prevented", "preventing",
        "prevents", "prick", "pricked", "pricking", "pricks", "prime", "primed", "primes", "priming", "print", "printed", "printing", "prints", "prioritize", "prioritized", "prioritizes", "prioritizing", "probe", "probed", "probes", "probing", "proceed", "proceeded", "proceeding",
        "proceeds", "process", "processed", "processes", "processing", "produce", "produced", "produces", "producing", "program", "programed", "programing", "programmed", "programming", "programs", "progress", "progressed", "progresses", "progressing", "project", "projected", "projecting", "projects", "prolong",
        "prolonged", "prolonging", "prolongs", "promise", "promised", "promises", "promising", "prompt", "prompted", "prompting", "prompts", "propagate", "propagated", "propagates", "propagating", "propose", "proposed", "proposes", "proposing", "protect", "protected", "protecting", "protects", "prove",
        "proved", "proven", "proves", "provide", "provided", "provides", "providing", "proving", "prune", "pruned", "prunes", "pruning", "pull", "pulled", "pulling", "pulls", "pump", "pumped", "pumping", "pumps", "punch", "punched", "punches", "punching",
        "puncture", "punctured", "punctures", "puncturing", "punish", "punished", "punishes", "punishing", "purchase", "purchased", "purchases", "purchasing", "pursue", "pursued", "pursues", "pursuing", "push", "pushed", "pushes", "pushing", "put", "puted", "puting", "puts",
        "putted", "putting", "quantified", "quantifies", "quantify", "question", "questioned", "questioning", "questions", "queue", "queued", "queues", "queuing", "quit", "quote", "quoted", "quotes", "quoting", "race", "raced", "races", "racing", "radiate", "radiated",
        "radiates", "radiating", "rain", "rained", "raining", "rains", "raise", "raised", "raises", "raising", "ran", "randomize", "randomized", "randomizes", "randomizing", "rang", "range", "ranged", "ranges", "ranging", "rank", "ranked", "ranking", "ranks",
        "rate", "rated", "rates", "rating", "reach", "reached", "reaches", "reaching", "read", "realise", "realised", "realises", "realising", "realize", "realized", "realizes", "realizing", "reason", "reasoned", "reasoning", "reasonned", "reasonning", "reasons", "reassign",
        "reassigned", "reassigning", "reassigns", "recall", "recalled", "recalling", "recalls", "receive", "received", "receives", "receiving", "recognise", "recognised", "recognises", "recognising", "recognize", "recognized", "recognizes", "recognizing", "recommend", "recommended", "recommending", "recommends", "reconcile",
        "reconciled", "reconciles", "reconciling", "record", "recorded", "recording", "records", "recover", "recovered", "recovering", "recoverred", "recoverring", "recovers", "rectified", "rectifies", "rectify", "recycle", "recycled", "recycles", "recycling", "reduce", "reduced", "reduces", "reducing",
        "reestablish", "reestablished", "reestablishes", "reestablishing", "refer", "refered", "refering", "referred", "referring", "refers", "reflect", "reflected", "reflecting", "reflects", "reform", "reformed", "reforming", "reforms", "refresh", "refreshed", "refreshes", "refreshing", "refuse", "refused",
        "refuses", "refusing", "refute", "refuted", "refutes", "refuting", "regard", "regarded", "regarding", "regards", "register", "registered", "registering", "registerred", "registerring", "registers", "regress", "regressed", "regresses", "regressing", "regret", "regreted", "regreting", "regrets",
        "regretted", "regretting", "regulate", "regulated", "regulates", "regulating", "rehearse", "rehearsed", "rehearses", "rehearsing", "reign", "reigned", "reigning", "reigns", "reject", "rejected", "rejecting", "rejects", "rejoice", "rejoiced", "rejoices", "rejoicing", "relate", "related",
        "relates", "relating", "release", "released", "releases", "releasing", "relied", "relies", "rely", "remain", "remained", "remaining", "remains", "remark", "remarked", "remarking", "remarks", "remember", "remembered", "remembering", "rememberred", "rememberring", "remembers", "remind",
        "reminded", "reminding", "reminds", "remove", "removed", "removes", "removing", "rename", "renamed", "renames", "renaming", "reorder", "reordered", "reordering", "reorderred", "reorderring", "reorders", "reorganize", "reorganized", "reorganizes", "reorganizing", "repair", "repaired", "repairing",
        "repairs", "repeat", "repeated", "repeating", "repeats", "replace", "replaced", "replaces", "replacing", "replicate", "replicated", "replicates", "replicating", "replied", "replies", "reply", "report", "reported", "reporting", "reports", "represent", "represented", "representing", "represents",
        "reproduce", "reproduced", "reproduces", "reproducing", "request", "requested", "requesting", "requests", "require", "required", "requires", "requiring", "rescue", "rescued", "rescues", "rescuing", "reselect", "reselected", "reselecting", "reselects", "resemble", "resembled", "resembles", "resembling",
        "resent", "resented", "resenting", "resents", "reserve", "reserved", "reserves", "reserving", "reset", "reseted", "reseting", "resets", "resetted", "resetting", "reshape", "reshaped", "reshapes", "reshaping", "reside", "resided", "resides", "residing", "resolve", "resolved",
        "resolves", "resolving", "resort", "resorted", "resorting", "resorts", "respect", "respected", "respecting", "respects", "rest", "rested", "resting", "restore", "restored", "restores", "restoring", "restrain", "restrained", "restraining", "restrains", "restrict", "restricted", "restricting",
        "restricts", "restructure", "restructured", "restructures", "restructuring", "rests", "result", "resulted", "resulting", "results", "retain", "retained", "retaining", "retains", "retire", "retired", "retires", "retiring", "retrieve", "retrieved", "retrieves", "retrieving", "return", "returned",
        "returning", "returns", "reuse", "reused", "reuses", "reusing", "reveal", "revealed", "revealing", "reveals", "reverse", "reversed", "reverses", "reversing", "review", "reviewed", "reviewing", "reviews", "revise", "revised", "revises", "revising", "revolve", "revolved",
        "revolves", "revolving", "reward", "rewarded", "rewarding", "rewards", "rewrite", "rewrited", "rewrites", "rewriting", "rhyme", "rhymed", "rhymes", "rhyming", "rid", "ridded", "ridden", "ridding", "ride", "rided", "rides", "riding", "rids", "ring",
        "ringed", "ringing", "rings", "rinse", "rinsed", "rinses", "rinsing", "rise", "rised", "risen", "rises", "rising", "risk", "risked", "risking", "risks", "rob", "robbed", "robbing", "robed", "robing", "robs", "rock", "rocked",
        "rocking", "rocks", "rode", "roll", "rolled", "rolling", "rolls", "rose", "rot", "roted", "roting", "rots", "rotted", "rotting", "rub", "rubbed", "rubbing", "rubed", "rubing", "rubs", "ruin", "ruined", "ruining", "ruins",
        "rule", "ruled", "rules", "ruling", "run", "rung", "rush", "rushed", "rushes", "rushing", "sack", "sacked", "sacking", "sacks", "said", "sail", "sailed", "sailing", "sails", "sang", "sank", "sat", "satisfied", "satisfies",
        "satisfy", "save", "saved", "saves", "saving", "saw", "sawed", "sawing", "saws", "say", "scale", "scaled", "scales", "scaling", "scare", "scared", "scares", "scaring", "scatter", "scattered", "scattering", "scatterred", "scatterring", "scatters",
        "schedule", "scheduled", "schedules", "scheduling", "scold", "scolded", "scolding", "scolds", "scorch", "scorched", "scorches", "scorching", "score", "scored", "scores", "scoring", "scrape", "scraped", "scrapes", "scraping", "scratch", "scratched", "scratches", "scratching",
        "scream", "screamed", "screaming", "screams", "screen", "screened", "screening", "screens", "screw", "screwed", "screwing", "screws", "scribble", "scribbled", "scribbles", "scribbling", "scrub", "scrubbed", "scrubbing", "scrubed", "scrubing", "scrubs", "seal", "sealed",
        "sealing", "seals", "search", "searched", "searches", "searching", "section", "sectioned", "sectioning", "sections", "secure", "secured", "secures", "securing", "see", "seek", "seen", "segment", "segmented", "segmenting", "segments", "select", "selected", "selecting",
        "selects", "sell", "send", "sended", "sending", "sends", "sense", "sensed", "senses", "sensing", "sent", "separate", "separated", "separates", "separating", "sequence", "sequenced", "sequences", "sequencing", "serialize", "serialized", "serializes", "serializing", "serve",
        "served", "serves", "serving", "set", "seted", "seting", "sets", "setted", "setting", "settle", "settled", "settles", "settling", "sever", "severed", "severing", "severred", "severring", "severs", "sew", "sewed", "sewn", "shade", "shaded",
        "shades", "shading", "shake", "shaked", "shaken", "shakes", "shaking", "shame", "shamed", "shames", "shaming", "shape", "shaped", "shapes", "shaping", "share", "shared", "shares", "sharing", "sharpen", "sharpened", "sharpening", "sharpenned", "sharpenning",
        "sharpens", "shave", "shaved", "shaven", "shaves", "shaving", "shear", "sheared", "shed", "shelter", "sheltered", "sheltering", "shelterred", "shelterring", "shelters", "shift", "shifted", "shifting", "shifts", "shine", "shined", "shines", "shining", "shiver",
        "shivered", "shivering", "shiverred", "shiverring", "shivers", "shock", "shocked", "shocking", "shocks", "shone", "shook", "shoot", "shop", "shoped", "shoping", "shopped", "shopping", "shops", "shorn", "shot", "show", "showed", "showing", "shown",
        "shows", "shrank", "shrink", "shrinked", "shrinking", "shrinks", "shrug", "shruged", "shrugged", "shrugging", "shruging", "shrugs", "shrunk", "shut", "shuted", "shuting", "shuts", "shutted", "shutting", "sieve", "sieved", "sieves", "sieving", "sigh",
        "sighed", "sighing", "sighs", "sign", "signal", "signaled", "signaling", "signalled", "signalling", "signals", "signed", "signified", "signifies", "signify", "signing", "signs", "simplified", "simplifies", "simplify", "simulate", "simulated", "simulates", "simulating", "sin",
        "sined", "sing", "sining", "sink", "sinned", "sinning", "sins", "sip", "siped", "siping", "sipped", "sipping", "sips", "sit", "situate", "situated", "situates", "situating", "sketch", "sketched", "sketches", "sketching", "ski", "skied",
        "skiing", "skip", "skiped", "skiping", "skipped", "skipping", "skips", "skis", "slap", "slaped", "slaping", "slapped", "slapping", "slaps", "slave", "slaved", "slaves", "slaving", "sleep", "sleeped", "sleeping", "sleeps", "slept", "slid",
        "slide", "slided", "slides", "sliding", "slip", "sliped", "sliping", "slipped", "slipping", "slips", "slit", "slited", "sliting", "slits", "slitted", "slitting", "smash", "smashed", "smashes", "smashing", "smell", "smelled", "smelling", "smells",
        "smile", "smiled", "smiles", "smiling", "smoke", "smoked", "smokes", "smoking", "snap", "snaped", "snaping", "snapped", "snapping", "snaps", "snatch", "snatched", "snatches", "snatching", "sneeze", "sneezed", "sneezes", "sneezing", "sniff", "sniffed",
        "sniffing", "sniffs", "snore", "snored", "snores", "snoring", "snow", "snowed", "snowing", "snows", "soak", "soaked", "soaking", "soaks", "sold", "solve", "solved", "solves", "solving", "soothe", "soothed", "soothes", "soothing", "sort",
        "sorted", "sorting", "sorts", "sought", "sound", "sounded", "sounding", "sounds", "span", "spaned", "spaning", "spanned", "spanning", "spans", "spare", "spared", "spares", "sparing", "spark", "sparked", "sparking", "sparkle", "sparkled", "sparkles",
        "sparkling", "sparks", "spat", "speak", "speaked", "speaking", "speaks", "specified", "specifies", "specify", "sped", "speed", "spell", "spelled", "spelling", "spells", "spend", "spended", "spending", "spends", "spent", "spill", "spilled", "spilling",
        "spills", "spin", "spined", "spining", "spinned", "spinning", "spins", "spit", "spited", "spiting", "spits", "spitted", "spitting", "splash", "splashed", "splashes", "splashing", "split", "splited", "spliting", "splits", "splitted", "splitting", "spoil",
        "spoiled", "spoiling", "spoils", "spoke", "spoken", "spot", "spoted", "spoting", "spots", "spotted", "spotting", "sprang", "spray", "sprayed", "spraying", "sprays", "spread", "spreaded", "spreading", "spreads", "spring", "sprinkle", "sprinkled", "sprinkles",
        "sprinkling", "sprout", "sprouted", "sprouting", "sprouts", "sprung", "spun", "square", "squared", "squares", "squaring", "squeak", "squeaked", "squeaking", "squeaks", "squeeze", "squeezed", "squeezes", "squeezing", "stabilize", "stabilized", "stabilizes", "stabilizing", "stack",
        "stacked", "stacking", "stacks", "stain", "stained", "staining", "stains", "stamp", "stamped", "stamping", "stamps", "stand", "standardize", "standardized", "standardizes", "standardizing", "stank", "stare", "stared", "stares", "staring", "start", "started", "starting",
        "starts", "state", "stated", "states", "stating", "stay", "stayed", "staying", "stays", "steal", "steer", "steered", "steering", "steers", "stem", "stemed", "steming", "stemmed", "stemming", "stems", "step", "steped", "steping", "stepped",
        "stepping", "steps", "stick", "stimulate", "stimulated", "stimulates", "stimulating", "sting", "stink", "stipulate", "stipulated", "stipulates", "stipulating", "stir", "stired", "stiring", "stirred", "stirring", "stirs", "stitch", "stitched", "stitches", "stitching", "stole",
        "stolen", "stood", "stop", "stoped", "stoping", "stopped", "stopping", "stops", "store", "stored", "stores", "storing", "strap", "straped", "straping", "strapped", "strapping", "straps", "strengthen", "strengthened", "strengthening", "strengthenned", "strengthenning", "strengthens",
        "stretch", "stretched", "stretches", "stretching", "stridden", "stride", "strike", "striked", "strikes", "striking", "string", "strip", "striped", "striping", "stripped", "stripping", "strips", "strive", "strived", "striven", "strives", "striving", "strode", "stroke",
        "stroked", "strokes", "stroking", "strove", "struck", "structure", "structured", "structures", "structuring", "strung", "stuck", "studied", "studies", "study", "stuff", "stuffed", "stuffing", "stuffs", "stung", "stunk", "subdivide", "subdivided", "subdivides", "subdividing",
        "subject", "subjected", "subjecting", "subjects", "submit", "submited", "submiting", "submits", "submitted", "submitting", "subordinate", "subordinated", "subordinates", "subordinating", "subscribe", "subscribed", "subscribes", "subscribing", "substantiate", "substantiated", "substantiates", "substantiating", "substitute", "substituted",
        "substitutes", "substituting", "subtract", "subtracted", "subtracting", "subtracts", "succeed", "succeeded", "succeeding", "succeeds", "suck", "sucked", "sucking", "sucks", "suffer", "suffered", "suffering", "sufferred", "sufferring", "suffers", "suffice", "sufficed", "suffices", "sufficing",
        "suggest", "suggested", "suggesting", "suggests", "suit", "suited", "suiting", "suits", "sum", "sumed", "suming", "summarize", "summarized", "summarizes", "summarizing", "summed", "summing", "sums", "sung", "sunk", "supersede", "superseded", "supersedes", "superseding",
        "supervise", "supervised", "supervises", "supervising", "supplement", "supplemented", "supplementing", "supplements", "supplied", "supplies", "supply", "support", "supported", "supporting", "supports", "suppose", "supposed", "supposes", "supposing", "suppress", "suppressed", "suppresses", "suppressing", "surf",
        "surfed", "surfing", "surfs", "surmount", "surmounted", "surmounting", "surmounts", "surpass", "surpassed", "surpasses", "surpassing", "surround", "surrounded", "surrounding", "surrounds", "survey", "surveyed", "surveying", "surveys", "survive", "survived", "survives", "surviving", "suspect",
        "suspected", "suspecting", "suspects", "suspend", "suspended", "suspending", "suspends", "sustain", "sustained", "sustaining", "sustains", "swallow", "swallowed", "swallowing", "swallows", "swam", "swap", "swaped", "swaping", "swapped", "swapping", "swaps", "swear", "sweared",
        "swearing", "swears", "sweep", "sweeped", "sweeping", "sweeps", "swell", "swelled", "swelling", "swells", "swept", "swim", "swimed", "swiming", "swimmed", "swimming", "swims", "swing", "swinged", "swinging", "swings", "swirl", "swirled", "swirling",
        "swirls", "switch", "switched", "switches", "switching", "swollen", "swore", "sworn", "swum", "swung", "symbolise", "symbolised", "symbolises", "symbolising", "symbolize", "symbolized", "symbolizes", "symbolizing", "synthesize", "synthesized", "synthesizes", "synthesizing", "systematize", "systematized",
        "systematizes", "systematizing", "tailor", "tailored", "tailoring", "tailorred", "tailorring", "tailors", "take", "taked", "taken", "takes", "taking", "tallied", "tallies", "tally", "target", "targeted", "targeting", "targets", "targetted", "targetting", "task", "tasked",
        "tasking", "tasks", "taste", "tasted", "tastes", "tasting", "taught", "teach", "teached", "teaches", "teaching", "tear", "tease", "teased", "teases", "teasing", "telephone", "telephoned", "telephones", "telephoning", "tell", "temper", "tempered", "tempering",
        "temperred", "temperring", "tempers", "tempt", "tempted", "tempting", "tempts", "terrified", "terrifies", "terrify", "test", "tested", "testing", "tests", "thank", "thanked", "thanking", "thanks", "thaw", "thawed", "thawing", "thaws", "think", "thought",
        "threw", "throw", "thrown", "thrust", "tick", "ticked", "ticking", "tickle", "tickled", "tickles", "tickling", "ticks", "tie", "tied", "ties", "tighten", "tightened", "tightening", "tightenned", "tightenning", "tightens", "tiing", "time", "timed",
        "times", "timing", "tip", "tiped", "tiping", "tipped", "tipping", "tips", "tire", "tired", "tires", "tiring", "toast", "toasted", "toasting", "toasts", "toddle", "toddled", "toddles", "toddling", "told", "took", "tore", "torn",
        "trace", "traced", "traces", "tracing", "track", "tracked", "tracking", "tracks", "trade", "traded", "trades", "trading", "train", "trained", "training", "trains", "transfer", "transfered", "transfering", "transferred", "transferring", "transfers", "transform", "transformed",
        "transforming", "transforms", "translate", "translated", "translates", "translating", "transmit", "transmited", "transmiting", "transmits", "transmitted", "transmitting", "transport", "transported", "transporting", "transports", "transpose", "transposed", "transposes", "transposing", "trap", "traped", "traping", "trapped",
        "trapping", "traps", "travel", "traveled", "traveling", "travelled", "travelling", "travels", "tread", "treat", "treated", "treating", "treats", "tremble", "trembled", "trembles", "trembling", "trick", "tricked", "tricking", "tricks", "tried", "tries", "trigger",
        "triggered", "triggering", "triggerred", "triggerring", "triggers", "trim", "trimed", "triming", "trimmed", "trimming", "trims", "trip", "triped", "triping", "tripped", "tripping", "trips", "trod", "trodden", "trot", "troted", "troting", "trots", "trotted",
        "trotting", "trouble", "troubled", "troubles", "troubling", "truncate", "truncated", "truncates", "truncating", "trust", "trusted", "trusting", "trusts", "try", "tug", "tuged", "tugged", "tugging", "tuging", "tugs", "tumble", "tumbled", "tumbles", "tumbling",
        "tune", "tuned", "tunes", "tuning", "turn", "turned", "turning", "turns", "twist", "twisted", "twisting", "twists", "type", "typed", "types", "typing", "uncover", "uncovered", "uncovering", "uncoverred", "uncoverring", "uncovers", "undergo", "undergoed",
        "undergoes", "undergoing", "underline", "underlined", "underlines", "underlining", "underscore", "underscored", "underscores", "underscoring", "understand", "understanded", "understanding", "understands", "understood", "undertake", "undertaked", "undertakes", "undertaking", "undo", "undoed", "undoes", "undoing", "undress",
        "undressed", "undresses", "undressing", "unfold", "unfolded", "unfolding", "unfolds", "unified", "unifies", "unify", "union", "unioned", "unioning", "unions", "unite", "united", "unites", "uniting", "unload", "unloaded", "unloading", "unloads", "unlock", "unlocked",
        "unlocking", "unlocks", "unpack", "unpacked", "unpacking", "unpacks", "update", "updated", "updates", "updating", "upgrade", "upgraded", "upgrades", "upgrading", "uphold", "upholded", "upholding", "upholds", "use", "used", "uses", "using", "utilize", "utilized",
        "utilizes", "utilizing", "validate", "validated", "validates", "validating", "value", "valued", "values", "valuing", "vanish", "vanished", "vanishes", "vanishing", "varied", "varies", "vary", "vend", "vended", "vending", "vends", "venture", "ventured", "ventures",
        "venturing", "verified", "verifies", "verify", "view", "viewed", "viewing", "views", "violate", "violated", "violates", "violating", "visit", "visited", "visiting", "visits", "visitted", "visitting", "visualize", "visualized", "visualizes", "visualizing", "vote", "voted",
        "votes", "voting", "wail", "wailed", "wailing", "wails", "wait", "waited", "waiting", "waits", "wake", "waked", "wakes", "waking", "walk", "walked", "walking", "walks", "wander", "wandered", "wandering", "wanderred", "wanderring", "wanders",
        "want", "wanted", "wanting", "wants", "warm", "warmed", "warming", "warms", "warn", "warned", "warning", "warns", "was", "wash", "washed", "washes", "washing", "waste", "wasted", "wastes", "wasting", "watch", "watched", "watches",
        "watching", "wave", "waved", "waves", "waving", "wear", "weave", "weep", "weigh", "weighed", "weighing", "weighs", "welcome", "welcomed", "welcomes", "welcoming", "went", "wept", "were", "whip", "whiped", "whiping", "whipped", "whipping",
        "whips", "whirl", "whirled", "whirling", "whirls", "whisper", "whispered", "whispering", "whisperred", "whisperring", "whispers", "whistle", "whistled", "whistles", "whistling", "widen", "widened", "widening", "widenned", "widenning", "widens", "win", "wind", "wink",
        "winked", "winking", "winks", "wipe", "wiped", "wipes", "wiping", "wish", "wished", "wishes", "wishing", "withdraw", "withdrawn", "withdrew", "witness", "witnessed", "witnesses", "witnessing", "wobble", "wobbled", "wobbles", "wobbling", "woke", "woken",
        "won", "wonder", "wondered", "wondering", "wonderred", "wonderring", "wonders", "wore", "work", "worked", "working", "works", "worn", "worried", "worries", "worry", "wound", "wove", "woven", "wrap", "wraped", "wraping", "wrapped", "wrapping",
        "wraps", "wreck", "wrecked", "wrecking", "wrecks", "wrestle", "wrestled", "wrestles", "wrestling", "wriggle", "wriggled", "wriggles", "wriggling", "wring", "write", "writed", "writes", "writing", "written", "wrote", "wrung", "yawn", "yawned", "yawning",
        "yawns", "yell", "yelled", "yelling", "yells", "yield", "yielded", "yielding", "yields", "zero", "zeroed", "zeroes", "zeroing", "zip", "ziped", "ziping", "zipped", "zipping", "zips", "zoom", "zoomed", "zooming", "zooms",
            "tend", "tends", "tended", "tending",
}
    word_set = {w.strip("(),.;:!?'\"") for w in words}
    lower_set = {w.lower() for w in word_set}
    if lower_set & common_verbs:
        return True

    # Words ending in -ed (likely past tense verbs) are verb indicators
    for w in lower_set:
        if w.endswith("ed") and len(w) >= 4 and w not in {"eed", "ied"}:
            return True

    # Check for math relation operators (predicate-like in math statements)
    # e.g., "X = Y" (equals), "X subseteq Y" (is subset of), "x in E" (is element of)
    # Only include actual relation symbols, NOT set operators like cup/cap
    math_operators = {"=", "equiv", "cong", "sim", "approx",
                      "subseteq", "supseteq", "subset", "supset",
                      "in", "notin",
                      "le", "ge", "ne", "neq"}

    # Condition-starter words: a node starting with these and ending with a comma
    # is a fragment regardless of math operators
    condition_starters = {"if", "unless", "provided", "suppose", "supposing",
                          "whenever", "when", "while", "whereas", "although",
                          "though", "even though", "since", "because"}
    # Check for math relation operators (predicate-like in math statements)
    if lower_set & math_operators:
        # If the ONLY reason for passing is math operators, check for conditional fragments
        # "If a ne 0," has math operator "ne" but is an incomplete conditional clause
        if not (lower_set & common_verbs):
            t_stripped = t.strip().lower()
            first_word = t_stripped.split()[0].strip("(),;:!?") if t_stripped.split() else ""
            if first_word in condition_starters and t_stripped.endswith(","):
                return False
        return True

    return False


def _merge_incomplete_nodes(nodes):
    """
    Merge nodes that lack subject + predicate structure.

    For each incomplete node:
    - If node starts with punctuation (,.!?;) -> merge with NEXT node
    - Else if node ends with punctuation          -> merge with PREVIOUS node
    - Otherwise                                   -> merge with NEXT node

    Merging: concatenate with a space (the separator between nodes is removed).
    """
    MAX_PASSES = 5
    for _ in range(MAX_PASSES):
        changed = False
        new_nodes = []
        i = 0
        while i < len(nodes):
            node = nodes[i].strip()

            if _has_subject_predicate(node):
                new_nodes.append(node)
                i += 1
                continue

            # Node is incomplete - determine merge direction
            stripped = node.strip()
            starts_with_punct = stripped and stripped[0] in ',;:!?.'
            ends_with_punct   = stripped and stripped[-1] in ',;:!?.'

            if starts_with_punct:
                # Merge with NEXT node
                if i + 1 < len(nodes):
                    merged = node + " " + nodes[i + 1].lstrip()
                    new_nodes.append(merged)
                    i += 2
                    changed = True
                else:
                    new_nodes.append(node)
                    i += 1
            elif ends_with_punct:
                # Merge with PREVIOUS node (if exists), otherwise with NEXT
                if new_nodes:
                    prev = new_nodes.pop()
                    merged = prev.rstrip() + " " + node.lstrip()
                    new_nodes.append(merged)
                    changed = True
                elif i + 1 < len(nodes):
                    # First node with trailing punct, merge with next instead
                    merged = node + " " + nodes[i + 1].lstrip()
                    new_nodes.append(merged)
                    i += 2
                    changed = True
                else:
                    new_nodes.append(node)
                i += 1
            else:
                # No punctuation attached - merge with NEXT node
                if i + 1 < len(nodes):
                    merged = node + " " + nodes[i + 1].lstrip()
                    new_nodes.append(merged)
                    i += 2
                    changed = True
                else:
                    new_nodes.append(node)
                    i += 1

        nodes = new_nodes
        if not changed:
            break

    return nodes


def _split_periods_if_complete(nodes):
    """
    Phase 7: split nodes that contain multiple sentences (period boundaries)
    into separate nodes, BUT only if both resulting pieces have subject +
    predicate (or math-operator-equivalent) structure.

    Scans each node left-to-right for period + space patterns (". ").
    For each such boundary, checks: would splitting here create two valid nodes?
    If yes, perform the split; otherwise keep merged.

    Example:
      "Hence {G_n} has a finite subcover. Since {G_n} is taken arbitrarily,"
      -> both pieces have SP -> split.
    """
    result = []
    for node in nodes:
        # Find all period-as-sentence-boundary positions: ". " or ".\n"
        boundaries = [m.start() for m in re.finditer(r'\.\s+', node)]
        if not boundaries:
            result.append(node)
            continue

        # Process left-to-right, trying splits
        pieces = []
        cur = 0
        changed = True
        while changed:
            changed = False
            for b_idx, b_pos in enumerate(boundaries):
                if b_pos < cur:
                    continue
                # Consider splitting at this period
                split_after = b_pos + 1  # include the period
                left = node[cur:split_after].strip()
                right = node[split_after:].strip()
                if left and right and _has_subject_predicate(left) and _has_subject_predicate(right):
                    pieces.append(left)
                    cur = split_after
                    changed = True
                    break  # restart to find next valid boundary
            if not changed:
                # No valid split point found for remaining text
                remaining = node[cur:].strip()
                if remaining:
                    pieces.append(remaining)
                break

        if not pieces:
            result.append(node)
        else:
            result.extend(pieces)

    return result


def classify_node_type(claim):
    text = claim.strip()
    lowered = text.lower()

    definition_patterns = [
        r"\bdefine\b",
        r"\bis called\b",
        r"\bwe say that\b",
        r"\blet\b.+\bdenote\b",
        r"\blet\b.+:=",
        r"\blet\b.+=",
        r"\bis the set of\b",
        r"(?:\u5b9a\u4e49|\u79f0.+\u4e3a|\u8bb0.+\u4e3a|\u8bb0\u4f5c|\u4ee4.+:=)",
    ]
    if any(re.search(pattern, lowered) for pattern in definition_patterns):
        return "definition"

    claim_patterns = [
        r"\bwe (will |shall |now |first )?(show|prove|claim|assert|establish) that\b",
        r"\bour (goal|aim) is to (show|prove|establish) that\b",
        r"\bwe aim to (show|prove|establish) that\b",
        r"\bwhat we need to prove is that\b",
        r"\bthe claim to be proved is that\b",
        r"\bwe wish to prove that\b",
        r"\bwe first prove a lemma\b",
        r"\bwe begin by showing that\b",
        r"(?:\u6211\u4eec|\u4e0b\u6587)?(?:\u8bc1\u660e|\u58f0\u79f0|\u65ad\u8a00|\u4e3b\u5f20)(?:\u547d\u9898|\u7ed3\u8bba|\u5f15\u7406)?",
    ]
    if any(re.search(pattern, lowered) for pattern in claim_patterns):
        return "claim"

    assumption_starts = (
        "if ",
        "assume ",
        "assume for contradiction",
        "suppose ",
        "suppose that",
        "case ",
        "otherwise",
        "unless ",
        "provided that",
        "\u5047\u8bbe",
        "\u5047\u5b9a",
        "\u4e0d\u59a8\u8bbe",
        "\u82e5",
        "\u5982\u679c",
        "\u5206\u60c5\u51b5",
        "\u60c5\u5f62",
    )
    if lowered.startswith(assumption_starts):
        return "assumption"

    # In Chinese stepwise proofs, a standalone "obtained ..." sentence normally
    # reports the result of the preceding operation.  Keep it as a conclusion
    # instead of reclassifying it as the operation itself.
    if re.match(r"^(?:\u5f97\u5230|\u53ef\u5f97\u7ed3\u8bba|\u6545\u6709)", text):
        return "conclusion"
    # The Chinese "because P, therefore Q" form presents Q as the result.
    # symbols inside P or Q do not by themselves turn the sentence into an
    # operation node.
    if re.match(r"^(?:\u56e0\u4e3a|\u7531\u4e8e).+(?:\u6240\u4ee5|\u56e0\u6b64|\u6545|\u4ece\u800c)", text):
        return "conclusion"

    introduction_patterns = [
        r"\bit suffices to show\b",
        r"\bit is enough to prove\b",
        r"\bit remains to show\b",
        r"\bwe need only prove\b",
        r"\bthe problem reduces to\b",
        r"\bby\b",
        r"\baccording to\b",
        r"\bwe recall\b",
        r"\blet\b",
        r"\btake\b",
        r"\bfor each\b",
        r"(?:\u6839\u636e|\u4f9d\u636e|\u5229\u7528|\u5f15\u7528).+(?:\u5b9a\u7406|\u5f15\u7406|\u6027\u8d28|\u5b9a\u4e49|\u6cd5\u5219)",
        r"(?:\u7531|\u6309).+(?:\u5b9a\u7406|\u5f15\u7406|\u5b9a\u4e49|\u6027\u8d28|\u6cd5\u5219)",
        r"^(?:\u8bbe|\u4ee4|\u53d6|\u9009\u53d6|\u8bb0|\u5b58\u5728)(?:\u6709)?",
        r"(?:\u53ea\u9700|\u8db3\u4ee5|\u5f52\u7ed3\u4e3a|\u5316\u5f52\u4e3a)(?:\u8bc1\u660e|\u8bf4\u660e)",
    ]
    if any(re.search(pattern, lowered) for pattern in introduction_patterns):
        return "introduction"

    chinese_known_fact_patterns = [
        r"^(?:\u56e0\u4e3a)?(?:\u5b9e\u6570)?(?:\u7684)?\u5e73\u65b9(?:\u662f|\u6052\u4e3a)?\u975e\u8d1f",
        r"^\u6b63\u6570(?:\u76f8\u4e58|\u7684\u4e58\u79ef|\u7684\u5012\u6570)",
        r"^\u65e0\u7406\u6570\u4e0d\u5c5e\u4e8e\u6709\u7406\u6570\u96c6",
        r"^(?:\u5199|\u8bbe|\u4ee4|\u53d6|\u8bb0)\s*[^\uff0c\u3002]+[=\u4e3a]",
    ]
    if any(re.search(pattern, text) for pattern in chinese_known_fact_patterns):
        return "introduction"

    has_symbolic_relation = bool(re.search(r"(=|<=|>=|<|>|\\le|\\ge)", text))
    calculation_cue = bool(re.search(
        r"\b(calculate|compute|evaluate|simplify|expand|factor|cancel|substitut|"
        r"rearrang|rationaliz|reduce|arithmetic|equivalent to)\b",
        lowered,
    )) or bool(re.search(
        r"(?:\u4ee3\u5165|\u5c55\u5f00|\u56e0\u5f0f\u5206\u89e3|\u914d\u65b9|\u79fb\u9879|\u5408\u5e76\u540c\u7c7b\u9879|\u7ea6\u53bb|\u6d88\u53bb|\u901a\u5206|\u5316\u7b80|"
        r"\u4e24\u8fb9(?:\u540c\u52a0|\u540c\u51cf|\u540c\u4e58|\u540c\u9664|\u5e73\u65b9|\u5f00\u5e73\u65b9)|\u53d6\u5012\u6570|\u5e73\u65b9|\u5f00\u5e73\u65b9|\u8ba1\u7b97|\u6574\u7406)",
        text,
    ))
    complete_relation = is_complete_calculation_relation(text)
    relation_count = len(re.findall(r"<=|>=|(?<![<>])=|(?<!\\)[<>]|\\le|\\ge", text))
    has_operation = any(
        marker in text for marker in ("+", "-", "*", "/", "\\cdot", "^", "|", "\\sqrt", "\\frac")
    )
    chinese_derivation = bool(re.search(r"(?:\u5f97\u5230|\u5f97|\u53ef\u5f97|\u63a8\u51fa|\u5316\u4e3a|\u7b49\u4ef7\u4e8e)", text))
    chinese_calculation_shape = bool(re.search(
        r"^(?:\u4e8e\u662f|\u90a3\u4e48|\u5219|\u5f53|\u7531|\u56e0\u4e3a|\u53c8\u56e0\u4e3a)|(?:\u5b83\u4eec\u7684\u548c|\u603b\u548c)\u4e3a|\u4ece\u800c.+[=<>\u2264\u2265]",
        text,
    ))
    if (has_symbolic_relation or calculation_cue or chinese_calculation_shape) and (
        (complete_relation and (has_operation or relation_count >= 2))
        or calculation_cue
        or (chinese_derivation and has_operation)
        or (chinese_calculation_shape and (has_operation or has_symbolic_relation))
        or (
            relation_count >= 2
            and contains_any(lowered, ["claim ", "we have", "we obtain", "which gives"])
        )
    ):
        return "calculation_step"

    conclusion_starts = (
        "hence",
        "therefore",
        "thus",
        "consequently",
        "as a result",
        "we deduce",
        "this implies",
        "so ",
        "which contradicts",
        "\u56e0\u6b64",
        "\u6240\u4ee5",
        "\u4ece\u800c",
        "\u6545",
        "\u4e8e\u662f",
        "\u53ef\u77e5",
        "\u8fd9\u8bf4\u660e",
    )
    if lowered.startswith(conclusion_starts):
        return "conclusion"

    return "conclusion"


def retrieval_decision(node_type, status):
    if node_type in {"definition", "assumption"}:
        return False, f"{node_type} nodes do not create theorem-retrieval obligations."

    if node_type == "introduction":
        return False, "Introduction nodes only organize the proof context."

    if status == "closed":
        return False, "The local obligation is already closed."

    if status == "downstream_invalid":
        return False, "Repair the earlier invalid node before retrieving rules here."

    if node_type == "claim":
        return True, "The claim is not locally closed and needs supporting rules."

    if node_type == "calculation_step":
        return True, "The calculation is not locally closed and needs a justification rule."

    if node_type == "conclusion":
        return True, "The conclusion does not follow directly from the accepted context."

    return False, "This node type does not require theorem retrieval."
