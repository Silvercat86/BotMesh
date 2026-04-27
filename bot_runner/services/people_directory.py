from dataclasses import dataclass
from datetime import date
from typing import Optional

import base64
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build


@dataclass
class Employee:
    fio: str

    username: Optional[str]
    birthday: Optional[date]
    start_date: Optional[date]

    status: Optional[str] = None
    position: Optional[str] = None
    employment_type: Optional[str] = None
    workload: Optional[str] = None
    format: Optional[str] = None
    engagement: Optional[str] = None
    zone: Optional[str] = None
    risk: Optional[str] = None
    comments: Optional[str] = None

    probation_end: Optional[date] = None
    current_date: Optional[date] = None

    resume: Optional[str] = None
    offer: Optional[str] = None
    employee_card: Optional[str] = None

    last_heat: Optional[date] = None
    next_heat: Optional[date] = None

    last_1to1: Optional[date] = None
    next_1to1: Optional[date] = None

    gender: Optional[str] = None
    stack: Optional[str] = None
    project: Optional[str] = None
    project_description: Optional[str] = None

    manager: Optional[str] = None
    phone: Optional[str] = None

    welcome_training: Optional[str] = None
    salary: Optional[str] = None
    social_package: Optional[str] = None
    salary_changes: Optional[str] = None

    children: Optional[str] = None
    address: Optional[str] = None
    telegram_contact: Optional[str] = None
    email: Optional[str] = None

    emergency_contact: Optional[str] = None

    photo_url: Optional[str] = None
    source: Optional[str] = None



import csv
import requests
import time

from datetime import datetime, date
from pathlib import Path
from io import StringIO
from typing import List, Optional, Dict


