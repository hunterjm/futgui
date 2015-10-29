# -*- mode: python -*-

block_cipher = None
my_data = [('.\\images', 'images'),
          ('.\\fonts', 'fonts'),
          ('.\\config', 'config')]


a = Analysis(['FIFA 16 Auto Buyer.py'],
             pathex=['..\\fut', '.'],
             binaries=None,
             datas=my_data,
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='FIFA 16 Auto Buyer',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='FIFA 16 Auto Buyer')
