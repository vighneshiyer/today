# Today: A File-Centric Task Management System

## Motivation

I've used GUI based "task management" apps in the past, such as Asana, Trello, Google Tasks, and recently Superproductivity.
I don't like these since they require a browser, are bloated, are GUI-driven, and are difficult to back up and version control.
However, they are nice when it comes to visualization of tasks, physically moving tasks across projects, and general readability and scanability.

I've also seen and used CLI based "task management" apps (Taskwarrior, Ultralist, Todo.txt).
I like that these apps often have easy backup strategies, are text driven, and are usually minimal, but overall I haven't been satisfied.

The CLI apps all seem to use a non-human-readable database format to store task and project descriptions such as a sqlite database or JSON.
As a result, all interaction with tasks goes through the CLI rather than a text editor directly.
The CLI will never be as ergonomic as browsing and editing projects and tasks with vim or using a GUI.
In other words, they are *cli-centric* rather than *file-centric*, and I think this is why GUI solutions still feel better despite the downsides.

But, there is another way (I think).

The benefit of the GUI approach is the quick editing, visualization, and readability.
This can be achieved by putting all tasks in files with human-readable markup; my notes are just plain Markdown files and that has worked perfectly for readability and quick scanning.
This also allows easy regrouping of tasks, moving them between projects, and editing description text in bulk, since those are easy with any text editor.

The benefit of the CLI approach is minimal bloat and a quick UI to view the daily task execution summary we want.
To mitigate the downside of editing tasks through the CLI, I propose a *read-only* CLI where task changes are made to the files directly, which serve as the golden source of truth.

## Task Definitions

- Tasks are kept in plain Markdown files. Each Markdown file represents a project. Ideally each project should be tightly scoped and not drag on forever.
    - You can save Markdown files on disk in any way you want. Add nested folders to represent hierarchy.
    - You can group tasks within a project any way you want. Add nested headings to represent hierarchy.

In `chores.md`:

```markdown
# Chores

## Purchases

## Bills

## Cleaning
```

- Tasks are designated by a Markdown checkbox.

```markdown
## Cleaning

- [ ] Home cleaning
```

### Tags

- A task can have one or more tags, designated by hashtags in the task title. Tags are highlighted when a task is displayed, but are otherwise useless.

```markdown
- [ ] Home cleaning #cleaning #house #offline
```

### Dates

- A task can have a created, due, and reminder date by placing it in square brackets with the prefix `c`, `d`, or `r`.
    - The date is in `month`/`day`/`year` format
    - You can also use `t` as a date. For example, to specify today as the due date, write: `[d:t]`

```markdown
- [ ] Home cleaning #cleaning #house #offline [c:1/3/2023] [r:2/27/2023] [d:3/1/2023]
```

### Descriptions

- You can add a description for a task directly underneath the task title. It can consist of any Markdown you want.

```markdown
- [ ] Home cleaning #cleaning #house #offline [c:1/3/2023] [r:2/27/2023] [d:3/1/2023]

Here is a description paragraph. You can put any Markdown (*execpt headings*) underneath a task and it will be part of the task's description.

- Some bullets
    - A nested bullet

> A quote

```

### Subtasks

- Subtasks can be specified by creating a list in the task description with the specific word 'Subtasks' and adding subtasks as elements of the list. Subtasks cannot have their own descriptions, but they can have tags and created/reminder/due dates.
    - If the main task has a created/reminder/due date, it will apply for all subtasks automatically, unless otherwise specified
    - Only one level of subtasks is supported

```markdown
- [ ] Home cleaning #cleaning #house #offline [c:1/3/2023] [r:2/27/2023] [d:3/1/2023]

I need to get this done soon.

- Subtasks
    - [ ] Sweep the floors [d:2/10/2023]
    - [ ] Wipe the countertops
    - [ ] Throw the trash
```

### Completed Tasks

- A task can be marked complete just by checking its checkbox. You can optionally specify a completion time with a finish `f` date.

```markdown
[x] Home cleaning #cleaning #house #offline [c:1/3/2023] [r:2/27/2023] [d:3/1/2023] [f:2/28/2023]
```

### Recurring Tasks

- A task can be made recurring by specifying a `[recur:]` string in the task title.
    - Recurring tasks cannot have any subtasks, but they can have a description
    - Recurring tasks should not be marked complete. They will show up in your daily report and there is a CLI option to mark an instance of the task complete. This completion isn't tracked anywhere explicitly.
    - Recurring tasks disappear after the day they are scheduled. If you forget to finish a recurring task, you must explicitly add an instance of it to a project if you wish to be reminded later.

```markdown
[ ] Daily journal [recur:daily]
[ ] Weekly tasks [recur:Sunday]
[ ] Monthly tasks [recur:eom]
```

- TBD: more complex recurrence descriptions, maybe use ical recur format string? This implementation also seems brittle and has many caveats - is there a better way?

## Today

The core CLI command is `today`. Running `today` will 

- will be placed in a "today" queue for you to review. The due date / reminder date can be changed if you wish to defer the task.

- Every day, you can get a view of the tasks you are to complete or at least review.
- `today` is a READ-ONLY view of the tasks scheduled for today
    - The only way to make changes is to directly change the files
    - There is no intermediary database
    - The files are the golden source of truth!

### Completing a Task

The files are the source of truth. If you've completed a task, mark it complete by checking its box.

### Editing a Task

The files are the source of truth. To edit a task's description, title, or due date, edit the file directly.

### Deleting / Archiving a Task

The files are the source of truth. To delete a task, just remove it from the file. To "archive" it, just remove its due date or mark it as completed and move it around in the file to an "Archived" section (or whatever you want).

### Moving Tasks Across Projects

## Limitations

- Time tracking
- Task History / Burndown rate
- Attachments
- Syncing

## Dev Notes

### TODO

- [ ] Capture file names and line numbers
- [ ] CLI
- [ ] Subtasks
- [ ] Links in the task title
- [ ] Recurring tasks
- [ ] Cancelled tasks

### Markdown Parser

- Python Markdown libraries
    - [Python-Markdown (3.1k)](https://github.com/Python-Markdown/markdown/) - most popular, middling performance, also not precisely CommonMark compliant
    - [mistune (2.2k)](https://github.com/lepture/mistune) - high performance, not precisely CommonMark compliant
      - Easy AST hacking, high perf, new 3.0 release incoming
    - [marko (179)](https://github.com/frostming/marko) - not popular, but claims best CommonMark compliance, middling performance
      - There is no Markdown renderer (for roundtrip)
    - [mistletoe (552)](https://github.com/miyuchina/mistletoe/) - less popular, claims fastest pure Python CommonMark compliance
      - AST hacking is painful, and no Markdown renderer (for roundtrip)
- Decision
  - All these seem to support raw AST dumping mode, which is what I'm looking for
  - **Initial thoughts**: mistletoe seems to be the best balance of performance and compliance and ease of working with the AST representation; mistune is a close second
  - **Update**: mistune is superior. Markdown renderer from AST, easy pure Python AST (just dicts and lists), fast
  - **Further update**: all these libraries are a pain to work with and have very minimal benefit for this project. I just want to parse very specific Markdown features and leave the rest of the document alone, so I have switched to manual and minimal parsing.

### Rich TUI Library

- [rich (41.6k)](https://github.com/Textualize/rich) seems to be the de-facto option
