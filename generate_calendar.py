#!/usr/bin/env python3

import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from config import (
    EXCLUDE_TYPES,
    EXCLUDE_EVENT_IDS,
    EXCLUDE_TITLES,
    INCLUDE_TYPES,
    EVENT_TYPE_SYMBOLS,
    DEFAULT_EVENT_SYMBOL,
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

    if s.endswith("Z"):
        dt = datetime.fromisoformat(s[:-1] + "+00:00")
        return dt.astimezone(LOCAL_TZ)

    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))

    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)

    return dt.astimezone(LOCAL_TZ)


def ics_escape(value):
    """
    Escape text for an iCalendar TEXT property.
    """
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r", "")
        .replace("\n", "\\n")
    )


def get_event_symbol(event_type):
    event_type = (event_type or "").strip().lower()

    return EVENT_TYPE_SYMBOLS.get(
        event_type,
        DEFAULT_EVENT_SYMBOL,
    )


def get_exclusion_reason(event):
    etype = (event.get("eventType") or "").strip().lower()
    eid = str(event.get("eventID") or "").strip()
    name = (event.get("name") or "").strip()
    heading = (event.get("heading") or "").strip()

    include_types = {
        str(x).strip().lower()
        for x in INCLUDE_TYPES
        if str(x).strip()
    }

    if include_types and etype not in include_types:
        return f"TYPE not in INCLUDE_TYPES: {etype or '[blank]'}"

    exclude_types = {
        str(x).strip().lower()
        for x in EXCLUDE_TYPES
        if str(x).strip()
    }

    if etype in exclude_types:
        return f"TYPE: {etype}"

    exclude_ids = {
        str(x).strip()
        for x in EXCLUDE_EVENT_IDS
        if str(x).strip()
    }

    if eid and eid in exclude_ids:
        return f"EVENT ID: {eid}"

    title_text = f"{name} {heading}".lower()

    for fragment in EXCLUDE_TITLES:
        fragment = str(fragment).strip()

        if fragment and fragment.lower() in title_text:
            return f"TITLE contains: {fragment}"

    return None


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
    excluded = 0
    missing_dates = 0

    exclusion_reasons = Counter()
    excluded_events = []

    for event in events:
        name = event.get("name") or "Pokémon GO Event"
        etype = event.get("eventType") or "[blank]"
        eid = event.get("eventID") or "[no ID]"

        reason = get_exclusion_reason(event)

        if reason:
            excluded += 1
            exclusion_reasons[reason] += 1

            symbol = get_event_symbol(etype)

            excluded_events.append(
                {
                    "name": name,
                    "type": etype,
                    "id": eid,
                    "reason": reason,
                    "symbol": symbol,
                }
            )

            continue

        start = parse_dt(event.get("start"))
        end = parse_dt(event.get("end"))

        if not start or not end:
            missing_dates += 1
            continue

        heading = (event.get("heading") or "").strip()
        link = (event.get("link") or "").strip()

        # Add the event-type symbol to the beginning of the title.
        symbol = get_event_symbol(etype)
        calendar_name = f"{symbol} {name}"

        # Keep the description clean.
        #
        # IMPORTANT:
        # Use a REAL newline here, not "\\n".
        # ics_escape() will convert the real newline into
        # the proper iCalendar "\\n" escape.
        #
        # The URL is ALSO placed in the dedicated URL property
        # below, which is the proper iCalendar field for the
        # event's web link.
        if heading and link:
            description = f"{heading}\n{link}"
        elif link:
            description = link
        else:
            description = heading

        uid = eid if eid != "[no ID]" else name

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{ics_escape(uid)}@anthony-pogo-calendar",
                f"DTSTAMP:{now}",
                (
                    f"DTSTART;TZID={TIMEZONE}:"
                    f"{start.strftime('%Y%m%dT%H%M%S')}"
                ),
                (
                    f"DTEND;TZID={TIMEZONE}:"
                    f"{end.strftime('%Y%m%dT%H%M%S')}"
                ),
                f"SUMMARY:{ics_escape(calendar_name)}",
                f"DESCRIPTION:{ics_escape(description)}",
            ]
        )

        # Put the event webpage in the dedicated iCalendar URL field.
        # Do NOT run the URL through ics_escape(), because URL is a URI
        # property rather than a TEXT property.
        if link:
            lines.append(f"URL:{link}")

        lines.append("END:VEVENT")

        included += 1

    lines.append("END:VCALENDAR")

    ics = "\r\n".join(lines) + "\r\n"

    return (
        ics,
        included,
        excluded,
        missing_dates,
        exclusion_reasons,
        excluded_events,
    )


def main():
    events = fetch_json()

    (
        ics,
        included,
        excluded,
        missing_dates,
        exclusion_reasons,
        excluded_events,
    ) = build_ics(events)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    OUT.write_text(
        ics,
        encoding="utf-8",
        newline="",
    )

    print(f"Generated {OUT}")
    print(f"Included events: {included}")
    print(f"Excluded events: {excluded}")
    print(f"Events missing dates: {missing_dates}")

    if exclusion_reasons:
        print("\nExclusion reasons:")

        for reason, count in sorted(exclusion_reasons.items()):
            print(f"  {count} × {reason}")

    if excluded_events:
        print("\nExcluded events:")

        for event in excluded_events:
            print(
                f"  {event['symbol']} {event['name']} "
                f"[{event['type']}] "
                f"({event['id']}) - {event['reason']}"
            )


if __name__ == "__main__":
    main()
