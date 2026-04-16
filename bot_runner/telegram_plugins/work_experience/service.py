# plugins/work_experience/service.py

import csv
import json
import logging
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

log = logging.getLogger("work_experience")


# ================= STATE =================

def load_state(state_path: Path) -> Dict:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    log.info(state_path)
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as e:
            log.info(f"Error with loading state {e}")
    else:
        log.info("state path doesnt exist")

    

    return {
        "last_sent_for_date": "",
        "last_image_index": -1,
    }


def save_state(state_path: Path, state: Dict):
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ================= DATA =================

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
        return 1/2

    if today == start_date + relativedelta(months=3):
        return 1/4

    if today == start_date + relativedelta(months=2):
        return 1/6

    if today == start_date + relativedelta(months=1):
        return 1/12

    years = today.year - start_date.year
    if years > 0 and today == start_date + relativedelta(years=years):
        return float(years)

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
    if not imgs:
        return None

    idx = (state.get("last_image_index", -1) + 1) % len(imgs)
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


# ================= CSV =================

def _open_csv_any(csv_path_or_url):
    p = str(csv_path_or_url)

    if p.startswith("http://") or p.startswith("https://"):
        log.info(f"Загружаю CSV по URL: {p}")
        r = requests.get(p, timeout=15)
        r.raise_for_status()
        text = r.content.decode("utf-8")
        return StringIO(text)

    return open(Path(p), "r", encoding="utf-8-sig", newline="")


def load_people(csv_path, column_map: dict) -> List[Person]:
    people = []


    f = _open_csv_any(csv_path)
    reader = csv.reader(f)
    rows = list(reader)

    if not rows:
        return []

    header = [h.strip().lower() for h in rows[0]]


    def find_index(column_name):
        if not column_name:
            return None
        for i, h in enumerate(header):
            if h == column_name.lower():
                return i
        return None

    if column_map:

        i_fio = find_index(column_map.get("fio"))
        i_user = find_index(column_map.get("username"))
        i_date = find_index(column_map.get("start_date"))
        i_photo = find_index(column_map.get("photo"))
    else:
        i_fio = 0
        i_user = 1
        i_date = 2
        i_photo = 3

    
    

    for r in rows[1:]:
        try:
            fio = r[i_fio] if i_fio is not None else ""
            username = r[i_user].lstrip("@") if i_user is not None else None
            start_date = datetime.strptime(r[i_date], "%d.%m.%Y").date()
            photo_url = r[i_photo] if i_photo is not None else None

            people.append(Person(fio, username, start_date, photo_url))

        except Exception as e:
            pass
    log.info(f"Загружено {len(people)} человек из CSV")

    return people



# ================= PAYLOADS =================

def build_payloads(
    for_date: date,
    people: List[Person],
    state: Dict,
    templates_by_years: Dict,
    images_dir: Path,
    external_images_dir: Path,
):
    payloads = []

    for p in people:
        years = _calc_years(p.start_date, for_date)
        if years is None:
            continue

        

        templates = templates_by_years.get(years)
        if not templates:
            continue

        name = None
        if p.fio and " " in p.fio:
            name = p.fio.split()[1]

        tpl = random.choice(templates)
        text = tpl.replace("{mention}", f"{name}" if name else f"{p.fio}" if p.fio else "Коллега")

        if p.username:
            text = f"@{p.username}\n" + text

        photo = None
        if p.photo_url:
            photo = get_or_download_external_image(p.photo_url, external_images_dir)

        if photo is None:
            photo = pick_next_image(state, images_dir)

        payloads.append({
            "text": text,
            "photo": str(photo) if photo else None,
        })

    return payloads


# ================= RUN =================

def daily_work_experience_run(
    send_fn,
    chat_id: int,
    csv_path,
    templates_by_years: Dict,
    state_path: Path,
    images_dir: Path,
    external_images_dir: Path,
    column_map: dict,
):
    state = load_state(state_path)
    today = today_almaty()

    if state.get("last_sent_for_date") == today.isoformat():
        log.info("Work experience already sent for today, skipping")
        return 0

    people = load_people(csv_path, column_map=column_map)

    payloads = build_payloads(
        today,
        people,
        state,
        templates_by_years,
        images_dir,
        external_images_dir,
    )

    if not payloads:
        return 0

    for p in payloads:
        send_fn(chat_id, p["text"], p["photo"])

    state["last_sent_for_date"] = today.isoformat()
    save_state(state_path, state)

    return len(payloads)

def test_work_experience_run(
    send_fn,
    test_date: date,
    chat_id: int,
    csv_path,
    templates_by_years: Dict,
    state_path: Path,
    images_dir: Path,
    external_images_dir: Path,
    column_map: dict,
):

    state = load_state(state_path).copy()

    people = load_people(csv_path, column_map=column_map)

    payloads = build_payloads(
        for_date=test_date,
        people=people,
        state=state,
        templates_by_years=templates_by_years,
        images_dir=images_dir,
        external_images_dir=external_images_dir,

    )

    if not payloads:
        log.info("TEST: нет совпадений")
        return []

    for p in payloads:
        send_fn(
            chat_id,
            f"[TEST {test_date.isoformat()}] {p['text']}",
            p["photo"],
        )

    log.info(f"TEST отправлено сообщений: {len(payloads)}")
    return payloads

