
# Copyright 2008 Michael Toth

import wx
import os
import wx.html
from wx.lib.wordwrap import wordwrap
import  wx.xrc  as  xrc

class LicenseFrame(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.html1 = wx.html.HtmlWindow(self, id, pos=(0,30), size=(800,600))
        self.html1.LoadPage('gpl-3.0-standalone.htm')

class ChooseFileType(wx.Dialog):
    def __init__(self,suffixList):
        wx.Dialog.__init__(self, None, -1, "Choose File Type")
        self.fileTypeChoice = None
        self.res = xrc.XmlResource('fileType.xrc')
        self.res.LoadDialog(self,'ID_WXDIALOG')
        self.dlg=xrc.XRCCTRL(self,'ID_WXDIALOG')
        self.radio = xrc.XRCCTRL(self.dlg,'FileType')
        for i in range(0,6):
            str=self.radio.GetString(i)
            str='.'+str.lower()
            if suffixList.__contains__(str):
                self.radio.EnableItem(i,True)
            else:
                self.radio.EnableItem(i,False)

        
        
            
        

        
class CreateNewPiece(wx.Dialog):
    """
    panel to create a new piece, presents a choice of from a pdf file or from a scanner. 
    """
    def __init__(self):
        wx.Dialog.__init__(self,None,-1)
        self.source = None
        self.res = xrc.XmlResource('newPiece.xrc')
        self.res.LoadDialog(self,'ID_WXDIALOG')
        self.dlg = xrc.XRCCTRL(self,'ID_WXDIALOG')
        if (self.dlg.ShowModal()==wx.ID_OK):
            ctrl = xrc.XRCCTRL(self.dlg,'ID_RADIOBUTTON1') # the Scanner Radio Button
            if ctrl.GetValue(): # pdf file
                self.source = 'PDF'
            else:
                self.source = 'Scanner'

class ImageMagickPanel(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self,None,-1)
        self.imageMagickPath = None
        self.res = xrc.XmlResource('imageMagick.xrc')
        self.res.LoadDialog(self,'ID_WXDIALOG')
        self.dlg = xrc.XRCCTRL(self,'ID_WXDIALOG')
        if (self.dlg.ShowModal() == wx.ID_OK):
            ctrl = xrc.XRCCTRL(self.dlg, 'HasImageMagick')
            if ctrl.GetValue():
                self.Fix1()
            ctrl = xrc.XRCCTRL(self.dlg,'NoImageMagick')
            if ctrl.GetValue():
                self.Fix2()
            ctrl = xrc.XRCCTRL(self.dlg,'ForgetIt')
            if ctrl.GetValue():
                return
    def Fix1(self):
        dlg=wx.DirDialog(self,message='Select ImageMagick Directory')
        if (dlg.ShowModal()==wx.ID_OK):
            self.imageMagickPath=dlg.GetPath()
    def Fix2(self):
        self.html1 = wx.html.HtmlWindow(self, id, pos=(0,30), size=(800,600))
        self.html1.LoadPage('http://www.imagemagick.org/script/binary-releases.php')
        wx.MessageBox('Click OK after you have installed ImageMagick')
        dlg=wx.DirDialog(self,message='Select ImageMagick Directory')
        if (dlg.ShowModal()==wx.ID_OK):
            self.imageMagickPath=dlg.GetPath()


            
    
class AnnotationsPanel(wx.Dialog):
    """
    panel to draw annotations using DialogBlocks and xrc resource file
    """
    def __init__(self):
        self.AnnotationText = None
        self.AnnotationFont = None
        self.accFont = wx.Font(pointSize=20,family=74,
                               style=90,weight=90,underline=False,encoding=33)
        self.accFont.SetFaceName('Accidentals')
        self.txtFont = wx.Font(pointSize=12,
                               family=wx.FONTFAMILY_DEFAULT,
                               style=wx.FONTSTYLE_NORMAL,
                               weight=wx.FONTWEIGHT_NORMAL, 
                               encoding=wx.FONTENCODING_DEFAULT)
        wx.Dialog.__init__(self, None, -1)
        self.res = xrc.XmlResource('annotations.xrc')
        self.res.LoadDialog(self,"AnnotationDialogBox")
        self.dlg=xrc.XRCCTRL(self,'AnnotationDialogBox')
        self.dlg.Bind(wx.EVT_BUTTON, self.OnSharp, id=xrc.XRCID('Sharp'))
        self.dlg.Bind(wx.EVT_BUTTON, self.OnFlat, id=xrc.XRCID('Flat'))
        self.dlg.Bind(wx.EVT_BUTTON, self.OnNatural, id=xrc.XRCID('Natural'))
        if (self.dlg.ShowModal()==wx.ID_OK):
            ctrl = xrc.XRCCTRL(self.dlg,'Text2Add')
            txt = ctrl.GetValue()
            if txt!='':
                self.AnnotationText = txt
                self.AnnotationFont = self.txtFont
            else:
                self.AnnotationText = None
                self.AnnotationFont = None
        self.dlg.Close()
        
    def OnSharp(self,event):
        self.AnnotationFont = self.accFont
        self.AnnotationText = 's'
        self.dlg.Close()
            
    def OnFlat(self,event):
        self.AnnotationFont = self.accFont
        self.AnnotationText = 'b'
        self.dlg.Close()
            
    def OnNatural(self,event):
        self.AnnotationFont = self.accFont
        self.AnnotationText = 'n'
        self.dlg.Close()
            
        
class OldAnnotationsPanel(wx.Dialog):
    """ 
    panel to draw annotations 
    
    """
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, "Annotate Page", size = (500,300))
        self.returnText = None
        panel = wx.Panel(self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        textSizer = wx.FlexGridSizer(cols=2,rows=2,hgap=5,vgap=5)
        textSizer.AddGrowableCol(1)
        self.textLbl = wx.StaticText(panel,-1, "Enter Text: ")
        self.Text2Add = wx.TextCtrl(panel, -1, size=(200,25))
        textSizer.Add(self.textLbl,wx.EXPAND)
        textSizer.Add(self.Text2Add,wx.EXPAND)
        
        accSizer = wx.FlexGridSizer(cols=3,rows=1,hgap=5,vgap=5)
        accFont = wx.Font(pointSize=20,family=74,style=90,weight=90,underline=False,encoding=33)
        accFont.SetFaceName('Accidentals')
        sharpButton = wx.Button(panel,wx.ID_OK,"s")
        sharpButton.SetFont(accFont)
        sharpButton.SetSize(wx.Size(w=30,h=50))
        # sharpButton.Bind(wx.EVT_BUTTON,self.OnSharp)
        
        flatButton = wx.Button(panel,wx.ID_ANY,'b')
        flatButton.SetFont(accFont)
        flatButton.SetSize(wx.Size(w=30,h=50))
        
        naturalButton = wx.Button(panel,wx.ID_ANY,'n')
        naturalButton.SetFont(accFont)
        naturalButton.SetSize(wx.Size(w=30,h=50))
        
        accSizer.Add(sharpButton,0,wx.LEFT| wx.EXPAND)
        accSizer.Add(flatButton,0,wx.CENTER|wx.EXPAND)
        accSizer.Add(naturalButton,0,wx.RIGHT|wx.EXPAND)
        
        okButton = wx.Button(panel,wx.ID_OK,"OK")
        cancelButton = wx.Button(panel,wx.ID_CANCEL,"Cancel")
        
        buttonSizer = wx.BoxSizer()
        buttonSizer.Add((10,10),2)
        buttonSizer.Add(cancelButton,0,wx.RIGHT,10)
        buttonSizer.Add((10,10),0)
        buttonSizer.Add(okButton,0,wx.RIGHT,10)
        buttonSizer.Add((10,10),0)  
        
        sizer.Add(textSizer,0,wx.EXPAND|wx.ALL,10)
        sizer.Add(accSizer,0,wx.EXPAND|wx.ALL,10)
        sizer.Add(buttonSizer,0,wx.BOTTOM|wx.RIGHT,10)
        
        panel.SetSizer(sizer)
        sizer.Fit(self)
        sizer.SetSizeHints(self)
        
    def OnSharp(self,event):
        self.returnText = '_sharp'
        self.ReturnCode=wx.ID_OK
        
    
        

class Options():
    """
    Options currently are saved in a file called vptoptions.txt which is located in the vpt folder (found by calling os.getcwd())
    I am looking for a better way to save and retrieve options in a python program.
    If anyone has advice on this I'd appreciate hearing it. 
    """
    def __init__(self,fileName=None):
        self.options = []
        if fileName:
            self.load(fileName)
        
    def save(self,fileName):
        """ Saves the options into the option file, fileName """
        if self.options != []:
            fptr = open(fileName,'w')
            for opt in self.options:
                fptr.write(str(opt))
                fptr.write('\n')
            fptr.close()
        
    def load(self,fileName):
        """ Loads the options from the option file, fileName. """
        fptr = open(fileName,'r')
        lines = fptr.readlines()
        self.options=[]
        for line in lines:
            # deal with line termination
            i=len(line)-1
            while line[i]!=']':
                line=line[0:i]
                i=i-1
            self.options.append(eval(line))
        fptr.close()
        
    def addOption(self,optionName,optionValue):
        for opt in self.options:
            if opt[0]==optionName:
                wx.MessageBox("Option, "+optionName+", already exists")
                return
        self.options.append([optionName,optionValue])
                
    def getOption(self,optionName):
        """ Returns the option associated with optionName.  Returns null string if not a valid option. """
        for opt in self.options:
            if opt[0]==optionName:
                return opt[1]
        return ''
    
    def setOption(self,optionName,optionValue):
        """ Sets the option, optiontName, to the value, optionValue. Does nothing if not a valid option. """ 
        for opt in self.options:
            if opt[0]==optionName:
                opt[1]=optionValue
                
                

        
class StartPanel(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self,None,-1)
        self.choice = None
        self.res = xrc.XmlResource('startPanel.xrc')
        self.res.LoadDialog(self,'ID_START_PANEL')
        self.dlg = xrc.XRCCTRL(self,'ID_START_PANEL')
        self.lastPiece = xrc.XRCCTRL(self,'ID_LAST_PIECE')
        self.lastCollection = xrc.XRCCTRL(self,'ID_LAST_COLLECTION')
        self.selPiece = xrc.XRCCTRL(self,'ID_SELECT_PIECE')
        self.selCollection = xrc.XRCCTRL(self,'ID_SELECT_COLLECTION')
        self.dlg.Bind(wx.EVT_BUTTON,self.OnLastPiece,id=xrc.XRCID('ID_LAST_PIECE'))
        self.dlg.Bind(wx.EVT_BUTTON,self.OnLastCollection,id=xrc.XRCID('ID_LAST_COLLECTION'))
        self.dlg.Bind(wx.EVT_BUTTON,self.OnSelPiece,id=xrc.XRCID('ID_SELECT_PIECE'))
        self.dlg.Bind(wx.EVT_BUTTON,self.OnSelCollection,id=xrc.XRCID('ID_SELECT_COLLECTION'))      
        
    def OnLastPiece(self,event):
        self.choice = 'last piece'
        self.dlg.Destroy()
        
    def OnLastCollection(self,event):
        self.choice = 'last collection'
        self.dlg.Destroy()
        
    def OnSelPiece(self,event):
        self.choice = 'select piece'
        self.dlg.Destroy()
        
    def OnSelCollection(self,event):
        self.choice = 'select collection'
        self.dlg.Destroy()
        
        
            
            
            
        
        
class OptionsPanel(wx.Dialog):
    """ panel to set program options """
    def __init__(self,options):
        wx.Dialog.__init__(self, None, -1, "Options")
        panel = wx.Panel(self)
        sizer=wx.BoxSizer(wx.VERTICAL)
        optionSizer = wx.FlexGridSizer(cols=2, rows=2, hgap=5, vgap=5)
        optionSizer.AddGrowableCol(1)
        
        viewLbl = wx.StaticText(panel, -1, "View Mode:")
        self.viewChoices = wx.RadioBox(panel, -1,"", (10,10), wx.DefaultSize, ["Fit Width","Two Page"])
        if options.getOption('VIEW_MODE')=='Fit Width':
            self.viewChoices.SetSelection(0)
        else:
            self.viewChoices.SetSelection(1)
        scrollLbl = wx.StaticText(panel, -1, "Scroll Amount:" )
        self.scrollAmount = wx.TextCtrl(panel,-1,value = str(options.getOption('SCROLL_AMOUNT')))
        musicDirLbl = wx.StaticText(panel, -1, "Music Directory:")
        self.musicDirValue = wx.TextCtrl(panel, -1, value = options.getOption('MUSIC_DIR'), size = (300,25))
        
        optionSizer.Add(viewLbl,wx.EXPAND)
        optionSizer.Add(self.viewChoices,wx.EXPAND)
        optionSizer.Add(scrollLbl,wx.EXPAND)
        optionSizer.Add(self.scrollAmount,wx.EXPAND)
        optionSizer.Add(musicDirLbl,wx.EXPAND)
        optionSizer.Add(self.musicDirValue,wx.EXPAND)
        
        
        okButton = wx.Button(panel,wx.ID_OK,"OK")
        cancelButton=wx.Button(panel,-1,"Cancel")
        buttonSizer=wx.BoxSizer()
        buttonSizer.Add((10,10),2)
        buttonSizer.Add(cancelButton,0,wx.RIGHT,10)
        buttonSizer.Add((10,10),0)
        buttonSizer.Add(okButton,0,wx.RIGHT,10)
        buttonSizer.Add((10,10),0)  
        
        sizer.Add(optionSizer,0,wx.EXPAND|wx.ALL,10)
        sizer.Add(buttonSizer,0,wx.BOTTOM|wx.RIGHT,10)
        panel.SetSizer(sizer)
        
        self.Bind(wx.EVT_BUTTON,self.OnCancel,cancelButton)
        sizer.Fit(self)
        sizer.SetSizeHints(self)
                       
    def OnCancel(self,event):
        self.Close()
        
        
        
class NewOptionsPanel(wx.Dialog):
    def __init__(self,options):
        wx.Dialog.__init__(self,None,-1)
        self.res = xrc.XmlResource('options.xrc')
        self.res.LoadDialog(self,'OptionsDialogBox')
        self.dlg=xrc.XRCCTRL(self,'OptionsDialogBox')
        self.musicDir = xrc.XRCCTRL(self.dlg,'MusicDirectory')
        self.twoPage = xrc.XRCCTRL(self.dlg,'TwoPage')
        self.fitWidth = xrc.XRCCTRL(self.dlg,'FitWidth')
        self.scrollAmount = xrc.XRCCTRL(self.dlg,'ScrollAmount')
        self.timerValue = xrc.XRCCTRL(self.dlg,'TimerValue')
        self.musicDir.SetValue(options.getOption('MUSIC_DIR'))
        if options.getOption('VIEW_MODE')=='Two Page':
            self.twoPage.SetValue(True)
            self.fitWidth.SetValue(False)
        else:
            self.twoPage.SetValue(False)
            self.fitWidth.SetValue(True)
        self.scrollAmount.SetValue(str(options.getOption('SCROLL_AMOUNT')))
        self.timerValue.SetValue(str(options.getOption('TIMER_VALUE')))
        
class CreateProgram(wx.Frame):
    """ panel to create a program file """
    def __init__(self,options):
        wx.Frame.__init__(self, None, -1, "Create/Edit Program", size = (500,300))
        
        self.nItems = 0
        self.pieceList = []
        self.musicDir = options.getOption('MUSIC_DIR')
        
        panel = wx.Panel(self, -1)
        self.listBox = wx.ListBox(panel, -1, (20,20), (500,300))

        self.okButton = wx.Button(panel, -1, "OK")
        cancelButton = wx.Button(panel, -1, "Cancel")
        selectButton = wx.Button(panel, -1, "Select Program")
        addButton = wx.Button(panel, -1, "Add Piece")
        removeButton = wx.Button(panel, -1, "Remove Piece")
        moveUpButton = wx.Button(panel, -1, "Move Up")
        moveDownButton = wx.Button(panel, -1, "Move Down")
        
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addButton)
        self.Bind(wx.EVT_BUTTON, self.OnSelect, selectButton)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, removeButton)
        self.Bind(wx.EVT_BUTTON, self.OnMoveUp, moveUpButton)
        self.Bind(wx.EVT_BUTTON, self.OnMoveDown, moveDownButton)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancelButton)
        #self.Bind(wx.EVT_BUTTON, self.OnOK, okButton)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        listSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer = wx.GridSizer(rows=1, cols=4, hgap=5,vgap=5)
        okSizer = wx.GridSizer(rows=1,cols=4,hgap=5,vgap=5)
        
        listSizer.Add(self.listBox)
        buttonSizer.Add(moveUpButton)
        buttonSizer.Add(moveDownButton)
        buttonSizer.Add(addButton)
        buttonSizer.Add(removeButton)
        okSizer.Add(selectButton)
        okSizer.Add((20,20),1)
        okSizer.Add(cancelButton)
        okSizer.Add(self.okButton)
        
        panel.SetSizer(mainSizer,20)
        
        mainSizer.Add(listSizer,0)
        mainSizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add(okSizer,0,wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT,10)
        
        okSizer.Fit(self)
        buttonSizer.Fit(self)
        listSizer.Fit(self)
        mainSizer.Fit(self)
        mainSizer.SetSizeHints(self)
        
        self.dirDialog = wx.DirDialog(self,message='Select Piece to Add')
        self.dirDialog.SetPath(self.musicDir)
        
    def OnSelect(self, event):
        fd = wx.FileDialog(self,message='Select Program File')
        if fd.ShowModal() == wx.ID_OK:
            self.nItems = 0
            path = fd.GetPath()
            f = open(path,'r')
            line = f.readline()
            while line != "": 
                line = line[0:len(line)-1] # remove \n
                self.pieceList.append(line)
                self.nItems = self.nItems + 1
                line = f.readline() 
            self.listBox.SetItems(self.pieceList)
            f.close()
        
    def OnAdd(self, event):
        global options
        if self.dirDialog.ShowModal() == wx.ID_OK:
            self.pieceList.append(self.dirDialog.GetPath())
            self.nItems = self.nItems + 1
            path = self.dirDialog.GetPath()
            self.listBox.InsertItems([path],self.nItems-1)
            
    def OnRemove(self, event):
        if self.nItems == 0:
            return
        itemNumber = self.listBox.GetSelection()
        if itemNumber < 0:
            return
        self.nItems = self.nItems-1
        self.listBox.Delete(itemNumber)
        
    def OnMoveUp(self, event):
        if self.nItems == 0:
            return
        itemNumber = self.listBox.GetSelection()
        if itemNumber < 0:
            return
        if itemNumber == 0:
            return
        selectedItem = self.listBox.GetStringSelection()
        self.listBox.Delete(itemNumber)
        self.listBox.InsertItems([selectedItem],itemNumber-1)
        self.listBox.SetSelection(itemNumber-1)
        
    def OnMoveDown(self, event):
        if self.nItems == 0:
            return
        itemNumber = self.listBox.GetSelection()
        if itemNumber < 0:
            return
        if itemNumber == self.nItems-1:
            return
        selectedItem = self.listBox.GetStringSelection()
        self.listBox.Delete(itemNumber)
        self.listBox.InsertItems([selectedItem],itemNumber+1)
        self.listBox.SetSelection(itemNumber+1)
        
    def OnCancel(self, event):
        self.Close()
        
    def OnOK(self, event):
        fd = wx.FileDialog(None, "File Name for Program", wildcard="*.txt", defaultFile="*.txt", style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if fd.ShowModal() == wx.ID_OK:
            self.fname = fd.GetPath()
            f = open(self.fname,"w")
            for p in self.listBox.GetItems():
                f.writelines(p)
                f.writelines("\n")
            f.close()
            self.Close()
            
        
class AboutPanel(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,-1,'About Virtual Page Turner',size=(400,300))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.textSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.textLbl = wx.StaticText(panel,-1,"Virtual Page Turner\ncopyright 2008\nMichael Toth")
        self.textSizer.Add(self.textLbl)
        okButton = wx.Button(panel,wx.ID_OK,"OK")
        splash = wx.Image("aboutimg.gif",wx.BITMAP_TYPE_GIF)
        bmap = splash.ConvertToBitmap()
        sizer.Add(self.textSizer,0,wx.EXPAND|wx.ALL,10)
        sizer.Add(bmap,0,wx.EXPAND|wx.ALL,10,size=(200,200))
        sizer.Add(okButton,0,wx.EXPAND|wx.ALL,10)
        panel.SetSizer(sizer)
        sizer.Fit(self)
        sizer.SetSizeHins(self)
    
class InitPanel(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self,None,-1)
        self.res = xrc.XmlResource('initOptions.xrc')
        self.res.LoadDialog(self,'ID_WXDIALOG')
        self.dlg = xrc.XRCCTRL(self,'ID_WXDIALOG')
        self.musicDir = xrc.XRCCTRL(self,'ID_DIRPICKERCTRL1')
        self.viewMode = xrc.XRCCTRL(self,'ID_RADIOBOX1')
        self.scrollAmount = xrc.XRCCTRL(self,'ID_TEXTCTRL1')
        self.timerValue = xrc.XRCCTRL(self,'ID_TEXTCTRL2')
    
    
    