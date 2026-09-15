# Pokémon GO calendar filters

# New Jersey / Eastern Time.
# Automatically handles EST in winter and EDT in summer.
TIMEZONE = "America/New_York"


# Event TYPES to exclude.
EXCLUDE_TYPES = [
    "go-battle-league",
]


# Specific event TITLE text to exclude.
#
# Matching is case-insensitive and partial.
#
# Example:
# "GO Fest"
# excludes titles containing "GO Fest".
EXCLUDE_TITLES = [
]


# Specific event IDs to exclude.
EXCLUDE_EVENT_IDS = [
]


# Optional advanced whitelist.
# Leave empty to include everything except exclusions above.
INCLUDE_TYPES = []


# ScrapedDuck event feed.
SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "bigfoott/ScrapedDuck/data/events.json"
)

CALENDAR_NAME = "Pokémon GO"
