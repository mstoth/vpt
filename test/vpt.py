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
import wx.lib.dialogs
import os
import re
import sys
import traceback
import wx.html
import commands

if wx.Platform == '__WXMSW__':
    import twain
from simple_base import TwainBase

import  wx.xrc  as  xrc
from panels import *
from Program import *

"""

Currently options are saved in a file under the vpt home directory.
We need to find a better method.

The options are saved in the format

         [ optionName, optionValue ]

There is one option per line.

A typical file will appear as follows:

['VIEW_MODE','Two Page']
['SCROLL_AMOUNT',300]
['MUSIC_DIR',os.getcwd()]

The important thing is to remember that each line must be able to be an argument to eval()
since a list is created by appending as follows:

self.options.append(eval(line))

where 'line' is the line read from the file

"""
vpthome = os.getenv('VPT_HOME')
if vpthome:
    optionsFile = vpthome + '/vptoptions.txt'
    if os.path.exists(optionsFile):
        options = Options(optionsFile)
    else:
        options = Options()
        

XferByFile='File'
XferNatively='Natively'
recognizedExtensions = ['gif','bmp','tiff','jpeg','jpg','png','pdf']

pgm = Program()

class vptFrame(wx.Frame, TwainBase):
    """ 
    Top Level Frame for Virtual Page Turner
    
    Inherits from wx.Frame, 
    Sets screen size to be display size.
    Uses the file "Welcome.gif" as the initial page image.
    Creates menus and binds menu items.
    Creates status bar. 
    Sets options to their initial default values.
    (To Do: Allow for options to be saved and restored when running again)
    page1 is the current page
    page2 is the next page

    """
    def __init__(self, parent=None, id=-1, pos=wx.DefaultPosition, title='Virtual Page Turner'):

        self.vpthome = os.getenv('VPT_HOME')
        if wx.Platform == '__WXMSW__':
            if self.vpthome:
                os.chdir(self.vpthome)
            else:
                wx.MessageBox('You need to have VPT_HOME set to run Virtual Page Turner.')
                sys.exit()
                
               
# Menu Handling Routines
        """Create a frame instance and show the initial banner"""
        self.screenSize = wx.GetDisplaySize()
        wx.Frame.__init__(self,None,id,title,pos) # no longer using screenSize because status bar is hidden behind Windows task bar and Apple Dock
        self.Maximize()
        image = wx.Image('Welcome.gif',wx.BITMAP_TYPE_GIF)

        # if we couldn't open up the options file, present the initialization panel to set options
        if not os.path.exists(optionsFile):
            ipnl = InitPanel()
            dlg = ipnl.dlg
            if (ipnl.dlg.ShowModal() == wx.ID_OK):
                musicDir = ipnl.musicDir.GetTextCtrlValue()
                viewMode = ipnl.viewMode.GetSelection()
                if viewMode == 0:
                    viewMode = "Two Page"
                else:
                    viewMode = "Fit Width"
                scrollAmount = ipnl.scrollAmount.GetValue()
                timerValue = ipnl.timerValue.GetValue()
                options.addOption('MUSIC_DIR',musicDir)
                options.addOption('SCROLL_AMOUNT',int(scrollAmount))
                options.addOption('TIMER_VALUE',float(timerValue))
                options.addOption('VIEW_MODE',viewMode)
                options.save(optionsFile)
            else:
                wx.MessageBox("You need to set options before running Virtual Page Turner.","Error")
                sys.exit()

        # xpos and ypos indicate the top left hand corner of the current page
        self.xpos = 0
        self.ypos = 0

        # options
        self.VIEWMODE = options.getOption('VIEW_MODE')
        self.SCROLL_AMOUNT = float(options.getOption('SCROLL_AMOUNT'))
        self.MUSIC_DIR = options.getOption('MUSIC_DIR')
        self.TIMER_VALUE = options.getOption('TIMER_VALUE')*1000.0
        
        self.timer = wx.Timer(self,1)
        self.Bind(wx.EVT_TIMER,self.OnTimer,self.timer)
        
        # page number when acquiring pages from twain source
        self.pageNum = 1
        self.pageStr = '01'
        self.dirName = '.'
        self.fname=''
        SM=None                               # Source Manager
        SD=None                                # Data Source
        ProductName='Virtual Page Turner'  # Name of this product
        XferMethod = XferNatively        # Transfer method currently in use
        AcquirePending = False           # Flag to indicate that there is an acquire pending
        mainWindow = None               # Window handle for the application window
        self.SourceName = None          # Holds the name of the twain source to prevent repeated select panels
        self.imageSuffix = '.gif'             # default suffix for the page images
        
        # twain initialization
        self.Initialise()
        
        # annotation variables
        self.oldPos = -1 # position of rectangle to move with mouse
        self.annotationText = None
        self.annotationFont = None
        self.Annotating = False
        self.currentPage = None
        self.nextPage = None
        self.prevPage = None
        self.page1 = image.ConvertToBitmap()
        self.page2 = self.page1
        self.clientSizeX , self.clientSizeY = self.GetClientSizeTuple()
        self.clientOriginX , self.clientOriginY = self.GetClientAreaOrigin()
        
        # Menu Creation
        self.createMenus()
        self.Bind(wx.EVT_WINDOW_DESTROY,self.OnQuit)
        
        # Bind Keys
        self.Bind(wx.EVT_CHAR, self.OnKeyDown)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Resize Handler
        self.Bind(wx.EVT_SIZE,self.OnResize)
        
        # Status Bar
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('No File Loaded')
                
        # Options Panel
        self.optPanel = OptionsPanel(options)
        
        # Directory Dialog
        # I define this here so the path is always remembered from the last invocation
        self.directoryDialog = wx.DirDialog( None, style = wx.OPEN, message='Select Piece to Load' )
        path=options.getOption('MUSIC_DIR')
        self.directoryDialog.SetPath(path)

        
