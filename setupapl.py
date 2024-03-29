"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['vpt.py']
DATA_FILES = ['Welcome.gif', 'Splash.bmp', 'GPL-license.txt', 'gpl-3.0-standalone.htm','annot.xrc','initOptions.xrc','shortcuts.xrc','annotations.xrc','newPiece.xrc','test1.xrc','fileType.xrc','options.xrc','vpt.xrc','imageMagick.xrc','resources.xrc']
OPTIONS = {'argv_emulation': True}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
