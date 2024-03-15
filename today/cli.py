import argparse
import sys
from pathlib import Path
import itertools
from datetime import date, timedelta
from typing import List, Optional
import functools
from dataclasses import dataclass

from rich.tree import Tree
from rich.console import Console
from rich.markdown import Markdown

from today.task import Task, task_sorter, days
from today.parser import parse_markdown


@dataclass(frozen=True)
class CliArgs:
    task_dir: Path
    today: date
    lookahead_days: timedelta
    task_id: Optional[int]

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
        "task_id",
        type=int,
        nargs="?",
        help="Show the description of this specific task",
    )
    return parser


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
    return CliArgs(
        task_dir=task_dir,
        lookahead_days=lookahead_days,
        today=today,
        task_id=ns.task_id,
    )


def parse_task_files(args: CliArgs) -> List[Task]:
    # Fetch Markdown task files
    md_files = list(args.task_dir.glob("**/*.md"))

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

    # Sort tasks by their headings and due dates
    tasks_visible.sort(key=functools.partial(task_sorter, today=args.today))
    return tasks_visible


def maybe_display_specific_task(
    args: CliArgs, tasks: List[Task], console: Console
) -> None:
    # If a specific task id is given, print its description and details and exit
    if args.task_id is not None:
        if args.task_id < 0 or args.task_id >= len(tasks):
            console.print(f"The task_id {args.task_id} does not exist")
            sys.exit(1)
        task = tasks[args.task_id]
        details = task.details(args.task_id, args.today)
        console.print("")
        console.print(Markdown(details))
        console.print("")

        if len(task.subtasks) > 0:
            console.print(Markdown("**Subtasks**:"))
        for subtask in task.subtasks:
            subtask_summary = subtask.summary(args.today)
            if subtask.done:
                console.print(
                    Markdown(f"- **DONE**: {subtask.title} {subtask_summary}")
                )
            else:
                console.print(Markdown(f"- {subtask.title} {subtask_summary}"))
        if len(task.subtasks) > 0:
            console.print("")

        sys.exit(0)


def tasks_to_tree(args: CliArgs, tasks: List[Task]) -> Tree:
    # Print tasks as a tree
    tree = Tree(
        f"[bold underline]Tasks for today[/bold underline] ({args.today})"
        + (
            ""
            if args.lookahead_days == timedelta(0)
            else f" (+{days(args.lookahead_days)})"
        )
    )

    def add_to_tree(task: Task, tree: Tree, task_idx: int, first_call: bool) -> Tree:
        if len(task.path) == 0:  # Base case
            parent = tree.add(
                Markdown(f"**{task_idx}** - {task.title} {task.summary(args.today)}")
            )
            if task.subtasks:
                for subtask in task.subtasks:
                    if subtask.done is False:
                        parent.add(
                            Markdown(f"{subtask.title} {subtask.summary(args.today)}")
                        )
            return tree
        else:
            labels = [t.label for t in tree.children]
            # Try to find the first heading in the current tree's children
            # The top-level heading should contain the file path of its associated markdown file
            # All the subheadings should just be the raw heading
            expected_label = (
                f"{task.path[0]}"
                if not first_call
                else f"[bold]{task.path[0]}[/bold] ([red italic]{task.file_path.relative_to(args.task_dir)}[/red italic])"
            )
            if (
                expected_label in labels
            ):  # The first heading has been found, continue to traverse down its children
                task.path = task.path[1:]
                return add_to_tree(
                    task, tree.children[labels.index(expected_label)], task_idx, False
                )
            else:  # The first heading doesn't exist, create it and traverse down its children
                child = tree.add(expected_label)
                task.path = task.path[1:]
                return add_to_tree(task, child, task_idx, False)

    for i, task in enumerate(tasks):
        add_to_tree(task, tree, i, True)
    return tree
