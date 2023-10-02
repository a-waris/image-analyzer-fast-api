import io
from typing import List
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from cv2 import cvtColor, COLOR_BGR2GRAY, threshold, THRESH_BINARY, absdiff
from fastapi import FastAPI, HTTPException, UploadFile, Form
from numpy import fliplr, var, sum
from pydantic import BaseModel
from sklearn.cluster import KMeans
from starlette.middleware.cors import CORSMiddleware


# Define Pydantic models for request and response validation
class CompositionAnalysisResponse(BaseModel):
    symmetry_score: float
    rule_of_thirds_score: float
    aesthetic_score: float
    feedback: List[str]


class ImageAnalysisRequest(BaseModel):
    file: UploadFile
    brand_color: Optional[str]


class ImageAnalysisResponse(BaseModel):
    dominant_color: List[int]
    average_colors: dict
    color_variation: dict
    predictive_score: int
    performance_tips: List[str]


app = FastAPI()

# Add CORS middleware for convenience in case frontend and backend are hosted on different domains/ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def compute_symmetry_score(image):
    """Compute a symmetry score for the image."""
    # Convert image to grayscale
    gray = cvtColor(image, COLOR_BGR2GRAY)

    # Split the image into left and right halves
    mid_x = int(gray.shape[1] / 2)
    left_half = gray[:, :mid_x]
    right_half = gray[:, mid_x:]

    # Flip the right half and compute the similarity (SSIM) with the left half
    right_half_flipped = fliplr(right_half)
    _, score = threshold(absdiff(left_half, right_half_flipped), 25, 255, THRESH_BINARY)

    # A lower score indicates more symmetry
    return 1 - (sum(score) / (score.size * 255))


def compute_rule_of_thirds_score(image):
    """Compute a score based on the rule of thirds."""
    # The idea is to check brightness variance at the rule of thirds lines
    third_x = int(image.shape[1] / 3)
    two_third_x = int(2 * image.shape[1] / 3)
    third_y = int(image.shape[0] / 3)
    two_third_y = int(2 * image.shape[0] / 3)

    rots_regions = [
        image[:third_y, :third_x], image[:third_y, two_third_x:],
        image[two_third_y:, :third_x], image[two_third_y:, two_third_x:]
    ]

    variances = [var(region) for region in rots_regions]
    average_variance = sum(variances) / 4

    # A higher variance indicates more visual interest at the rule of thirds intersections
    return average_variance / 255


def extract_dominant_color(image, k=1):
    """Extract the dominant color from an image."""
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.reshape((image.shape[0] * image.shape[1], 3))

    clt = KMeans(n_clusters=k)
    clt.fit(image)

    return [int(value) for value in clt.cluster_centers_[0]]  # Convert float values to integers


@app.get("/")
async def root():
    return {"message": "Python-driven MVP in the works: an image analysis tool aimed at boosting brand conversions on "
                       "major ad platforms"}


@app.post("/composition-analysis", response_model=CompositionAnalysisResponse)
async def composition_analysis(file: UploadFile = Form(...)):
    try:
        # Read the image
        image_content = await file.read()
        image = cv2.imdecode(np.frombuffer(image_content, np.uint8), -1)

        # Compute the symmetry and rule of thirds scores
        symmetry_score = compute_symmetry_score(image)
        rots_score = compute_rule_of_thirds_score(image)

        # Compute the overall aesthetic score (average for now)
        aesthetic_score = (symmetry_score + rots_score) / 2

        # Provide feedback based on the score
        feedback = []
        if aesthetic_score < 0.5:
            feedback.append("Consider improving the image's composition for better aesthetic appeal.")
        else:
            feedback.append("The image has good compositional elements.")

        # Construct the result
        result = {
            'symmetry_score': symmetry_score,
            'rule_of_thirds_score': rots_score,
            'aesthetic_score': aesthetic_score,
            'feedback': feedback
        }

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_ad_image(file: UploadFile = Form(...), brand_color: Optional[str] = Form(None)):
    try:
        # Read and open the image
        image_content = await file.read()
        image = Image.open(io.BytesIO(image_content))
        image = np.array(image)

        # Extract the dominant color - RGB list of integers
        dominant_color = extract_dominant_color(image)

        # Convert HEX brand color to RGB if provided
        if brand_color:
            brand_color = [int(brand_color[i:i + 2], 16) for i in (1, 3, 5)]

        # Analyze the image properties
        mean_red, mean_green, mean_blue = np.mean(image[:, :, 0]), np.mean(image[:, :, 1]), np.mean(image[:, :, 2])
        std_red, std_green, std_blue = np.std(image[:, :, 0]), np.std(image[:, :, 1]), np.std(image[:, :, 2])

        # Compute the predictive score
        score = 50  # Starting score
        if brand_color and np.allclose(dominant_color, brand_color, atol=50):
            score += 25
        if (mean_red <= 50 or mean_red >= 200) or (mean_green <= 50 or mean_green >= 200) or (
                mean_blue <= 50 or mean_blue >= 200):
            pass
        else:
            score += 25

        # Generate performance tips
        tips = []
        if score < 75:
            tips.append("Consider enhancing the image brightness and contrast for better ad performance.")
            if brand_color and not np.allclose(dominant_color, brand_color, atol=50):
                tips.append(
                    f"Ensure the ad image aligns closer to the brand color {brand_color} for better brand consistency.")

        # Construct the result
        result = {
            'dominant_color': dominant_color,
            'average_colors': {
                'red': mean_red,
                'green': mean_green,
                'blue': mean_blue
            },
            'color_variation': {
                'red': std_red,
                'green': std_green,
                'blue': std_blue
            },
            'predictive_score': score,
            'performance_tips': tips
        }

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
