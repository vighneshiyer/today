use clap::Parser;
use today::cli::{CliArgs, parse_task_files, display_specific_task, display_tasks_tree};
use std::process;

fn main() {
    if let Err(e) = run() {
        eprintln!("Error: {}", e);
        process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let args = CliArgs::parse();
    let today = args.get_today()?;

    // Parse all task files
    let tasks = parse_task_files(&args)?;

    // If a specific task_id is provided, display that task
    if let Some(task_id_result) = args.get_task_id() {
        match task_id_result {
            Ok(task_id) => {
                if task_id >= tasks.len() {
                    return Err(format!("Task ID {} does not exist (only {} tasks found)", task_id, tasks.len()));
                }
                display_specific_task(&tasks[task_id], today);
            }
            Err(task_str) => {
                return Err(format!("Invalid task ID: {}", task_str));
            }
        }
    } else {
        // Display all tasks as a tree
        display_tasks_tree(&args, &tasks)?;
    }

    Ok(())
}