# Menu Creation        
    def MenuTitles(self):
        return ['&File','&Edit','&View','&Help']
        
    def MenuItemData(self,type=None):
        if type == '&File':
            # we don't have a twain interface on the Apple yet. So we can't create a piece. 
            # Need to just manually scan on the Apple for now. 
            if wx.Platform == '__WXMSW__':
                return [['&Create/Edit Program...',self.OnCreateProgram],
                        ['Load &Program...',self.OnLoadProgram],
                        ['&Load Piece...',self.OnLoadPiece],
                        ['Create Piece...',self.OnCreatePiece],
                        ['&Options..',self.OnOptions],
                        ['&Quit',self.OnQuit]]
            else:
                return [['&Create/Edit Program...',self.OnCreateProgram],
                        ['Load &Program...',self.OnLoadProgram],
                        ['&Load Piece...',self.OnLoadPiece],
                        ['&Options..',self.OnOptions],
                        ['&Quit',self.OnQuit]]
                
        if type == '&Edit':
            return[['&Add Annotation...',self.OnAnnotate],
                   ['&Remove Annotation...',self.OnRemoveAnn]]
        if type == '&View':
            return [['&Go to Piece...',self.OnGoToPiece]]
        if type == '&Help':
            return [['&About',self.OnAbout],
                    ['&Keyboard Shortcuts',self.OnShortcuts],
                    ['&License',self.OnLicense]]
        # No match for type, retun null list
        return []
    
    def OnShortcuts(self,event):
        res = xrc.XmlResource('shortcuts.xrc')
        pnl = res.LoadDialog(self,'ID_WXDIALOG')
        pnl.ShowModal()
        
    def OnLicense(self,event):
        frame = wx.Frame(None, -1, pos=(0,30), size=(820,680))
        LicenseFrame(frame, -1)
        frame.Show(True)


    def createMenus(self):
        self.menus = []
        # create the menu bar
        self.menubar = wx.MenuBar()
        # create each menu for the menu bar
        for t in self.MenuTitles():
            menu = wx.Menu()
            # create each item in this menu
            # each item is a list of two elements; the label and the callback routine
            for item in self.MenuItemData(t):
                lbl = item[0]
                callbk = item[1]
                menuItem = wx.MenuItem(menu,wx.ID_ANY,lbl)
                id = menuItem.GetId()
                menu.AppendItem(menuItem)
                self.Bind(wx.EVT_MENU,callbk,id = menuItem.GetId())
            self.menubar.Append(menu,t) 
        self.SetMenuBar(self.menubar)        

     
# Twain Methods
    def LogMessage(self, message):
        self.statusbar.SetStatusText(message)
    def Initialise(self):
        """
        Set up the variables used by this class
        """
        (self.SD, self.SM) = (None, None)
        self.ProductName='Virtual Page Turner'
        self.XferMethod = XferNatively
        self.AcquirePending = False
        self.mainWindow = None


    def Terminate(self):
        """
        Destroy the data source and source manager objects.
        """
        if self.SD: self.SD.destroy()
        if self.SM: self.SM.destroy()
        (self.SD, self.SM) = (None, None)

    def Acquire(self):
        """
        Begin the acquisition process. The actual acquisition will be notified by 
        either polling or a callback function.
        """
        if not self.SD:
            if not self.SourceName:
                self.OpenScanner()
            else:
                self.OpenScanner(self.SourceName)
        if not self.SD: return
        try:
            self.SD.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, 100.0) 
        except:
            pass
        cap = self.SD.GetCapability(twain.ICAP_IMAGEFILEFORMAT)
        self.SD.RequestAcquire(1, 1)  # 1,1 to show scanner user interface
        self.AcquirePending=True

    def AcquireNatively(self,fileName='tmp.bmp'):
        """
        Acquire Natively - this is a memory based transfer
        """
        self.XferMethod = XferNatively
        tmpfilename = fileName
        return self._Acquire()
        
    def OpenScanner(self, mainWindow=None, ProductName=None, UseCallback=False):
        """
        Connect to the scanner
        """
        if ProductName: self.ProductName = ProductName
        if mainWindow: self.mainWindow = mainWindow
        if not self.SM:
            self.SM = twain.SourceManager(self.mainWindow, ProductName=self.ProductName)
        if not self.SM:
            return
        if self.SD:
            self.SD.destroy()
            self.SD=None
        if self.SourceName == None:
            self.SD = self.SM.OpenSource()
        else:
            self.SD = self.SM.OpenSource(self.SourceName)
        if self.SD:
            self.LogMessage(self.ProductName+': ' + self.SD.GetSourceName())
            self.SourceName = self.SD.GetSourceName()

        if UseCallback:
            self.SM.SetCallback(self.OnTwainEvent)

