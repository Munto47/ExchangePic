from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.detector import detect_right_side_avatars
from backend.replacer import replace_avatars
from backend.schemas import CandidateBox, DetectResponse
from backend.utils import decode_image_bytes, image_to_png_bytes


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="ExchangePic", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/detect", response_model=DetectResponse)
async def detect(screenshot: UploadFile = File(...)) -> DetectResponse:
    screenshot_bytes = await screenshot.read()
    try:
        image = decode_image_bytes(screenshot_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    candidates = detect_right_side_avatars(image)
    boxes = [
        CandidateBox(
            id=f"candidate-{index}",
            x=candidate.x,
            y=candidate.y,
            width=candidate.width,
            height=candidate.height,
            corner_radius=candidate.corner_radius,
            score=candidate.score,
            selected=True,
        )
        for index, candidate in enumerate(candidates, start=1)
    ]

    message = None
    if not boxes:
        message = "未检测到右侧可替换头像，请尝试更清晰的微信风格聊天截图。"

    return DetectResponse(
        image_width=image.shape[1],
        image_height=image.shape[0],
        candidates=boxes,
        message=message,
    )


@app.post("/replace")
async def replace(
    screenshot: UploadFile = File(...),
    avatar: UploadFile = File(...),
    candidates_json: str = Form(...),
) -> Response:
    screenshot_bytes = await screenshot.read()
    avatar_bytes = await avatar.read()

    try:
        screenshot_image = decode_image_bytes(screenshot_bytes)
        avatar_image = decode_image_bytes(avatar_bytes, preserve_alpha=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        raw_candidates = json.loads(candidates_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="候选框参数格式不正确。") from exc

    if not isinstance(raw_candidates, list):
        raise HTTPException(status_code=400, detail="候选框参数必须是数组。")

    selected_boxes: List[dict] = []
    for item in raw_candidates:
        if not isinstance(item, dict):
            continue
        if not item.get("selected", True):
            continue
        selected_boxes.append(item)

    if not selected_boxes:
        raise HTTPException(status_code=400, detail="没有选中任何需要替换的头像。")

    result = replace_avatars(screenshot_image, avatar_image, selected_boxes)
    png_bytes = image_to_png_bytes(result)
    headers = {"Content-Disposition": 'attachment; filename="exchange-result.png"'}
    return Response(content=png_bytes, media_type="image/png", headers=headers)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
