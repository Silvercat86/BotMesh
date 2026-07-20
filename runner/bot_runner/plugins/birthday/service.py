# plugins/birthday/service.py
# -*- coding: utf-8 -*-

import csv
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, date
from io import StringIO
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any

import requests
from services.people_directory import Employee

# ===================== LOGGING =====================

log = logging.getLogger("birthdays")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

# ===================== TZ =====================

try:
    from zoneinfo import ZoneInfo

    TZ = ZoneInfo("Asia/Almaty")
except Exception:
    TZ = None
    log.warning("ZoneInfo недоступен, используется локальное время")


# ===================== DATA =====================

@dataclass
class Person:
    fio: str
    username: Optional[str]
    month: int
    day: int
    photo_url: Optional[str] = None





# ===================== STATE =====================

def today_almaty() -> date:
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        result = datetime.now(ZoneInfo("Asia/Almaty")).date()
        return result
    except Exception as e:
        log.info(e)
        return datetime.utcnow().date()


def load_state(state_path: Path) -> Dict:
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            return state
        except Exception as e:
            log.error(f"Ошибка чтения state: {e}")

    log.info("State отсутствует, создаётся новый")
    return {
        "last_template_index": -1,
        "last_sent_for_date": "",
        "last_image_index": -1,
    }


def save_state(state_path: Path, state: Dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def pick_next_template(state: Dict, templates: list[str]) -> str:
    idx = (state.get("last_template_index", -1) + 1) % len(templates)
    state["last_template_index"] = idx
    return templates[idx]


# ===================== IMAGES =====================

def _list_images(images_dir: Path) -> List[Path]:
    images_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif"):
        files.extend(images_dir.glob(ext))
    return sorted(files)


def pick_next_image(state: Dict, images_dir: Path) -> Optional[Path]:
    imgs = _list_images(images_dir)
    if not imgs:
        log.warning(f"Нет изображений в папке {images_dir}")
        return None

    idx = (state.get("last_image_index", -1) + 1) % len(imgs)
    state["last_image_index"] = idx
    img = imgs[idx]
    return img


def normalize_drive_url(url: str) -> Optional[str]:
    if not url:
        return None

    if "drive.google.com/uc?id=" in url:
        return url

    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return f"https://drive.google.com/uc?id={m.group(1)}"

    return None


def get_or_download_external_image(url: str, external_images_dir: Path) -> Optional[Path]:
    external_images_dir.mkdir(parents=True, exist_ok=True)

    url = normalize_drive_url(url)
    if not url:
        return None

    name = hashlib.sha1(url.encode()).hexdigest() + ".jpg"
    path = external_images_dir / name

    if path.exists():
        return path

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        if not r.headers.get("Content-Type", "").startswith("image/"):
            return None

        path.write_bytes(r.content)
        return path

    except Exception as e:
        return None


# ===================== PAYLOADS =====================

def build_payloads(
    for_date: date,
    people: List[Employee],
    state: Dict,
    templates: list[str],
    images_dir: Path,
    external_images_dir: Path,
) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []

    todays = []
    for p in people:
        if p.birthday:
            if (p.birthday.month, p.birthday.day) == (for_date.month, for_date.day):
                todays.append(p)
        else:
            log.info(f"У {p.fio} нет даты рождения, пропуск")
                
        


    log.info(f"Именинники на {for_date}: {len(todays)}")

    for p in todays:
        tpl = pick_next_template(state, templates)

        name = ""
        if p.fio and " " in p.fio:
            name = p.fio.split()[1]
        

        text = tpl.replace("{mention}", name if name else p.fio if p.fio else "Коллега")
        if p.username:
            text = f" @{p.username}\n" + text

        photo = None
        if p.photo_url:
            photo = get_or_download_external_image(p.photo_url, external_images_dir)

        if photo is None:
            photo = pick_next_image(state, images_dir)

        state["last_sent_for_date"] = for_date.isoformat()

        payloads.append(
            {
                "text": text,
                "photo": str(photo) if photo else None,
            }
        )

    return payloads





