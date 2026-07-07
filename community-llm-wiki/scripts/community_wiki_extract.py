#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
community_wiki_extract.py — 从 URL 获取内容，保存到 asset/，辅助提取 Event 信息

只保留人类可读文本内容，保存为 Markdown 格式。

用法：
    # 从 URL 获取内容并保存到 asset/
    python community_wiki_extract.py --community ./my-community --url "https://..."

    # 查看 asset/ 目录中已保存的内容
    python community_wiki_extract.py --community ./my-community --list

    # 查看单条已保存内容
    python community_wiki_extract.py --community ./my-community --show <filename>
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


class TextExtractor(HTMLParser):
    """Extract readable text from HTML, preserving paragraph structure."""

    def __init__(self):
        super().__init__()
        self._text = []
        self._skip = False
        self._skip_tags = {"script", "style", "noscript"}
        self._block_tags = {"p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6",
                            "li", "tr", "th", "td", "blockquote", "section", "article",
                            "header", "footer", "nav", "main", "aside"}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip = True
        if tag == "br" and self._text:
            self._text.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip = False
        if tag in self._block_tags and self._text:
            self._text.append("\n\n")

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._text.append(text)

    def get_text(self) -> str:
        raw = "".join(self._text)
        lines = [line.strip() for line in raw.split("\n")]
        text = "\n".join(line for line in lines if line)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_text(html: str) -> str:
    extractor = TextExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass
    return extractor.get_text()


def is_html(content: str) -> bool:
    head = content[:500].strip().lower()
    return head.startswith("<!doctype") or head.startswith("<html") or "<meta" in head


def git_commit(repo_dir: str, message: str):
    git_dir = os.path.join(repo_dir, ".git")
    if not os.path.isdir(git_dir):
        return
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_dir, check=True, capture_output=True, text=True,
        )
        if not result.stdout.strip():
            return
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=repo_dir, check=True, capture_output=True)
        print(f"Git commit: {message}")
    except subprocess.CalledProcessError:
        pass


def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.netloc.replace("www.", "").replace(".", "-")
    path = parsed.path.strip("/").replace("/", "-") if parsed.path else "index"
    if len(path) > 80:
        path = path[:80]
    return f"{hostname}-{path}"


def fetch_url(url: str) -> tuple[str | None, str | None]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            text = content.decode(charset, errors="replace")
            return text, None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"URL Error: {e.reason}"
    except Exception as e:
        return None, f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(description="Fetch URL content and save to community asset/")
    parser.add_argument("--community", required=True, help="Community directory path")
    parser.add_argument("--url", help="URL to fetch")
    parser.add_argument("--list", action="store_true", help="List saved assets")
    parser.add_argument("--show", help="Show saved asset content by filename")
    args = parser.parse_args()

    asset_dir = os.path.join(args.community, "asset")
    os.makedirs(asset_dir, exist_ok=True)

    if args.list:
        files = [f for f in os.listdir(asset_dir)
                 if os.path.isfile(os.path.join(asset_dir, f)) and f.endswith(".md")]
        if not files:
            print("asset/ 目录为空")
            return
        print(f"asset/ 中共 {len(files)} 个文件：")
        for f in sorted(files):
            fpath = os.path.join(asset_dir, f)
            size = os.path.getsize(fpath)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
            print(f"  {f}  ({size} bytes, {mtime})")
        return

    if args.show:
        fpath = os.path.join(asset_dir, args.show)
        if not os.path.isfile(fpath):
            print(f"Error: 文件不存在 - {args.show}")
            return
        with open(fpath, "r", encoding="utf-8") as f:
            print(f.read())
        return

    if not args.url:
        parser.error("请提供 --url 或使用 --list / --show")

    print(f"正在获取: {args.url}")
    content, error = fetch_url(args.url)

    if error:
        print(f"获取失败: {error}", file=sys.stderr)
        print("建议：可以手动将内容粘贴到 asset/ 下的文件中，然后由 LLM 提取 Event 信息。")
        sys.exit(1)

    # Convert HTML to readable text
    if is_html(content):
        print("检测到 HTML 格式，提取可读文本...")
        text = html_to_text(content)
        if not text.strip():
            print("警告: 未能从 HTML 中提取到可读文本（页面可能依赖 JavaScript 渲染）", file=sys.stderr)
            print("建议：使用 LLM 的 webfetch 工具获取内容后手动保存到 asset/")
            sys.exit(1)
        print(f"提取到 {len(text)} 字符的可读文本")
    else:
        text = content

    # Save to asset/
    base_name = sanitize_filename(args.url)
    fname = f"{base_name}.md"
    fpath = os.path.join(asset_dir, fname)

    header = (
        f"---\n"
        f"source: {args.url}\n"
        f"collected: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"type: asset\n"
        f"---\n\n"
        f"# 来源: {args.url}\n\n"
    )

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(header + text)

    print(f"已保存: {fpath} ({os.path.getsize(fpath)} bytes)")

    meta_path = os.path.join(asset_dir, f"{base_name}.meta.json")
    meta = {
        "url": args.url,
        "file": fname,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "status": "saved",
        "was_html": is_html(content),
        "text_length": len(text),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    git_commit(args.community, f"extract: Add asset {fname}")


if __name__ == "__main__":
    main()
