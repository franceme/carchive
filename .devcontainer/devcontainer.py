#!/usr/bin/env python3
import os,sys

try:
	import funbelts as ut
except:
	os.system(f"{sys.executable} -m pip install --upgrade funbelts")
	import funbelts as ut

def run(package):
	cmd = f"code-server --install-extension {package}"
	print(cmd)
	try:
		os.system(cmd)
	except Exception as e:
		print(e)

devcontainer = os.path.join(os.path.dirname(__file__), 'devcontainer.json')
for extension in ut.cmt_json(devcontainer)['customizations']['vscode']['extensions']:
	run(f"{sys.executable} -m pip install {extension}")