# Event Handlers
    def OnGoToPiece(self,event):
        self.GoToPiece()
    def GoToPiece(self):
        pieces = pgm.GetPieceNames()
        dlg=wx.SingleChoiceDialog( None, "Go To Piece", "Pieces", pieces)
        dlg.ShowModal()
        choice = dlg.GetStringSelection()
        pgm.SetPieceByName(choice)
        self.LoadCurrentPiece()
        dlg.Destroy()
        
    def OnOpenScanner(self, event):
        
        self.OpenScanner(self.GetHandle(), ProductName="Virtual Page Turner", UseCallback=True)
        pass

    def OnAcquireNatively(self, event):
        return self.AcquireNatively()

    def OnAcquireByFile(self, event):
        return self.AcquireByFile()

    def OnCreatePiece(self,event):
        cp = CreateNewPiece()
        if cp.source == None:
            return
        if cp.source == 'Scanner':
            self.OpenScanner(self.GetHandle(), ProductName="Virtual Page Turner", UseCallback=True)
            self.pageNum = 1
            self.pageStr = '01'
            if self.directoryDialog.ShowModal() == wx.ID_OK:
                self.dirName = self.directoryDialog.GetPath()
                if wx.Platform == '__WXMSW__':
                    self.fname = self.dirName + '\\Page' + self.pageStr + self.imageSuffix
                else:
                    self.fname = self.dirName + '/Page' + self.pageStr + self.imageSuffix
                self.AcquireNatively(fileName=self.fname)
        if cp.source == 'PDF':
            dialog = wx.FileDialog(self,message='Choose PDF File',defaultFile='*.pdf')
            musicDir = options.getOption('MUSIC_DIR')
            dialog.SetPath(musicDir)
            if (dialog.ShowModal() == wx.ID_OK):
                sel=dialog.GetFilenames()
                for s in sel:
                    dir=dialog.GetDirectory()
                    msg = 'Select Destination for ' + s
                    dialog = wx.DirDialog(self,message = msg)
                    dialog.SetPath(dir)
                    if (dialog.ShowModal() == wx.ID_OK):
                        destDir = dialog.GetPath()
                        root = s.split('.')
                        root = root[0]
                        newName = root + '%02d.gif'
                        magickHome = options.getOption('MAGICK_HOME')
                        if not magickHome:
                            magickHome = os.environ.get('MAGICK_HOME')
                            if not magickHome:
                                pnl=ImageMagickPanel()
                                if pnl.imageMagickPath:
                                    options.setOption('MAGICK_HOME',pnl.imageMagickPath)
                                    options.save(optionsFile)
                                    magickHome = pnl.imageMagickPath
                                else:
                                    return
                        if wx.Platform == '__WXMSW__':
                            cmd = '""' + magickHome + '\\convert.exe" "' + dir + '\\' + s + '" "'+ destDir + '\\' + newName + '"'
                           # os.system('convert.exe  "' + dir + '\\' + s + ' "' + destDir + '\\' + newName + '"')
                           # os.system('\"%s\\%s" "%s\\%s" "%s\\%s"') % (magickHome,'convert.exe',dir,s,destDir,newName)
                        else:
                            cmd = magickHome + '/convert ' + dir + '/' + s + ' '+ destDir + '/' + newName
                        input,output,errors = os.popen3(cmd)
                        errors = errors.read()
                        if errors:
                            wx.MessageBox(errors,'error')
                            return
                        if (wx.MessageBox('PDF File Converted\nDo you want to load the file?',style=wx.YES_NO)==wx.YES):
                            piece = Piece(destDir)
                            pgm.SetCurrentPiece(piece)
                            self.UpdateStatusBar()
                            self.LoadCurrentPiece()
            
    def OnTwainEvent(self, event):
        """
        This is an event handler for the twain event. It is called 
        by the thread that set up the callback in the first place.
        It is only reliable on wxPython. Otherwise use the Polling mechanism above.
        """
        try:
            if event == twain.MSG_XFERREADY:
                self.AcquirePending = False
                self.ProcessXFer(self.fname)
                dlg = wx.MessageDialog(self,"Another Page? (Put the new page in the scanner)","Continue scanning",style=wx.YES_NO)
                rc = dlg.ShowModal()
                if (rc == wx.ID_YES):
                    self.GetNextPage()
                else:
                    self.statusbar.SetStatusText('Piece Created')  
                    self.Terminate()
            elif event == twain.MSG_CLOSEDSREQ:
                self.SD = None
                pass
        except:
            # Display information about the exception
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2])
            
    def OnOptions(self,event):
        self.SetOptions()
    def OnTimer(self,event):
        self.forwardOnePage()
        

    def OnLoadPiece(self,event):
        self.LoadPiece()     
    def OnCreateProgram(self,event):        
        def OnOK(event):
            fd = wx.FileDialog(None, "File Name for Collection", wildcard="*.txt", defaultFile="*.txt", style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
            if fd.ShowModal() == wx.ID_OK:
                fname = fd.GetPath()
                f = open(fname,"w")
                for p in dialog.listBox.GetItems():
                    f.writelines(p)
                    f.writelines("\n")
                f.close()
                dialog.Close()
                if wx.MessageBox("Do you want to load this program?",style=wx.YES_NO) == wx.YES:
                    self.LoadProgram(fname)
                    self.lastCollection = fname
                
        dialog = CreateProgram(options)
        dialog.Bind(wx.EVT_BUTTON,OnOK,dialog.okButton)
        dialog.Show()

    def OnLoadProgram(self,event):
        self.LoadProgram()
                
    def OnKeyDown(self,event):
        """
        key press handler
        """
        # handle up and down arrows
        # we need to change this to use defined constants rather than 'magic' numbers
        # something like wx.KEY_UP_ARROW but I don't know what the constants are. 
        def updateToBookmark(pos):
            self.xpos = pos[0]
            self.ypos = pos[1]
            self.LoadCurrentPiece()
            self.Refresh()
            
        if event.AltDown(): # alt keys are for menu selection
            event.Skip()
            
        k=event.KeyCode
        ck=''
        if k > 255:
            if k == 317: # up arrow
                ck='f'
            if k == 315: # down arrow
                ck='b'
            if ck == '':
                event.Skip()
        else:
            ck = chr(k)
        if ck == '\x1b': # escape key
            self.Bind(wx.EVT_LEFT_DOWN,None)
            self.UpdateStatusBar()
            return
        if ck == 'x':
            if (wx.MessageBox("Are you sure you want to quit?","Quit",style=wx.YES_NO)==wx.YES):
                self.Close(True)
                sys.exit()
            event.Skip()
        if ck == 'f' or ck == ' ': # forward one page
            if pgm.currentPiece:
                self.forwardOnePage()
            event.Skip()
        if ck == 'b': # back one page
            if pgm.currentPiece:
                self.backwardOnePage()
            event.Skip() 
        if ck == 'F': # next piece
            if self.currentPiece:
                self.currentPiece = pgm.NextPiece()
                self.LoadCurrentPiece()
                self.UpdateStatusBar()
                self.ScrollTop()
            event.Skip()
        if ck == 'G': # Go To Piece
            self.GoToPiece()
            event.Skip()
            
        if ck == 'B': # previous piece
            if self.currentPiece:
                self.currentPiece = pgm.PrevPiece()
                self.LoadCurrentPiece()
                self.UpdateStatusBar()
                self.ScrollTop()
            event.Skip()
        if ck == 'L': # load program
            self.LoadProgram()
            self.Skip()
        if ck == 'l': # load piece
            self.LoadPiece()
            event.Skip()
        if ck == 'O': # set options
            self.SetOptions()
            event.Skip()
        if ck == 'A': # add annotation
            if self.currentPiece:
                self.AddAnnotation()
            event.Skip()
        if ck == 'R':  # remove annotation
            if self.currentPiece:
                self.RemoveAnnotations()
            event.Skip()
        if ck == 'q': # speed up timer
            self.SpeedUpTimer()
            event.Skip()
        if ck == 's': # slow down timer
            self.SlowDownTimer()
            event.Skip()
        if ck == 't': # toggle timer on and off
            if self.timer.IsRunning():
                self.TurnOffTimer()
            else:
                self.TurnOnTimer()
            event.Skip()
        if ck == 'v': # toggle view mode
            self.VIEWMODE = options.getOption('VIEW_MODE')
            if self.VIEWMODE == 'Two Page':
                self.VIEWMODE = 'Fit Width'
                options.setOption('VIEW_MODE','Fit Width')
            else:
                self.VIEWMODE = 'Two Page'
                options.setOption('VIEW_MODE','Two Page')
            options.save('vptoptions.txt')
            self.LoadCurrentPiece()
            self.ypos=0
            self.Refresh(True)
                    
        if ck == '>' or ck == '.': # increase font size of annotation
            if self.annotationFont:
                pointSize = self.annotationFont.GetPointSize()
                pointSize = pointSize + 2
                self.annotationFont.SetPointSize(pointSize)
                self.Refresh(False)
                event.Skip()
        if ck == '<' or ck == ',': # decrease font size of annotation
            if self.annotationFont:
                pointSize = self.annotationFont.GetPointSize()
                pointSize = pointSize - 2
                self.annotationFont.SetPointSize(pointSize)
                self.Refresh(False)
                event.Skip()

        if ck == '0': # go to beginning of piece
            self.xpos = 0
            self.ypos = 0
            self.currentPiece.SetCurrentPage(0)
            self.LoadCurrentPiece()
            self.Refresh
        if ck == '-': # Remove all bookmarks
            self.currentPiece.RemoveAllBookmarks()
            self.SetStatusText("All Bookmarks Removed")
            event.Skip()
            
        if ck == '1':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(1)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '!':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),1)
                self.SetStatusText("Bookmark 1 Set")
            event.Skip()
        if ck == '2':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(2)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '@':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),2)
                self.SetStatusText("Bookmark 2 Set")
            event.Skip()
        if ck == '3':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(3)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '#':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),3)
                self.SetStatusText("Bookmark 3 Set")
            event.Skip()
        if ck == '4':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(4)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '$':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),4)
                self.SetStatusText("Bookmark 4 Set")
            event.Skip()
        if ck == '5':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(5)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '%':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),5)
                self.SetStatusText("Bookmark 5 Set")
            event.Skip()
        if ck == '6':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(6)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '^':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),6)
                self.SetStatusText("Bookmark 6 Set")
            event.Skip()
        if ck == '7':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(7)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '&':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),7)
                self.SetStatusText("Bookmark 7 Set")
            event.Skip()
        if ck == '8':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(1)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '*':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),8)
                self.SetStatusText("Bookmark 8 Set")
            event.Skip()
        if ck == '9':
            if self.currentPiece:
                pos = self.currentPiece.GoToBookmark(9)
                if pos:
                    updateToBookmark(pos)
            event.Skip()
        if ck == '(':
            if self.currentPage:
                pageNum = self.currentPage.GetPageNumber()
                self.currentPiece.AddBookmark(pageNum,(self.xpos,self.ypos),9)
                self.SetStatusText("Bookmark 9 Set")
            event.Skip()
            
    def OnAnnotate(self,event):
        if not self.currentPage:
            wx.MessageBox("You need to load a piece before applying annotations.","Error")
            return
        self.AddAnnotation()
        
    def OnRemoveAnn(self,event):
        self.RemoveAnnotations()
        event.Skip()
        
    def OnLeftClickForRemove(self,event):
        (x,y) = self.ClientToScreen(event.GetPositionTuple())
        (x,y) = self.Map2Screen(x,y)
        # mp=self.ScreenToClient(wx.GetMousePosition())
        if self.currentPage:
            annots = self.currentPage.GetAnnotations()
            for a in annots:
                d2 = ((x-a.x)*(x-a.x)) + ((y-a.y)*(y-a.y))
                if d2<500:
                    self.currentPage.RemoveAnnotation(a)
                    self.SaveAnnotations()
                    self.Refresh()
    
    def OnQuit(self,event):
        self.SaveStartup()
        self.Close(True)
        sys.exit()
    def OnPaint(self, event):
        self.DrawImages()
         

    def OnLeftClick(self,event):
        (x,y) = self.ClientToScreen(event.GetPositionTuple())
        (x,y) = self.Map2Screen(x,y)
        mode = options.getOption('VIEW_MODE')
        a = Annotation(x,y,self.annotationText,self.annotationFont,mode)
        self.currentPage.AddAnnotation(a)
        self.SaveAnnotations()
        self.annotationText = None
        self.annotationFont = None
        self.Bind(wx.EVT_MOTION,None)
        self.Bind(wx.EVT_LEFT_DOWN,None)
        
    def OnMouseMove(self,event):
        self.Refresh(False)
      
    def OnResize(self,event):
        self.clientSizeX , self.clientSizeY = self.GetClientSizeTuple()
        self.LoadCurrentPiece()

    def OnAbout(self,event):
        info = wx.AboutDialogInfo()
        info.Name = "About Virtual Page Turner"
        info.Version = "0.1"
        info.Copyright = "(C) 2008 Michael Toth"
        info.Description = wordwrap(
            "Virtual Page Turner is designed to assist"
            " performers who need to turn pages while"
            " both hands are busy." ,
            350,wx.ClientDC(self))
        info.WebSite = ("http://www.virtualpianist.com/vpt",
                        "Virtual Page Turner Welcome Page")
        info.Developers = [ "Michael Toth", "Monica Toth", "Helper Robot #?" ]
        f = open("GPL-license.txt")
        t = f.read()
        info.License = wordwrap(" GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007", 350, wx.ClientDC(self))
        f.close()
        wx.AboutBox(info)

