# Personal Pokémon GO Calendar

This repository generates one auto-updating iCalendar feed from the
ScrapedDuck Pokémon GO event data.

## What it does

ScrapedDuck JSON → your filters → `pokemon-go.ics` → Apple Calendar

The generator runs automatically four times per day using GitHub Actions.

## Setup

1. Create a **public GitHub repository**, e.g. `pokemon-go-calendar`.
2. Upload these files/folders to the repository:
   - `generate_calendar.py`
   - `config.py`
   - `.github/workflows/update.yml`
3. In GitHub, open **Settings → Pages**.
4. Set **Source** to **GitHub Actions**.
5. Open **Actions** and run **Update Pokémon GO calendar** once manually.
6. Your feed will be:

   `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/pokemon-go.ics`

GitHub documents the Pages/Actions setup here:
https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Filtering

Edit `config.py`.

### Exclude whole categories

For example:

    EXCLUDE_TYPES = [
        "go-battle-league",
        "event",
    ]

### Exclude individual events

    EXCLUDE_EVENT_IDS = [
        "lego-pokemon-go-2026",
    ]

### Exclude by text

    EXCLUDE_TEXT = [
        "Web Store",
        "Showcase",
    ]

### Include only selected categories

If `INCLUDE_TYPES` is non-empty, everything else is excluded:

    INCLUDE_TYPES = [
        "pokemon-spotlight-hour",
        "raid-hour",
        "raid-day",
        "max-mondays",
        "community-day",
    ]

The source currently exposes fields such as `eventID`, `name`, `eventType`,
`heading`, `link`, `start`, and `end`, so filtering can be done without
scraping the rendered PoGO Calendar website.

## Apple Calendar

On iPhone:

Settings → Apps → Calendar → Calendar Accounts → Add Account →
Other → Add Subscribed Calendar

Paste the `.ics` URL above.

Alternatively, open the URL in Safari and use the subscription option if
iOS presents it.

## Notes

- The feed is public because GitHub Pages is public on GitHub Free.
- Do not put secrets or private information in this repository.
- Unspecific upstream events with no start/end time are skipped.
- Unsuffixed upstream timestamps are treated as America/New_York.
- UTC timestamps are converted to America/New_York.
