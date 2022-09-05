#!/usr/bin/env python3
import os,sys
run = lambda x:os.system(x)

for x in ['Gruntfuggly.todo-tree', 'ms-python.python', 'actboy168.tasks', 'dchanco.vsc-invoke', 'donjayamanne.githistory', 'alefragnani.Bookmarks', 'littlefoxteam.vscode-python-test-adapter', 'njpwerner.autodocstring', 'sourcery.sourcery', 'GitHub.copilot', 'hbenl.vscode-test-explorer']:
	run(f"code-server --install-extension {x}")
