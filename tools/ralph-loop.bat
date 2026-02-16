@echo off
REM Ralph Wiggum Loop Runner
REM Usage: ralph-loop.bat "Process Needs_Action" --max-iterations 10

REM Change to the project directory
cd /d "%~dp0.."

REM Run the Python script with the provided arguments
python tools/ralph_loop_runner.py %*