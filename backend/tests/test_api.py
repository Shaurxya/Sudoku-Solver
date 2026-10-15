import io
import cv2
from fastapi.testclient import TestClient
from backend.main import app
from backend.tests.synthetic_sudoku import generate_synthetic_sudoku_image

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_api_validate():
    valid_grid = [[0 for _ in range(9)] for _ in range(9)]
    valid_grid[0][0] = 5
    res = client.post("/api/validate", json={"grid": valid_grid})
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["is_solvable"] is True

    # Invalid duplicate
    valid_grid[0][1] = 5
    res = client.post("/api/validate", json={"grid": valid_grid})
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


def test_api_hint():
    grid = [
        [1, 2, 3, 4, 5, 6, 7, 8, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    res = client.post("/api/hint", json={"grid": grid})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["hint"]["value"] == 9
    assert data["hint"]["row"] == 0
    assert data["hint"]["col"] == 8
    assert data["overlay_image"].startswith("data:image/png;base64,")


def test_api_solve():
    grid = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    res = client.post("/api/solve", json={"grid": grid})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["solved_grid"] is not None
    assert data["solved_grid"][0][0] == 5


def test_api_scan():
    grid = [[0 for _ in range(9)] for _ in range(9)]
    grid[0][0] = 5
    img, _ = generate_synthetic_sudoku_image(grid, image_size=450, margin=20)

    _, encoded = cv2.imencode(".png", img)
    file_bytes = io.BytesIO(encoded.tobytes())

    res = client.post(
        "/api/scan",
        files={"file": ("sudoku.png", file_bytes, "image/png")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "grid" in data
    assert "images" in data


def test_api_samples():
    res = client.get("/api/samples")
    assert res.status_code == 200
    data = res.json()
    assert "samples" in data
    assert len(data["samples"]) >= 1
    sample = data["samples"][0]
    assert "name" in sample
    assert "label" in sample
    assert sample["image"].startswith("data:image/png;base64,")


def test_api_candidates():
    grid = [[0 for _ in range(9)] for _ in range(9)]
    grid[0][0] = 5
    res = client.post("/api/candidates", json={"grid": grid})
    assert res.status_code == 200
    data = res.json()
    assert "candidates" in data
    assert len(data["candidates"]) == 9
    assert len(data["candidates"][0]) == 9
    assert data["candidates"][0][0] == []  # Non-empty cell has 0 candidates
    assert 5 not in data["candidates"][0][1]  # Adjacent cell cannot have 5

