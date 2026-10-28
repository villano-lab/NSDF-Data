"""`python -m goldsluice run|check|algorithms`: batch mode (see `goldsluice.batch`)."""
import argparse
import sys

from . import ALGORITHMS, batch


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m goldsluice", description="Run goldsluice processing over a dataset definition.")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="process every raw file that is new or changed")
    r.add_argument("dataset", help="the dataset definition (TOML)")
    r.add_argument("--chunk", type=int, default=1000, help="events read at once (default 1000)")
    r.add_argument("--force", action="store_true", help="redo files that are unchanged")
    r.add_argument("--backend", choices=("rust", "python"), default="rust", help="python runs the mirrors (slow, for comparison)")
    r.add_argument("--allow-output-in-repo", action="store_true", help="allow an output folder inside a Git working tree that does not ignore it")
    c = sub.add_parser("check", help="read the definition and list the raw files that would be looked at")
    c.add_argument("dataset")
    c.add_argument("--allow-output-in-repo", action="store_true", help="allow an output folder inside a Git working tree that does not ignore it")
    sub.add_parser("algorithms", help="list the algorithms")
    args = p.parse_args(argv)
    try:
        if args.command == "algorithms":
            for name, module in sorted(ALGORITHMS.items()):
                print(f"{name}: outputs {list(module.OUTPUTS)}")
        elif args.command == "check":
            files = batch.check(args.dataset, allow_output_in_repo=args.allow_output_in_repo)
            for source, path in files:
                print(f"{source}: {path}")
            print(f"{len(files)} raw file(s)")
        else:
            print(batch.run(args.dataset, chunk=args.chunk, force=args.force, backend=args.backend,
                            allow_output_in_repo=args.allow_output_in_repo))
    except (ValueError, KeyError, TypeError, FileNotFoundError, ImportError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
