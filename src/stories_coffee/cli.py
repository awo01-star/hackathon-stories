"""Command-line interface for the current workflow."""
import argparse
from pathlib import Path

from .paths import DEFAULT_DATA, DEFAULT_REPORTS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Train, verify or run Stories Coffee's weekly transaction forecast.")
    parser.add_argument("command", nargs="?", choices=["all", "train", "validate", "predict"], default="all")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORTS)
    args = parser.parse_args(argv)
    try:
        if args.command in {"all", "train"}:
            from .pipeline import train

            print("Training on March/April, selecting on May, evaluating June...")
            result = train(args.data, args.out)
            print(f"June score (100% - WAPE): {1-result['selected']['wape']:.2%}; baseline {1-result['baseline']['wape']:.2%}")
            print("June is an exploratory historical evaluation, not guaranteed future accuracy.")
        if args.command in {"all", "validate"}:
            from .validation import validate

            result = validate(args.data, args.out)
            print(f"Validation: {result['status']} ({result['checks_run']:,} checks)")
            if result["failures"]:
                for failure in result["failures"][:10]:
                    print("  " + failure)
                return 1
        if args.command == "predict":
            from .pipeline import predict_next

            origin = predict_next(args.data, args.out)
            print(f"Forecast starts {origin.date()}, after the last source observation.")
        print(f"Reports: {args.out.resolve()}")
        print(f"Forecast: {(args.out / 'tables/forecast_next_7_days.csv').resolve()}")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
