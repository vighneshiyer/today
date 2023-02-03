from pathlib import Path
from datetime import date, timedelta
from today.cli import build_parser, parse_args, CliArgs


class TestCli:
    parser = build_parser()

    def test_cli_argparse0(self) -> None:
        cli_args = parse_args(self.parser, [])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date.today(), lookahead_days=timedelta(days=0), task_id=None)

    def test_cli_argparse1(self) -> None:
        cli_args = parse_args(self.parser, ["--dir", "example/"])
        assert cli_args == CliArgs(task_dir=Path.cwd() / "example", today=date.today(), lookahead_days=timedelta(days=0), task_id=None)

    def test_cli_argparse2(self) -> None:
        cli_args = parse_args(self.parser, ["--days", "10"])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date.today(), lookahead_days=timedelta(days=10), task_id=None)

    def test_cli_argparse3(self) -> None:
        cli_args = parse_args(self.parser, ["--today", "1/2/2022"])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date(2022, 1, 2), lookahead_days=timedelta(days=0), task_id=None)

    def test_cli_argparse4(self) -> None:
        cli_args = parse_args(self.parser, ["--today", "1/2/2022", "3"])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date(2022, 1, 2), lookahead_days=timedelta(days=0), task_id=3)
