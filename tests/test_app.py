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


# def test_black_image():
#     with open("tests/data/black_image.jpg", "rb") as img_file:
#         response = client.post("/analyze", files={"file": img_file.read()})
#     assert response.status_code == 200
#     json_data = response.json()
#     # Validate the output - dominant color should be black, variation should be low
#     assert json_data["dominant_color"] == [0, 0, 0]
#     assert all(value < 5 for value in json_data["color_variation"].values())


def test_white_image():
    with open("tests/data/white_image.png", "rb") as img_file:
        response = client.post("/analyze", files={"file": img_file.read()})
    assert response.status_code == 200
    json_data = response.json()
    # Validate the output - dominant color should be white, variation should be low
    assert json_data["dominant_color"] == [255, 255, 255]
    assert all(value < 5 for value in json_data["color_variation"].values())


def test_high_variation_image():
    with open("tests/data/high_variation_image.jpeg", "rb") as img_file:
        response = client.post("/analyze", files={"file": img_file.read()})
    assert response.status_code == 200
    json_data = response.json()
    # Validate the output - variation should be high
    assert all(value > 100 for value in json_data["color_variation"].values())


def test_low_quality_image():
    with open("tests/data/low_quality_image.jpeg", "rb") as img_file:
        response = client.post("/analyze", files={"file": img_file.read()})
    assert response.status_code == 200
    json_data = response.json()
    # Validate the output - ensure the API can handle low-quality images and returns some sensible output
    assert json_data is not None