# General Methods
    def LoadStartup(self):
        # get startup information
        self.lastPiece = None
        self.lastCollection = None
        fname = self.vpthome + '/startup.txt'
        if os.path.exists(fname):
            f = open(fname,'r')
            lines = f.readlines()
            f.close()
            if len(lines)>0:
                self.lastPiece=lines[0].strip('\n')
                if len(lines)>1:
                    self.lastCollection = lines[1].strip('\n')
        sp=StartPanel()
        
        if not self.lastPiece:
            sp.lastPiece.Enabled=False
        else:
            if wx.Platform == '__WXMSW__':
                sp.lastPiece.SetLabel(self.lastPiece.split('\\')[len(self.lastPiece.split('\\'))-1])
            else:
                sp.lastPiece.SetLabel(self.lastPiece.split('/')[len(self.lastPiece.split('/'))-1])
            

            
        if not self.lastCollection:
            sp.lastCollection.Enabled = False
        else:
            if wx.Platform == '__WXMSW__':
                sp.lastCollection.SetLabel(self.lastCollection.split('\\')[len(self.lastCollection.split('\\'))-1])
            else:
                sp.lastCollection.SetLabel(self.lastCollection.split('/')[len(self.lastCollection.split('/'))-1])
            
        sp.dlg.ShowModal()
        choice = sp.choice
        if choice == 'last piece':
            if self.lastPiece:
                self.LoadLastPiece(self.lastPiece)
            return
        if choice == 'last collection':
            if self.lastCollection:
                self.LoadProgram(self.lastCollection)
            return
        if choice == 'select piece':
            self.LoadPiece()
            return
        if choice == 'select collection':
            self.LoadProgram()
            return
        
                
            
    def SaveStartup(self):
        fname = self.vpthome + '/startup.txt'
        f = open(fname,'w')
        if self.lastPiece:
            if self.lastCollection:
                f.writelines([self.lastPiece,'\n',self.lastCollection,'\n'])
            else:
                f.writelines([self.lastPiece,'\n'])
        f.close()
            
    def LoadLastPiece(self,dir):
        piece = Piece(dir)
        if piece:
            pgm.SetCurrentPiece(piece)
            self.UpdateStatusBar()
            self.LoadCurrentPiece()
            
    def LoadPiece(self):
        if self.directoryDialog.ShowModal() == wx.ID_OK:
            dirName = self.directoryDialog.GetPath()
            self.lastPiece = dirName
            piece = Piece(dirName)
            if piece:
                pgm.Clear()
                pgm.SetCurrentPiece(piece)
                self.UpdateStatusBar()
                self.LoadCurrentPiece()
        return
        
    def AddAnnotation(self):
        pageName = self.currentPage.GetFileName()
        ap=AnnotationsPanel()
        self.annotationText = ap.AnnotationText
        self.annotationFont = ap.AnnotationFont
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClick)

    def RemoveAnnotations(self):
        if not self.currentPage:
            wx.MessageBox("You need to load a piece before removing annotations.","Error")
            return
        pageName = self.currentPage.GetFileName()
        self.statusbar.SetStatusText('Removing Annotations. Hit escape to quit.')
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClickForRemove)
    def ConstructAnnotationFileName(self,page):
        dir = self.currentPiece.GetName() # get the directory of the piece
        fname = page.GetFileName()
        s = fname.split('.')
        sep = '.'
        fname = sep.join([s[0],'ann'])
        if wx.Platform == '__WXMSW__':
            sep = "\\"
        else:
            sep = "/"
        path = sep.join([dir,fname])
        return(path)

    
    def Map2Image(self,x,y):
        newX = x+self.xpos
        newY = y+self.ypos
        return (newX,newY)
    
    def Map2Screen(self,x,y):
        newX = x-self.xpos
        newY = y-self.ypos
        return (newX,newY)
    
    def SetOptions(self):
        optPanel = NewOptionsPanel(options)
        if (optPanel.dlg.ShowModal()==wx.ID_OK):
            self.MUSIC_DIR = optPanel.musicDir.GetValue()
            options.setOption('MUSIC_DIR',self.MUSIC_DIR)
            self.SCROLL_AMOUNT = int(optPanel.scrollAmount.GetValue())
            options.setOption('SCROLL_AMOUNT',self.SCROLL_AMOUNT)
            if optPanel.twoPage.GetValue():
                self.VIEWMODE = 'Two Page'
            else:
                self.VIEWMODE = 'Fit Width'
            options.setOption('VIEW_MODE',self.VIEWMODE)
            self.TIMER_VALUE = float(optPanel.timerValue.GetValue())*1000.0
            options.setOption('TIMER_VALUE',self.TIMER_VALUE/1000.0)
            options.save('vptoptions.txt')
            if self.currentPiece:
                self.currentPiece.scrollAmount = self.SCROLL_AMOUNT
                self.currentPiece.timerValue = self.TIMER_VALUE/1000.0
                self.currentPiece.SaveParameters()
                self.LoadCurrentPiece()
            self.ypos=0
            self.Refresh(True)

    def TurnOnTimer(self):
        self.timer.Start(options.getOption('TIMER_VALUE')*1000)
    def TurnOffTimer(self):
        self.timer.Stop()
    def SpeedUpTimer(self):
        speed = options.getOption('TIMER_VALUE')*1000.0
        speed = speed-(0.1*speed)
        options.setOption('TIMER_VALUE',speed/1000.0)
        if self.timer.IsRunning():
            self.timer.Start(speed)
        
    def SlowDownTimer(self):
        speed = options.getOption('TIMER_VALUE')*1000.0
        speed = speed + (0.1*speed)
        options.setOption('TIMER_VALUE',speed/1000.0)
        self.timer.Start(speed)
        
    def LoadCurrentPiece(self):
        self.currentPiece = pgm.GetCurrentPiece()
        if self.currentPiece:
            self.pieceName = self.currentPiece.GetName()
            self.currentPage = self.currentPiece.GetCurrentPage()
            timerValue = self.currentPiece.timerValue
            options.setOption('TIMER_VALUE',timerValue)
            scrollAmount = self.currentPiece.scrollAmount
            options.setOption('SCROLL_AMOUNT',scrollAmount)
            if self.currentPage:
                pageName = self.currentPage.GetFileName()
                self.Bind(wx.EVT_PAINT, self.OnPaint)
                fileName = ''.join([self.pieceName,'/',pageName])
                self.image1 = wx.Image(fileName)
                self.GetAnnotations()
                self.nextPage = self.currentPiece.GetNextPage()
                if self.nextPage != None:
                    pageName = self.nextPage.GetFileName()
                    fileName = ''.join([self.pieceName,'/',pageName])
                    self.image2 = wx.Image(fileName)
                else:
                    self.image2 = self.image1
                self.SetImages(self.image1, self.image2)
                self.Refresh(True)
            else:
                self.image1 = wx.Image('Welcome.gif')
                self.image2 = wx.Image('Welcome.gif')                    


    
