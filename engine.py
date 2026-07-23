import sys
import argparse

from core.uci_handler import UCIHandler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Coco Chess Engine - Unified UCI Binary",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Matches the available factory engine IDs: gen1, gen2, gen2.1, gen3
    parser.add_argument(
        "-e", "--engine",
        type=str,
        default="gen3",
        choices=["gen1", "gen2", "gen2.1", "gen3"],
        help="Default engine personality to initialize at startup."
    )

    # Sets the startup default depth, modifiable later via UCI 'setoption name Depth'
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=6,
        help="Default search depth fallback for bare 'go' commands."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        # Initialize the protocol handler with CLI startup defaults
        handler = UCIHandler(engine_id=args.engine, default_depth=args.depth)

        # Enter the standard input listening loop
        handler.listen()

    except KeyboardInterrupt:
        # Catch SIGINT (Ctrl+C) to exit cleanly without dumping Python tracebacks
        sys.exit(0)
    except Exception as e:
        # Route fatal initialization errors to stderr to protect the Erlang Port stdout stream
        print(f"Fatal engine error during boot: {e}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()