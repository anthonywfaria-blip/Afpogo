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
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r", "")
        .replace("\n", "\\n")
    )


def get_event_symbol(event_type):
    """
    Return the configured symbol for an event type.
    Falls back to DEFAULT_EVENT_SYMBOL for new/unrecognized types.
    """

    event_type = (event_type or "").strip().lower()

    return EVENT_TYPE_SYMBOLS.get(
        event_type,
        DEFAULT_EVENT_SYMBOL,
    )


def get_exclusion_reason(event):
    """
    Returns the reason an event should be excluded,
    or None if the event should be included.
    """

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

        heading = event.get("heading") or ""
        link = event.get("link") or ""

        symbol = get_event_symbol(etype)

        # Add the symbol to the beginning of the calendar title.
        calendar_name = f"{symbol} {name}"

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


def print_report(
    total,
    included,
    excluded,
    missing_dates,
    exclusion_reasons,
    excluded_events,
):
    print("")
    print("=" * 70)
    print("POKÉMON GO CALENDAR FILTER REPORT")
    print("=" * 70)

    print(f"Events fetched:          {total}")
    print(f"Events included:         {included}")
    print(f"Events excluded:         {excluded}")
    print(f"Events missing dates:    {missing_dates}")

    print("-" * 70)
    print("EXCLUSION SUMMARY")
    print("-" * 70)

    if not exclusion_reasons:
        print("No events were excluded.")

    else:
        for reason, count in sorted(
            exclusion_reasons.items(),
            key=lambda x: (-x[1], x[0]),
        ):
            print(f"{count:4}  {reason}")

    print("-" * 70)
    print("EXCLUDED EVENTS")
    print("-" * 70)

    if not excluded_events:
        print("No excluded events.")

    else:
        for event in excluded_events:
            print(
                f"{event['symbol']} "
                f"[{event['reason']}] "
                f"{event['name']} "
                f"(type={event['type']}, id={event['id']})"
            )

    print("-" * 70)
    print("EVENT TYPE SYMBOLS")
    print("-" * 70)

    for event_type, symbol in sorted(
        EVENT_TYPE_SYMBOLS.items()
    ):
        print(f"{symbol}  {event_type}")

    print("=" * 70)
    print("")


def main():
    print("Fetching Pokémon GO events...")
    print(f"Source: {SOURCE_URL}")
    print(f"Timezone: {TIMEZONE}")

    events = fetch_json()

    if isinstance(events, dict):
        if isinstance(events.get("events"), list):
            events = events["events"]
        else:
            raise ValueError(
                "Unexpected JSON format: could not find event list."
            )

    if not isinstance(events, list):
        raise ValueError(
            "Unexpected JSON format: expected a list of events."
        )

    print(f"Fetched {len(events)} events.")

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

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{CALENDAR_NAME}</title>
</head>
<body>
<h1>{CALENDAR_NAME}</h1>
<p>Filtered auto-updating calendar.</p>
<p>Generated events: {included}</p>
<p>Excluded events: {excluded}</p>
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

    print_report(
        len(events),
        included,
        excluded,
        missing_dates,
        exclusion_reasons,
        excluded_events,
    )

    print(
        f"Generated {OUT} with {included} events."
    )


if __name__ == "__main__":
    main()
