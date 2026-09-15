#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from config import (
    EXCLUDE_TYPES,
    EXCLUDE_EVENT_IDS,
    EXCLUDE_TITLES,
    INCLUDE_TYPES,
    TIMEZONE,
    CALENDAR_NAME,
    SOURCE_URL,
)

OUT = Path("site/pokemon-go.ics")
LOCAL_TZ = ZoneInfo(TIMEZONE)


def fetch_json():
    req = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "pokemon-go-calendar-filter/1.0"},
    )

    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def parse_dt(value):
    if not value:
        return None

    s = value.strip()

    # Explicit UTC timestamp
    if s.endswith("Z"):
        dt = datetime.fromisoformat(s[:-1] + "+00:00")
        return dt.astimezone(LOCAL_TZ)

    # Timestamp with an explicit timezone
    dt = datetime.fromisoformat(s)

    # Timestamp without timezone:
    # treat it as Eastern local time.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)

    return dt.astimezone(LOCAL_TZ)


def ics_escape(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r", "")
        .replace("\n", "\\n")
    )


def excluded(event):
    event_type = str(event.get("eventType") or "").strip().lower()
    event_id = str(event.get("eventID") or "").strip()

    name = str(event.get("name") or "")
    heading = str(event.get("heading") or "")

    # ---------------------------------------------------------
    # 1. Optional whitelist
    # ---------------------------------------------------------
    include_types = {
        str(x).strip().lower()
        for x in INCLUDE_TYPES
        if str(x).strip()
    }

    if include_types and event_type not in include_types:
        return True

    # ---------------------------------------------------------
    # 2. Exclude entire event types
    # ---------------------------------------------------------
    exclude_types = {
        str(x).strip().lower()
        for x in EXCLUDE_TYPES
        if str(x).strip()
    }

    if event_type in exclude_types:
        return True

    # ---------------------------------------------------------
    # 3. Exclude specific event IDs
    # ---------------------------------------------------------
    exclude_ids = {
        str(x).strip()
        for x in EXCLUDE_EVENT_IDS
        if str(x).strip()
    }

    if event_id in exclude_ids:
        return True

    # ---------------------------------------------------------
    # 4. Exclude events based on title text
    # ---------------------------------------------------------
    exclude_titles = [
        str(x).strip().lower()
        for x in EXCLUDE_TITLES
        if str(x).strip()
    ]

    # Match title/name and heading.
    title_text = f"{name} {heading}".lower()

    for phrase in exclude_titles:
        if phrase in title_text:
            return True

    return False


def build_ics(events):
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Anthony//Pokemon GO Filtered Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(CALENDAR_NAME)}",
        f"X-WR-TIMEZONE:{TIMEZONE}",
    ]

    included = 0
    excluded_count = 0

    for event in events:

        if excluded(event):
            excluded_count += 1
            continue

        start = parse_dt(event.get("start"))
        end = parse_dt(event.get("end"))

        if not start or not end:
            continue

        event_id = (
            event.get("eventID")
            or event.get("name")
            or f"event-{included}"
        )

        name = event.get("name") or "Pokémon GO Event"
        heading = event.get("heading") or ""
        link = event.get("link") or ""

        description = heading

        if link:
            description = (
                f"{heading}\\n{link}"
                if heading
                else link
            )

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{ics_escape(event_id)}@anthony-pogo-calendar",
                f"DTSTAMP:{now}",
                (
                    f"DTSTART;TZID={TIMEZONE}:"
                    f"{start.strftime('%Y%m%dT%H%M%S')}"
                ),
                (
                    f"DTEND;TZID={TIMEZONE}:"
                    f"{end.strftime('%Y%m%dT%H%M%S')}"
                ),
                f"SUMMARY:{ics_escape(name)}",
                f"DESCRIPTION:{ics_escape(description)}",
            ]
        )

        if link:
            lines.append(f"URL:{link}")

        lines.extend(
            [
                "END:VEVENT",
            ]
        )

        included += 1

    lines.append("END:VCALENDAR")

    return (
        "\r\n".join(lines) + "\r\n",
        included,
        excluded_count,
    )


def main():
    events = fetch_json()

    ics, included, excluded_count = build_ics(events)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    OUT.write_text(
        ics,
        encoding="utf-8",
        newline="",
    )

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{CALENDAR_NAME}</title>
</head>
<body>
<h1>{CALENDAR_NAME}</h1>
<p>
Filtered auto-updating calendar.
</p>
<p>
Events included: {included}
</p>
<p>
Events excluded by filters: {excluded_count}
</p>
<p>
<a href="pokemon-go.ics">
Subscribe/download the ICS feed
</a>
</p>
</body>
</html>
"""

    (OUT.parent / "index.html").write_text(
        html,
        encoding="utf-8",
    )

    print(f"Generated {OUT}")
    print(f"Events included: {included}")
    print(f"Events excluded: {excluded_count}")


if __name__ == "__main__":
    main()
