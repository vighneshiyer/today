import sys

from rich.console import Console

from today.cli import build_parser, parse_args, parse_task_files, maybe_display_specific_task, tasks_to_tree


def run(args) -> None:
    parser = build_parser()
    cli_args = parse_args(parser, args)
    console = Console()

    tasks = parse_task_files(cli_args)
    maybe_display_specific_task(cli_args, tasks, console)  # If a specific task is displayed, the program will exit

    tree = tasks_to_tree(cli_args, tasks)
    console.print("")
    console.print(tree)
    console.print("")


def main():
    sys.exit(run(sys.argv[1:]))
