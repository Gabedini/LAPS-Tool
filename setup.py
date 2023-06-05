from setuptools import setup

APP=['LAPSTool.py']
OPTIONS = {
	'iconfile':'images/icon.icns'
}

setup(
	app=APP,
	options={'py2app': OPTIONS},
	setup_requires=['py2app']
)