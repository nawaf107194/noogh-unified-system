import pytest

def extract_json_payload(text: str) -> Optional[str]:
    tag = re.search(r"<json>\s*(\{.*\})\s*</json>", text, re.DOTALL)
    if tag:
        return tag.group(1)

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None

@pytest.mark.parametrize("text, expected", [
    ('<json>{"key": "value"}</json>', '{"key": "value"}'),
    ('{"key": "value"}', '{"key": "value"}'),
    ('This is a string with {no json}', None),
    ('', None),
    (None, None),
    ('   <json>  {"key": "value"} </json>  ', '{"key": "value"}'),
])
def test_extract_json_payload(text, expected):
    result = extract_json_payload(text)
    assert result == expected

@pytest.mark.parametrize("text", [
    '<json>{"key": "value',
    'This is a string with {no json}',
    '',
    None,
    '{}{"invalid": "json"}{}'
])
def test_extract_json_payload_error_cases(text):
    result = extract_json_payload(text)
    assert result is None