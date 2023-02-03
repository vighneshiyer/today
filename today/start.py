import sys
from pathlib import Path
import subprocess

from today.cli import build_parser, parse_args, parse_task_files


def run(args) -> None:
    parser = build_parser()
    cli_args = parse_args(parser, args)
    task_file = Path("/tmp/task")

    if cli_args.task_id is None:
        task_file.write_text("")
    else:
        tasks = parse_task_files(cli_args)
        task = tasks[cli_args.task_id]
        path = " → ".join(task.path)
        task_snippet = f"<span color='white'><span weight='bold'>Current Task -</span> {path} <span weight='bold'>-</span> {task.title}</span>"
        Path("/tmp/task").write_text(task_snippet)
        # https://i3wm.org/docs/i3status.html

    subprocess.run("killall -USR1 i3status", shell=True)
    sys.exit(0)


def main():
    sys.exit(run(sys.argv[1:]))
