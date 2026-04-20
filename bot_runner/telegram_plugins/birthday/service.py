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


# ===================== CSV =====================

def _open_csv_any(csv_path_or_url):
    p = str(csv_path_or_url)

    if p.startswith("http://") or p.startswith("https://"):
        log.info(f"Загружаю CSV по URL: {p}")
        r = requests.get(p, timeout=15)
        r.raise_for_status()
        text = r.content.decode("utf-8")
        log.info(f"CSV загружен, {len(text)} байт")
        return StringIO(text)

    return open(Path(p), "r", encoding="utf-8-sig", newline="")


def _parse_date(cell: str) -> Tuple[int, int]:
    cell = (cell or "").strip()
    for fmt in ("%d.%m.%Y", "%d.%m", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(cell, fmt)
            return dt.month, dt.day
        except ValueError:
            continue
    raise ValueError(cell)


def load_people(csv_path) -> List[Person]:
    people: List[Person] = []

    try:
        f = _open_csv_any(csv_path)
        reader = csv.reader(f)
        rows = list(reader)
    except Exception as e:
        log.error(f"Ошибка чтения CSV: {e}")
        return []

    if not rows:
        log.warning("CSV пустой")
        return []

    header = [h.lower() for h in rows[0]]

    has_real_header = any(
        h in ("фио", "fio", "name", "username", "user", "ник", "дата", "date")
        for h in header
    )

    if has_real_header:
        rows = rows[1:]
    else:
        log.warning("Первая строка не является заголовком — используется как данные")

    def idx(*names):
        for n in names:
            if n in header:
                return header.index(n)
        return None

    i_fio = idx("фио", "fio", "name")
    i_user = idx("контакт тг", "user", "ник")
    i_date = idx("день рождения", "дата")
    i_photo = 3  # всегда 4-я колонка, если есть

    if i_fio is None and i_date is None:
        log.warning(
            "Заголовки не распознаны, используется позиционный режим: "
            "ФИО | USERNAME | ДАТА | (ФОТО)"
        )
        i_fio = 0
        i_user = 1
        i_date = 2


    for r in rows:
        try:
            fio = r[i_fio].strip() if i_fio is not None and len(r) > i_fio else ""
            date_cell = r[i_date].strip() if i_date is not None and len(r) > i_date else ""
            username = (
                r[i_user].strip().lstrip("@")
                if i_user is not None and len(r) > i_user
                else None
            )
            photo_url = r[i_photo].strip() if len(r) > i_photo and r[i_photo].strip() else None

            if not fio or not date_cell:
                continue

            m, d = _parse_date(date_cell)

            people.append(
                Person(
                    fio=fio,
                    username=username,
                    month=m,
                    day=d,
                    photo_url=photo_url,
                )
            )
        except Exception as e:
            pass
    log.info(f"Загружено людей: {len(people)}")
    return people


# ===================== STATE =====================

def today_almaty() -> date:
    log.info("startingtoday")
    from datetime import datetime
    log.info("imported datetime")
    try:
        from zoneinfo import ZoneInfo
        log.info("imported zoneinfo")
        result = datetime.now(ZoneInfo("Asia/Almaty")).date()
        log.info(result)
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
    log.info(f"Выбрано дефолтное изображение: {img.name}")
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
        log.info(f"Фото из кэша: {path.name}")
        return path

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        if not r.headers.get("Content-Type", "").startswith("image/"):
            log.warning("Ссылка не ведёт на изображение")
            return None

        path.write_bytes(r.content)
        log.info(f"Фото скачано из таблицы: {path.name}")
        return path

    except Exception as e:
        log.warning(f"Не удалось скачать фото: {e}")
        return None


# ===================== PAYLOADS =====================

def build_payloads(
    for_date: date,
    people: List[Employee],
    state: Dict,
    state_path: Path,
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
        log.info(f"{p.fio} (tg: @{p.username if p.username else 'нет'}, фото: {'есть' if p.photo_url else 'нет'})")
        tpl = pick_next_template(state, templates)

        name = ""
        if p.fio and " " in p.fio:
            name = p.fio.split()[1]
        

        text = tpl.replace("{mention}", name if name else p.fio if p.fio else "Коллега")
        if p.username:
            text = f" @{p.username}\n" + text

        photo = None
        if p.photo_url:
            log.info(f"Пробуем фото из таблицы для {p.fio}")
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
    save_state(state_path, state)

    return payloads





