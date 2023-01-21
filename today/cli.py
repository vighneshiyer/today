import argparse
import sys
from pathlib import Path
import itertools
from datetime import date, timedelta
from typing import Dict, List, Tuple

from rich import print as rprint
from rich.tree import Tree

from today.task import parse_markdown, task_should_be_displayed, Task


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
    # Sort tasks by their headings

    # Print tasks as a tree
    tree = Tree(f"Tasks for Today {date.today()}" + ("" if args.days == 0 else f" (+{args.days} days)"))
    tree_cache: Dict[Tuple[str], Tree] = {}

    def add_to_tree(task: Task, tree: Tree) -> Tree:
        if len(task.path) == 0:  # Base case
            tree.add(task.title)
            return tree
        else:
            # Try to find the first heading in the current tree's children
            labels = [t.label for t in tree.children]
            if task.path[0] in labels:  # The first heading has been found, continue to traverse down its children
                first_heading = task.path[0]
                task.path = task.path[1:]
                add_to_tree(task, tree.children[labels.index(first_heading)])
            else:  # The first heading doesn't exist, create it and traverse down its children
                child = tree.add(task.path[0])
                task.path = task.path[1:]
                add_to_tree(task, child)

    for task in tasks:
        add_to_tree(task, tree)
        # print(task)
        # rprint(tree)
        # path = tuple(task.path)
        # if path in tree_cache:
        #     tree_cache[path].add(task.title)
        # elif path[:-1] in tree_cache:
        #     parent = tree_cache[path[:-1]]
        #     child = parent.add(path[-1])
        #     child.add(task.title)
        #     tree_cache[path] = child
        # else:
        #     child = tree.add(path[0])
        #     tree_cache[path[0]] = child
        #     for i, item in enumerate(path[1:]):
        #         child = tree_cache[path[i]]
        #         tree_cache[path[i]] = child
        #         if i == len(path)-1:
        #             child.add(task.title)

    #baz_tree = tree.add("baz")
    #baz_tree.add("[red]Red").add("[green]Green").add("[blue]Blue")
    rprint(tree)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--dir', type=str, required=False,
                        help='Directory to search for Markdown task files in')
    parser.add_argument('--days', type=int, default=0,
                        help='Number of days in the future to look for tasks that have reminders or are due')
    parser.add_argument('--today', type=str, required=False,
                        help='Use this date as "today"\'s date')
    parser.add_argument('task-id', type=int, nargs='?',
                        help='Show the description of this specific task')

    sys.exit(run(parser.parse_args()))
