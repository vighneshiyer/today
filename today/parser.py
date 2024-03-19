from typing import Sequence, Tuple, List, Optional
from datetime import date
import re
from more_itertools import windowed

from today.task import (
    AssignmentAttribute,
    PriorityAttribute,
    Task,
    Heading,
    TaskAttributes,
    TaskTitle,
)

task_attr_re = re.compile(r"\[(?P<prefix>(.:|@|!))(?P<value>.*?)\]\s?")
task_re = re.compile(r"^- \[[ xX]\] ")
subtask_re = re.compile(r"^[ \t]+- \[[ xX]\] ")


def parse_heading(s: str) -> Heading:
    for i in range(len(s)):
        if s[i] == " ":
            return Heading(level=i, name=s[i + 1 :])
        elif s[i] == "#":
            continue
        else:
            raise ValueError(f"Malformed heading {s}")
    raise ValueError("This should never happen")


# Given the current state of headings in [headings_stack] and a new heading [heading_raw],
# validate that the new heading has the correct indentation and return a new heading stack
def handle_headings_stack(headings_stack: List[str], heading_raw: str) -> List[str]:
    heading = parse_heading(heading_raw)
    last_level = len(headings_stack)
    if heading.level > last_level:  # deeper into hierarchy
        if heading.level is not last_level + 1:
            raise ValueError(f"Heading {heading} nested too deep")
    elif heading.level == last_level:  # same hierarchy level, different heading
        headings_stack.pop()
    else:  # higher hierarchy level, pop off current level and upper level
        for _ in range(last_level - heading.level + 1):
            headings_stack.pop()
    headings_stack.append(heading.name)
    return headings_stack


def md_checkbox(s: str) -> Optional[bool]:
    # None = not a checkbox, True = checked, False = unchecked
    if s.startswith("[ ]"):
        return False
    elif s.startswith("[x]") or s.startswith("[X]"):
        return True
    else:
        return None


# Mutates the fields of [task_attr] based on a raw attribute string (prefix + value)
# of the form [d:<date>] (prefix='d:', value='<date>') or [@person] or [!2]
# If the prefix or value are malformed, return an error message
def assign_task_attr(
    prefix: str, value: str, task_attr: TaskAttributes, today: date
) -> None | str:
    if prefix == "@":
        # This is an assignment attribute
        task_attr.assn_attr = AssignmentAttribute(value)
        return
    elif prefix == "!":
        # This is a priority attribute
        task_attr.priority_attr = PriorityAttribute(int(value))
        return
    else:
        # This must be a date attribute
        prefix = prefix[0]  # the raw prefix passed is of the form 'd:'
        date_raw = value
        date_value: date
        if date_raw == "t":
            date_value = today
        else:
            date_split = [int(d) for d in date_raw.split("/")]
            if len(date_split) == 3:  # month / day / year
                date_value = date(
                    year=date_split[2], month=date_split[0], day=date_split[1]
                )
            elif len(date_split) == 2:  # month / day (year is implicitly today's year)
                date_value = date(
                    year=today.year, month=date_split[0], day=date_split[1]
                )
            else:
                return f"Date attribute value '{value}' is improperly formatted"
        if prefix == "c":
            task_attr.date_attr.created_date = date_value
        elif prefix == "d":
            task_attr.date_attr.due_date = date_value
        elif prefix == "r":
            task_attr.date_attr.reminder_date = date_value
        elif prefix == "f":
            task_attr.date_attr.finished_date = date_value
        else:
            return f"Date attribute prefix '{prefix}' isn't recognized"
        return


def extract_task_attrs(
    raw_task_title: str, today: date
) -> Tuple[TaskAttributes, TaskTitle]:
    task_attr = TaskAttributes()

    # Find all matches for the attribute regex and parse each one while mutating [task_attr]
    task_attr_matches = list(re.finditer(task_attr_re, raw_task_title))
    if len(task_attr_matches) == 0:
        # short circuit when there are no attributes to parse
        return task_attr, raw_task_title
    for match in task_attr_matches:
        prefix = match.group("prefix")
        value = match.group("value")
        error_msg = assign_task_attr(prefix, value, task_attr, today)
        if error_msg is not None:
            raise RuntimeError(
                f"An error was encountered when parsing the task title '{raw_task_title}'. Error: {error_msg}"
            )

    # Strip all the task attribute matches from the [raw_task_title]
    # Do this efficiently by first computing the substring indices we need, then constructing the new string
    match_spans: List[Tuple[int, int]] = [m.span(0) for m in task_attr_matches]
    not_match_spans = (
        [(0, match_spans[0][0])]
        + [
            (span1[1], span2[0])
            for (span1, span2) in windowed(match_spans, 2)
            if span1 is not None and span2 is not None
        ]
        + [(match_spans[-1][1], len(raw_task_title))]
    )
    task_title = ""
    for span in not_match_spans:
        task_title = task_title + raw_task_title[span[0] : span[1]]
    return task_attr, task_title.rstrip()


def parse_task_title(title: str, today: date) -> Task:
    task_attr, task_title = extract_task_attrs(title, today)
    t = Task(title=task_title, attrs=task_attr)
    return t


def parse_markdown(md: Sequence[str], today: date = date.today()) -> List[Task]:
    headings_stack: List[str] = []
    current_task: Optional[Task] = None
    tasks: List[Task] = []
    for i, line in enumerate(md):
        if line.startswith("#"):  # This is a heading
            headings_stack = handle_headings_stack(headings_stack, line)
            # Headings terminate any task already being parsed
            if current_task is not None:
                tasks.append(current_task)
                current_task = None
        elif task_re.match(line):  # This is a Markdown checkbox (a task)
            task_status = md_checkbox(line[len("- ") :])
            if task_status is not None:
                if current_task is not None:
                    tasks.append(current_task)
                current_task = parse_task_title(line[len("- [ ] ") :], today)
                current_task.path = headings_stack.copy()
                current_task.done = task_status
                current_task.line_number = i + 1
            else:  # Malformed Markdown checkbox
                raise ValueError(f"Malformed Markdown checkbox on line {i}: {line}")
        elif (match := subtask_re.match(line)) is not None:
            if current_task is None:
                raise ValueError(
                    f"Encountered subtask without a main task on line {i}: {line}"
                )
            subtask_status = md_checkbox(line[line.index("[") :])
            assert subtask_status is not None  # The checkbox must not be malformed
            subtask = parse_task_title(line[match.end(0) :], today)
            subtask.path = headings_stack.copy()
            subtask.done = subtask_status
            subtask.line_number = i + 1
            subtask.attrs.merge_attributes(current_task.attrs)
            current_task.subtasks.append(subtask)
        elif len(line) == 0 and current_task is None:
            continue
        else:
            if current_task is None:  # Unparsed text right after a header
                continue
                # raise ValueError(f"Encountered description not associated with a task on line {i}: {line}")
            current_task.description = (
                current_task.description + "\n" + line
            )  # This is part of the description of a current task

    if current_task is not None:
        tasks.append(current_task)

    # Post-process descriptions - remove trailing or leading newlines and spaces
    for i in range(len(tasks)):
        tasks[i].description = tasks[i].description.strip("\n ")
    return tasks
