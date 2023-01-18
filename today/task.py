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


def parse_task_title(headings_stack: List[str], title: str) -> Task:
    return Task(path=headings_stack, title=title[len("[ ]")+1:], done=False)


def parse_markdown_str(md: List[str]) -> List[Task]:
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


def parse_markdown(md: List[Any]) -> List[Task]:
    md_renderer = MarkdownRenderer()

    headings_stack: List[str] = []
    current_task: Optional[Task] = None
    tasks: List[Task] = []

    for item in md:
        if item['type'] == "heading":
            headings_stack.append(item['children'][0]['raw'])
        elif item['type'] == "blank_line":
            continue
        elif item['type'] == "list":
            list_items = item['children']
            for list_item in list_items:
                assert len(list_item['children']) == 1
                text_ast = list_item['children'][0]

                assert text_ast['type'] in ('paragraph', 'block_text')
                list_item_text = "".join([child['raw'] for child in text_ast['children']])

                list_item_is_task = md_checkbox(list_item_text)
                if list_item_is_task is not None:  # This the start of a new task
                    if current_task is not None:  # Another task was being parsed
                        tasks.append(current_task)
                    current_task = parse_task_title(headings_stack, list_item_text)
                    current_task.done = list_item_is_task
        else:
            # This item is part of the current task's description
            print(item)
            assert current_task is not None
            if current_task.description is not None:
                current_task.description = current_task.description + "\n" + md_renderer([item], BlockState())
            else:
                current_task.description = md_renderer([item], BlockState())

    if current_task is not None:
        tasks.append(current_task)

    return tasks
