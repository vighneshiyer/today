# Today: A File-Centric Task Management System

![PR CI](https://github.com/vighneshiyer/today/actions/workflows/pr.yml/badge.svg?event=push) ![Publish CI](https://github.com/vighneshiyer/today/actions/workflows/publish.yml/badge.svg) [![PyPI version](https://badge.fury.io/py/todo-today-cli.svg)](https://badge.fury.io/py/todo-today-cli)

## Quickstart

Install: `pip install todo-today-cli`

Create a file (`tasks.md`) and add the following:

```markdown
# My Tasks

## Household

- [x] Pay the monthly bills [d:1/1/2023]
- [ ] Sweep the floors [d:t]
- [ ] Take out the trash [r:1/2/2023]

- The trash can is outside the garage

> Trash pickup is deferred until next week if it lands on NYE
```

Run `today`, and you'll get a listing of tasks that are assigned for today (sorted by Markdown headings and overdue status).

```text
Tasks for today (2023-02-06)
└── My Tasks
    └── Household
        ├── 0 - Take out the trash [Reminder 35 days ago]
        └── 1 - Sweep the floors [Due today]
```

To display the description of a task, specify its number.
A task description can contain any Markdown.

```text
$ today 0

Title: Take out the trash (id = 0)
Reminder date: 2023-01-02 (Reminder 35 days ago)
Description:

 • The trash can is outside the garage

▌ Trash pickup is deferred until next week if it lands on NYE
```

The task files are the only source of truth!
`today` is a read-only utility to display what's planned for today.
To mark a task complete, edit `tasks.md` and tick its Markdown checkbox.

## Detailed Docs

### Task Files

Tasks are kept in plain Markdown files.
Each Markdown file represents a project.
Ideally each project should be tightly scoped and not drag on forever.

- You can save Markdown files on disk in any way you want. Add nested folders to encode hierarchy.
- You can group tasks within a task file any way you want. Add nested Markdown headings to encode hierarchy.

### Task Definitions

Tasks are defined with a list item that starts with a Markdown checkbox.

A task can have a created, reminder, due, and finished date by placing it in square brackets with the prefix `c:`, `r:`, `d:`, or `f:`.

- The date is in `month`/`day`/`year` format
- `t` is a shorthand date for today. For example, if a task should be due today, use: `[d:t]`

You can add a description for a task underneath the task title. It can consist of any Markdown you want (*except headings*).

Subtasks are specified with a nested list of checkboxes under the main task.

- Subtasks cannot have their own descriptions, but they can have their own created/reminder/due dates.
- If the main task has a created/reminder/due date, it will apply for all subtasks automatically, unless otherwise specified
- Only one level of subtasks is supported

A task can be marked complete just by checking its checkbox. You can optionally specify a completion time with a finish `f` date.

Here is a complete example:

```markdown
- [x] Pay the electricity bill [d:t] [f:2/20/2023]
- [ ] Home cleaning [c:1/3/2023] [r:2/27/2023] [d:3/1/2023]
    - [ ] Sweep the floors [d:2/10/2023]
    - [ ] Wipe the countertops
    - [ ] Throw the trash

Any text here will be part of the main task's description.

- Some bullets
    - A nested bullet

> A quote
```

### Task Wrangling

Super easy. No databases, no "state" in the task manager. Directly edit the task files.

- **Adding a task**: add a Markdown checkbox to a task file
- **Completing a task**: check the Markdown checkbox of the task you've completed
- **Editing a task**: edit the task's description or dates in the task file
- **Deleting a task**: remove it from the task file
- **Archiving a task**: if the task isn't done, remove any due/reminder dates. Then, move the task to an "Archived" section of your task file (or wherever you want).
- **Moving tasks across projects**: copy the task from one task file and paste it into another task file

### The Today CLI

The core CLI command is `today`.
Running `today` will parse all the Markdown files in the current directory, and display all the tasks that are due or have reminders for today (or are overdue).
The tasks will be ordered by heading and criticality of due/reminder dates.

- To specify a directory to look for Markdown task files in, use `today --dir /path/to/md/files`.
- To look ahead 10 days in advance for tasks that are due or have reminders, do `today --days 10`.
- To display the details of a specific task, provide its task number e.g. `today 3`.
- Summary: `today` is a READ-ONLY view of the tasks scheduled for today

### i3 Integration

Just displaying the tasks that need to be done today is fine, but often we want more direction about what we should be doing *right now* in contrast to *merely today*.
There is another included CLI program `start` which given a task id, will emit the formatted task title to `/tmp/task`.
Then this task title can be displayed prominently using your window manager's notification area.

For i3 (w/ i3status and i3bar), you can add this to your `~/.config/i3status/config`:

```conf
general {
    colors = true
    markup = "pango"
}

order += "read_file task"

read_file task {
  format = "%content"
  path = "/tmp/task"
}
```

Now when you run `start <task_id>`, the task title will show up in your statusbar to remind you of what you should be working on *at this moment*.

`start` takes the same command line arguments as `today`.
If you run `start` without a task id, it will clear the task file.

You may want to include aliases to `today` and `start` for your shell:

```fish
alias t 'today --dir $HOME/task_folder'
alias s 'start --dir $HOME/task_folder'
```

## Motivation

I've used GUI based "task management" apps in the past, such as Asana, Trello, Google Tasks, and recently Superproductivity.
I don't like these since they require a browser, are bloated, are GUI-driven, and are difficult to back up and version control.
However, they are nice when it comes to visualization of tasks, physically moving tasks across projects, and general readability and scanability.

I've also seen and used CLI based "task management" apps (Taskwarrior, Ultralist, Todo.txt).
I like that these apps often have easy backup strategies, are text driven, and are usually minimal, but overall I haven't been satisfied.

The CLI apps all seem to use a non-human-readable/editable database format to store task and project descriptions such as a sqlite database or JSON.
As a result, all interaction with tasks goes through the CLI rather than a text editor directly.
The CLI will never be as ergonomic as browsing and editing projects and tasks with vim or using a GUI.
In other words, they are *cli-centric* rather than *file-centric*, and I think this is why GUI solutions still feel better despite the downsides.

But, there is another way (I think).

The benefit of the GUI approach is the quick editing, visualization, and readability.
This can be achieved by putting all tasks in files with human-readable markup (e.g. my notes are just plain Markdown files and that has worked perfectly for readability and scanning).
This also allows regrouping of tasks, moving them between projects, and editing description text in bulk, since those are easy with any text editor.

The benefit of the CLI approach is minimal bloat and a quick UI to view the daily TODO summary we want.
To mitigate the downside of editing tasks through the CLI, I propose a *read-only* CLI where task changes are made to the Markdown files directly, which serve as the golden source of truth.

### The "Today" Strategy

One common issue with task management systems is they are a great place to dump loads of tasks, but when it comes to "what should I do now?" at the start of the day, they provide little assistance.
Often, you scroll through your projects and ad-hoc decide what to work on, or you suddenly realize I need to work on *this*.
While you can use basic Markdown files or Trello boards to enumerate your tasks, `today` offers a directed view of what you should do *today* to counter analysis paralysis.

It is based on Superproductivity's approach where, every day, you would get a list of tasks that are due or have reminders for today or earlier.
You would then pick which tasks you want to work on today, and snooze (defer) the rest of them.
Then you get a 'daily' view of what to do and can tick things off from there (without having to go into different boards or project Markdown files).

## Limitations

- **Time tracking**: since there is no emphermal task state, it may be hard to record time tracking info in an automated way to the task Markdown
- **Task history / burndown rate**: there is no way to enforce specification of a 'finish' date for a task, so it is not possible in general to calculate a burndown rate

In general, I think these 'quantification' things are mostly useless and can often be distracting - just focus on what needs to get done today.

- **Attachments**: there is no way to 'attach' a PDF or image to a task, unless it is a URL.
- **Syncing / phone editing**: version control is easy, but live syncing and collaborative editing of Markdown task files may be difficult without a Markdown CRDT. Similarly, editing files on your phone via raw text is harder than with a nice GUI.
