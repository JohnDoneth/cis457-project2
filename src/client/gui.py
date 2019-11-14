import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from common import Event


class ClientGUI:

    connect_dialog = None
    window = None
    pipe = None

    def __init__(self, pipe):
        self.pipe = pipe

        builder = Gtk.Builder()
        builder.add_from_file("resources/gui.glade")
        # builder.connect_signals(self)

        handlers = {
            "onDestroy": Gtk.main_quit,
            "on_connect_cancel": self.on_connect_cancel,
            "open_connect_dialog": self.open_connect_dialog,
        }
        builder.connect_signals(handlers)

        # builder.connect("on_connect_cancel", self.on_connect_cancel)

        # print(f"blah: { builder.get_object('connect_dialog') }")

        self.connect_dialog = builder.get_object("connect_dialog")
        self.connect_dialog.show_all()

        # self.window = builder.get_object("main_window")
        # self.window.show_all()

        # print(self.connect_dialog.signals)
        self.connect_dialog.connect("destroy", self.on_destroy)

        Gtk.main()

    def onButtonCancel(self, _):
        print("cancel")

    def on_connect_cancel(self, _):
        self.on_destroy(_)

    def on_destroy(self, _):
        self.pipe.send(Event.QUIT)
        Gtk.main_quit()

    def open_connect_dialog(self, button):
        print("connect")
        self.connect_dialog.show_all()
        pass