class PeopleDirectoryService:

    name = "people"

    def __init__(self, sources: Dict[str, dict], cache_ttl: int = 300):

        """
        sources:

        {
            "employees": {
                "url": "https://docs.google.com/...csv"
            },

            "work_anniversary_1": {
                "url": "..."
            }
        }
        """

        self.sources = sources
        self.cache_ttl = cache_ttl

        self._cache: Dict[str, List[Employee]] = {}
        self._cache_time: Dict[str, float] = {}

    def get_people(self, source: str) -> List[Employee]:

        self._ensure_cache(source)

        return self._cache[source]

    

    def get_birthdays(self, source: str, day: date) -> List[Employee]:

        self._ensure_cache(source)

        result = []

        for p in self._cache[source]:

            if not p.birthday:
                continue

            if (p.birthday.month, p.birthday.day) == (day.month, day.day):
                result.append(p)

        return result

    def get_work_anniversaries(self, source: str, day: date) -> List[Employee]:

        self._ensure_cache(source)

        result = []

        for p in self._cache[source]:

            if not p.start_date:
                continue

            if (p.start_date.month, p.start_date.day) == (day.month, day.day):
                result.append(p)

        return result

    def _load_mixed_people(self, mixed_source_dict: dict) -> List[Employee]:

        merged: Dict[str, Employee] = {}

        key_field = mixed_source_dict.get("key_field", "username")
        field_mapping = mixed_source_dict.get("field_mapping", {})

        for source in mixed_source_dict.get("sources", []):

            self._ensure_cache(source)

            for p in self._cache[source]:

                key_value = getattr(p, key_field, None)

                if not key_value:
                    continue

                if key_value not in merged:

                    merged[key_value] = Employee(
                        fio=None,
                        username=None,
                        birthday=None,
                        start_date=None,
                        source=source
                    )

                target = merged[key_value]

                for field, src in field_mapping.items():

                    if src != source:
                        continue

                    value = getattr(p, field, None)

                    if value:
                        setattr(target, field, value)

        return list(merged.values())

    def _ensure_cache(self, source: str):

        if source not in self.sources:
            raise RuntimeError(f"Unknown people source: {source}")

        now = time.time()

        if source in self._cache_time:
            if now - self._cache_time[source] < self.cache_ttl:
                return

        source_dict = self.sources[source]

        source_type = source_dict.get("type", "usual")

        people = []

        if source_type == "mixed":
            extra_sources = source_dict.get("sources", [])
            
            people = self._load_mixed_people(source_dict)

        else:
            try:
                people = self._load_people(source_dict)
            except Exception as e:
                print(f"[PeopleDirectoryService] failed to load source '{source}': {e}")
                raise


        

        self._cache[source] = people
        self._cache_time[source] = now

    def _load_people(self, source_cfg: dict) -> List[Employee]:
        import csv
        from io import StringIO

        def norm(s: str) -> str:
            return (s or "").strip().lstrip("\ufeff").lower()

        def get_field_value(row: List[str], field_name: str) -> Optional[str]:
            idx = field_indexes.get(field_name)
            
            if idx is None:
                return None
            if 0 <= idx < len(row):
                v = row[idx]
                return v.strip() if isinstance(v, str) else v
            return None

        source = source_cfg.get("name", "unknown")

        url = source_cfg.get("url")
        path = source_cfg.get("path")

        mode = source_cfg.get("mode", "indexed")  # "indexed" | "named"
        required_fields = tuple(source_cfg.get("required_fields", ("fio",)))
        fields_mapping = dict(source_cfg.get("fields_mapping", {}))
        has_header = bool(source_cfg.get("has_header", False)) 
        field_indexes: dict[str, int] = {}

        if not url and not path:
            raise RuntimeError("People source must contain url or path")

        service_account_b64 = source_cfg.get("service_account_b64")

        if service_account_b64 and url and "docs.google.com" in url:
            print("Loading using Google Sheets API, url:", url)

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

        else:
            print("Loading without Google Sheets API, url:", url)

            if url:
                r = requests.get(url, timeout=15)
                r.raise_for_status()

                text = r.content.decode("utf-8-sig", errors="replace")

                head = text[:200].lower()
                if "<html" in head or "<!doctype" in head:
                    raise RuntimeError(
                        "Google Sheets returned HTML instead of CSV. "
                        "Check sharing/publish settings for the sheet."
                    )

                f = StringIO(text)

            else:
                f = open(Path(path), "r", encoding="utf-8-sig", newline="")

            try:
                reader = csv.reader(f)
                rows = list(reader)
            finally:
                try:
                    f.close()
                except:
                    pass

                if not rows:
                    return []

                field_indexes: dict[str, int] = {}

        

        if mode == "indexed":
            for k, v in fields_mapping.items():
                if v is None:
                    continue
                if not isinstance(v, int):
                    raise RuntimeError(f"indexed mode expects int index for '{k}', got {v!r}")
                if v < 0:
                    raise RuntimeError(f"indexed mode: negative index for '{k}': {v}")
                field_indexes[k] = v

            for rf in required_fields:
                if rf not in field_indexes:
                    raise RuntimeError(f"Required field '{rf}' missing in fields_mapping (indexed mode)")

            data_rows = rows[1:] if has_header else rows

        elif mode == "named":
            header = rows[0]
            header_map = {norm(col): i for i, col in enumerate(header) if norm(col)}

            for internal_field, real_col_name in fields_mapping.items():
                if real_col_name is None:
                    continue
                if not isinstance(real_col_name, str):
                    raise RuntimeError(f"named mode expects str column name for '{internal_field}', got {real_col_name!r}")

                key = norm(real_col_name)
                if key in header_map:
                    field_indexes[internal_field] = header_map[key]

            for rf in required_fields:
                if rf not in field_indexes:
                    want = fields_mapping.get(rf)
                    raise RuntimeError(
                        f"Required field '{rf}' not found in header (wanted column name: {want!r})"
                    )

            data_rows = rows[1:] 

        else:
            raise RuntimeError(f"Unknown mode: {mode!r}")

        people: List[Employee] = []
        for row in data_rows:
            fio = get_field_value(row, "fio") or ""
            if not fio.strip():
                continue



            people.append(
                Employee(
                    fio=fio.strip(),
                    username=self._normalize_username(get_field_value(row, "username")),
                    birthday=self._parse_date(get_field_value(row, "birthday")),
                    start_date=self._parse_date(get_field_value(row, "start_date")),

                    status=get_field_value(row, "status"),
                    position=get_field_value(row, "position"),
                    workload=get_field_value(row, "workload"),
                    employment_type=get_field_value(row, "employment_type"),
                    format=get_field_value(row, "format"),
                    engagement=get_field_value(row, "engagement"),
                    zone=get_field_value(row, "zone"),
                    risk=get_field_value(row, "risk"),
                    comments=get_field_value(row, "comments"),

                    probation_end=self._parse_date(get_field_value(row, "probation_end")),
                    current_date=self._parse_date(get_field_value(row, "current_date")),

                    resume=get_field_value(row, "resume"),
                    offer=get_field_value(row, "offer"),
                    employee_card=get_field_value(row, "employee_card"),

                    last_heat=self._parse_date(get_field_value(row, "last_heat")),
                    next_heat=self._parse_date(get_field_value(row, "next_heat")),

                    last_1to1=self._parse_date(get_field_value(row, "last_1to1")),
                    next_1to1=self._parse_date(get_field_value(row, "next_1to1")),

                    gender=get_field_value(row, "gender"),
                    stack=get_field_value(row, "stack"),
                    project=get_field_value(row, "project"),
                    project_description=get_field_value(row, "project_description"),

                    manager=get_field_value(row, "manager"),
                    phone=get_field_value(row, "phone"),

                    welcome_training=get_field_value(row, "welcome_training"),
                    salary=get_field_value(row, "salary"),
                    social_package=get_field_value(row, "social_package"),
                    salary_changes=get_field_value(row, "salary_changes"),

                    children=get_field_value(row, "children"),
                    address=get_field_value(row, "address"),
                    telegram_contact=get_field_value(row, "telegram_contact"),
                    email=get_field_value(row, "email"),

                    emergency_contact=get_field_value(row, "emergency_contact"),

                    photo_url=get_field_value(row, "photo_url"),
                    

                    source=source
                    )


                )



        return people

    def _parse_date(self, value: Optional[str]) -> Optional[date]:

        if not value:
            return None

        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m"):

            try:

                d = datetime.strptime(value, fmt)

                if fmt == "%d.%m":
                    return date(2000, d.month, d.day)

                return d.date()

            except:
                pass

        return None

    def _normalize_username(self, username: Optional[str]):

        if not username:
            return None
        if username.startswith("@"):

            return username.lstrip("@")
        if username.startswith("https://t.me/"):

            return username.split("https://t.me/")[1].rstrip("/")
            
        
        return username

        