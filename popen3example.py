import wx, os

if '__WXMSW__' in wx.PlatformInfo:
    PRESETS = [
        'ipconfig',
        ]
else:
    PRESETS = [
        '/sbin/ifconfig',
        ]

class MyPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        
        self.output = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
    
        runButton = wx.Button(self, -1, "Run Command")
        self.Bind(wx.EVT_BUTTON, self.OnClick, runButton)

        self.command = wx.ComboBox(self, -1, choices = PRESETS)

        sizer2.AddMany([
            (self.command, 1, wx.ALL, 5),
            (runButton, 0, wx.ALL, 5),
            ])
        
        sizer.AddMany([
            (self.output, 1, wx.EXPAND | wx.ALL, 5),
            (sizer2, 0, wx.EXPAND),
            ])

    def OnClick(self, event):
        cmd = self.command.GetValue()
        if cmd:
            input, output, errors = os.popen3(cmd)
            errors = errors.read()
            if errors:
                dlg = wx.MessageDialog(self, errors,
                                       'An error occurred',
                                       wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                self.output.SetValue('')
            else:
                self.output.SetValue(output.read())

class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'Test')
        p = MyPanel(self, -1)
        self.Show(True)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = MyFrame()
    app.MainLoop() 