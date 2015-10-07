SHELL := /bin/bash

macbundle:
	if [ -e cookies.txt ]; then mv cookies.txt .cookies.txt; fi
	if [ -e config/login.json ]; then mv config/login.json config/.login.json; fi
	rm -rf build dist
	python3 setup.py py2app --packages=requests
	dmgbuild -s dmg/settings.py "Auto Buyer Installer" dist/AutoBuyerInstaller.dmg
	if [ -e .cookies.txt ]; then mv .cookies.txt cookies.txt; fi
	if [ -e config/.login.json ]; then mv config/.login.json config/login.json; fi