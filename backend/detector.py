from __future__ import annotations

from dataclasses import dataclass
from typing import List

import cv2
import numpy as np


@dataclass
class AvatarCandidate:
    x: int
    y: int
    width: int
    height: int
    corner_radius: int
    score: float


def detect_right_side_avatars(image: np.ndarray) -> List[AvatarCandidate]:
    normalized, scale = _normalize_image(image)
    bubbles = _detect_right_bubbles(normalized)
    candidates = _detect_candidates_from_bubbles(normalized, bubbles)
    deduped = _dedupe_candidates(candidates)

    if scale != 1.0:
        return [
            AvatarCandidate(
                x=int(candidate.x / scale),
                y=int(candidate.y / scale),
                width=int(candidate.width / scale),
                height=int(candidate.height / scale),
                corner_radius=max(1, int(candidate.corner_radius / scale)),
                score=round(candidate.score, 4),
            )
            for candidate in deduped
        ]

    return [
            AvatarCandidate(
                x=candidate.x,
                y=candidate.y,
                width=candidate.width,
                height=candidate.height,
                corner_radius=candidate.corner_radius,
                score=round(candidate.score, 4),
            )
            for candidate in deduped
        ]


def _normalize_image(image: np.ndarray) -> tuple[np.ndarray, float]:
    height, width = image.shape[:2]
    if width <= 1280:
        return image.copy(), 1.0

    scale = 1280.0 / float(width)
    resized = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
    return resized, scale


