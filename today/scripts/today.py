import sys

# Lazy import console - only load when displaying
from today.cli import (
    parse_task_files,
    display_specific_task,
    tasks_to_tree,
)


def run(args) -> None:
    # Fast path: detect --fast flag early and avoid argparse overhead
    if "--fast" in args:
        from today.fast_args import parse_fast_args
        cli_args = parse_fast_args(args)
    else:
        from today.cli import build_parser, parse_args
        parser = build_parser()
        cli_args = parse_args(parser, args)

    # TODO: cache task parsing for each markdown file based on file hash
    tasks = parse_task_files(cli_args)
    
    # Fast mode: use simple text output without rich
    if cli_args.fast:
        from today.simple_output import simple_display
        
        # If a specific task is displayed, print it simply
        if cli_args.task_id is not None:
            assert isinstance(cli_args.task_id, int)
            if cli_args.task_id < 0 or cli_args.task_id >= len(tasks):
                print(f"The task_id {args.task_id} does not exist")
                sys.exit(1)
            task = tasks[cli_args.task_id]
            print(f"\nTitle: {task.title}")
            print(task.attrs.date_attr.details(cli_args.today))
            if task.description:
                print(f"Description:\n{task.description}")
            sys.exit(0)
        
        simple_display(cli_args, tasks)
        return
    
    # Regular mode: use rich for pretty output
    from rich.console import Console
    console = Console()

    # If a specific task is displayed, the program will exit
    if cli_args.task_id is not None:
        assert isinstance(cli_args.task_id, int)
        if cli_args.task_id < 0 or cli_args.task_id >= len(tasks):
            console.print(f"The task_id {args.task_id} does not exist")
            sys.exit(1)
        task = tasks[cli_args.task_id]
        display_specific_task(task, cli_args.today, console)
        sys.exit(0)

    tree = tasks_to_tree(cli_args, tasks)
    console.print("")
    console.print(tree)
    console.print("")


def main():
    sys.exit(run(sys.argv[1:]))
