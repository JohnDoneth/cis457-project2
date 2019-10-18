import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class ClientGUI:

    connect_dialog = None
    window = None

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("gui.glade")
        builder.connect_signals(self)

        self.connect_dialog = builder.get_object("connect_dialog")
        self.connect_dialog.show_all()

        #self.window = builder.get_object("main_window")
        #self.window.show_all()
        
        #self.window.connect("destroy", Gtk.main_quit)
        #self.window.connect("connect", self.open_connect_dialog)

        Gtk.main()

    def open_connect_dialog(self, button):
        print("connect")
        self.connect_dialog.show_all()
        pass
