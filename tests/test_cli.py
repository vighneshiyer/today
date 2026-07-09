from pathlib import Path
from datetime import date, timedelta
from today.cli import (
    build_parser,
    parse_args,
    parse_task_files,
    CliArgs,
    _is_ignored,
    task_status,
    task_bucket,
    task_breadcrumb,
    order_tasks_for_display,
    TaskBucket,
)
from today.task import Task, TaskAttributes, DateAttribute, PriorityAttribute


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

    def test_task_status_compact(self) -> None:
        today = date(2026, 7, 8)
        overdue = Task(attrs=TaskAttributes(date_attr=DateAttribute(due_date=date(2026, 6, 30))))
        assert task_status(overdue, today) == "Due 8d ago"
        due_today = Task(attrs=TaskAttributes(date_attr=DateAttribute(due_date=today)))
        assert task_status(due_today, today) == "Due today"
        reminder = Task(attrs=TaskAttributes(date_attr=DateAttribute(reminder_date=date(2026, 7, 1))))
        assert task_status(reminder, today) == "Reminder 7d ago"

    def test_task_bucket(self) -> None:
        today = date(2026, 7, 8)
        priority = Task(
            attrs=TaskAttributes(
                date_attr=DateAttribute(due_date=date(2026, 6, 1)),
                priority_attr=PriorityAttribute(priority=0),
            )
        )
        overdue = Task(attrs=TaskAttributes(date_attr=DateAttribute(due_date=date(2026, 6, 1))))
        due_today = Task(attrs=TaskAttributes(date_attr=DateAttribute(due_date=today)))
        upcoming = Task(attrs=TaskAttributes(date_attr=DateAttribute(due_date=date(2026, 7, 10))))
        assert task_bucket(priority, today) == TaskBucket.PRIORITY
        assert task_bucket(overdue, today) == TaskBucket.OVERDUE
        assert task_bucket(due_today, today) == TaskBucket.TODAY
        assert task_bucket(upcoming, today) == TaskBucket.UPCOMING

    def test_order_tasks_for_display(self) -> None:
        today = date(2026, 7, 8)
        upcoming = Task(title="Later", attrs=TaskAttributes(date_attr=DateAttribute(due_date=date(2026, 7, 10))))
        overdue_old = Task(title="Old", attrs=TaskAttributes(date_attr=DateAttribute(due_date=date(2026, 6, 1))))
        overdue_new = Task(title="Recent", attrs=TaskAttributes(date_attr=DateAttribute(due_date=date(2026, 7, 1))))
        due_today = Task(title="Now", attrs=TaskAttributes(date_attr=DateAttribute(due_date=today)))
        priority = Task(
            title="P0",
            attrs=TaskAttributes(
                date_attr=DateAttribute(due_date=date(2026, 6, 15)),
                priority_attr=PriorityAttribute(priority=0),
            ),
        )
        ordered = order_tasks_for_display(
            [upcoming, overdue_new, due_today, overdue_old, priority], today
        )
        assert [t.title for t in ordered] == ["P0", "Old", "Recent", "Now", "Later"]

    def test_task_breadcrumb(self, tmp_path: Path) -> None:
        path = tmp_path / "finances" / "investments.md"
        path.parent.mkdir()
        path.write_text("")
        task = Task(
            path=["Investment Accounts", "UC DCP"],
            file_path=path,
            line_number=7,
        )
        assert task_breadcrumb(task, tmp_path) == (
            "finances/investments.md:7 · Investment Accounts / UC DCP"
        )
