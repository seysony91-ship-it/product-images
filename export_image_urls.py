#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
from pathlib import Path
from urllib.parse import quote

# ✅ 네 GitHub 정보 (필요시 수정)
GITHUB_USER = "seysony91-ship-it"
REPO_NAME = "product-images"
BRANCH = "main"

# ✅ 로컬 기준 이미지 폴더
ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "images"

# ✅ 허용 확장자
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMG_EXTS and p.name != ".DS_Store"


def extract_num(name: str) -> int:
    """
    파일명에서 가장 마지막에 등장하는 숫자 덩어리를 뽑아 정렬에 사용.
    예) '메인 이미지_03.jpg' -> 3
    숫자가 없으면 큰 값(9999)으로 보내서 뒤로 밀림.
    """
    nums = re.findall(r"(\d+)", name)
    return int(nums[-1]) if nums else 9999


def make_raw_url(rel_path: Path) -> str:
    """
    raw.githubusercontent.com URL 생성.
    한글/공백 안전하게 URL 인코딩(quote) 처리.
    """
    # rel_path 예: images/1200/메인 이미지_01.jpg
    parts = [quote(part) for part in rel_path.as_posix().split("/")]
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/" + "/".join(parts)


def pick_four(files: list[Path]) -> list[Path]:
    """
    폴더 내 이미지 파일 목록에서 대표1 + 상세3을 최대한 규칙적으로 고른다.
    """
    # 1) 대표 후보
    thumb_keywords = ("ㄷㅍ", "대표", "thumb", "cover")
    thumbs = [p for p in files if any(k.lower() in p.name.lower() for k in thumb_keywords)]

    # 2) 상세 후보
    detail_keywords = ("메인 이미지", "상세", "detail", "main")
    details = [p for p in files if any(k.lower() in p.name.lower() for k in detail_keywords)]

    # 정렬 (숫자 우선)
    thumbs_sorted = sorted(thumbs, key=lambda p: (extract_num(p.name), p.name))
    details_sorted = sorted(details, key=lambda p: (extract_num(p.name), p.name))

    chosen: list[Path] = []

    # 대표 1장
    if thumbs_sorted:
        chosen.append(thumbs_sorted[0])

    # 상세 3장
    for p in details_sorted:
        if p not in chosen:
            chosen.append(p)
        if len(chosen) >= 4:
            break

    # 부족하면 나머지로 채움
    if len(chosen) < 4:
        rest = [p for p in sorted(files, key=lambda p: (extract_num(p.name), p.name)) if p not in chosen]
        chosen.extend(rest[: (4 - len(chosen))])

    # 그래도 4개 미만이면 있는 것만 반환
    return chosen[:4]


def main():
    if not IMAGES_DIR.exists():
        raise SystemExit(f"❌ images 폴더를 찾을 수 없음: {IMAGES_DIR}")

    out_csv = ROOT / "image_urls.csv"

    rows = []
    folder_count = 0

    # 폴더명(숫자) 우선 정렬, 그 외 폴더도 포함
    subfolders = [p for p in IMAGES_DIR.iterdir() if p.is_dir()]
    subfolders.sort(key=lambda p: (0, int(p.name)) if p.name.isdigit() else (1, p.name))

    for folder in subfolders:
        files = [p for p in folder.iterdir() if is_image(p)]
        if not files:
            continue

        picked = pick_four(files)
        rels = [p.relative_to(ROOT) for p in picked]
        urls = [make_raw_url(rel) for rel in rels]

        # 4칸 고정 (부족하면 빈칸)
        while len(urls) < 4:
            urls.append("")

        rows.append({
            "folder": folder.name,
            "url_1": urls[0],  # 대표(추정)
            "url_2": urls[1],
            "url_3": urls[2],
            "url_4": urls[3],
            "file_1": picked[0].name if len(picked) > 0 else "",
            "file_2": picked[1].name if len(picked) > 1 else "",
            "file_3": picked[2].name if len(picked) > 2 else "",
            "file_4": picked[3].name if len(picked) > 3 else "",
        })
        folder_count += 1

    # CSV 저장
    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["folder", "url_1", "url_2", "url_3", "url_4", "file_1", "file_2", "file_3", "file_4"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ 완료: {folder_count}개 폴더 처리")
    print(f"📄 CSV 생성: {out_csv}")


if __name__ == "__main__":
    main()
