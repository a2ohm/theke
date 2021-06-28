#! /usr/bin/python3
# -*- coding:utf-8 -*-

import sys
import logging
import theke.main

if "--debug" in sys.argv or "-d" in sys.argv:
    logging.basicConfig(level=logging.DEBUG)

ThekeApp = theke.main.ThekeApp()
ThekeApp.run(sys.argv)