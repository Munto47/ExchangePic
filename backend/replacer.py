from __future__ import annotations

import cv2
import numpy as np


def replace_avatars(image: np.ndarray, avatar_image: np.ndarray, selected_boxes: list[dict]) -> np.ndarray:
    result = image.copy()
    avatar_rgba = _prepare_avatar(avatar_image)

    for box in selected_boxes:
        x = int(box["x"])
        y = int(box["y"])
        width = int(box["width"])
        height = int(box["height"])
        corner_radius = int(box.get("corner_radius", max(4, min(width, height) * 0.16)))
        _paste_avatar(result, avatar_rgba, x, y, width, height, corner_radius)

    return result


def _prepare_avatar(avatar_image: np.ndarray) -> np.ndarray:
    if avatar_image.ndim == 2:
        avatar_image = cv2.cvtColor(avatar_image, cv2.COLOR_GRAY2BGRA)
    if avatar_image.shape[2] == 4:
        rgba = cv2.cvtColor(avatar_image, cv2.COLOR_BGRA2RGBA)
    else:
        rgba = cv2.cvtColor(avatar_image, cv2.COLOR_BGR2RGBA)
    return rgba


def _paste_avatar(
    target: np.ndarray,
    avatar_rgba: np.ndarray,
    x: int,
    y: int,
    width: int,
    height: int,
    corner_radius: int,
) -> None:
    frame_height, frame_width = target.shape[:2]
    x = max(0, min(x, frame_width - 1))
    y = max(0, min(y, frame_height - 1))
    width = max(1, min(width, frame_width - x))
    height = max(1, min(height, frame_height - y))

    resized_avatar = _resize_and_cover(avatar_rgba, width, height)
    radius = int(np.clip(corner_radius, 0, min(width, height) // 2))
    mask = _build_rounded_rect_mask(width, height, radius)

    avatar_rgb = resized_avatar[:, :, :3]
    avatar_alpha = resized_avatar[:, :, 3].astype(np.float32) / 255.0
    blended_alpha = np.minimum(avatar_alpha, mask)

    region = target[y : y + height, x : x + width].astype(np.float32)
    avatar_rgb = cv2.cvtColor(avatar_rgb, cv2.COLOR_RGB2BGR).astype(np.float32)
    alpha = blended_alpha[:, :, None]
    composited = (avatar_rgb * alpha) + (region * (1.0 - alpha))
    target[y : y + height, x : x + width] = np.clip(composited, 0, 255).astype(np.uint8)


def _resize_and_cover(avatar_rgba: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
    src_height, src_width = avatar_rgba.shape[:2]
    scale = max(target_width / float(src_width), target_height / float(src_height))
    resized_width = max(1, int(round(src_width * scale)))
    resized_height = max(1, int(round(src_height * scale)))
    resized = cv2.resize(avatar_rgba, (resized_width, resized_height), interpolation=cv2.INTER_AREA)

    left = max(0, (resized_width - target_width) // 2)
    top = max(0, (resized_height - target_height) // 2)
    return resized[top : top + target_height, left : left + target_width]


def _build_rounded_rect_mask(width: int, height: int, radius: int) -> np.ndarray:
    if radius <= 1:
        return np.ones((height, width), dtype=np.float32)

    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(mask, (radius, 0), (width - radius - 1, height - 1), 255, thickness=-1)
    cv2.rectangle(mask, (0, radius), (width - 1, height - radius - 1), 255, thickness=-1)

    corners = [
        (radius, radius),
        (width - radius - 1, radius),
        (radius, height - radius - 1),
        (width - radius - 1, height - radius - 1),
    ]
    for center in corners:
        cv2.circle(mask, center, radius, 255, thickness=-1, lineType=cv2.LINE_AA)

    sigma = max(0.8, radius / 10.0)
    softened = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return np.clip(softened, 0.0, 1.0)
