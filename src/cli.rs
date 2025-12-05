use crate::parser::parse_markdown;
use crate::task::{Task, format_days};
use crate::markdown::{render_markdown, render_markdown_detail};
use chrono::{NaiveDate, Duration, Local};
use clap::Parser;
use owo_colors::OwoColorize;
use std::path::PathBuf;
use walkdir::WalkDir;

/// CLI arguments structure
#[derive(Parser, Debug, Clone)]
#[command(name = "today")]
#[command(about = "A file-centric task management system", long_about = None)]
pub struct CliArgs {
    /// Search for Markdown task files in this directory
    #[arg(long, value_name = "DIR")]
    pub dir: Option<PathBuf>,

    /// Look ahead this number of days in the future for tasks
    #[arg(long, value_name = "DAYS")]
    pub days: Option<i64>,

    /// Use this date as today's date (format: M/D/Y)
    #[arg(long, value_name = "DATE")]
    pub today: Option<String>,

    /// Show the description of this specific task
    #[arg(value_name = "TASK_ID")]
    pub task_id: Option<String>,
}

impl CliArgs {
    /// Get the task directory (defaults to current directory)
    pub fn task_dir(&self) -> Result<PathBuf, String> {
        if let Some(ref dir) = self.dir {
            let path = std::fs::canonicalize(dir)
                .map_err(|e| format!("Failed to resolve directory {:?}: {}", dir, e))?;
            if !path.is_dir() {
                return Err(format!("Provided --dir {:?} is not a directory", dir));
            }
            Ok(path)
        } else {
            std::env::current_dir()
                .map_err(|e| format!("Failed to get current directory: {}", e))
        }
    }

    /// Get lookahead days (defaults to 0)
    pub fn lookahead_days(&self) -> i64 {
        self.days.unwrap_or(0)
    }

    /// Get today's date (defaults to actual today)
    pub fn get_today(&self) -> Result<NaiveDate, String> {
        if let Some(ref today_str) = self.today {
            parse_date_arg(today_str)
        } else {
            Ok(Local::now().naive_local().date())
        }
    }

    /// Get task date filter (today + lookahead)
    pub fn task_date_filter(&self) -> Result<NaiveDate, String> {
        let today = self.get_today()?;
        Ok(today + Duration::days(self.lookahead_days()))
    }

    /// Parse task_id as integer or string
    pub fn get_task_id(&self) -> Option<Result<usize, String>> {
        self.task_id.as_ref().map(|s| {
            s.parse::<usize>()
                .map_err(|_| s.clone())
        })
    }
}

/// Parse a date string in M/D/Y format
fn parse_date_arg(date_str: &str) -> Result<NaiveDate, String> {
    let parts: Vec<&str> = date_str.split('/').collect();
    if parts.len() != 3 {
        return Err(format!("Date must be in M/D/Y format, got: {}", date_str));
    }

    let month = parts[0].parse::<u32>()
        .map_err(|_| format!("Invalid month: {}", parts[0]))?;
    let day = parts[1].parse::<u32>()
        .map_err(|_| format!("Invalid day: {}", parts[1]))?;
    let year = parts[2].parse::<i32>()
        .map_err(|_| format!("Invalid year: {}", parts[2]))?;

    NaiveDate::from_ymd_opt(year, month, day)
        .ok_or_else(|| format!("Invalid date: {}/{}/{}", month, day, year))
}

/// Parse all task files in the given directory
pub fn parse_task_files(args: &CliArgs) -> Result<Vec<Task>, String> {
    let task_dir = args.task_dir()?;
    let today = args.get_today()?;

    // Find all markdown files
    let md_files: Vec<PathBuf> = WalkDir::new(&task_dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.path().extension()
                .and_then(|s| s.to_str())
                .map(|s| s == "md")
                .unwrap_or(false)
        })
        .filter(|e| !e.path_is_symlink() || e.path().exists())
        .map(|e| e.path().to_path_buf())
        .collect();

    // Parse each markdown file
    let mut all_tasks = Vec::new();
    for file in md_files {
        let content = std::fs::read_to_string(&file)
            .map_err(|e| format!("Failed to read file {:?}: {}", file, e))?;
        
        let lines: Vec<String> = content.lines().map(|s| s.to_string()).collect();
        let mut tasks = parse_markdown(&lines, today)?;
        
        // Set file path for each task
        for task in &mut tasks {
            task.file_path = file.clone();
        }
        
        all_tasks.extend(tasks);
    }

    // Filter to only visible tasks
    let lookahead = args.lookahead_days();
    let mut visible_tasks: Vec<Task> = all_tasks
        .into_iter()
        .filter(|task| task.is_displayed(today, lookahead))
        .collect();

    // Sort tasks
    visible_tasks.sort_by_key(|task| task.sort_key(today));

    Ok(visible_tasks)
}

/// Display a specific task with details
pub fn display_specific_task(task: &Task, today: NaiveDate) {
    println!();
    print!("{}", render_markdown_detail(&task.details(today)));
    println!();
    println!();

    if !task.subtasks.is_empty() {
        println!("{}", "Subtasks:".bold());
        for subtask in &task.subtasks {
            let summary = render_markdown(&subtask.summary(today));
            if subtask.done {
                println!("- {}: {} {}", "DONE".bold(), render_markdown(&subtask.title), summary);
            } else {
                println!("- {} {}", render_markdown(&subtask.title), summary);
            }
        }
        println!();
    }
}

