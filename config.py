# Pokémon GO calendar filters

# New Jersey / Eastern Time.
# Automatically handles:
# EST (UTC-5) in winter
# EDT (UTC-4) in summer
TIMEZONE = "America/New_York"

# Event TYPES to exclude.
# Only GO Battle League is excluded by default.
EXCLUDE_TYPES = [
    "go-battle-league",
]

# Specific event TITLE text to exclude.
#
# Matching is case-insensitive and partial.
#
# Examples:
#
# "GO Fest"
# would exclude:
# "Pokémon GO Fest 2026"
# "Pokémon GO Fest: Global"
#
# "Web Store"
# would exclude titles containing "Web Store".
EXCLUDE_TITLES = [
]

# Specific event IDs to exclude.
EXCLUDE_EVENT_IDS = [
]

# Optional advanced whitelist.
# Leave this EMPTY.
# If you put event types here, ONLY those types will appear.
INCLUDE_TYPES = []

# ScrapedDuck event feed.
SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "bigfoott/ScrapedDuck/data/events.json"
)

CALENDAR_NAME = "Pokémon GO"
