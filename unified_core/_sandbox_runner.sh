#!/bin/bash
# _sandbox_runner.sh — Execute a command and write results to temp files
# Usage: _sandbox_runner.sh <cmd_file> <stdout_file> <stderr_file> <exitcode_file> <timeout> [workspace]
#
# This script exists to bypass Python's os.fork() deadlock when CUDA/PyTorch
# threads are active. It runs as a standalone shell process.

# CRITICAL: Prevent CUDA context from leaking into child processes
export CUDA_VISIBLE_DEVICES=""

CMD_FILE="$1"
STDOUT_FILE="$2"
STDERR_FILE="$3"
EXIT_FILE="$4"
TIMEOUT="$5"
WORKSPACE="${6:-.}"

cd "$WORKSPACE" 2>/dev/null

CMD=$(cat "$CMD_FILE")

timeout "$TIMEOUT" bash -c "$CMD" > "$STDOUT_FILE" 2> "$STDERR_FILE"
echo $? > "$EXIT_FILE"
