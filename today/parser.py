from typing import Tuple, List, Optional
from datetime import date
import re

from today.task import (
    AssignmentAttribute,
    PriorityAttribute,
    Task,
    Heading,
    TaskAttributes,
    TaskTitle,
)

task_attr_re = re.compile(r"\[.:.")
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


# Mutates the fields of [task_attr] based on the [attr_string]
# [attr_string] is of the form [d:<date>] or [@person] () or [!2] (priority flag)
# If the [attr_string] is malformed, return an error message
def assign_task_attr(
    attr_string: str, task_attr: TaskAttributes, today: date
) -> None | str:
    if attr_string[:2] == "@:":
        # This is an assignment attribute
        task_attr.assn_attr = AssignmentAttribute(attr_string[2:])
        return
    elif attr_string[:2] == "!:":
        # This is a priority attribute
        task_attr.priority_attr = PriorityAttribute(int(attr_string[2:]))
        return
    else:
        # This must be a date attribute
        assert attr_string[1] == ":"
        prefix = attr_string[0]
        date_raw = attr_string[2:]
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
                return f"Date attribute '{attr_string}' is improperly formatted"
        if prefix == "c":
            task_attr.date_attr.created_date = date_value
        elif prefix == "d":
            task_attr.date_attr.due_date = date_value
        elif prefix == "r":
            task_attr.date_attr.reminder_date = date_value
        elif prefix == "f":
            task_attr.date_attr.finished_date = date_value
        else:
            return f"Date attribute prefix '{prefix}' in date attribute '{attr_string}' isn't recognized"
        return


def extract_task_attrs(
    raw_task_title: str, today: date
) -> Tuple[TaskAttributes, TaskTitle]:
    task_attr = TaskAttributes()

    # remove attributes from the [raw_task_title] iteratively until no more are left
    while (match := task_attr_re.search(raw_task_title)) is not None:
        start_idx = raw_task_title.find("[", match.start())
        end_idx = raw_task_title.find("]", match.start())
        attr_string = raw_task_title[start_idx + 1 : end_idx]
        error_msg = assign_task_attr(attr_string, task_attr, today)
        if error_msg is not None:
            raise RuntimeError(
                f"An error was encountered when parsing the task title '{raw_task_title}'. Error: {error_msg}"
            )
        # Remove the parsed attribute from the title
        raw_task_title = raw_task_title.replace(
            raw_task_title[start_idx : end_idx + 2], ""
        )
    return task_attr, raw_task_title.rstrip()


def parse_task_title(title: str, today: date) -> Task:
    task_attr, task_title = extract_task_attrs(title, today)
    t = Task(title=task_title, attrs=task_attr)
    return t


# def extract_task_defns(title: str) -> List[TaskAttribute]:
#     date_defns: List[str] = []
#
#     # remove date defns iteratively until nothing is left
#     while (match := task_attr_re.search(title)) is not None:
#         start_idx = title.find("[", match.start())
#         end_idx = title.find("]", match.start())
#         date_defns.append(title[start_idx + 1 : end_idx])
#         title = title.replace(title[start_idx : end_idx + 2], "")
#     return date_defns, title.rstrip()


# def parse_task_title(title: str, today: date) -> Task:
#     date_defns, task_title = extract_date_defns(title)
#     t = Task(title=task_title)
#     for defn in date_defns:
#         prefix = defn[0]
#         assert defn[1] == ":"
#         if defn[2:] == "t":
#             date_value = today
#         else:
#             date_split = [int(d) for d in defn[2:].split("/")]
#             if len(date_split) == 3:
#                 date_value = date(
#                     year=date_split[2], month=date_split[0], day=date_split[1]
#                 )
#             elif len(date_split) == 2:
#                 date_value = date(
#                     year=today.year, month=date_split[0], day=date_split[1]
#                 )
#             else:
#                 raise ValueError(
#                     f"Unable to parse date for task {title} and date string {defn}"
#                 )
#         if prefix == "c":
#             t.created_date = date_value
#         elif prefix == "r":
#             t.reminder_date = date_value
#         elif prefix == "d":
#             t.due_date = date_value
#         elif prefix == "f":
#             t.finished_date = date_value
#         else:
#             raise ValueError(
#                 f"Prefix {prefix} in date definition string {defn} is not recognized"
#             )
#     return t


def parse_markdown(md: List[str], today: date = date.today()) -> List[Task]:
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
            if not subtask.due_date and current_task.due_date:
                subtask.due_date = current_task.due_date
            if not subtask.reminder_date and current_task.reminder_date:
                subtask.reminder_date = current_task.reminder_date
            if not subtask.finished_date and current_task.finished_date:
                subtask.finished_date = current_task.finished_date
            if not subtask.created_date and current_task.created_date:
                subtask.created_date = current_task.created_date
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
