from pathlib import Path
from datetime import date, timedelta
from today.cli import build_parser, parse_args, parse_task_files, CliArgs, _is_ignored


class TestCli:
    parser = build_parser()

    def test_cli_argparse0(self) -> None:
        cli_args = parse_args(self.parser, [])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date.today(), lookahead_days=timedelta(days=0), task_id=None, ignore_paths=[])

    def test_cli_argparse1(self) -> None:
        cli_args = parse_args(self.parser, ["--dir", "example/"])
        assert cli_args == CliArgs(task_dir=Path.cwd() / "example", today=date.today(), lookahead_days=timedelta(days=0), task_id=None, ignore_paths=[])

    def test_cli_argparse2(self) -> None:
        cli_args = parse_args(self.parser, ["--days", "10"])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date.today(), lookahead_days=timedelta(days=10), task_id=None, ignore_paths=[])

    def test_cli_argparse3(self) -> None:
        cli_args = parse_args(self.parser, ["--today", "1/2/2022"])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date(2022, 1, 2), lookahead_days=timedelta(days=0), task_id=None, ignore_paths=[])

    def test_cli_argparse4(self) -> None:
        cli_args = parse_args(self.parser, ["--today", "1/2/2022", "3"])
        assert cli_args == CliArgs(task_dir=Path.cwd(), today=date(2022, 1, 2), lookahead_days=timedelta(days=0), task_id=3, ignore_paths=[])

    def test_cli_argparse_ignore(self) -> None:
        cli_args = parse_args(self.parser, ["--dir", "example/", "--ignore", "chores.md"])
        assert cli_args == CliArgs(
            task_dir=Path.cwd() / "example",
            today=date.today(),
            lookahead_days=timedelta(days=0),
            task_id=None,
            ignore_paths=[(Path.cwd() / "example" / "chores.md").resolve()],
        )

    def test_cli_argparse_ignore_multiple(self) -> None:
        cli_args = parse_args(self.parser, ["--ignore", "a.md", "--ignore", "subdir"])
        assert cli_args.ignore_paths == [
            (Path.cwd() / "a.md").resolve(),
            (Path.cwd() / "subdir").resolve(),
        ]

    def test_is_ignored_file(self) -> None:
        ignore = Path("/tasks/archive.md").resolve()
        assert _is_ignored(Path("/tasks/archive.md"), [ignore])
        assert not _is_ignored(Path("/tasks/other.md"), [ignore])

    def test_is_ignored_directory(self) -> None:
        ignore = Path("/tasks/archive").resolve()
        assert _is_ignored(Path("/tasks/archive/old.md"), [ignore])
        assert _is_ignored(Path("/tasks/archive/nested/old.md"), [ignore])
        assert not _is_ignored(Path("/tasks/active.md"), [ignore])

    def test_parse_task_files_ignores_file(self, tmp_path: Path) -> None:
        (tmp_path / "keep.md").write_text("- [ ] Keep me [d:t]\n")
        (tmp_path / "skip.md").write_text("- [ ] Skip me [d:t]\n")
        args = CliArgs(
            task_dir=tmp_path,
            today=date.today(),
            lookahead_days=timedelta(days=0),
            task_id=None,
            ignore_paths=[(tmp_path / "skip.md").resolve()],
        )
        tasks = parse_task_files(args)
        assert len(tasks) == 1
        assert tasks[0].title == "Keep me"

    def test_parse_task_files_ignores_directory(self, tmp_path: Path) -> None:
        (tmp_path / "keep.md").write_text("- [ ] Keep me [d:t]\n")
        archive = tmp_path / "archive"
        archive.mkdir()
        (archive / "old.md").write_text("- [ ] Skip me [d:t]\n")
        args = CliArgs(
            task_dir=tmp_path,
            today=date.today(),
            lookahead_days=timedelta(days=0),
            task_id=None,
            ignore_paths=[archive.resolve()],
        )
        tasks = parse_task_files(args)
        assert len(tasks) == 1
        assert tasks[0].title == "Keep me"
