#!/usr/bin/env bash
# -*- coding: utf-8 -*-

pygount --folders-to-skip .git,venv,scripts,htmlcov,img,config,background,.idea,.vscode --suffix py,sh .

pygount --format=summary --folders-to-skip .git,venv,scripts,htmlcov,img,config,background,.idea,.vscode --suffix py,sh .