# Image Manipulation   
    def LoadProgram(self,fname=None):
        if fname == None:
            dialog = wx.FileDialog( None, style = wx.OPEN )
            dialog.SetDirectory(options.getOption('MUSIC_DIR'))
            if dialog.ShowModal() == wx.ID_OK:
                fname = dialog.GetPath()
                self.lastCollection = fname
            else:
                return
        pgm.SetName(fname)
        self.LoadCurrentPiece()
        

    def PageType(self,name):
        return name.split('.')[1]
    
        
    

    
    def scaleImage(self,image):
        iSizeX = image.GetWidth()
        iSizeY = image.GetHeight()
        if self.VIEWMODE == "Fit Width":
            wfac = float(self.clientSizeX)/float(iSizeX)
            image.Rescale(wfac*iSizeX,wfac*iSizeY)
        if self.VIEWMODE == "Two Page":
            wfacx = float(self.clientSizeX)/float(iSizeX)/2
            wfacy = float(self.clientSizeY)/float(iSizeY)
            image.Rescale(wfacx*iSizeX,wfacy*iSizeY)
        return image
    
    def SetImages(self, image1=None, image2=None):
        """
        sets the images in the frame. 
        rescales according to view mode
        """
        
        if image1 != None:
            img1 = self.scaleImage(image1)
            img2 = self.scaleImage(image2)
            self.ConvertImages(img1, img2)
            
    def DrawImages(self):
        self.currentPiece = pgm.GetCurrentPiece()
        if self.currentPiece:
            self.pieceName = self.currentPiece.GetName()
            self.currentPage = self.currentPiece.GetCurrentPage()
            if self.currentPage:
                pageName = self.currentPage.GetFileName()
        dc = wx.BufferedPaintDC(self)
        # viewMode = options.getOption('VIEW_MODE')
        if self.VIEWMODE == "Fit Width":
            dc.DrawBitmap(self.page1,self.xpos,self.ypos,True)
            h = self.page1.GetHeight()
            dc.DrawBitmap(self.page2,self.xpos,self.ypos+h,True)
        if self.VIEWMODE == "Two Page":
            dc.DrawBitmap(self.page1,self.xpos, self.ypos, True)
            w = self.page1.GetWidth()
            dc.DrawBitmap(self.page2, self.xpos+w, self.ypos, True)
        if self.currentPage:
            annots = self.currentPage.GetAnnotations()
            # write the annotations for this page
            if len(annots) > 0:
                for a in annots:
                    if a.GetMode() == self.VIEWMODE:
                        (x,y)=a.GetPosition()
                        (x,y)=self.Map2Image(x,y)
                        (x,y)=self.ScreenToClient((x,y))
                        t = a.GetText()
                        f = a.GetFont()
                        dc.SetFont(f)
                        dc.SetTextForeground(wx.RED)
                        dc.DrawText(t,x,y)
        if self.nextPage and self.VIEWMODE == "Two Page":
            annots = self.nextPage.GetAnnotations()
            # write the annotations for second page
            if len(annots) > 0:
                for a in annots:
                    if a.GetMode() == self.VIEWMODE:
                        (x,y)=a.GetPosition()
                        (x,y)=self.Map2Image(x,y)
                        (x,y)=self.ScreenToClient((x,y))
                        t = a.GetText()
                        f = a.GetFont()
                        dc.SetFont(f)
                        dc.SetTextForeground(wx.RED)
                        dc.DrawText(t,x+w,y)
            # write the current annotation if we are placeing one now
        if self.annotationText:
            mp=self.ScreenToClient(wx.GetMousePosition())
            dc.SetFont(self.annotationFont)
            wx.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            dc.SetTextForeground(wx.RED)
            dc.DrawText(self.annotationText,mp.x,mp.y)
        else:
            wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        return
        
    def ConvertImages(self, img1, img2):
        self.page1 = img1.ConvertToBitmap()
        self.page2 = img2.ConvertToBitmap()
        
    def Page1Visible(self):
        """ returns True if Page 1 is visible, False otherwise """
        if (self.ypos + self.page1.GetHeight() > 0) and (self.ypos <  self.clientSizeY):
            return True
        else:
            return False
        
    def Page2Visible(self):
        """ returns True if Page 2 is visible.  False otherwise 
            only meaningful when VIEWMODE is 'Fit Width' 
        """
        if (self.ypos + self.page1.GetHeight() + self.page2.GetHeight() > 0) and (self.ypos + self.page1.GetHeight() < self.clientSizeY):
            return True
        else:
            return False
            
    def UpdateStatusBar(self):
        if pgm == None:
            pgmName = "None"
        else:
            pgmName = pgm.GetName()
            if pgmName == None:
                pgmName = "None"
                
        piece = pgm.GetCurrentPiece()
        if piece == None:
            pieceName = "None"
        else:
            pieceName = piece.GetName()
            if pieceName == None:
                pieceName = "None"
        self.statusbar.SetStatusText(''.join(["Program: ", pgmName, "    Piece:  ", pieceName]))
        
