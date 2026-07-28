# TK CLI 运营工具（本机运行）

云端沙盒已被 TikTok 按 IP 封锁（实测：API 端点全部超时）。这个工具跑在**你自己的电脑**上——本机住宅 IP 不会被风控。一次扫码登录后，发帖全部命令行完成。

## 安装（一次性）

```bash
pip install playwright
playwright install chromium
```

## 使用

```bash
# 1. 登录（打开浏览器，手机 TikTok 扫码，只需一次）
python3 tk.py login

# 2. 检查状态
python3 tk.py status

# 3. 发单条（--ai-label 自动勾选 AI 内容标签）
python3 tk.py post videos/tk_v1_artdeco_room.mp4 \
  --caption "POV: your living room but it looks like a 1920s Gatsby hotel lobby" \
  --tags "#gallerywall #artdeco #homedecor #printableart" \
  --ai-label

# 先试跑不真发（浏览器停留60秒供检查）
python3 tk.py post videos/tk_v1_artdeco_room.mp4 --caption "test" --dry-run

# 4. 批量排期发帖
python3 tk.py batch schedule.csv
```

## schedule.csv 格式

```csv
video,caption,tags,ai_label,posted,gap_seconds
videos/tk_v1_artdeco_room.mp4,"POV: Gatsby hotel lobby","#gallerywall #artdeco",yes,,1800
```

- `posted` 留空=待发；发完手动标 yes
- `gap_seconds` 每条间隔，默认 1800 秒（30分钟），防触发发布频率风控

## 注意

1. **登录态保存在 ~/.tk_cli_session**，不要删除；过期后重跑 `login`
2. 新账号每天发帖 ≤3 条，一周后再加量
3. 发布页的文案编辑器/按钮结构若因 TK 改版失效，脚本会自动截图 `post_error_*.png`，此时改为手动发帖，文案从 ../tk_campaign/captions.md 复制
4. 本工具只在你本机操作你自己的账号，请勿用于批量矩阵号——关联连坐封号
5. 视频素材和文案在 ../tk_campaign/ 目录
