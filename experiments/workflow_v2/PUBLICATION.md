# Repository evidence availability

This directory contains workflow v2 code snapshots, experimental inputs, readable raw calls, frozen results, reports and blank human-review packets. Frozen evidence uses original bytes without Git line-ending normalization. The implementation snapshots are included so archive hashes can be checked after checkout.

The original `pilot2_pipeline48_20260912` run was interrupted. 33 local file or directory entries remain unreadable with OS error 22; they are excluded from Git and listed in [publication_omissions.json](publication_omissions.json). The list describes unavailable entries, not a complete count of files beneath inaccessible directories. Existing local remnants have not been removed or replaced.

The complete continuation `pilot2_resumed48_20260912` contains 108 frozen runtime results and 108 judgments. The mechanism run and final 18-task regression are complete in their own directories. Their completed evidence is unaffected by the original interruption. The original interrupted attempt still has 10 calls without complete usage, so combined cost is reported as a lower bound.

Server databases, local state, generated tool logs and locks are excluded. RPC evidence and response records needed for verification remain included. Human-review templates are blank; only distribute `human/public` to reviewers and keep method mappings, model judgments and this results repository hidden until reviews are submitted. Repository publication does not establish independent human calibration.

See [the latest report](../../docs/workflow_v2/LATEST_RUN.md) for results and their limitations.
