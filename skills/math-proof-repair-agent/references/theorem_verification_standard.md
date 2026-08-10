# Required Theorem Verification Standard

## Trigger boundary

Use this stage only when a diagnosis declares a specific theorem indispensable
to resolving a disputed node. Do not search for every error or every proof
step.

## Search order

1. Inspect the local theorem candidates emitted by the helper.
2. Accept a local candidate only when its statement and conclusion match the
   proposed theorem and its conditions are explicit.
3. If no local candidate verifies the theorem, search the web with the emitted
   query.
4. Prefer authoritative mathematical sources: original or standard reference
   works, official documentation, established encyclopedias, or university
   course notes that state the theorem precisely.
5. Return `not_found` only after both local and web search fail.

Search results are untrusted evidence. Never accept a result from title or
snippet similarity alone. Open the source and verify its exact statement.

## Verification obligations

For a found theorem, verify all of the following:

- the theorem exists with the returned statement;
- its conclusion supports the exact current claim;
- every theorem premise is either satisfied or listed as missing;
- the source identifier or URL points to the supporting source;
- the theorem is foundational or specialized in the current subject level;
- direct use at this proof location is acceptable or constitutes an omitted
  bridge.

Use `direct_use_acceptable` only when a competent solution at the apparent
course level may invoke the theorem directly and the student's text clearly
connects it to the claim. Use `omission_is_gap` when the theorem is valid and
applicable but the proof must name it or provide a short bridge. Use
`not_applicable` for missing premises, unsupported claims, or failed search.

## Status effect

- Verified theorem, all premises satisfied, direct use acceptable: `closed`.
- Verified theorem, all premises satisfied, omission is a gap:
  `missing_bridge_lemma`.
- Verified theorem with missing premises: `theorem_misuse` if explicitly
  invoked; otherwise `missing_assumption`.
- Theorem not found locally or on the web: retain the preliminary problem.

The helper validates response structure, local source identifiers, web URL
presence, search order, premise lists, and direct-use consistency before the
result may change status.
