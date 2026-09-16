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
EXCLUDE_EVENT_IDS = []


# Optional advanced whitelist.
# Leave empty to include everything except exclusions above.
INCLUDE_TYPES = []


# ---------------------------------------------------------
# EVENT TYPE SYMBOLS
# ---------------------------------------------------------
#
# The symbol is placed at the beginning of the calendar
# event title.
#
# Example:
# "🐲 Raid Hour: ..."
#
# If ScrapedDuck adds a new event type that is not listed
# here, the DEFAULT_EVENT_SYMBOL is used.
#

EVENT_TYPE_SYMBOLS = {

    # Showcases
    "pokestop-showcase": "🏆",

    # Raids
    "raid-day": "🐲",
    "raid-hour": "🐲",
    "raid-battles": "🐲",
    "raid-weekend": "🐲",
    "elite-raids": "🐲",

    # Spotlight / Community
    "pokemon-spotlight-hour": "🔦",
    "community-day": "🌐",
    "community-day-classic": "🌐",

    # GO Battle League
    "go-battle-league": "⚔️",

    # Research
    "limited-research": "⏳",
    "research": "🔬",

    # Max Battles
    "max-mondays": "💥",
    "max-battles": "💥",

    # Major events
    "pokemon-go-fest": "🎉",
    "pokemon-go-tour": "🌎",
    "wild-area": "🌲",
    "live-event": "🎟️",

    # Seasonal / general
    "season": "🍂",
    "choose-your-path": "🛤️",
    "event": "📅",
}


# Used automatically for any new/unrecognized event type.
DEFAULT_EVENT_SYMBOL = "📅"


# ScrapedDuck event feed.
SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "bigfoott/ScrapedDuck/data/events.json"
)

CALENDAR_NAME = "Pokémon GO"
