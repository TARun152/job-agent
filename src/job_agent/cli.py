"""Command-line entrypoints for Job Agent."""

from __future__ import annotations

import argparse
import json

from job_agent.config import get_settings
from job_agent.db.session import init_db
from job_agent.logging_setup import configure_logging, get_logger
from job_agent.scheduler.daily import start_scheduler
from job_agent.scheduler.pipeline import run_discover_match_tailor_enqueue

pclog = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI argument parser.

    Returns:
        Configured ``ArgumentParser``.
    """
    parser = argparse.ArgumentParser(prog="job-agent", description="Job Agent CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create SQLite tables")
    sub.add_parser("run-once", help="Discover, match, tailor, and enqueue once")
    sub.add_parser("discover", help="Alias for run-once")
    sub.add_parser("scheduler", help="Run daily scheduler (blocking)")
    sub.add_parser("queue", help="Start the approval queue UI")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI main entry.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)
    pclog.info("CLI command=%s env=%s", args.command, settings.job_agent_env)

    if args.command == "init-db":
        init_db()
        print("Database initialized.")
        return 0

    if args.command in {"run-once", "discover"}:
        counts = run_discover_match_tailor_enqueue(settings)
        print(json.dumps(counts, indent=2))
        return 0

    if args.command == "scheduler":
        start_scheduler()
        return 0

    if args.command == "queue":
        import uvicorn

        from job_agent.queue.app import create_app

        # Import UI stack only for the queue command.
        app = create_app()
        uvicorn.run(app, host=settings.queue_host, port=settings.queue_port)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