# Navigation
    def GetNextPage(self):
        self.pageNum = self.pageNum + 1
        if (self.pageNum<10):
            self.pageStr = '0'+str(self.pageNum)
        else:
            self.pageStr = str(self.pageNum)
        if wx.Platform == '__WXMSW__':
            self.fname = self.dirName + '\\Page' + self.pageStr + self.imageSuffix
        else:
            self.fname = self.dirName + '/Page' + self.pageStr + self.imageSuffix
        self.AcquireNatively(fileName=self.fname)
     
    def forwardOnePage(self):
        if options.getOption('VIEW_MODE') == "Fit Width":
            self.ScrollUp()
            if self.Page1Visible():
                self.Refresh(eraseBackground=False)
                return
            else:
                self.image1=self.image2
                if pgm.currentPiece.TurnForward() == True:
                    self.ypos = self.ypos + self.page1.GetHeight()
                    self.prevPage = self.currentPiece.GetPreviousPage()
                    self.currentPage = self.currentPiece.GetCurrentPage()
                    self.nextPage = self.currentPiece.GetNextPage()
                    if self.nextPage:
                        pageName = self.nextPage.GetFileName()
                        fileName = ''.join([self.pieceName,'/',pageName])
                        self.image2 = wx.Image(fileName)
                    else:
                        self.image2 = self.image1
                else:
                    self.image2 = self.image1                    
                self.SetImages(self.image1, self.image2)
                self.Refresh(eraseBackground=False)
                self.UpdateStatusBar()
            return
        if self.VIEWMODE == "Two Page":
            if pgm.currentPiece:
                if pgm.currentPiece.TurnForward() == True:
                    self.LoadCurrentPiece()
                    self.UpdateStatusBar()
            return
    def backwardOnePage(self):
        if self.VIEWMODE == "Fit Width":
            self.ScrollDown()
            if self.Page2Visible():
                self.Refresh(eraseBackground=False)
                return
            else:
                if pgm.currentPiece:
                    if pgm.currentPiece.TurnBackward() == True:
                        self.nextPage = self.currentPiece.GetNextPage()
                        self.currentPage = self.currentPiece.GetCurrentPage()
                        self.prevPage = self.currentPiece.GetPreviousPage()
                        if self.currentPage:
                            pageName = self.currentPage.GetFileName()
                            fileName = ''.join([self.pieceName,'/',pageName])
                            self.image1 = wx.Image(fileName)
                            img1 = self.scaleImage(self.image1)
                            self.ypos = self.ypos - img1.GetHeight()
                        if self.nextPage:
                            pageName = self.nextPage.GetFileName()
                            fileName = ''.join([self.pieceName,'/',pageName])
                            self.image2 = wx.Image(fileName)
                        else:
                            self.image1 = self.image2
                    else:
                        pageName = self.currentPage.GetFileName()
                        fileName = ''.join([self.pieceName,'/',pageName])
                        self.image1 = wx.Image(fileName)
                    self.SetImages(self.image1, self.image2)
                    self.Refresh(False)
                    self.UpdateStatusBar()
            return
        if options.getOption('VIEW_MODE') == 'Two Page':
            if pgm.currentPiece:
                if pgm.currentPiece.TurnBackward() == True:
                    self.LoadCurrentPiece()
                    self.UpdateStatusBar()
            return
                        
    def ScrollTop(self):
        self.ypos = 0
        self.Refresh(eraseBackground=False)
        
    def ScrollDown(self):
        self.ypos = self.ypos + self.SCROLL_AMOUNT
        return self.ypos + self.page1.GetHeight()
            
    def ScrollUp(self):
        self.ypos = self.ypos - self.SCROLL_AMOUNT
        return self.ypos + self.page1.GetHeight()

