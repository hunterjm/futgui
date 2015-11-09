# Releases
Download pre-built releases on the [releases](https://github.com/hunterjm/futgui/releases) page.

## Requirements
This has only been tested and built with Python 3.5.  You must also use my fork of ozkers/fut in order to rate limit the requests properly and mitigate being banned.
```
pip install -r requirements.txt
```

## Build (Mac):
```
make macbundle
```

## Build (Windows):
Make sure to delete `build` and `dist` folders before re-building, as well as `config\login.json` and `config\players.json` (unless you *want* to give your credentials out).
```
pyinstaller '.\FIFA 16 Auto Buyer.spec'
```
