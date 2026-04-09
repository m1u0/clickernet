# Clickernet

Tiny Playwright helper that opens iClicker, lets you log in, then continuously polls for a selector and clicks it when found.

## Run

```bash
python clicker.py
```

## Flags

- `--selector`: CSS selector to wait for and click
- `--headless`: run the browser headlessly
- `--state-file`: Playwright storage state file for cached login
