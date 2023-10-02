from fastapi.testclient import TestClient

from app.app import app

# Initialize the TestClient
client = TestClient(app)


def test_composition_analysis():
    # Use a sample image from the tests/data directory for testing
    with open("tests/data/symmetric_image.jpeg", "rb") as img_file:
        response = client.post("/composition-analysis", files={"file": img_file.read()})
    assert response.status_code == 200
    json_data = response.json()
    assert "symmetry_score" in json_data
    assert "rule_of_thirds_score" in json_data
    assert "aesthetic_score" in json_data
    assert "feedback" in json_data


def test_analyze():
    # Use a sample image from the tests/data directory for testing
    with open("tests/data/high_variance_image.jpeg", "rb") as img_file:
        response = client.post("/analyze", data={"brand_color": "#FF5733"}, files={"file": img_file.read()})
    assert response.status_code == 200
    json_data = response.json()
    assert "dominant_color" in json_data
    assert "average_colors" in json_data
    assert "color_variation" in json_data
    assert "predictive_score" in json_data
    assert "performance_tips" in json_data
