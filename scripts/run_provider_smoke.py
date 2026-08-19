#!/usr/bin/env python3
"""Run explicit M5/M6 Provider smoke assignments with append-only evidence."""

import argparse
import json
from pathlib import Path

from harness.provider_runner import AppendOnlyEvidenceStore, ProviderRunConfig, ProviderRunner, build_openai_adapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Frozen JSON configuration")
    parser.add_argument("--assignments", required=True, help="JSONL: sample_id, method_id, input_payload")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--execute", action="store_true", help="Required for any Provider call")
    args = parser.parse_args()

    if not args.execute:
        raise SystemExit("Provider calls are disabled; review frozen inputs, then pass --execute explicitly")

    raw_config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    prices = raw_config.pop("prices_usd_per_million")
    config = ProviderRunConfig(**raw_config)
    prompt = Path(args.prompt).read_text(encoding="utf-8")
    assignments = [json.loads(line) for line in Path(args.assignments).read_text(encoding="utf-8").splitlines() if line.strip()]
    adapter = build_openai_adapter(input_usd_per_million=prices["input"],
                                   output_usd_per_million=prices["output"])
    runner = ProviderRunner(config, AppendOnlyEvidenceStore(Path(args.output_dir)), adapter,
                            execution_enabled=args.execute)
    for item in assignments:
        row = runner.run(run_id=args.run_id, sample_id=item["sample_id"],
                         method_id=item["method_id"], prompt=prompt,
                         input_payload=item["input_payload"])
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
