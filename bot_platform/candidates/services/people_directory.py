from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Dict

import csv
import requests
import time
from io import StringIO


# =========================
# RAW МОДЕЛЬ
# =========================

@dataclass
class RawEmployee:
    data: Dict[str, str]
    source: str
    row_id: str


# =========================
# НОРМ МОДЕЛЬ
# =========================

@dataclass
class Employee:
    fio: Optional[str]
    username: Optional[str]
    phone: Optional[str]
    email: Optional[str]

    birthday: Optional[date]
    start_date: Optional[date]

    position: Optional[str]
    manager: Optional[str]

    source: Optional[str]

    extra_data: Dict[str, str]


# =========================
# СЕРВИС
# =========================

class PeopleDirectoryService:

    def __init__(self, sources: Dict[str, dict], cache_ttl: int = 300):
        self.sources = sources
        self.cache_ttl = cache_ttl

        self._cache: Dict[str, List[RawEmployee]] = {}
        self._cache_time: Dict[str, float] = {}

    # -------------------------
    # PUBLIC
    # -------------------------

    def get_raw(self, source: str) -> List[RawEmployee]:
        self._ensure_cache(source)
        return self._cache[source]

    def get_people(self, source: str) -> List[Employee]:
        raw_list = self.get_raw(source)
        return [self._map_to_employee(r) for r in raw_list]

    # -------------------------
    # CACHE
    # -------------------------

    def _ensure_cache(self, source: str):
        if source not in self.sources:
            raise RuntimeError(f"Unknown source: {source}")

        now = time.time()

        if source in self._cache_time:
            if now - self._cache_time[source] < self.cache_ttl:
                return

        cfg = self.sources[source]

        try:
            raw = self._load_raw(cfg)
        except Exception as e:
            print(f"[ERROR] load source={source}: {e}")
            raise

        self._cache[source] = raw
        self._cache_time[source] = now

    # -------------------------
    # LOAD RAW (CSV + GOOGLE API)
    # -------------------------

    def _load_raw(self, cfg: dict) -> List[RawEmployee]:

        import base64
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        url = cfg.get("url")
        path = cfg.get("path")
        service_account_b64 = cfg.get("service_account_b64")

        if not url and not path:
            raise RuntimeError("source must have url or path")

        rows = []

        # === GOOGLE API ===
        if service_account_b64 and url and "docs.google.com" in url:

            sheet_id = url.split("/d/")[1].split("/")[0]

            creds_json = base64.b64decode(service_account_b64).decode("utf-8")
            creds_dict = json.loads(creds_json)

            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )

            service = build("sheets", "v4", credentials=credentials)

            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range="A1:ZZ"
            ).execute()

            rows = result.get("values", [])

            if not rows:
                return []

            header = rows[0]
            data_rows = rows[1:]

            result_list: List[RawEmployee] = []

            for i, row in enumerate(data_rows):
                row_dict = {}

                for j, col in enumerate(header):
                    key = col.strip()
                    value = row[j].strip() if j < len(row) else None
                    row_dict[key] = value

                result_list.append(
                    RawEmployee(
                        data=row_dict,
                        source=cfg.get("name", "unknown"),
                        row_id=str(i)
                    )
                )

            return result_list

        # === CSV ===
        if url:
            r = requests.get(url, timeout=15)
            r.raise_for_status()

            text = r.content.decode("utf-8-sig", errors="replace")

            if "<html" in text[:200].lower():
                raise RuntimeError("Got HTML instead of CSV")

            f = StringIO(text)
        else:
            f = open(path, "r", encoding="utf-8-sig", newline="")

        try:
            reader = csv.DictReader(f)
            rows = list(reader)
        finally:
            f.close()

        result_list: List[RawEmployee] = []

        for i, row in enumerate(rows):
            clean_row = {k.strip(): (v.strip() if v else None) for k, v in row.items()}

            result_list.append(
                RawEmployee(
                    data=clean_row,
                    source=cfg.get("name", "unknown"),
                    row_id=str(i)
                )
            )

        return result_list

    # -------------------------
    # MAPPING
    # -------------------------

    def _map_to_employee(self, raw: RawEmployee) -> Employee:

        d = raw.data

        

        def g(key: str) -> Optional[str]:
            return d.get(key)

        def parse_date(value: Optional[str]) -> Optional[date]:
            if not value:
                return None

            for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m", "%d/%m/%Y"):
                try:
                    dt = datetime.strptime(value, fmt)
                    if fmt == "%d.%m":
                        return date(2000, dt.month, dt.day)
                    return dt.date()
                except:
                    pass

            return None

        KNOWN = {
            "ФИО",
            "Должность",
            "Телефон",
            "почта",
            "контакт ТГ",
            "дата выхода",
            "День рождения",
            "Руководитель",
        }

        extra = {k: v for k, v in d.items() if k not in KNOWN}

        # КРИТИЧНО
        extra["__row_id__"] = raw.row_id

        print (g("ФИО"))
        print (g("День рождения"))
        print (g("дата выхода"))
        

        return Employee(
            fio=g("ФИО"),
            username=self._normalize_username(g("контакт ТГ")),
            phone=g("Телефон"),
            email=g("почта"),

            birthday=parse_date(g("День рождения")),
            start_date=parse_date(g("дата выхода")),

            position=g("Должность"),
            manager=g("Руководитель"),

            source=raw.source,
            extra_data=extra
        )

    # -------------------------
    # UTILS
    # -------------------------

    def _normalize_username(self, username: Optional[str]) -> Optional[str]:
        if not username:
            return None
        return username.lstrip("@")