# Annotation
    def LoadAnnotations(self,page,path):
        if os.path.exists(path):
            fptr = open(path,'r')
            aFile = fptr.readlines() # get the file
            fptr.close()
            sFile = []
            for line in aFile:
                line = line.strip('\n')
                line = line.strip('\r')
                sFile.append(line)
            page.ClearAnnotations()
            if len(aFile)>0:
                nAnnotations = int(sFile[0]) # number of annotations
                idx = 1
                for aNum in range(0,nAnnotations):
                    x = int(sFile[idx])
                    y = int(sFile[idx+1])
                    txt = sFile[idx+2]
                    txt = txt.strip('\n')
                    pointSize = int(sFile[idx+3])
                    family = int(sFile[idx+4])
                    style = int(sFile[idx+5])
                    weight = int(sFile[idx+6])
                    encoding = int(sFile[idx+7])
                    faceName = sFile[idx+8]
                    faceName = faceName.strip('\n')
                    font = wx.Font(pointSize=pointSize,family=family,
                                   style=style,weight=weight,encoding=encoding)
                    font.SetFaceName(faceName)
                    mode = sFile[idx+9]
                    mode = mode.strip('\n')
                    a = Annotation(x,y,txt,font,mode)
                    page.AddAnnotation(a)
                    idx=idx+10 
        
    def GetAnnotations(self):
        page = self.currentPiece.GetCurrentPage()
        if page:
            path = self.ConstructAnnotationFileName(page)
            if path:
                self.LoadAnnotations(page,path)
        page = self.currentPiece.GetNextPage()
        if page:
            path = self.ConstructAnnotationFileName(page)
            if path:
                self.LoadAnnotations(page,path)
        
    def SaveAnnotations(self):
        path = self.ConstructAnnotationFileName(self.currentPage)
        fptr = open(path,'w')
        annots = self.currentPage.GetAnnotations()
        if len(annots) > 0:
            fptr.writelines([str(len(annots)),'\n'])
            for a in annots:
                (x,y)=a.GetPosition()
                txt = a.GetText()
                txt = txt.strip('\n')
                font = a.GetFont()
                pointSize = font.GetPointSize()
                family = font.GetFamily()
                style = font.GetStyle()
                weight = font.GetWeight()
                encoding = font.GetEncoding()
                faceName = font.GetFaceName()
                mode = a.GetMode()
                for line in [str(int(x)),'\n',str(int(y)),'\n',txt,'\n',
                             str(pointSize),'\n',str(family),'\n',
                             str(style),'\n',str(weight),'\n',str(encoding),'\n',faceName,'\n',mode,'\n']:
                    fptr.writelines(line)
        fptr.close()
    

    def drawRectangle(self,pos,size):
        """ Draws a rectangle at the position, 'pos', and size, 'size' """
        dc = wx.BufferedPaintDC(self)
        lo = dc.LogicalOrigin
        if self.oldPos == -1:
            self.oldPos = pos
            self.oldSize = size
        else:
            dc.SetPen(wx.Pen((0,0,0),style=wx.INVERT))
            dc.SetBrush(wx.Brush((0,0,0),style=wx.INVERT))
            dc.DrawRectangle(self.oldPos.x,self.oldPos.y,size.x,size.y)
        self.oldPos = pos
        self.oldSize = size
        rect = wx.Rect(pos.x,pos.y,size.x,size.y)
        dc.SetBrush(wx.Brush((0,0,0),style=wx.TRANSPARENT))
        dc.DrawRectangle(pos.x,pos.y,size.x,size.y)
               
def main():
    app = wx.PySimpleApp()
    frame = vptFrame()
    frame.Show(True)
    frame.LoadStartup()
    app.MainLoop()    

if __name__ == '__main__':
    main()
