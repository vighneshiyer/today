from typing import Optional, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import date
import re

from mistune import BlockState
from mistune.renderers.markdown import MarkdownRenderer


@dataclass
class Task:
    path: List[str]
    title: str
    done: bool
    description: str = "" # A Markdown string with the task description
    subtasks: List["Task"] = field(default_factory=lambda: [])
    created_date: Optional[date] = None
    reminder_date: Optional[date] = None
    due_date: Optional[date] = None
    finished_date: Optional[date] = None


def parse_heading(s: str) -> Tuple[int, str]:
    for i in range(len(s)):
        if s[i] == " ":
            return i, s[i+1:]
        elif s[i] == "#":
            continue
        else:
            raise ValueError(f"Malformed heading {s}")
    raise ValueError


def handle_headings_stack(headings_stack: List[str], heading: str) -> List[str]:
    heading_depth, heading_str = parse_heading(heading)
    if heading_depth > len(headings_stack):  # deeper into hierarchy
        if heading_depth is not len(headings_stack) + 1:
            raise ValueError(f"Heading {heading} nested too deep")
    elif heading_depth == len(headings_stack):  # same hierarchy level, different heading
        headings_stack.pop()
    else:  # higher hierarchy level, pop off current level and upper level
        for _ in range(len(headings_stack) - heading_depth + 1):
            headings_stack.pop()
    headings_stack.append(heading_str)
    return headings_stack


def md_checkbox(s: str) -> Optional[bool]:
    # None = not a checkbox, True = checked, False = unchecked
    if s.startswith("[ ]"):
        return False
    elif s.startswith("[x]") or s.startswith("[X]"):
        return True
    else:
        return None


def extract_date_defns(title: str) -> Tuple[List[str], str]:
    date_defns_partial = title.split('[')[1:]
    date_defns = [x[:x.find(']')] for x in date_defns_partial]

    # remove date defns iteratively until nothing is left
    while "[" in title:
        start_idx = title.find('[')
        end_idx = title.find(']')
        title = title.replace(title[start_idx:end_idx+2], '')
    return date_defns, title.rstrip()


def parse_task_title(headings_stack: List[str], title: str, done: bool) -> Task:
    date_defns = extract_date_defns(title[len("[ ] "):])
    t = Task(path=headings_stack, title=title[len("[ ]")+1:], done=done)
    #if title.


def parse_markdown(md: List[str]) -> List[Task]:
    headings_stack: List[str] = []
    current_task: Optional[Task] = None
    tasks: List[Task] = []
    for line in md:
        if line.startswith("#"):  # This is a heading
            headings_stack = handle_headings_stack(headings_stack, line)
            # Headings terminate any task already being parsed
            if current_task is not None:
                tasks.append(current_task)
                current_task = None
        elif line.startswith("- ["):  # This might be a checkbox
            task_status = md_checkbox(line[len("- "):])
            if task_status is not None:
                if current_task is not None:
                    tasks.append(current_task)
                current_task = Task(path=headings_stack.copy(), title=line[len("- [ ] "):], done=task_status)
            else:
                assert False
        elif len(line) == 0 and current_task is None:
            continue
        else:  # This is part of the description of a current task
            assert current_task is not None
            current_task.description = current_task.description + "\n" + line

    if current_task is not None:
        tasks.append(current_task)

    # Post-process descriptions - remove trailing or leading newlines
    for i in range(len(tasks)):
        tasks[i].description = tasks[i].description.strip("\n")
    return tasks
