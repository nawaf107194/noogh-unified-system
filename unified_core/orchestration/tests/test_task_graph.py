import pytest

from unified_core.orchestration.task_graph import TaskGraph, Node

def test_validate_happy_path():
    nodes = {
        'task1': Node('task1', ['task2']),
        'task2': Node('task2', [])
    }
    graph = TaskGraph(nodes)
    assert graph.validate() == (True, None)

def test_validate_empty_graph():
    graph = TaskGraph({})
    assert graph.validate() == (False, "Task 0 depends on non-existent task 0")

def test_validate_missing_dependency():
    nodes = {
        'task1': Node('task1', ['task2']),
        'task3': Node('task3', [])
    }
    graph = TaskGraph(nodes)
    assert graph.validate() == (False, "Task task1 depends on non-existent task task2")

def test_validate_cycle_detected():
    nodes = {
        'task1': Node('task1', ['task2']),
        'task2': Node('task2', ['task3']),
        'task3': Node('task3', ['task1'])
    }
    graph = TaskGraph(nodes)
    assert graph.validate() == (False, "Graph contains cycles")

def test_validate_dangerous_chain_detected():
    nodes = {
        'task1': Node('task1', ['task2']),
        'task2': Node('task2', ['task3']),
        'task3': Node('task3', ['task4'])
    }
    graph = TaskGraph(nodes)
    assert graph.validate() == (False, "Dangerous tool chaining detected: task1 -> task2 -> task3 -> task4")

def test_validate_max_tasks_limit():
    nodes = {f'task{i}': Node(f'task{i}', []) for i in range(11)}
    graph = TaskGraph(nodes)
    assert graph.validate() == (False, "Too many tasks (11). Max 10 per plan.")