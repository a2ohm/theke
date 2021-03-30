#! /usr/bin/python3
# -*- coding:utf-8 -*-

import Sword
import theke.gui.mainwindow

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, WebKit2

# Main windows
TW = theke.gui.mainwindow.ThekeWindow()
TW.connect("destroy", Gtk.main_quit)

# Load some text
key = "John 1:1"
moduleName = "MorphGNT"

markup = Sword.MarkupFilterMgr(Sword.FMT_OSIS)
markup.thisown = False

mgr = Sword.SWMgr(markup)
mgr.setGlobalOption("Strong's Numbers", "Off")
mgr.setGlobalOption("Cross-references", "Off")
mgr.setGlobalOption("Lemmas", "Off")
mgr.setGlobalOption("Morphological Tags", "Off")

mod = mgr.getModule(moduleName)

vk = Sword.VerseKey(key)
vk.setPersist(True)

mod.setKey(vk)

verse = str(mod.renderText())
vk.increment()

while vk.getChapter() == 1:
    verse += " " + str(mod.renderText())
    vk.increment()

# Format the html page
html = "<h1>{mod_name}</h1><p>{mod_description}</p><p>{text}</p>".format(
    mod_name = mod.getName(),
    mod_description = mod.getDescription(),
    text = verse)

# Display the html page
TW.load_html(html)
TW.show_all()
Gtk.main()