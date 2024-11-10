# Task Manager Application

This application is built using Dash and Flask to manage tasks and save them to a SQLite database.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Run setup**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **View app**
   Open your browser and navigate to: http://127.0.0.1:8050/

## Files

- app.py: Combined Flask backend and Dash frontend.
- requirements.txt: List of required Python packages.
- setup.sh: Script to set up the Anaconda environment.

## Features

- Add new tasks with details such as name, complexity, type, due date, priority, and repeatable status.
- View all current tasks in a table.
- Recommend tasks based on user's mood.
- Start a task and log the start time.
- Stop a task and log the end time, updating the total time worked.
- Finish a task, log the end time, update the total time worked, and rate the task.
