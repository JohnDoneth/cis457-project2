#! /bin/python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


builder = Gtk.Builder()
builder.add_from_file("gui.glade")
#builder.connect_signals(Handler())

window = builder.get_object("window")
window.show_all()
window.connect("destroy", Gtk.main_quit)

Gtk.main()