import argparse
import sys
from pathlib import Path
import itertools
from datetime import date, timedelta
from typing import List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text

from today.task import Task, days
from today.parser import parse_markdown


class TaskBucket(Enum):
    PRIORITY = "PRIORITY"
    OVERDUE = "OVERDUE"
    TODAY = "TODAY"
    UPCOMING = "UPCOMING"


@dataclass(frozen=True)
class CliArgs:
    task_dir: Path
    today: date
    lookahead_days: timedelta
    task_id: Optional[Union[int, str]]
    ignore_paths: List[Path]

    # Only display tasks that are due / have reminders up to and including this day
    def task_date_filter(self) -> date:
        return self.today + self.lookahead_days


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dir",
        type=str,
        required=False,
        help="Search for Markdown task files in this directory",
    )
    parser.add_argument(
        "--days",
        type=int,
        required=False,
        help="Look ahead this number of days in the future for tasks that have reminders or are due",
    )
    parser.add_argument(
        "--today",
        type=str,
        required=False,
        help="Use this date as today's date, e.g. --today 3/4/2022",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        action="append",
        default=[],
        help="Ignore a file or directory relative to --dir (can be repeated)",
    )
    parser.add_argument(
        "task_id",
        type=str,
        nargs="?",
        help="Show the description of this specific task",
    )
    return parser


def _is_ignored(file: Path, ignore_paths: List[Path]) -> bool:
    """Return True if file matches an ignored path or is under an ignored directory."""
    resolved = file.resolve()
    for ignore in ignore_paths:
        if resolved == ignore:
            return True
        try:
            resolved.relative_to(ignore)
            return True
        except ValueError:
            continue
    return False


def parse_args(parser: argparse.ArgumentParser, args: List[str]) -> CliArgs:
    ns = parser.parse_args(args)
    if ns.dir:
        task_dir = Path(ns.dir).resolve()
        if not task_dir.is_dir():
            raise ValueError(f"Provided --dir {ns.dir} is not a directory")
    else:
        task_dir = Path.cwd().resolve()

    if ns.days:
        lookahead_days = timedelta(days=int(ns.days))
    else:
        lookahead_days = timedelta(days=0)

    if ns.today:
        today_split = ns.today.split("/")
        today = date(int(today_split[2]), int(today_split[0]), int(today_split[1]))
    else:
        today = date.today()
    task_id: Optional[Union[int, str]]
    if not ns.task_id:
        task_id = None
    else:
        try:
            task_id = int(ns.task_id)
        except ValueError:
            task_id = ns.task_id

    ignore_paths = [(task_dir / path).resolve() for path in ns.ignore]

    return CliArgs(
        task_dir=task_dir,
        lookahead_days=lookahead_days,
        today=today,
        task_id=task_id,
        ignore_paths=ignore_paths,
    )


def parse_task_files(args: CliArgs) -> List[Task]:
    # Fetch Markdown task files
    md_files = list(args.task_dir.glob("**/*.md"))

    # Filter out broken symlinks (symlinks that don't exist)
    md_files = [
        file for file in md_files if not (file.is_symlink() and not file.exists())
    ]

    # Filter out ignored files and directories
    md_files = [
        file for file in md_files if not _is_ignored(file, args.ignore_paths)
    ]

    # Parse each Markdown task file
    tasks_by_file: List[List[Task]] = [
        parse_markdown(file.read_text().split("\n"), today=args.today)
        for file in md_files
    ]

    # Set each task's file path
    for filepath, tasklist in zip(md_files, tasks_by_file):
        for task in tasklist:
            task.file_path = filepath

    # Flatten the task list
    tasks: List[Task] = list(itertools.chain(*tasks_by_file))

    # Only look at tasks that have a due/reminder date on today or number of 'days' in the future
    tasks_visible: List[Task] = [
        task for task in tasks if task.is_displayed(args.task_date_filter())
    ]

    return order_tasks_for_display(tasks_visible, args.today)


def compact_days(delta: timedelta) -> str:
    n = abs(delta.days)
    return f"{n}d"


def compact_relative_date(d: date, today: date, prefix: str) -> str:
    if d < today:
        return f"{prefix}{compact_days(today - d)} ago"
    elif d == today:
        return f"{prefix}today"
    else:
        return f"{prefix}in {compact_days(d - today)}"


def task_status(task: Task, today: date) -> str:
    """Short status token for list display, e.g. 'Due 8d ago' or 'Reminder today'."""
    due = task.attrs.date_attr.due_date
    reminder = task.attrs.date_attr.reminder_date

    if due and not reminder:
        return compact_relative_date(due, today, "Due ")
    if reminder and not due:
        return compact_relative_date(reminder, today, "Reminder ")
    if due and reminder:
        # Prefer due once overdue/today; otherwise show the actionable reminder
        if due <= today:
            return compact_relative_date(due, today, "Due ")
        if reminder <= today:
            return compact_relative_date(reminder, today, "Reminder ")
        return compact_relative_date(due, today, "Due ")
    return ""


