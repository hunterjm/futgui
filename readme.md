Build (Mac):
```
rm -rf build dist
python3 setup.py py2app --packages=requests
dmgbuild -s dmg/settings.py "Auto Buyer Installer" dist/AutoBuyerInstaller.dmg
```

Build (Windows):
```
rm .\config\login.json
pyinstaller '.\FIFA 16 Auto Buyer.spec'
```