"""CLI entrypoint for Module C.2 Ranking Scorer."""

import argparse
import json
import sys
from pathlib import Path

from scoring.core.ranking_scorer import compute_ranking
from scoring.models.common import AggregationMode
from scoring.models.ranking_output import RequirementWeights


def main():
    parser = argparse.ArgumentParser(description="Deterministic Ranking Scorer (Module C.2)")
    parser.add_argument("input_file", help="Path to Genie retrieval JSON file (Module D output)")
    parser.add_argument("--output", "-o", help="Optional output JSON file path (defaults to stdout)")
    parser.add_argument("--aggregation", choices=["max", "mean", "top_k_mean"], default="max", help="Aggregation method")
    parser.add_argument("--policy-version", default="ranking-v1", help="Policy version identifier")
    parser.add_argument("--w-required", type=float, default=1.0, help="Weight for required skills")
    parser.add_argument("--w-preferred", type=float, default=0.6, help="Weight for preferred skills")
    parser.add_argument("--w-bonus", type=float, default=0.3, help="Weight for bonus skills")

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File {input_path} not found.", file=sys.stderr)
        return 1

    try:
        raw_data = json.loads(input_path.read_text())
        weights = RequirementWeights(
            required=args.w_required,
            preferred=args.w_preferred,
            bonus=args.w_bonus,
        )
        agg_mode = AggregationMode(args.aggregation)

        result = compute_ranking(
            retrieval_input=raw_data,
            policy_version=args.policy_version,
            custom_weights=weights,
            aggregation_mode=agg_mode,
        )

        output_json = result.model_dump_json(indent=2)

        if args.output:
            Path(args.output).write_text(output_json)
            print(f"Saved ranking results to {args.output}")
        else:
            print(output_json)

        return 0
    except Exception as e:
        print(f"Error during scoring: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
