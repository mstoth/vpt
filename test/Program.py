#!/usr/bin/env python
# Copyright 2008 Michael Toth

import wx
import os
import re
from panels import *

class Annotation:
    """
    Annotation object to hold x,y coordinates, text, and font.
    Arguments are x,y,txt, and font
    Methods are:
       GetText() - gets the text of the annotation
       GetFont() - returns the font
       GetPosition() - returns the (x,y) tuple
       SetText(txt) - sets the text to the string passed in
       SetFont(font) - sets the font
       SetPosition((x,y)) - sets the position 
    """
    def __init__(self,x=None,y=None,txt=None,font=None,mode=None):
        self.x = x
        self.y = y
        self.txt = txt
        self.font = font
        self.mode = mode
    
    def SetMode(self,mode):
        self.mode = mode
    
    def GetMode(self):
        return self.mode
    
    def GetText(self):
        return(self.txt)
    
    def GetFont(self):
        return(self.font)
    
    def GetPosition(self):
        return((int(self.x),int(self.y)))
    
    def SetText(self,txt):
        self.txt = txt
        
    def SetFont(self,font):
        self.font = font
        
    def SetPosition(self,pos):
        self.x = pos.x
        self.y = pos.y

        
class Program:
    """ Program Definition 
        Methods: 
            GetPieces - Given a file name, reads in each line of the file and creates one piece (object) per line
    """
    def __init__(self, fileName=None):
        self.fileName=fileName
        self.pieces=[]
        self.nPieces = 0
        self.currentPiece = None
        if fileName != None:
            self.GetPieces(fileName)

    def GetPieces(self,fileName):
        self.pieces=[]
        self.nPieces = 0
        self.currentPiece = None
        if self.fileName == None:
            return False
        else: 
            f = open(fileName,'r')
            lines = f.readlines()
            f.close()
            for dirName in lines:
                dirName = dirName[0:len(dirName)-1] # remove \n
                if not os.path.exists(dirName):
                    msg=''.join(["File ",dirName," does not exist... Aborting"])
                    wx.MessageBox(msg,'Getting Pieces')
                    self.nPieces = 0
                    self.pieces=[]
                    self.currentPiece=None
                    self.fileName=None
                    return None
                self.pieces.append(Piece(dirName))
            self.nPieces = len(self.pieces)
            if self.nPieces > 0:
                self.currentPiece = self.pieces[0]
                return True
            else:
                self.currentPiece = None
                return False
            

    def NumberOfPieces(self, name):
        return self.nPieces

    def SetName(self, fname):
        self.fileName = fname
        if fname != None:
            self.GetPieces(self.fileName)
            
    def GetPieceNames(self):
        names=[]
        if self.nPieces == 0:
            return []
        for p in self.pieces:
            names.append(p.shortName)
        return names
    
    def Clear(self):
        self.fileName = None
        self.nPieces = 0
        self.pieces = []
        
    def GetName(self):
        return self.fileName
    
    def GetCurrentPiece(self):
        return self.currentPiece
     
    def SetCurrentPiece(self, piece=None):
        if piece != None:
            self.currentPiece = piece
        return
    
    def NextPiece(self):
        if len(self.pieces) == 1:
            return self.currentPiece
        try:
            if self.pieces.index(self.currentPiece) == len(self.pieces)-1:
                return self.currentPiece
            self.currentPiece = self.pieces[self.pieces.index(self.currentPiece)+1]
            return self.currentPiece
        except ValueError:
            return self.currentPiece
        
        
    def SetPieceByName(self,name):
        """ changes current piece to the one named """
        for p in self.pieces:
            if p.name == name:
                self.currentPiece = p
                
    
    def PrevPiece(self):
        if (len(self.pieces)) == 1:
            return self.currentPiece
        try:
            if self.pieces.index(self.currentPiece) == 0:
                return self.currentPiece
        except ValueError: 
            return self.currentPiece
        self.currentPiece = self.pieces[self.pieces.index(self.currentPiece)-1]
        
        

