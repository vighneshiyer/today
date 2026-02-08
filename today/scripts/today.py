import sys

from rich.console import Console

from today.cli import (
    build_parser,
    parse_args,
    parse_task_files,
    display_specific_task,
    tasks_to_tree,
)


def run(args) -> None:
    parser = build_parser()
    cli_args = parse_args(parser, args)
    console = Console()

    # TODO: cache task parsing for each markdown file based on file hash
    tasks = parse_task_files(cli_args)

    # If a specific task is displayed, the program will exit
    if cli_args.task_id is not None:
        assert isinstance(cli_args.task_id, int)
        if cli_args.task_id < 0 or cli_args.task_id >= len(tasks):
            console.print(f"The task_id {args.task_id} does not exist")
            sys.exit(1)
        task = tasks[cli_args.task_id]
        display_specific_task(task, cli_args.today, console)
        sys.exit(0)

    try:
        tree = tasks_to_tree(cli_args, tasks)
        console.print("")
        console.print(tree)
        console.print("")
    except ValueError as e:
        console.print(f"[red]{str(e)}[/red]")
        sys.exit(1)


def main():
    sys.exit(run(sys.argv[1:]))