/// Display tasks as a tree
pub fn display_tasks_tree(args: &CliArgs, tasks: &[Task]) -> Result<(), String> {
    let today = args.get_today()?;
    let task_dir = args.task_dir()?;
    let lookahead = args.lookahead_days();

    // Print header
    let header = if lookahead == 0 {
        format!("Tasks for today ({})", today)
    } else {
        format!("Tasks for today ({}) (+{})", today, format_days(Duration::days(lookahead)))
    };
    println!();
    println!("{}", header.bold().underline());

    // Separate priority and non-priority tasks
    let (priority_tasks, other_tasks): (Vec<_>, Vec<_>) = tasks.iter()
        .enumerate()
        .partition(|(_, t)| t.attrs.priority_attr.is_some());

    // Display priority tasks
    if !priority_tasks.is_empty() {
        println!("{}", "└── Priority Tasks".bold());
        for (i, task) in priority_tasks {
            let rel_path = task.file_path.strip_prefix(&task_dir)
                .unwrap_or(&task.file_path);
            
            // Render markdown in path components, then join
            let rendered_path: Vec<String> = task.path.iter()
                .map(|p| render_markdown(p))
                .collect();
            let path_str = rendered_path.join(" / ");
            
            println!("    {} - {} → {} {} ({}:{})",
                i.to_string().bold(),
                path_str.cyan(),
                render_markdown(&task.title),
                render_markdown(&task.summary(today)),
                rel_path.display().italic().dimmed(),
                task.line_number
            );
        }
    }

    // Build tree for other tasks
    if !other_tasks.is_empty() {
        let mut tree = TaskTree::new();
        for (i, task) in other_tasks {
            tree.add_task(task, i, today, &task_dir);
        }
        tree.print(today, &task_dir, lookahead);
    }

    println!();
    Ok(())
}

/// Simple tree structure for displaying tasks
struct TaskTree {
    nodes: Vec<TreeNode>,
}

struct TreeNode {
    label: String,
    task_info: Option<(usize, Task)>,
    children: Vec<TreeNode>,
}

impl TaskTree {
    fn new() -> Self {
        Self { nodes: Vec::new() }
    }

    fn add_task(&mut self, task: &Task, index: usize, _today: NaiveDate, task_dir: &PathBuf) {
        if task.path.is_empty() {
            // Task with no path, add directly
            self.nodes.push(TreeNode {
                label: String::new(),
                task_info: Some((index, task.clone())),
                children: Vec::new(),
            });
        } else {
            // Add task to tree structure
            let mut path = task.path.clone();
            let file_label = format!("{} ({})",
                path[0].clone(),
                task.file_path.strip_prefix(task_dir)
                    .unwrap_or(&task.file_path)
                    .display()
            );
            
            // Find or create the root node
            let root_idx = self.nodes.iter()
                .position(|n| n.label == file_label)
                .unwrap_or_else(|| {
                    self.nodes.push(TreeNode {
                        label: file_label.clone(),
                        task_info: None,
                        children: Vec::new(),
                    });
                    self.nodes.len() - 1
                });

            path.remove(0);
            Self::add_to_node(&mut self.nodes[root_idx], &path, task, index);
        }
    }

    fn add_to_node(node: &mut TreeNode, path: &[String], task: &Task, index: usize) {
        if path.is_empty() {
            // Add task here
            node.children.push(TreeNode {
                label: String::new(),
                task_info: Some((index, task.clone())),
                children: Vec::new(),
            });
        } else {
            // Find or create child node
            let label = path[0].clone();
            let child_idx = node.children.iter()
                .position(|n| n.label == label)
                .unwrap_or_else(|| {
                    node.children.push(TreeNode {
                        label: label.clone(),
                        task_info: None,
                        children: Vec::new(),
                    });
                    node.children.len() - 1
                });

            Self::add_to_node(&mut node.children[child_idx], &path[1..], task, index);
        }
    }

    fn print(&self, today: NaiveDate, task_dir: &PathBuf, lookahead: i64) {
        for node in &self.nodes {
            self.print_node(node, "└── ", "    ", today, task_dir, lookahead);
        }
    }

    fn print_node(&self, node: &TreeNode, prefix: &str, indent: &str, today: NaiveDate, task_dir: &PathBuf, lookahead: i64) {
        if let Some((index, ref task)) = node.task_info {
            // Print task
            let rel_path = task.file_path.strip_prefix(task_dir)
                .unwrap_or(&task.file_path);
            println!("{}{} - {} {} ({}:{})",
                prefix,
                index.to_string().bold(),
                render_markdown(&task.title),
                render_markdown(&task.summary(today)),
                rel_path.display().italic().dimmed(),
                task.line_number
            );

            // Print visible subtasks
            for subtask in &task.subtasks {
                if !subtask.done && subtask.is_displayed(today, lookahead) {
                    println!("{}    ├── {} {}",
                        indent,
                        render_markdown(&subtask.title),
                        render_markdown(&subtask.summary(today))
                    );
                }
            }
        } else if !node.label.is_empty() {
            // Print heading (headings may contain markdown too)
            println!("{}{}", prefix, render_markdown(&node.label).bold());
            for (i, child) in node.children.iter().enumerate() {
                let is_last = i == node.children.len() - 1;
                let child_prefix = if is_last { "└── " } else { "├── " };
                let child_indent = if is_last { "    " } else { "│   " };
                self.print_node(
                    child,
                    &format!("{}{}", indent, child_prefix),
                    &format!("{}{}", indent, child_indent),
                    today,
                    task_dir,
                    lookahead
                );
            }
        }
    }
}

