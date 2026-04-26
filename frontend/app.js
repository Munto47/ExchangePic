const screenshotInput = document.getElementById("screenshot");
const avatarInput = document.getElementById("avatar");
const detectButton = document.getElementById("detectButton");
const replaceButton = document.getElementById("replaceButton");
const statusText = document.getElementById("status");
const previewImage = document.getElementById("previewImage");
const overlay = document.getElementById("overlay");
const context = overlay.getContext("2d");

let screenshotUrl = null;
let detectedCandidates = [];
let displayScaleX = 1;
let displayScaleY = 1;

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "var(--danger)" : "var(--muted)";
}

function revokeScreenshotUrl() {
  if (screenshotUrl) {
    URL.revokeObjectURL(screenshotUrl);
    screenshotUrl = null;
  }
}

function resetPreview() {
  detectedCandidates = [];
  replaceButton.disabled = true;
  previewImage.style.display = "none";
  overlay.style.display = "none";
  context.clearRect(0, 0, overlay.width, overlay.height);
}

function drawCandidates() {
  context.clearRect(0, 0, overlay.width, overlay.height);
  detectedCandidates.forEach((candidate) => {
    const x = candidate.x * displayScaleX;
    const y = candidate.y * displayScaleY;
    const width = candidate.width * displayScaleX;
    const height = candidate.height * displayScaleY;

    context.lineWidth = 3;
    context.strokeStyle = candidate.selected ? "#2f8f57" : "#d95c5c";
    context.fillStyle = candidate.selected ? "rgba(47, 143, 87, 0.16)" : "rgba(217, 92, 92, 0.14)";
    context.beginPath();
    context.roundRect(x, y, width, height, 12);
    context.fill();
    context.stroke();

    context.fillStyle = candidate.selected ? "#21683f" : "#a14545";
    context.font = "600 14px 'Segoe UI'";
    context.fillText(candidate.selected ? "替换" : "跳过", x + 10, y + 22);
  });
}

function syncOverlaySize() {
  const renderedWidth = previewImage.clientWidth;
  const renderedHeight = previewImage.clientHeight;
  overlay.width = renderedWidth;
  overlay.height = renderedHeight;
  overlay.style.width = `${renderedWidth}px`;
  overlay.style.height = `${renderedHeight}px`;
  displayScaleX = renderedWidth / previewImage.naturalWidth;
  displayScaleY = renderedHeight / previewImage.naturalHeight;
  drawCandidates();
}

function ensureFilesReady() {
  if (!screenshotInput.files[0]) {
    setStatus("请先上传聊天截图。", true);
    return false;
  }
  if (!avatarInput.files[0]) {
    setStatus("请先上传新头像。", true);
    return false;
  }
  return true;
}

async function runDetection() {
  if (!ensureFilesReady()) {
    return;
  }

  setStatus("正在识别右侧头像候选框...");
  detectButton.disabled = true;
  replaceButton.disabled = true;

  revokeScreenshotUrl();
  screenshotUrl = URL.createObjectURL(screenshotInput.files[0]);
  previewImage.onload = () => {
    previewImage.style.display = "block";
    overlay.style.display = "block";
    syncOverlaySize();
  };
  previewImage.src = screenshotUrl;

  const formData = new FormData();
  formData.append("screenshot", screenshotInput.files[0]);

  try {
    const response = await fetch("/detect", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "识别失败。");
    }

    detectedCandidates = payload.candidates || [];
    drawCandidates();

    if (detectedCandidates.length === 0) {
      setStatus(payload.message || "未检测到可替换头像。", true);
      return;
    }

    replaceButton.disabled = false;
    const count = detectedCandidates.length;
    setStatus(`已检测到 ${count} 个右侧头像候选框，可直接点击进行修正。`);
  } catch (error) {
    resetPreview();
    setStatus(error.message || "识别失败。", true);
  } finally {
    detectButton.disabled = false;
  }
}

function findCandidateAt(canvasX, canvasY) {
  return detectedCandidates.find((candidate) => {
    const x = candidate.x * displayScaleX;
    const y = candidate.y * displayScaleY;
    const width = candidate.width * displayScaleX;
    const height = candidate.height * displayScaleY;
    return canvasX >= x && canvasX <= x + width && canvasY >= y && canvasY <= y + height;
  });
}

async function runReplacement() {
  if (!ensureFilesReady()) {
    return;
  }
  if (!detectedCandidates.some((candidate) => candidate.selected)) {
    setStatus("请至少保留一个要替换的头像框。", true);
    return;
  }

  setStatus("正在生成替换结果...");
  replaceButton.disabled = true;

  const formData = new FormData();
  formData.append("screenshot", screenshotInput.files[0]);
  formData.append("avatar", avatarInput.files[0]);
  formData.append("candidates_json", JSON.stringify(detectedCandidates));

  try {
    const response = await fetch("/replace", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail || "替换失败。");
    }

    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = "exchange-result.png";
    link.click();
    URL.revokeObjectURL(downloadUrl);
    setStatus("替换完成，结果图已开始下载。");
  } catch (error) {
    setStatus(error.message || "替换失败。", true);
  } finally {
    replaceButton.disabled = false;
  }
}

detectButton.addEventListener("click", runDetection);
replaceButton.addEventListener("click", runReplacement);

overlay.addEventListener("click", (event) => {
  const rect = overlay.getBoundingClientRect();
  const canvasX = event.clientX - rect.left;
  const canvasY = event.clientY - rect.top;
  const candidate = findCandidateAt(canvasX, canvasY);
  if (!candidate) {
    return;
  }
  candidate.selected = !candidate.selected;
  drawCandidates();
});

window.addEventListener("resize", () => {
  if (previewImage.style.display !== "none") {
    syncOverlaySize();
  }
});

screenshotInput.addEventListener("change", () => {
  resetPreview();
  revokeScreenshotUrl();
  setStatus("聊天截图已更新，请重新进行自动识别。");
});

avatarInput.addEventListener("change", () => {
  if (detectedCandidates.length > 0) {
    setStatus("新头像已更新，可直接生成结果或重新识别。");
  } else {
    setStatus("新头像已上传，等待识别聊天截图。");
  }
});
