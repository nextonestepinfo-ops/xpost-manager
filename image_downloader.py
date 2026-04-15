#!/usr/bin/env python3
"""
画像一括ダウンローダー
指定URLのページから全画像を取得し、指定フォルダに保存します。

使い方:
  python image_downloader.py <URL> [保存先フォルダ]

例:
  python image_downloader.py https://example.com/products ./images
  python image_downloader.py https://example.com/gallery

※ 保存先を省略すると ./downloaded_images に保存されます
※ ダウンロードした画像の利用は著作権・利用規約をご確認ください
"""

import os
import re
import sys
import time
import hashlib
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

# ─── 設定 ───
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
TIMEOUT = 15
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".avif"}
MIN_SIZE_BYTES = 1024  # 1KB未満の画像はスキップ（アイコン等を除外）


def sanitize_filename(name, max_len=100):
    """ファイル名として安全な文字列にする"""
    name = unquote(name)
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name)
    name = name.strip(". ")
    if len(name) > max_len:
        base, ext = os.path.splitext(name)
        name = base[: max_len - len(ext)] + ext
    return name or "image"


def get_extension(url, content_type=""):
    """URLまたはContent-Typeから拡張子を推定"""
    # URLのパスから
    path = urlparse(url).path
    _, ext = os.path.splitext(path.split("?")[0])
    ext = ext.lower()
    if ext in IMAGE_EXTENSIONS:
        return ext

    # Content-Typeから
    ct_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/bmp": ".bmp",
        "image/avif": ".avif",
        "image/x-icon": ".ico",
    }
    for ct, e in ct_map.items():
        if ct in content_type:
            return e

    return ".jpg"  # デフォルト


def extract_image_urls(page_url, html):
    """HTMLから画像URLを抽出（重複排除）"""
    soup = BeautifulSoup(html, "html.parser")
    urls = set()

    # <img> タグ
    for img in soup.find_all("img"):
        for attr in ["src", "data-src", "data-lazy-src", "data-original", "data-srcset"]:
            val = img.get(attr)
            if val:
                # srcset の場合は最初のURLを取得
                val = val.split(",")[0].strip().split(" ")[0]
                if val and not val.startswith("data:"):
                    urls.add(urljoin(page_url, val))

    # <source> タグ (picture要素内)
    for source in soup.find_all("source"):
        srcset = source.get("srcset", "")
        for part in srcset.split(","):
            u = part.strip().split(" ")[0]
            if u and not u.startswith("data:"):
                urls.add(urljoin(page_url, u))

    # <a> タグで画像への直リンク
    for a in soup.find_all("a", href=True):
        href = a["href"]
        _, ext = os.path.splitext(urlparse(href).path.lower())
        if ext in IMAGE_EXTENSIONS:
            urls.add(urljoin(page_url, href))

    # CSSの background-image
    for tag in soup.find_all(style=True):
        style = tag["style"]
        bg_urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
        for bu in bg_urls:
            if not bu.startswith("data:"):
                urls.add(urljoin(page_url, bu))

    # <meta property="og:image">
    for meta in soup.find_all("meta", attrs={"property": "og:image"}):
        content = meta.get("content")
        if content:
            urls.add(urljoin(page_url, content))

    return sorted(urls)


def download_images(page_url, output_dir, skip_small=True):
    """メイン処理: ページ取得 → 画像URL抽出 → ダウンロード"""

    print(f"\n{'='*60}")
    print(f"  画像一括ダウンローダー")
    print(f"{'='*60}")
    print(f"  URL:    {page_url}")
    print(f"  保存先: {os.path.abspath(output_dir)}")
    print(f"{'='*60}\n")

    # ページ取得
    print("[1/3] ページを取得中...")
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ✕ ページの取得に失敗しました: {e}")
        return []

    print(f"  ✓ ステータス: {resp.status_code}")

    # 画像URL抽出
    print("\n[2/3] 画像URLを抽出中...")
    image_urls = extract_image_urls(page_url, resp.text)
    print(f"  ✓ {len(image_urls)}件の画像URLを検出")

    if not image_urls:
        print("\n  画像が見つかりませんでした。")
        return []

    # 保存先フォルダ作成
    os.makedirs(output_dir, exist_ok=True)

    # ダウンロード
    print(f"\n[3/3] 画像をダウンロード中...")
    downloaded = []
    skipped = 0
    failed = 0
    seen_hashes = set()

    for i, img_url in enumerate(image_urls, 1):
        progress = f"  [{i:3d}/{len(image_urls)}]"

        try:
            img_resp = requests.get(img_url, headers=HEADERS, timeout=TIMEOUT, stream=True)
            img_resp.raise_for_status()

            content = img_resp.content

            # サイズチェック
            if skip_small and len(content) < MIN_SIZE_BYTES:
                print(f"{progress} ⊘ スキップ (小さすぎる: {len(content)}B) {img_url[:60]}")
                skipped += 1
                continue

            # 重複チェック (ハッシュ)
            h = hashlib.md5(content).hexdigest()
            if h in seen_hashes:
                print(f"{progress} ⊘ スキップ (重複) {img_url[:60]}")
                skipped += 1
                continue
            seen_hashes.add(h)

            # ファイル名決定
            ext = get_extension(img_url, img_resp.headers.get("Content-Type", ""))
            url_path = urlparse(img_url).path
            base_name = os.path.basename(url_path.split("?")[0])
            if not base_name or base_name == "/":
                base_name = f"image_{i:04d}"

            base_name = sanitize_filename(base_name)
            if not base_name.lower().endswith(ext):
                base_name = os.path.splitext(base_name)[0] + ext

            # 連番プレフィックスで順番を保持
            filename = f"{i:04d}_{base_name}"
            filepath = os.path.join(output_dir, filename)

            # 同名ファイル回避
            counter = 1
            while os.path.exists(filepath):
                name_part, ext_part = os.path.splitext(filename)
                filepath = os.path.join(output_dir, f"{name_part}_{counter}{ext_part}")
                counter += 1

            with open(filepath, "wb") as f:
                f.write(content)

            size_kb = len(content) / 1024
            print(f"{progress} ✓ {filename} ({size_kb:.1f}KB)")
            downloaded.append(filepath)

            time.sleep(0.3)  # サーバー負荷軽減

        except requests.RequestException as e:
            print(f"{progress} ✕ 失敗: {str(e)[:50]} | {img_url[:50]}")
            failed += 1
        except Exception as e:
            print(f"{progress} ✕ エラー: {str(e)[:50]}")
            failed += 1

    # サマリー
    print(f"\n{'='*60}")
    print(f"  完了!")
    print(f"  ✓ ダウンロード: {len(downloaded)}枚")
    print(f"  ⊘ スキップ:     {skipped}枚")
    print(f"  ✕ 失敗:         {failed}枚")
    print(f"  保存先: {os.path.abspath(output_dir)}")
    print(f"{'='*60}\n")

    return downloaded


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./downloaded_images"

    # URL検証
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        print(f"エラー: 有効なURLを指定してください: {url}")
        sys.exit(1)

    download_images(url, output_dir)


if __name__ == "__main__":
    main()