class Bookmark:
    """
    A bookmark is a position in a piece. A piece contains a list of bookmarks. Bookmarks are numbered 0 to 9
    """
    def __init__(self,pageNum=None,pos=None,num=None):
        self.pageNumber = pageNum
        self.position = pos
        self.number = num
    def SetPosition(self,x,y):
        self.position = (x,y)
    def GetPosition(self):
        return self.position
    def SetPageNumber(self,pageNum):
        self.pageNumber = pageNum
    def GetPageNumber(self):
        return self.pageNumber
    
class Page:
    """
    Page object contained inside a piece object
    Also contains a list of annotations
    """
    def __init__(self, fname=None, pageNum = None):
        self.name = fname
        self.pageNum = pageNum
        self.annotations = []
        
    def SetFileName(self,fname=None):
        self.name = fname
    def GetPageNumber(self):
        return self.pageNum
    def GetFileName(self):
        return self.name
    def AddAnnotation(self,annot):
        self.annotations.append(annot)
    def ClearAnnotations(self):
        self.annotations = []
    def RemoveAnnotation(self,annot):
        for a in self.annotations:
            if a == annot:
                self.annotations.remove(a)
    def GetAnnotations(self):
        return self.annotations

class Piece:
    """ 
    Piece Definition 
    Methods: NumberOfPages - returns the number of pages in a piece
             SetName - Sets the name of the piece (equivalent to the directory) 
             GetName - Returns tne name of the piece
             GetCurrentPage - Returns the current page (object) 
             GetNextPage - returns the next pages 
             TurnForward - turns the current page forward by 1 page (returns True if successful) 
             TurnBackward - turns the current page backward by 1 page (returns True if successful) 
        
    """
    def __init__(self, dirName=None):
        recognizedExtensions = ['.gif','.bmp','.tiff','.jpeg','.jpg','.png']
        self.currentPage = None
        self.name = dirName
        d = dirName.split('/')
        self.shortName = d[len(d)-1]
        self.nPages = 0
        self.bookMarks = []
        self.pages = []
        self.scrollAmount = 200 
        self.timerValue = 10
        if self.name:
            if not os.path.exists(self.name):
                msg=''.join(["File ",self.name," does not exist... Aborting"])
                wx.MessageBox(msg,'Piece Initialize')
                return None                
            fileList = os.listdir(self.name)
            matchedPatterns = []
            matchedPattern = None
            for suffix in recognizedExtensions:
                pat = re.compile('.+\\' + suffix)
                for fileName in fileList:
                    if pat.match(fileName):
                        if not matchedPatterns.__contains__(suffix):
                            matchedPatterns.append(suffix)
            if len(matchedPatterns) == 0:
                wx.MessageBox("Sorry, can't find a recognized file type.","Error")
                return None
            if len(matchedPatterns) > 1:
                cft=ChooseFileType(matchedPatterns)
                if (cft.dlg.ShowModal()==wx.ID_OK):
                    str = cft.radio.GetStringSelection()
                    matchedPattern = '.'+str.lower()
                    matchedPatterns = [matchedPattern]
                else:
                    return
            if len(matchedPatterns) == 1:
                matchedPattern = matchedPatterns[0]
            pat = re.compile('.+\\' + matchedPattern)
            pageNum = 1
            for fileName in fileList:
                if pat.match(fileName):
                    self.pages.append(Page(fileName,pageNum))
                    pageNum = pageNum + 1
                    self.nPages = self.nPages + 1
            if self.nPages > 0:
                self.currentPage = self.pages[0]
                if self.nPages > 1:
                    self.nextPage = self.pages[1]
                else:
                    self.nextPage = self.currentPage
            else:
                self.currentPage = None
                self.nextPage = None
            self.LoadBookmarks()
            self.LoadParameters()

    def SetCurrentPage(self,pageNumber):
        if pageNumber+1 > self.nPages:
            return
        self.currentPage = self.pages[pageNumber]
        if pageNumber+2 > self.nPages:
            self.nextPage = self.currentPage
        else:
            self.nextPage = self.pages[pageNumber+1]
        
    def NumberOfPages(self):
        """ returns the number of pages in the piece """
        return len(self.pages)

    def SetName(self,dname):
        """ sets the name of the directory """
        self.name = dname
        
    def GetName(self):
        """ Returns the name of the piece (equivalent to the directory) """
        return self.name

    def GetPreviousPage(self):
        idx = self.pages.index(self.currentPage)
        if idx==0:
            return None
        else:
            return self.pages[idx-1]
        
    def GetCurrentPage(self):
        """ Returns the current page (page objects are created in __init__ )"""
        return self.currentPage
    
    def GetNextPage(self):
        idx = self.pages.index(self.currentPage)
        if (idx+1) == self.nPages:
            return None
        else:
            return self.pages[idx+1]
        
    def TurnForward(self):
        """ 
        Turns one page forward 
        returns True if successful, False if on last page.
        """
        idx = self.pages.index(self.currentPage)
        if (idx+1) < self.nPages:
            self.currentPage = self.pages[self.pages.index(self.currentPage)+1]
            if (idx+2) < self.nPages: 
                self.nextPage = self.pages[self.pages.index(self.currentPage)+1]
            else:
                self.nextPage = self.currentPage
            return True
        else:
            return False
    
    def TurnBackward(self):
        """ 
        Turns back one page 
        Returns True if successful, 
        Returns False if on first page.
        """
        idx = self.pages.index(self.currentPage)
        if idx == 0:
            return False
        else:
            self.nextPage = self.currentPage
            self.currentPage = self.pages[self.pages.index(self.currentPage)-1]
            return True
        
    def GetPage(self,pageNum):
        for p in self.pages:
            if p.pageNum == pageNum:
                return p
        return None
        
    def AddBookmark(self,pageNum,pos,num):
        for b in self.bookMarks:
            if b.number == num:
                self.bookMarks.remove(b)
        self.bookMarks.append(Bookmark(pageNum,pos,num))
        self.SaveBookmarks()
    
    def RemoveAllBookmarks(self):
        self.bookMarks = []
        self.SaveBookmarks()
        
    def SaveBookmarks(self):
        fname = self.name + '/Bookmarks.txt'
        f = open(fname,'w')
        f.writelines([str(len(self.bookMarks)),'\n'])
        for b in self.bookMarks:
            f.writelines([str(b.pageNumber),'\n',str(int(b.position[0])),'\n',str(int(b.position[1])),'\n',
                          str(b.number),'\n'])
        f.close()
       
    def SaveParameters(self):
        fname = self.name + '/Parameters.txt'
        f = open(fname,'w')
        f.writelines([str(self.scrollAmount),'\n',str(self.timerValue),'\n'])
        f.close()
        
        
    def LoadBookmarks(self):
        fname = self.name + '/Bookmarks.txt'
        if os.path.exists(fname):
            f = open(fname,'r')
            lines = f.readlines()
            f.close()
            nBookmarks = int(lines[0])
            idx = 1
            for i in range(0,nBookmarks): 
                self.AddBookmark(int(lines[idx].strip('\n')),(int(lines[idx+1].strip('\n')),int(lines[idx+2])),int(lines[idx+3].strip('\n')))
                idx = idx + 4
        
    def LoadParameters(self):
        fname = self.name + '/Parameters.txt'
        if os.path.exists(fname):
            f = open(fname,'r')
            lines = f.readlines()
            f.close()
            self.scrollAmount = int(lines[0].strip('\n'))
            self.timerValue = float(lines[1].strip('\n'))
            
    def RemoveBookmark(self,num):
        for b in self.bookMarks:
            if b.num == num:
                self.bookMarks.remove(b)
        self.SaveBookmarks()
                
    def GetBookmark(self,num):
        for b in self.bookMarks:
            if b.num == num:
                return b
        return None
    
    def GoToBookmark(self,num):
        for b in self.bookMarks:
            if b.number == num:
                self.currentPage = self.GetPage(b.pageNumber)
                if self.GetPage(b.pageNumber + 1):
                    self.nextPage = self.GetPage(b.pageNumber + 1)
                else:
                    self.nextPage = self.currentPage
                return b.position
        return None
    
