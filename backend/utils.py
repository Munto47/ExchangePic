from __future__ import annotations

from io import BytesIO

import cv2
import numpy as np
from PIL import Image


def decode_image_bytes(file_bytes: bytes, preserve_alpha: bool = False) -> np.ndarray:
    array = np.frombuffer(file_bytes, dtype=np.uint8)
    flag = cv2.IMREAD_UNCHANGED if preserve_alpha else cv2.IMREAD_COLOR
    image = cv2.imdecode(array, flag)
    if image is None:
        raise ValueError("无法读取图片，请确认上传的是有效的 PNG 或 JPEG 文件。")

    if not preserve_alpha and image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image


def normalize_for_detection(image: np.ndarray, max_width: int = 1280) -> tuple[np.ndarray, float]:
    height, width = image.shape[:2]
    if width <= max_width:
        return image.copy(), 1.0

    scale = max_width / float(width)
    resized = cv2.resize(
        image,
        (int(width * scale), int(height * scale)),
        interpolation=cv2.INTER_AREA,
    )
    return resized, scale


def image_to_png_bytes(image: np.ndarray) -> bytes:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()
