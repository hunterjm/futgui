# Releases
Download pre-built releases on the [releases](https://github.com/hunterjm/futgui/releases) page.

## Contributors
[Jason Hunter](https://github.com/hunterjm) - Core Development

[Piotr Staroszczyk](https://github.com/oczkers) & others - FUT API Library

[Fabiano Francesconi](https://github.com/elbryan)

### Requirements
This has only been tested and built with Python 3.5.
```
pip install -r requirements.txt
```

### Build (Mac):
```
make macbundle
```

### Build (Windows):
Make sure to delete `build` and `dist` folders before re-building, as well as `config\login.json`, `config\players.json`, and `config\settings.json` (unless you *want* to give your credentials out).
```
pyinstaller '.\FIFA 16 Auto Buyer.spec'
```
