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
        if cli_args.task_id >= len(tasks):
            print(f"The task id provided ({cli_args.task_id}) is not in range, rerun today")
            sys.exit(1)
        task = tasks[cli_args.task_id]
        path = " → ".join(task.path)
        current_task = f"<span weight='bold'> Current Task ({cli_args.task_id}) -</span>" if False else ""
        rel_path = task.file_path.relative_to(cli_args.task_dir)
        task_snippet = f"<span color='white'>{current_task} {path} <span weight='bold'>→</span> {task.title} ({rel_path})</span>"
        Path("/tmp/task").write_text(task_snippet)

    # https://i3wm.org/docs/i3status.html
    subprocess.run("killall -USR1 i3status", shell=True)
    sys.exit(0)


def main():
    sys.exit(run(sys.argv[1:]))
