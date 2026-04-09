# Clickernet

Tiny Playwright helper that opens iClicker, lets you log in, then continuously polls for a selector and clicks it when found.

## Run

```bash
python clicker.py
```

Example with spoofed browser geolocation:

```bash
python clicker.py --latitude 37.7749 --longitude -122.4194 --accuracy 50
```

## Flags

- `--selector`: CSS selector to wait for and click
- `--headless`: run the browser headlessly
- `--state-file`: Playwright storage state file for cached login
- `--latitude` and `--longitude`: enable Geolocation API spoofing for sites that request precise location
- `--accuracy`: reported geolocation accuracy in meters
