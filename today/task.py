from typing import Optional, List, Any
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    path: List[str]
    title: str
    done: bool
    subtasks: List["Task"] = field(default_factory=lambda: [])
    created_date: Optional[date] = None
    reminder_date: Optional[date] = None
    due_date: Optional[date] = None
    finished_date: Optional[date] = None


def parse_task_title(headings_stack: List[str], title: str) -> Task:
    assert title.startswith("[ ]")
    return Task(path=headings_stack, title=title[4:], done=False)


def parse_markdown(md: List[Any]) -> List[Task]:
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

                assert text_ast['type'] == 'paragraph'
                list_item_text = "".join([child['raw'] for child in text_ast['children']])

                if list_item_text.startswith("[ ]"):  # This the start of a new task
                    if current_task is not None:  # Another task was being parsed
                        tasks.append(current_task)
                        current_task = parse_task_title(headings_stack, list_item_text)
                    else:  # No task has been seen yet
                        current_task = parse_task_title(headings_stack, list_item_text)
        else:
            print(item)
            assert False

    if current_task is not None:
        tasks.append(current_task)

    return tasks
