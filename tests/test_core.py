import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from backend.app.agent.core import (
    load_dataframe,
    build_prompt,
    call_claude,
    execute_code,
    analyze,
)


# ── load_dataframe ─────────────────────────────────────────────────────────────

def test_load_dataframe_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("col1,col2\n1,a\n2,b\n")
    df = load_dataframe(str(csv_file))
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["col1", "col2"]
    assert len(df) == 2


def test_load_dataframe_excel(tmp_path):
    excel_file = tmp_path / "data.xlsx"
    pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]}).to_excel(str(excel_file), index=False)
    df = load_dataframe(str(excel_file))
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["col1", "col2"]
    assert len(df) == 2


def test_load_dataframe_unsupported_format_raises(tmp_path):
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("some content")
    with pytest.raises(ValueError, match="Format non supporté"):
        load_dataframe(str(txt_file))


# ── build_prompt ───────────────────────────────────────────────────────────────

def test_build_prompt_contains_question():
    df = pd.DataFrame({"age": [25, 30], "salaire": [3000, 4000]})
    prompt = build_prompt("Quelle est la moyenne des salaires ?", df)
    assert "Quelle est la moyenne des salaires ?" in prompt


def test_build_prompt_contains_row_count():
    df = pd.DataFrame({"a": range(42)})
    prompt = build_prompt("test", df)
    assert "42" in prompt


def test_build_prompt_contains_column_names():
    df = pd.DataFrame({"age": [1], "salaire": [2]})
    prompt = build_prompt("test", df)
    assert "age" in prompt
    assert "salaire" in prompt


def test_build_prompt_contains_data_preview():
    df = pd.DataFrame({"x": [10, 20, 30, 40, 50, 60]})
    prompt = build_prompt("test", df)
    assert "10" in prompt
    assert "50" in prompt


def test_build_prompt_mentions_result_variables():
    df = pd.DataFrame({"a": [1]})
    prompt = build_prompt("test", df)
    assert "result_text" in prompt
    assert "result_fig" in prompt
    assert "result_df" in prompt


# ── call_claude ────────────────────────────────────────────────────────────────

def test_call_claude_returns_stripped_code():
    mock_message = MagicMock()
    mock_message.content[0].text = "  result_text = 'hello'  "

    with patch("backend.app.agent.core.client") as mock_client:
        mock_client.messages.create.return_value = mock_message
        result = call_claude("some prompt")

    assert result == "result_text = 'hello'"


def test_call_claude_sends_user_message():
    mock_message = MagicMock()
    mock_message.content[0].text = "code"

    with patch("backend.app.agent.core.client") as mock_client:
        mock_client.messages.create.return_value = mock_message
        call_claude("mon prompt")
        kwargs = mock_client.messages.create.call_args.kwargs

    assert kwargs["max_tokens"] == 1024
    assert kwargs["messages"][0] == {"role": "user", "content": "mon prompt"}


# ── execute_code ───────────────────────────────────────────────────────────────

def test_execute_code_text_result():
    df = pd.DataFrame({"a": [1, 2, 3]})
    code = "result_text = str(df['a'].mean())"
    result = execute_code(code, df)
    assert result["text"] == "2.0"
    assert result["figure"] is None
    assert result["dataframe"] is None


def test_execute_code_strips_python_markdown_fences():
    df = pd.DataFrame({"a": [1]})
    code = "```python\nresult_text = 'ok'\n```"
    result = execute_code(code, df)
    assert result["text"] == "ok"


def test_execute_code_strips_generic_markdown_fences():
    df = pd.DataFrame({"a": [1]})
    code = "```\nresult_text = 'clean'\n```"
    result = execute_code(code, df)
    assert result["text"] == "clean"


def test_execute_code_default_text_when_not_set():
    df = pd.DataFrame({"a": [1]})
    result = execute_code("x = 1", df)
    assert result["text"] == "Analyse terminée."


def test_execute_code_with_dataframe_result():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    code = "result_text = 'filtré'\nresult_df = df[df['a'] > 1]"
    result = execute_code(code, df)
    assert isinstance(result["dataframe"], pd.DataFrame)
    assert len(result["dataframe"]) == 2


def test_execute_code_raises_on_invalid_code():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="bad code"):
        execute_code("raise ValueError('bad code')", df)


def test_execute_code_df_accessible_in_code():
    df = pd.DataFrame({"val": [10, 20, 30]})
    code = "result_text = str(len(df))"
    result = execute_code(code, df)
    assert result["text"] == "3"


# ── analyze ────────────────────────────────────────────────────────────────────

def test_analyze_full_flow(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("age,salaire\n25,3000\n30,4000\n")

    with patch("backend.app.agent.core.call_claude") as mock_claude:
        mock_claude.return_value = "result_text = str(df['salaire'].mean())"
        result = analyze("Moyenne des salaires ?", str(csv_file))

    assert result["text"] == "3500.0"
    assert result["figure"] is None
    assert result["dataframe"] is None


def test_analyze_passes_question_to_claude(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("a,b\n1,2\n")

    with patch("backend.app.agent.core.call_claude") as mock_claude:
        mock_claude.return_value = "result_text = 'ok'"
        analyze("Ma question spécifique", str(csv_file))
        prompt_used = mock_claude.call_args.args[0]

    assert "Ma question spécifique" in prompt_used


def test_analyze_unsupported_file_raises(tmp_path):
    bad_file = tmp_path / "data.json"
    bad_file.write_text("{}")

    with pytest.raises(ValueError, match="Format non supporté"):
        analyze("question", str(bad_file))
 