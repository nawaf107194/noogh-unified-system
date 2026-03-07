import pytest

def format_gsm8k(example):
    return {"text": f"Q: {example['question']}\nA: {example['answer']}"} if example else None

def test_format_gsm8k_happy_path():
    example = {'question': 'What is the capital of France?', 'answer': 'Paris'}
    assert format_gsm8k(example) == {"text": "Q: What is the capital of France?\nA: Paris"}

def test_format_gsm8k_empty_input():
    example = {}
    assert format_gsm8k(example) is None

def test_format_gsm8k_none_input():
    example = None
    assert format_gsm8k(example) is None

def test_format_gsm8k_boundary_case_question_only():
    example = {'question': 'What is the capital of France?'}
    assert format_gsm8k(example) is None

def test_format_gsm8k_boundary_case_answer_only():
    example = {'answer': 'Paris'}
    assert format_gsm8k(example) is None