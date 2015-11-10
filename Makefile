SHELL := /bin/bash

macbundle:
	if [ -e cookies.txt ]; then mv cookies.txt .cookies.txt; fi
	if [ -e config/login.json ]; then mv config/login.json config/.login.json; fi
	if [ -e config/players.json ]; then mv config/players.json config/.players.json; fi
	if [ -e config/settings.json ]; then mv config/settings.json config/.settings.json; fi
	rm -rf build dist
	python3 setup.py py2app --packages=requests
	dmgbuild -s dmg/settings.py "Auto Buyer Installer" dist/AutoBuyerInstaller.dmg
	if [ -e .cookies.txt ]; then mv .cookies.txt cookies.txt; fi
	if [ -e config/.login.json ]; then mv config/.login.json config/login.json; fi
	if [ -e config/.players.json ]; then mv config/.players.json config/players.json; fi
	if [ -e config/.settings.json ]; then mv config/.settings.json config/settings.json; fi