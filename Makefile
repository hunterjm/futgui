SHELL := /bin/bash

macbundle:
	for file in *.txt; do if [ -e $$file ]; then mv -n "$$file" ".$${file}"; fi; done
	cd config/
	for file in *.json; do if [ -e $$file ]; then mv -n "$$file" ".$${file}"; fi; done
	cd ../
	rm -rf build dist
	python3 setup.py py2app --packages=requests
	dmgbuild -s dmg/settings.py "Auto Buyer Installer" dist/AutoBuyerInstaller.dmg
	for file in .*.txt; do if [ -e $$file ]; then mv -n "$$file" "$${file#.}"; fi; done
	cd config/
	for file in .*.json; do if [ -e $$file ]; then mv -n "$$file" "$${file#.}"; fi; done
	cd ../