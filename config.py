# Pokémon GO calendar filters
# Leave these empty to include everything from ScrapedDuck.

# Exact eventType values to exclude.
EXCLUDE_TYPES = [
    # "go-battle-league",
    # "event",
]

# Event IDs to exclude. Exact matches.
EXCLUDE_EVENT_IDS = [
]

# Case-insensitive text fragments. If a fragment appears in the
# event name, heading, or eventType, the event is excluded.
EXCLUDE_TEXT = [
    # "Web Store",
]

# Optional: if you prefer a whitelist, put eventTypes here.
# When non-empty, ONLY these types are included.
INCLUDE_TYPES = [
]

TIMEZONE = "America/New_York"
CALENDAR_NAME = "Pokémon GO"
SOURCE_URL = "https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/events.json"
