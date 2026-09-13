"""Command-line entry point for OpenFC."""

from __future__ import annotations

import argparse
from typing import Optional, Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser used by :func:`main`."""
    parser = argparse.ArgumentParser(
        prog="openfc",
        description="Tools for modeling fusion-plant tritium fuel cycles.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("info",),
        help="optional command to run (default: show help)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the OpenFC command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "info":
        print(f"OpenFC {__version__}: fusion tritium fuel-cycle model")
    else:
        parser.print_help()
    return 0
