SHELL := /bin/bash
DMGBUILD := $(shell command -v dmgbuild 2> /dev/null)

macbundle:
	rm -rf build dist
	python3 setup.py py2app --packages=requests,PIL
ifdef DMGBUILD
	dmgbuild -s dmg/settings.py "Auto Buyer Installer" dist/AutoBuyerInstaller.dmg
endif