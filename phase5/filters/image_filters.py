"""
Phase 5: Image Filters (OpenCV)
A collection of filters that can be applied to scene images for video_frame edits.
Supports: darken, brighten, sepia, grayscale, blur, sharpen, saturate, warm, cool, vintage
"""

import cv2
import numpy as np
from pathlib import Path


# ─── Filter Registry ─────────────────────────────────────────────────────────

AVAILABLE_FILTERS = [
    "darken", "brighten", "sepia", "grayscale", "blur",
    "sharpen", "saturate", "desaturate", "warm", "cool", "vintage",
    "contrast_boost", "vignette", "edge_enhance"
]


def apply_filter_to_image(image_path: str, filter_name: str, params: dict = None) -> dict:
    """
    Apply a named filter to a single image file (in-place replacement).

    Args:
        image_path: Path to the PNG/JPG image
        filter_name: Name of the filter (see AVAILABLE_FILTERS)
        params: Optional extra parameters (e.g. brightness offset)

    Returns:
        dict with success (bool) and message (str)
    """
    if params is None:
        params = {}

    path = Path(image_path)
    if not path.exists():
        return {"success": False, "message": f"Image not found: {image_path}"}

    img = cv2.imread(str(path))
    if img is None:
        return {"success": False, "message": f"Could not read image: {image_path}"}

    try:
        result = _dispatch_filter(img, filter_name.lower(), params)
    except Exception as e:
        return {"success": False, "message": f"Filter error: {e}"}

    cv2.imwrite(str(path), result)
    return {"success": True, "message": f"Filter '{filter_name}' applied to {path.name}"}


def apply_filter_to_all_scenes(images_dir: str, filter_name: str, params: dict = None) -> dict:
    """Apply a filter to every image in a directory."""
    if params is None:
        params = {}

    folder = Path(images_dir)
    image_files = list(folder.glob("*.png")) + list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg"))

    if not image_files:
        return {"success": False, "message": "No images found in directory."}

    errors = []
    for img_path in image_files:
        result = apply_filter_to_image(str(img_path), filter_name, params)
        if not result["success"]:
            errors.append(result["message"])

    if errors:
        return {"success": False, "message": f"Some images failed: {'; '.join(errors)}"}

    return {"success": True, "message": f"Filter '{filter_name}' applied to {len(image_files)} images."}


# ─── Filter Implementations ──────────────────────────────────────────────────

def _dispatch_filter(img: np.ndarray, filter_name: str, params: dict) -> np.ndarray:
    filters = {
        "darken": _darken,
        "brighten": _brighten,
        "sepia": _sepia,
        "grayscale": _grayscale,
        "blur": _blur,
        "sharpen": _sharpen,
        "saturate": _saturate,
        "desaturate": _desaturate,
        "warm": _warm,
        "cool": _cool,
        "vintage": _vintage,
        "contrast_boost": _contrast_boost,
        "vignette": _vignette,
        "edge_enhance": _edge_enhance,
    }
    fn = filters.get(filter_name)
    if fn is None:
        raise ValueError(f"Unknown filter: '{filter_name}'. Available: {AVAILABLE_FILTERS}")
    return fn(img, params)


def _darken(img: np.ndarray, params: dict) -> np.ndarray:
    amount = params.get("brightness", -60)  # negative = darker
    return cv2.convertScaleAbs(img, alpha=1.0, beta=amount)


def _brighten(img: np.ndarray, params: dict) -> np.ndarray:
    amount = params.get("brightness", 60)
    return cv2.convertScaleAbs(img, alpha=1.0, beta=amount)


def _grayscale(img: np.ndarray, params: dict) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def _sepia(img: np.ndarray, params: dict) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    normalized = gray / 255.0
    sepia = np.zeros_like(img, dtype=np.float64)
    sepia[:, :, 0] = normalized * 112   # B
    sepia[:, :, 1] = normalized * 66    # G  (brown-ish)  wait BGR
    sepia[:, :, 2] = normalized * 100   # R

    # Proper sepia tone
    sepia_kernel = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]
    ])
    img_float = img.astype(np.float64) / 255.0
    sepia_img = np.clip(img_float @ sepia_kernel.T, 0, 1)
    return (sepia_img * 255).astype(np.uint8)


def _blur(img: np.ndarray, params: dict) -> np.ndarray:
    radius = params.get("radius", 5)
    ksize = radius * 2 + 1  # must be odd
    return cv2.GaussianBlur(img, (ksize, ksize), 0)


def _sharpen(img: np.ndarray, params: dict) -> np.ndarray:
    kernel = np.array([
        [0, -1,  0],
        [-1,  5, -1],
        [0, -1,  0]
    ])
    return cv2.filter2D(img, -1, kernel)


def _saturate(img: np.ndarray, params: dict) -> np.ndarray:
    factor = params.get("factor", 1.5)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def _desaturate(img: np.ndarray, params: dict) -> np.ndarray:
    factor = params.get("factor", 0.4)
    return _saturate(img, {"factor": factor})


def _warm(img: np.ndarray, params: dict) -> np.ndarray:
    """Add warm (orange-ish) tint."""
    result = img.copy().astype(np.float32)
    result[:, :, 2] = np.clip(result[:, :, 2] * 1.15, 0, 255)  # boost Red
    result[:, :, 0] = np.clip(result[:, :, 0] * 0.9, 0, 255)   # reduce Blue
    return result.astype(np.uint8)


def _cool(img: np.ndarray, params: dict) -> np.ndarray:
    """Add cool (blue-ish) tint."""
    result = img.copy().astype(np.float32)
    result[:, :, 0] = np.clip(result[:, :, 0] * 1.15, 0, 255)  # boost Blue
    result[:, :, 2] = np.clip(result[:, :, 2] * 0.9, 0, 255)   # reduce Red
    return result.astype(np.uint8)


def _vintage(img: np.ndarray, params: dict) -> np.ndarray:
    """Combine sepia + vignette for a vintage look."""
    sepia_img = _sepia(img, {})
    return _vignette(sepia_img, {"strength": 0.5})


def _contrast_boost(img: np.ndarray, params: dict) -> np.ndarray:
    alpha = params.get("alpha", 1.4)  # contrast multiplier
    beta = params.get("beta", -20)    # brightness offset
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def _vignette(img: np.ndarray, params: dict) -> np.ndarray:
    """Darken the edges to create a vignette effect."""
    strength = params.get("strength", 0.6)
    rows, cols = img.shape[:2]

    # Create Gaussian kernels
    sigma_x = cols * strength
    sigma_y = rows * strength
    kernel_x = cv2.getGaussianKernel(cols, sigma_x)
    kernel_y = cv2.getGaussianKernel(rows, sigma_y)
    kernel = kernel_y * kernel_x.T
    mask = kernel / kernel.max()

    result = img.copy().astype(np.float32)
    for i in range(3):
        result[:, :, i] = result[:, :, i] * mask
    return np.clip(result, 0, 255).astype(np.uint8)


def _edge_enhance(img: np.ndarray, params: dict) -> np.ndarray:
    """Subtle edge enhancement (unsharp mask style)."""
    blurred = cv2.GaussianBlur(img, (0, 0), 3)
    return cv2.addWeighted(img, 1.5, blurred, -0.5, 0)
