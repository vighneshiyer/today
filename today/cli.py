import argparse
import sys
from pathlib import Path
import itertools
from datetime import date, timedelta

from today.task import parse_markdown, task_should_be_displayed


def run(args):
    if args.dir:
        assert Path(args.dir).is_dir()
        root = Path(args.dir)
    else:
        root = Path.cwd()
    md_files = list(root.resolve().glob("*.md"))
    tasks = [parse_markdown(file.read_text().split('\n')) for file in md_files]
    # Set each task's file
    for filepath, tasklist in zip(md_files, tasks):
        for task in tasklist:
            task.file_path = filepath
    # Flatten the task list
    tasks = list(itertools.chain(*tasks))
    # Only look at tasks due/reminder today or 'days' in advance
    task_date_limit = date.today() + timedelta(days=args.days)
    tasks = [task for task in tasks if task_should_be_displayed(task, task_date_limit)]
    print(tasks)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--dir', type=str, required=False,
                        help='Directory to search for Markdown task files in')
    parser.add_argument('--days', type=int, default=0,
                        help='Number of days in the future to look for tasks that have reminders or are due')
    parser.add_argument('task-id', type=int, nargs='?',
                        help='Show the description of this specific task')

    sys.exit(run(parser.parse_args()))
