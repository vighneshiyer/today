use clap::Parser;
use today::cli::{CliArgs, parse_task_files};
use std::fs;
use std::path::Path;
use std::process::{self, Command};

fn main() {
    if let Err(e) = run() {
        eprintln!("Error: {}", e);
        process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let args = CliArgs::parse();
    let task_file = Path::new("/tmp/task");

    if args.task_id.is_none() {
        // Clear the task file
        fs::write(task_file, "")
            .map_err(|e| format!("Failed to write to /tmp/task: {}", e))?;
    } else {
        // Parse tasks and write the selected task
        let tasks = parse_task_files(&args)?;
        let task_dir = args.task_dir()?;

        let task_snippet = if let Some(task_id_result) = args.get_task_id() {
            match task_id_result {
                Ok(task_id) => {
                    if task_id >= tasks.len() {
                        return Err(format!(
                            "The task id provided ({}) is not in range, rerun today",
                            task_id
                        ));
                    }
                    let task = &tasks[task_id];
                    let path = task.path.join(" <span weight='bold'>/</span> ");
                    let rel_path = task.file_path.strip_prefix(&task_dir)
                        .unwrap_or(&task.file_path);
                    
                    format!(
                        "<span color='white'> {} <span weight='bold' color='red'>→</span> {} <span color='lightgray'>({}: {})</span></span>",
                        path,
                        task.title,
                        rel_path.display(),
                        task.line_number
                    )
                }
                Err(task_str) => {
                    // Ad-hoc task
                    format!(
                        "<span color='white' weight='bold'>Ad-hoc task:</span> <span color='lightgrey'>{}</span>",
                        task_str
                    )
                }
            }
        } else {
            String::new()
        };

        fs::write(task_file, task_snippet)
            .map_err(|e| format!("Failed to write to /tmp/task: {}", e))?;
    }

    // Signal i3status to reload
    let _ = Command::new("killall")
        .args(["-USR1", "i3status"])
        .output();

    Ok(())
}
