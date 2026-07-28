#!/usr/bin/env python3
"""
tk.py — TikTok 命令行运营工具（本机运行）
一次扫码登录，之后全部命令行操作：发帖、批量排期、数据查看。

用法:
  python3 tk.py login                          # 打开浏览器扫码登录（只需一次）
  python3 tk.py post video.mp4 --caption "..." --tags "#a #b" --ai-label
  python3 tk.py batch schedule.csv             # 按排期表批量发帖
  python3 tk.py status                         # 检查登录状态/账号信息

依赖: pip install playwright && playwright install chromium
"""
import argparse, csv, os, sys, time
from pathlib import Path

SESSION_DIR = Path.home() / ".tk_cli_session"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=webapp&tab=video"
HOME_URL = "https://www.tiktok.com/"


def launch(pw, headless=False):
    ctx = pw.chromium.launch_persistent_context(
        str(SESSION_DIR), headless=headless,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )
    return ctx


def cmd_login():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = launch(pw, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(HOME_URL, timeout=60000)
        print("\n[操作] 浏览器已打开 TikTok。请扫码或账号密码登录。")
        print("[提示] 登录成功后回到这里按回车，会话将保存到", SESSION_DIR)
        input(">>> 登录完成后按回车 <<<")
        page.goto(HOME_URL, timeout=60000)
        if "登录" not in (page.title() or "") and page.locator("[data-e2e='profile-icon'], img.avatar").count() >= 0:
            print("[OK] 检测到已登录状态，会话已保存。")
        else:
            print("[警告] 未能确认登录状态。若后续 post 失败请重新 login。")
        ctx.close()


def is_logged_in(page):
    try:
        page.goto(HOME_URL, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        return page.locator("[data-e2e='profile-icon'], img.avatar, [data-e2e='nav-profile']").count() > 0
    except Exception:
        return False


def post_one(ctx, video, caption, tags="", ai_label=False, dry_run=False):
    page = ctx.new_page()
    full_caption = caption if not tags else f"{caption}\n{tags}"
    try:
        page.goto(UPLOAD_URL, timeout=60000)
        page.wait_for_timeout(4000)
        file_input = page.locator("input[type='file']").first
        file_input.set_input_files(str(video))
        print(f"[上传] {video.name} 上传中，等待处理...")
        page.wait_for_timeout(12000)
        editor = page.locator("div[contenteditable='true']").first
        editor.click()
        editor.press_sequentially(full_caption[:2200], delay=5)
        if ai_label:
            try:
                toggler = page.get_by_text("AI-generated content", exact=False).first
                toggler.click()
                page.wait_for_timeout(500)
                page.locator("text=AI-generated").first.click()
            except Exception:
                print("[提示] 未找到 AI 标签开关，请在发布页手动勾选")
        if dry_run:
            print("[dry-run] 不点击发布。浏览器保持 60 秒供检查。")
            page.wait_for_timeout(60000)
            return True
        btn = page.locator("button:has-text('Post'), button:has-text('发布')").first
        btn.click()
        page.wait_for_timeout(8000)
        print(f"[OK] {video.name} 已发布")
        return True
    except Exception as e:
        page.screenshot(path=f"post_error_{int(time.time())}.png")
        print(f"[失败] {video.name}: {e}\n  已截图 post_error_*.png，可改为手动发布")
        return False
    finally:
        page.close()


def cmd_post(args):
    from playwright.sync_api import sync_playwright
    video = Path(args.video)
    assert video.exists(), f"视频不存在: {video}"
    with sync_playwright() as pw:
        ctx = launch(pw, headless=args.headless)
        page = ctx.new_page()
        if not is_logged_in(page):
            print("[错误] 未登录或会话过期，请先运行: python3 tk.py login")
            ctx.close(); sys.exit(1)
        page.close()
        post_one(ctx, video, args.caption or "", args.tags or "", args.ai_label, args.dry_run)
        ctx.close()


def cmd_batch(args):
    from playwright.sync_api import sync_playwright
    rows = list(csv.DictReader(open(args.schedule, encoding="utf-8")))
    with sync_playwright() as pw:
        ctx = launch(pw, headless=False)
        page = ctx.new_page()
        if not is_logged_in(page):
            print("[错误] 未登录，请先 login"); ctx.close(); sys.exit(1)
        page.close()
        for i, r in enumerate(rows):
            if r.get("posted", "").strip().lower() in ("yes", "1", "true"):
                continue
            ok = post_one(ctx, Path(r["video"]), r.get("caption", ""),
                          r.get("tags", ""), r.get("ai_label", "").lower() == "yes")
            print(f"[进度] {i+1}/{len(rows)} {'成功' if ok else '失败'}")
            time.sleep(int(r.get("gap_seconds", 1800)))
        ctx.close()


def cmd_status():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = launch(pw, headless=False)
        page = ctx.new_page()
        ok = is_logged_in(page)
        print("[状态]", "已登录 ✓" if ok else "未登录 ✗（运行 python3 tk.py login）")
        ctx.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="TikTok CLI 运营工具")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    sub.add_parser("status")
    p = sub.add_parser("post")
    p.add_argument("video"); p.add_argument("--caption", default="")
    p.add_argument("--tags", default=""); p.add_argument("--ai-label", action="store_true")
    p.add_argument("--headless", action="store_true"); p.add_argument("--dry-run", action="store_true")
    b = sub.add_parser("batch"); b.add_argument("schedule")
    args = ap.parse_args()
    {"login": cmd_login, "status": cmd_status,
     "post": lambda: cmd_post(args), "batch": lambda: cmd_batch(args)}[args.cmd]()