def task_bucket(task: Task, today: date) -> TaskBucket:
    if task.attrs.priority_attr is not None:
        return TaskBucket.PRIORITY

    due = task.attrs.date_attr.due_date
    reminder = task.attrs.date_attr.reminder_date

    if due and due < today:
        return TaskBucket.OVERDUE
    if (due and due == today) or (reminder and reminder <= today):
        return TaskBucket.TODAY
    return TaskBucket.UPCOMING


def _urgency_sort_key(task: Task, today: date) -> Tuple:
    """Most overdue / soonest first, then title."""
    due = task.attrs.date_attr.due_date
    reminder = task.attrs.date_attr.reminder_date
    if due is not None:
        primary = due - today
    elif reminder is not None:
        primary = reminder - today
    else:
        primary = timedelta(days=0)
    priority = (
        task.attrs.priority_attr.priority
        if task.attrs.priority_attr is not None
        else 100000
    )
    return (priority, primary, task.title.lower())


def order_tasks_for_display(tasks: List[Task], today: date) -> List[Task]:
    """Order tasks by bucket (PRIORITY → OVERDUE → TODAY → UPCOMING), then urgency."""
    bucket_order = [
        TaskBucket.PRIORITY,
        TaskBucket.OVERDUE,
        TaskBucket.TODAY,
        TaskBucket.UPCOMING,
    ]
    by_bucket = {b: [] for b in bucket_order}
    for task in tasks:
        by_bucket[task_bucket(task, today)].append(task)
    ordered: List[Task] = []
    for bucket in bucket_order:
        group = by_bucket[bucket]
        group.sort(key=lambda t: _urgency_sort_key(t, today))
        ordered.extend(group)
    return ordered


def task_breadcrumb(task: Task, task_dir: Path) -> str:
    rel = task.file_path.relative_to(task_dir)
    location = f"{rel}:{task.line_number}"
    if task.path:
        return f"{location} · {' / '.join(task.path)}"
    return location


def display_specific_task(task: Task, today: date, console: Console) -> None:
    details = task.details(today)
    console.print("")
    console.print(Markdown(details))
    console.print("")

    if len(task.subtasks) > 0:
        console.print(Markdown("**Subtasks**:"))
    for subtask in task.subtasks:
        subtask_summary = subtask.summary(today)
        if subtask.done:
            console.print(Markdown(f"- **DONE**: {subtask.title} {subtask_summary}"))
        else:
            console.print(Markdown(f"- {subtask.title} {subtask_summary}"))
    if len(task.subtasks) > 0:
        console.print("")

    sys.exit(0)


def display_tasks(args: CliArgs, tasks: List[Task], console: Console) -> None:
    header = Text()
    header.append("Tasks for today", style="bold underline")
    header.append(f" · {args.today}")
    if args.lookahead_days != timedelta(0):
        header.append(f" (+{days(args.lookahead_days)})")
    header.append(f" · {len(tasks)} task{'s' if len(tasks) != 1 else ''}")

    console.print("")
    console.print(header)
    if not tasks:
        console.print("")
        return

    id_width = len(str(len(tasks) - 1))
    status_width = max((len(task_status(t, args.today)) for t in tasks), default=0)

    bucket_order = [
        TaskBucket.PRIORITY,
        TaskBucket.OVERDUE,
        TaskBucket.TODAY,
        TaskBucket.UPCOMING,
    ]
    by_bucket = {b: [] for b in bucket_order}
    for idx, task in enumerate(tasks):
        by_bucket[task_bucket(task, args.today)].append((idx, task))

    for bucket in bucket_order:
        entries = by_bucket[bucket]
        if not entries:
            continue
        console.print("")
        console.print(Text(bucket.value, style="bold"))
        for idx, task in entries:
            status = task_status(task, args.today)
            line1 = Text()
            line1.append(f"  {idx:>{id_width}}  ")
            if status:
                # Emphasize overdue / today statuses
                due = task.attrs.date_attr.due_date
                reminder = task.attrs.date_attr.reminder_date
                urgent = (due is not None and due <= args.today) or (
                    reminder is not None and reminder <= args.today
                )
                line1.append(
                    f"{status:<{status_width}}  ",
                    style="bold" if urgent else "dim",
                )
            line1.append(task.title)

            line2_indent = 2 + id_width + 2
            if status:
                line2_indent += status_width + 2
            console.print(line1)
            console.print(
                Padding(
                    Text(task_breadcrumb(task, args.task_dir), style="dim"),
                    (0, 0, 0, line2_indent),
                )
            )

    console.print("")
