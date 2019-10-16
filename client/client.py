#! /bin/python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Handler:
    def onDestroy(self, *args):
        Gtk.main_quit()

    def open_connect_dialog():
        print("connect")


class ClientGUI:

    connect_dialog = None
    window = None

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("gui.glade")
        builder.connect_signals(Handler())

        self.connect_dialog = builder.get_object("connect_dialog")

        self.window = builder.get_object("main_window")
        self.window.show_all()
        
        #self.window.connect("destroy", Gtk.main_quit)
        #self.window.connect("connect", self.open_connect_dialog)

    def connect(button):
        print("connect")
        connect_dialog.show_all()
        pass

    def open_connect_dialog():
        print("connect")
        connect_dialog.show_all()
        pass


client = ClientGUI()

Gtk.main()