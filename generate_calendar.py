#!/usr/bin/env python3
import json
import re
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from config import (
    EXCLUDE_TYPES, EXCLUDE_EVENT_IDS, EXCLUDE_TEXT,
    INCLUDE_TYPES, TIMEZONE, CALENDAR_NAME, SOURCE_URL
)

OUT = Path("site/pokemon-go.ics")
LOCAL_TZ = ZoneInfo(TIMEZONE)

def fetch_json():
    req = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "pokemon-go-calendar-filter/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def parse_dt(value):
    if not value:
        return None
    s = value.strip()
    # ScrapedDuck uses ISO timestamps, sometimes with Z and sometimes
    # without a timezone suffix. Unsuffixed values are treated as local
    # Pokémon GO event times (Eastern for this personal calendar).
    if s.endswith("Z"):
        dt = datetime.fromisoformat(s[:-1] + "+00:00")
        return dt.astimezone(LOCAL_TZ)
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)

def ics_escape(value):
    return (str(value)
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\r", "")
            .replace("\n", "\\n"))

def fold_ics_line(line, limit=75):
    # RFC 5545 line folding is by octets; this simple ASCII-heavy
    # implementation is adequate for generated property lines.
    if len(line) <= limit:
        return [line]
    out = []
    while len(line) > limit:
        out.append(line[:limit])
        line = " " + line[limit:]
    out.append(line)
    return out

def excluded(event):
    etype = (event.get("eventType") or "").lower()
    eid = event.get("eventID") or ""
    name = event.get("name") or ""
    heading = event.get("heading") or ""
    haystack = " ".join([name, heading, etype]).lower()

    if INCLUDE_TYPES and etype not in {x.lower() for x in INCLUDE_TYPES}:
        return True
    if etype in {x.lower() for x in EXCLUDE_TYPES}:
        return True
    if eid in set(EXCLUDE_EVENT_IDS):
        return True
    if any(fragment.lower() in haystack for fragment in EXCLUDE_TEXT):
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
    for e in events:
        if excluded(e):
            continue

        start = parse_dt(e.get("start"))
        end = parse_dt(e.get("end"))
        if not start or not end:
            # Some upstream events have no date/time. They cannot be
            # represented usefully as normal calendar events.
            continue

        eid = e.get("eventID") or e.get("name") or f"event-{included}"
        name = e.get("name") or "Pokémon GO Event"
        heading = e.get("heading") or ""
        link = e.get("link") or ""

        description = heading
        if link:
            description = f"{heading}\\n{link}" if heading else link

        lines += [
            "BEGIN:VEVENT",
            f"UID:{ics_escape(eid)}@anthony-pogo-calendar",
            f"DTSTAMP:{now}",
            f"DTSTART;TZID={TIMEZONE}:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID={TIMEZONE}:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{ics_escape(name)}",
            f"DESCRIPTION:{ics_escape(description)}",
        ]
        if link:
            lines.append(f"URL:{link}")
        lines += ["END:VEVENT"]
        included += 1

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n", included

def main():
    events = fetch_json()
    ics, count = build_ics(events)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(ics, encoding="utf-8", newline="")
    # Simple landing page so the Pages site has a useful root.
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{CALENDAR_NAME}</title></head>
<body>
<h1>{CALENDAR_NAME}</h1>
<p>Filtered auto-updating calendar. Current generated event count: {count}.</p>
<p><a href="pokemon-go.ics">Subscribe/download the ICS feed</a></p>
</body></html>
"""
    (OUT.parent / "index.html").write_text(html, encoding="utf-8")
    print(f"Generated {OUT} with {count} events.")

if __name__ == "__main__":
    main()
