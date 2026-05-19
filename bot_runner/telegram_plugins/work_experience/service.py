# plugins/work_experience/service.py

import csv
import json
import random
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests
from io import StringIO
from dateutil.relativedelta import relativedelta

import logging

@dataclass
class Person:
    fio: str
    username: Optional[str]
    start_date: date
    photo_url: Optional[str] = None


# ================= HELPERS =================

def today_almaty() -> date:
    return datetime.now().date()


def _calc_years(start_date: date, today: date) -> float | None:
    
    if today == start_date + relativedelta(months=6):
        logging.info(f"{today} - {start_date+relativedelta(months=6)} (1/2)")
        return 1/2

    if today == start_date + relativedelta(months=3):
        logging.info(f"{today} - {start_date+relativedelta(months=3)} (1/4)")
        return 1/4

    if today == start_date + relativedelta(months=2):
        logging.info(f"{today} - {start_date+relativedelta(months=2)} (1/6)")
        return 1/6

    if today == start_date + relativedelta(months=1):
        logging.info(f"{today} - {start_date+relativedelta(months=1)} (1/12)")
        return 1/12

    years = today.year - start_date.year


    if years > 0 and today == start_date + relativedelta(years=years):
        logging.info(f"{today} - {start_date+relativedelta(years=years)} ({years})")
        return float(years)
    
    logging.info(f"{today} - {start_date} (no match)")

    return None


# ================= IMAGES =================

def normalize_drive_url(url: str) -> str | None:
    if not url:
        return None

    if "drive.google.com/uc?id=" in url:
        return url

    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return f"https://drive.google.com/uc?id={m.group(1)}"

    return url


def _list_images(images_dir: Path):
    images_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for ext in ("*.jpg", "*.png", "*.jpeg", "*.webp"):
        files.extend(images_dir.glob(ext))
    return sorted(files)


def pick_next_image(state: Dict, images_dir: Path):
    imgs = _list_images(images_dir)
    logging.info(f"Found {len(imgs)} images in {images_dir}")
    if not imgs:
        return None

    idx = (state.get("last_image_index", -1) + 1) % len(imgs)
    logging.info(f"Selected image {idx} from {len(imgs)} in {images_dir}")
    state["last_image_index"] = idx
    return imgs[idx]


def get_or_download_external_image(url: str, external_images_dir: Path):
    external_images_dir.mkdir(parents=True, exist_ok=True)

    name = hashlib.sha1(url.encode()).hexdigest() + ".jpg"
    path = external_images_dir / name

    if path.exists():
        return path

    url = normalize_drive_url(url)

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    if not r.headers.get("Content-Type", "").startswith("image/"):
        return None

    path.write_bytes(r.content)
    return path





# ================= PAYLOADS =================

def build_payloads(
    for_date: date,
    people: List,
    state: Dict,
    templates_by_years: Dict,
    images_dir: Path,
    external_images_dir: Path,
):
    payloads = []

    used_templates_by_years = {}

    for p in people:
        if not p.start_date:
            continue

        years = _calc_years(p.start_date, for_date)
        if years is None:
            continue

        templates = templates_by_years.get(years)
        if not templates:
            continue

        if years not in used_templates_by_years:
            used_templates_by_years[years] = templates.copy()
            random.shuffle(used_templates_by_years[years])

        pool = used_templates_by_years[years]

        if not pool:
            pool.extend(templates.copy())
            random.shuffle(pool)

        tpl = pool.pop()

        name = None
        if p.fio and " " in p.fio:
            name = p.fio.split()[1]

        text = tpl.replace(
            "{mention}",
            name if name else p.fio if p.fio else "Коллега"
        )

        if p.username:
            text = f"@{p.username}\n" + text

        photo = None
        if p.photo_url:
            photo = get_or_download_external_image(p.photo_url, external_images_dir)

        if photo is None:
            photo = pick_next_image(state, images_dir)

        state["last_sent_for_date"] = for_date.isoformat()

        payloads.append({
            "text": text,
            "photo": str(photo) if photo else None,
        })

    return payloads


# ================= RUN =================


