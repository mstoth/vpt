"""
Virtual Page Turner, a program to help musicians view and turn pages using a computer.

    Copyright (C) 2008  Michael Toth

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import wx
if wx.Platform == '__WXMSW__':
  from wx.lib.pdfwin import PDFWindow
  
class PDFPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent, id=-1)
    self.pdf = None
    sizer = wx.BoxSizer(wx.VERTICAL)
    btnSizer = wx.BoxSizer(wx.HORIZONTAL)
    self.pdf = PDFWindow(self, style=wx.SUNKEN_BORDER)
    sizer.Add(self.pdf, proportion=1, flag=wx.EXPAND)
    btn = wx.Button(self, wx.NewId(), "Open PDF File")
    self.Bind(wx.EVT_BUTTON, self.OnOpenButton, btn)
    btnSizer.Add(btn, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
    btn = wx.Button(self, wx.NewId(), "Previous Page")
    self.Bind(wx.EVT_BUTTON, self.OnPrevPageButton, btn)
    btnSizer.Add(btn, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
    btn = wx.Button(self, wx.NewId(), "Next Page")
    self.Bind(wx.EVT_BUTTON, self.OnNextPageButton, btn)
    btnSizer.Add(btn, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
    btnSizer.Add((50,-1), proportion=2, flag=wx.EXPAND)
    sizer.Add(btnSizer, proportion=0, flag=wx.EXPAND)
    self.SetSizer(sizer)
    self.SetAutoLayout(True)
  
  def OnOpenButton(self, event):
    # make sure you have PDF files available on your drive
    dlg = wx.FileDialog(self, wildcard="*.pdf")
    if dlg.ShowModal() == wx.ID_OK:
      wx.BeginBusyCursor()
      self.pdf.LoadFile(dlg.GetPath())
      wx.EndBusyCursor()
      dlg.Destroy()
      
  def OnPrevPageButton(self, event):
    self.pdf.gotoPreviousPage()
    
  def OnNextPageButton(self, event):
      self.pdf.gotoNextPage()   
      
  def LoadFile(self,name):
    self.pdf.LoadFile(name)
    
app = wx.PySimpleApp()
# create window/frame, no parent, -1 is default ID, title, size
frame = wx.Frame(None, -1, "PDFWindow", size = (640, 480))
# make an instance of the class
PDFPanel(frame)
# show the frame
frame.Show(True)
# start the event loop
app.MainLoop()