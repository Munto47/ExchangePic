# ExchangePic

一个面向微信风格聊天截图的头像替换 MVP。上传聊天截图和新头像后，工具会自动识别截图右侧“我发送的消息”头像位置，支持点选修正后导出结果图。

## 功能范围

- 自动识别微信风格聊天截图中的右侧头像候选框
- 基于“右侧头像 + 左侧消息气泡”规则过滤误检
- 支持在预览中点选候选框，决定哪些头像参与替换
- 用新头像批量替换选中的头像，并导出 PNG 结果图

## 技术栈

- FastAPI
- OpenCV
- Pillow
- NumPy
- 原生 HTML/CSS/JavaScript

## 启动方式

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

## API

### `POST /detect`

`multipart/form-data`

- `screenshot`: 聊天截图

返回：

```json
{
  "image_width": 1170,
  "image_height": 2532,
  "candidates": [
    {
      "id": "candidate-1",
      "x": 1020,
      "y": 320,
      "width": 72,
      "height": 72,
      "score": 0.41,
      "selected": true
    }
  ],
  "message": null
}
```

### `POST /replace`

`multipart/form-data`

- `screenshot`: 原始聊天截图
- `avatar`: 新头像
- `candidates_json`: 前端确认后的候选框数组 JSON

成功后直接返回 `image/png` 文件流。

## 当前假设

- 只适配微信风格单聊截图
- 不依赖旧头像样本
- 优先处理常见圆形头像显示
- 允许少量误检，通过点选修正来兜底

## 后续可扩展方向

- 增加 OCR 和昵称识别，提升群聊与复杂主题兼容性
- 针对长截图和不同分辨率调优检测阈值
- 支持批量处理和桌面端封装
"# ExchangePic" 