def _detect_right_bubbles(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    frame_height, frame_width = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    bubble_mask = cv2.inRange(hsv, (32, 45, 70), (95, 255, 255))

    bgr = image.astype(np.int16)
    green_dominance = (bgr[:, :, 1] > bgr[:, :, 2] + 10) & (bgr[:, :, 1] > bgr[:, :, 0] + 8)
    right_side_mask = np.zeros((frame_height, frame_width), dtype=np.uint8)
    right_side_mask[:, int(frame_width * 0.42) :] = 255
    combined = cv2.bitwise_and(bubble_mask, bubble_mask, mask=right_side_mask)
    combined[green_dominance] = 255

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bubbles: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        area = width * height
        if area < 2200:
            continue
        if width < int(frame_width * 0.09) or height < int(frame_height * 0.018):
            continue
        if x + width < int(frame_width * 0.66):
            continue
        if width < height * 1.15:
            continue
        bubbles.append((x, y, width, height))

    return sorted(bubbles, key=lambda item: item[1])


def _detect_candidates_from_bubbles(
    image: np.ndarray,
    bubbles: list[tuple[int, int, int, int]],
) -> list[AvatarCandidate]:
    frame_height, frame_width = image.shape[:2]
    background_color = _estimate_background_color(image)
    candidates: list[AvatarCandidate] = []

    for bubble_x, bubble_y, bubble_width, bubble_height in bubbles:
        avatar = _locate_avatar_near_bubble(
            image,
            bubble_x,
            bubble_y,
            bubble_width,
            bubble_height,
            background_color,
        )
        if avatar is None:
            avatar = _fallback_avatar_box(frame_width, frame_height, bubble_x, bubble_y, bubble_width, bubble_height)

        x, y, width, height, score = avatar
        if width <= 0 or height <= 0:
            continue

        radius = _estimate_corner_radius(image, x, y, width, height, background_color)
        candidates.append(
            AvatarCandidate(
                x=x,
                y=y,
                width=width,
                height=height,
                corner_radius=radius,
                score=score,
            )
        )

    return candidates


def _locate_avatar_near_bubble(
    image: np.ndarray,
    bubble_x: int,
    bubble_y: int,
    bubble_width: int,
    bubble_height: int,
    background_color: np.ndarray,
) -> tuple[int, int, int, int, float] | None:
    frame_height, frame_width = image.shape[:2]
    x0 = min(frame_width - 1, bubble_x + bubble_width + max(6, int(frame_width * 0.007)))
    x1 = min(frame_width, bubble_x + bubble_width + int(frame_width * 0.18))
    y0 = max(0, bubble_y - int(bubble_height * 0.16))
    y1 = min(frame_height, bubble_y + bubble_height + int(bubble_height * 0.16))
    if x1 - x0 < 24 or y1 - y0 < 24:
        return None

    roi = image[y0:y1, x0:x1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 55, 150)

    diff = np.linalg.norm(roi.astype(np.int16) - background_color.astype(np.int16), axis=2).astype(np.uint8)
    _, foreground = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)

    merged = cv2.bitwise_or(edges, foreground)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    merged = cv2.morphologyEx(merged, cv2.MORPH_CLOSE, kernel, iterations=2)
    merged = cv2.morphologyEx(merged, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_box: tuple[int, int, int, int, float] | None = None
    best_score = -1.0
    bubble_center_y = bubble_y + (bubble_height / 2.0)

    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if width * height < 900:
            continue

        aspect_ratio = width / float(height)
        if aspect_ratio < 0.82 or aspect_ratio > 1.18:
            continue

        if width < int(bubble_height * 0.55) or width > int(bubble_height * 1.25):
            continue

        full_x = x0 + x
        full_y = y0 + y
        vertical_offset = abs((full_y + height / 2.0) - bubble_center_y) / max(1.0, bubble_height)
        right_margin = (frame_width - (full_x + width)) / max(1.0, frame_width)
        size_similarity = min(width, bubble_height) / max(width, bubble_height)

        score = (size_similarity * 1.2) + ((1.0 - min(vertical_offset, 1.0)) * 1.4) + ((1.0 - min(right_margin * 8.0, 1.0)) * 1.0)
        if score > best_score:
            best_score = score
            best_box = (full_x, full_y, width, height, score)

    return best_box


def _fallback_avatar_box(
    frame_width: int,
    frame_height: int,
    bubble_x: int,
    bubble_y: int,
    bubble_width: int,
    bubble_height: int,
) -> tuple[int, int, int, int, float]:
    size = int(np.clip(bubble_height * 0.92, frame_width * 0.045, frame_width * 0.12))
    gap = max(8, int(size * 0.18))
    x = min(frame_width - size - max(8, int(frame_width * 0.03)), bubble_x + bubble_width + gap)
    y = int(np.clip(bubble_y + ((bubble_height - size) / 2.0), 0, frame_height - size))
    return x, y, size, size, 0.24


def _estimate_background_color(image: np.ndarray) -> np.ndarray:
    frame_height, frame_width = image.shape[:2]
    border = max(8, int(min(frame_height, frame_width) * 0.012))
    samples = np.concatenate(
        [
            image[:border, :, :].reshape(-1, 3),
            image[-border:, :, :].reshape(-1, 3),
            image[:, :border, :].reshape(-1, 3),
            image[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    return np.median(samples, axis=0)


def _estimate_corner_radius(
    image: np.ndarray,
    x: int,
    y: int,
    width: int,
    height: int,
    background_color: np.ndarray,
) -> int:
    crop = image[y : y + height, x : x + width]
    if crop.size == 0:
        return max(4, int(min(width, height) * 0.16))

    size = min(width, height)
    default_radius = max(4, int(size * 0.16))
    best_radius = default_radius
    best_distance = float("inf")

    for radius in range(max(4, int(size * 0.1)), max(5, int(size * 0.28)), 2):
        outside_mask = _build_outside_corner_mask(width, height, radius)
        if outside_mask is None:
            continue
        sample = crop[outside_mask]
        if sample.size == 0:
            continue
        distance = np.mean(np.linalg.norm(sample.astype(np.int16) - background_color.astype(np.int16), axis=1))
        if distance < best_distance:
            best_distance = distance
            best_radius = radius

    return best_radius


def _build_outside_corner_mask(width: int, height: int, radius: int) -> np.ndarray | None:
    if radius <= 0 or radius * 2 >= min(width, height):
        return None

    mask = np.zeros((height, width), dtype=bool)

    patch_y, patch_x = np.indices((radius, radius))
    tl = np.sqrt((patch_x - (radius - 1)) ** 2 + (patch_y - (radius - 1)) ** 2) >= radius
    tr = np.sqrt(patch_x**2 + (patch_y - (radius - 1)) ** 2) >= radius
    bl = np.sqrt((patch_x - (radius - 1)) ** 2 + patch_y**2) >= radius
    br = np.sqrt(patch_x**2 + patch_y**2) >= radius

    mask[0:radius, 0:radius] = tl
    mask[0:radius, width - radius : width] = tr
    mask[height - radius : height, 0:radius] = bl
    mask[height - radius : height, width - radius : width] = br

    return mask


def _dedupe_candidates(candidates: list[AvatarCandidate]) -> list[AvatarCandidate]:
    result: list[AvatarCandidate] = []
    for candidate in sorted(candidates, key=lambda item: (item.y, -item.score)):
        if any(_overlaps(candidate, existing) for existing in result):
            continue
        result.append(candidate)
    return sorted(result, key=lambda item: item.y)


def _overlaps(left: AvatarCandidate, right: AvatarCandidate) -> bool:
    x1 = max(left.x, right.x)
    y1 = max(left.y, right.y)
    x2 = min(left.x + left.width, right.x + right.width)
    y2 = min(left.y + left.height, right.y + right.height)
    if x2 <= x1 or y2 <= y1:
        return False

    intersection = (x2 - x1) * (y2 - y1)
    left_area = left.width * left.height
    right_area = right.width * right.height
    smaller = min(left_area, right_area)
    return intersection / float(smaller) > 0.35
