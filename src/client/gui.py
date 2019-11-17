import wx


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((484, 747))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.server_hostname = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "127.0.0.1", style=wx.TE_PROCESS_ENTER
        )
        self.server_port = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "12345", style=wx.TE_PROCESS_ENTER
        )
        self.username = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER
        )
        self.hostname = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "John/127.0.0.1", style=wx.TE_PROCESS_ENTER
        )
        self.connection_speed = wx.ComboBox(
            self.panel_1,
            wx.ID_ANY,
            choices=["Ethernet", "Dial-up", "64K Modem", "Gigabit"],
            style=wx.CB_DROPDOWN,
        )
        self.connect_button = wx.Button(self.panel_1, wx.ID_ANY, "Connect")
        self.disconnect_button = wx.Button(self.panel_1, wx.ID_ANY, "Disconnect")
        self.search_input = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER
        )
        self.search_button = wx.Button(self.panel_1, wx.ID_ANY, "Search")
        self.search_output = wx.ListCtrl(
            self.panel_1, wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES
        )
        self.search_progress = wx.Gauge(self.panel_1, wx.ID_ANY, 10)
        self.ftp_input = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER
        )
        self.ftp_button = wx.Button(self.panel_1, wx.ID_ANY, "Execute")
        self.ftp_output = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY
        )

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("GV Napster Host")
        self.connection_speed.SetSelection(0)
        self.connect_button.SetMinSize((200, 40))
        self.disconnect_button.SetMinSize((200, 40))
        self.disconnect_button.Enable(False)
        self.search_output.AppendColumn(
            "Filename", format=wx.LIST_FORMAT_LEFT, width=-1
        )
        self.search_output.AppendColumn(
            "Hostname", format=wx.LIST_FORMAT_LEFT, width=-1
        )
        self.search_output.AppendColumn("Speed", format=wx.LIST_FORMAT_LEFT, width=-1)
        self.search_progress.Enable(False)
        self.search_progress.Hide()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_1, wx.ID_ANY, "FTP"), wx.VERTICAL
        )
        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_1, wx.ID_ANY, "Search"), wx.VERTICAL
        )
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_1, wx.ID_ANY, "Connection"), wx.VERTICAL
        )
        sizer_8 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_9 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(5, 2, 0, 5)
        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Server Hostname")
        grid_sizer_1.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.server_hostname, 1, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)
        label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "Port")
        grid_sizer_1.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.server_port, 1, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)
        label_5 = wx.StaticText(self.panel_1, wx.ID_ANY, "Username")
        grid_sizer_1.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.username, 1, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)
        label_6 = wx.StaticText(self.panel_1, wx.ID_ANY, "Hostname")
        grid_sizer_1.Add(label_6, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.hostname, 1, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)
        label_7 = wx.StaticText(self.panel_1, wx.ID_ANY, "Connection Speed")
        grid_sizer_1.Add(label_7, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.connection_speed, 1, wx.EXPAND, 0)
        grid_sizer_1.AddGrowableCol(1)
        sizer_8.Add(grid_sizer_1, 1, wx.ALL | wx.EXPAND, 5)
        sizer_9.Add(self.connect_button, 0, wx.ALL | wx.EXPAND, 0)
        sizer_9.Add(self.disconnect_button, 0, wx.EXPAND, 0)
        sizer_8.Add(sizer_9, 0, wx.ALIGN_BOTTOM | wx.ALL, 5)
        sizer_3.Add(sizer_8, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 0, wx.ALL | wx.EXPAND, 5)
        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Keyword")
        label_1.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_5.Add(label_1, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 10)
        sizer_5.Add(
            self.search_input, 1, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 5
        )
        sizer_5.Add(self.search_button, 0, wx.ALL, 5)
        sizer_4.Add(sizer_5, 0, wx.EXPAND, 0)
        sizer_4.Add(self.search_output, 1, wx.ALL | wx.EXPAND, 5)
        sizer_4.Add(self.search_progress, 0, wx.ALL | wx.EXPAND, 5)
        sizer_2.Add(sizer_4, 1, wx.ALL | wx.EXPAND, 5)
        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Enter Command")
        label_2.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_7.Add(label_2, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 10)
        sizer_7.Add(self.ftp_input, 1, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 5)
        sizer_7.Add(self.ftp_button, 0, wx.ALL, 5)
        sizer_6.Add(sizer_7, 0, wx.EXPAND, 0)
        sizer_6.Add(self.ftp_output, 1, wx.ALL | wx.EXPAND, 5)
        sizer_2.Add(sizer_6, 1, wx.ALL | wx.EXPAND, 5)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.SetSizeHints(self)
        self.Layout()
        self.Centre()
        # end wxGlade


# end of class MyFrame
