#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

GITHUB_USER = "seysony91-ship-it"
REPO_NAME = "product-images"
BRANCH = "main"

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "images"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".png", ".webp"}

def extract_num(name: str) -> int:
    nums = re.findall(r"(\d+)", name)
    return int(nums[-1]) if nums else 9999

def is_image_path(path: str) -> bool:
    p = Path(path)
    return p.suffix.lower() in IMG_EXTS and p.name != ".DS_Store"

def make_raw_url(path_from_repo_root: str) -> str:
    parts = [quote(part) for part in path_from_repo_root.split("/")]
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/" + "/".join(parts)

def pick_four(file_names: list[str]) -> list[str]:
    thumb_keywords = ("ㄷㅍ", "대표", "thumb", "cover")
    detail_keywords = ("메인 이미지", "상세", "detail", "main")

    thumbs = [n for n in file_names if any(k.lower() in n.lower() for k in thumb_keywords)]
    details = [n for n in file_names if any(k.lower() in n.lower() for k in detail_keywords)]

    thumbs_sorted = sorted(thumbs, key=lambda n: (extract_num(n), n))
    details_sorted = sorted(details, key=lambda n: (extract_num(n), n))

    chosen = []
    if thumbs_sorted:
        chosen.append(thumbs_sorted[0])

    for n in details_sorted:
        if n not in chosen:
            chosen.append(n)
        if len(chosen) >= 4:
            break

    if len(chosen) < 4:
        rest = [n for n in sorted(file_names, key=lambda n: (extract_num(n), n)) if n not in chosen]
        chosen.extend(rest[: (4 - len(chosen))])

    return chosen[:4]

def ensure_origin_main():
    subprocess.run(["git", "fetch", "--all", "--prune"], check=True)

def get_repo_paths_origin_main() -> list[str]:
    cp = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-tree", "-r", "-z", "--name-only", "origin/main"],
        check=True,
        capture_output=True,
    )
    raw = cp.stdout.decode("utf-8", errors="replace")
    return [p for p in raw.split("\0") if p]

def main():
    if not IMAGES_DIR.exists():
        raise SystemExit(f"❌ images 폴더를 찾을 수 없음: {IMAGES_DIR}")

    ensure_origin_main()
    all_paths = get_repo_paths_origin_main()

    by_folder = {}
    for path in all_paths:
        if not path.startswith("images/"):
            continue
        if not is_image_path(path):
            continue
        parts = path.split("/", 2)
        if len(parts) < 3:
            continue
        folder = parts[1]
        by_folder.setdefault(folder, []).append(path)

    subfolders = [p for p in IMAGES_DIR.iterdir() if p.is_dir()]
    subfolders.sort(key=lambda p: (0, int(p.name)) if p.name.isdigit() else (1, p.name))

    out_csv = ROOT / "image_urls.csv"
    rows = []

    for folder in subfolders:
        paths = by_folder.get(folder.name, [])
        if not paths:
            continue

        file_names = [Path(p).name for p in paths]
        picked = pick_four(file_names)

        urls = []
        for name in picked:
            p = next(x for x in paths if Path(x).name == name)
            urls.append(make_raw_url(p))

        while len(urls) < 4:
            urls.append("")

        rows.append({
            "folder": folder.name,
            "url_1": urls[0],
            "url_2": urls[1],
            "url_3": urls[2],
            "url_4": urls[3],
        })

    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"📄 CSV 생성 완료: {out_csv}")

if __name__ == "__main__":
    main()
