import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ── GET /health ────────────────────────────────────────────────────────────────

def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# ── POST /analyze ──────────────────────────────────────────────────────────────

def test_analyze_returns_text_result():
    mock_result = {"text": "La moyenne est 42", "figure": None, "dataframe": None}

    with patch("backend.app.api.routes.analyze", return_value=mock_result):
        response = client.post(
            "/analyze",
            data={"question": "Quelle est la moyenne ?"},
            files={"file": ("data.csv", b"col1,col2\n1,a\n2,b\n", "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "La moyenne est 42"
    assert data["figure"] is None
    assert data["dataframe"] is None


def test_analyze_returns_dataframe_as_records():
    df_result = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    mock_result = {"text": "Résultat", "figure": None, "dataframe": df_result}

    with patch("backend.app.api.routes.analyze", return_value=mock_result):
        response = client.post(
            "/analyze",
            data={"question": "Montre le tableau"},
            files={"file": ("data.csv", b"a,b\n1,x\n2,y\n", "text/csv")},
        )

    assert response.status_code == 200
    assert response.json()["dataframe"] == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_analyze_returns_figure_as_json():
    mock_fig = MagicMock()
    mock_fig.to_json.return_value = '{"data": [], "layout": {}}'
    mock_result = {"text": "Graphique généré", "figure": mock_fig, "dataframe": None}

    with patch("backend.app.api.routes.analyze", return_value=mock_result):
        response = client.post(
            "/analyze",
            data={"question": "Montre un graphique"},
            files={"file": ("data.csv", b"x,y\n1,2\n3,4\n", "text/csv")},
        )

    assert response.status_code == 200
    assert response.json()["figure"] == '{"data": [], "layout": {}}'


def test_analyze_calls_figure_to_json():
    mock_fig = MagicMock()
    mock_fig.to_json.return_value = "{}"
    mock_result = {"text": "ok", "figure": mock_fig, "dataframe": None}

    with patch("backend.app.api.routes.analyze", return_value=mock_result):
        client.post(
            "/analyze",
            data={"question": "test"},
            files={"file": ("data.csv", b"a\n1\n", "text/csv")},
        )

    mock_fig.to_json.assert_called_once()


def test_analyze_returns_500_on_core_exception():
    with patch("backend.app.api.routes.analyze", side_effect=Exception("Erreur inattendue")):
        response = client.post(
            "/analyze",
            data={"question": "test"},
            files={"file": ("data.csv", b"a\n1\n", "text/csv")},
        )

    assert response.status_code == 500
    assert "Erreur inattendue" in response.json()["detail"]


def test_analyze_missing_question_returns_422():
    response = client.post(
        "/analyze",
        files={"file": ("data.csv", b"a\n1\n", "text/csv")},
    )
    assert response.status_code == 422


def test_analyze_missing_file_returns_422():
    response = client.post(
        "/analyze",
        data={"question": "test"},
    )
    assert response.status_code == 422


def test_analyze_cleans_up_temp_file():
    mock_result = {"text": "ok", "figure": None, "dataframe": None}

    with patch("backend.app.api.routes.analyze", return_value=mock_result), \
         patch("backend.app.api.routes.os.unlink") as mock_unlink:
        response = client.post(
            "/analyze",
            data={"question": "test"},
            files={"file": ("data.csv", b"a\n1\n", "text/csv")},
        )

    assert response.status_code == 200
    mock_unlink.assert_called_once()


def test_analyze_cleans_up_temp_file_even_on_error():
    with patch("backend.app.api.routes.analyze", side_effect=Exception("crash")), \
         patch("backend.app.api.routes.os.unlink") as mock_unlink:
        client.post(
            "/analyze",
            data={"question": "test"},
            files={"file": ("data.csv", b"a\n1\n", "text/csv")},
        )

    mock_unlink.assert_called_once()


def test_analyze_passes_question_to_core():
    mock_result = {"text": "réponse", "figure": None, "dataframe": None}

    with patch("backend.app.api.routes.analyze", return_value=mock_result) as mock_analyze:
        client.post(
            "/analyze",
            data={"question": "Combien de lignes ?"},
            files={"file": ("data.csv", b"a\n1\n2\n", "text/csv")},
        )
        call_kwargs = mock_analyze.call_args.kwargs

    assert call_kwargs["question"] == "Combien de lignes ?"


def test_analyze_preserves_excel_file_extension():
    mock_result = {"text": "ok", "figure": None, "dataframe": None}
    captured_paths = []

    def fake_analyze(question, file_path):
        captured_paths.append(file_path)
        return mock_result

    with patch("backend.app.api.routes.analyze", side_effect=fake_analyze), \
         patch("backend.app.api.routes.os.unlink"):
        client.post(
            "/analyze",
            data={"question": "test"},
            files={"file": ("report.xlsx", b"fake excel content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert captured_paths[0].endswith(".xlsx")
