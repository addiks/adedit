
from PySide6 import QtCore, QtWidgets, QtGui
from os.path import basename, dirname, abspath
from PySide6.QtCore import QTimer

import subprocess
import os
import hashlib
import re

from py.Widgets.TextField import TextField
from py.Widgets.LineNumbers import LineNumbers
from py.MessageBroker import MessageBroker
from py.Languages.LanguageSelector import LanguageSelector
from py.Languages.Language import Language, LanguageFromSyntaxTreeHighlighter

class EditorWindow(QtWidgets.QMainWindow): # QWidget

    def __init__(self, filePath = None):
        super(EditorWindow, self).__init__()
        
        self.lineNumbers = LineNumbers(self)
        self.textField = TextField(self)
        
        self.messageBroker = None
        
        if filePath != None:
            self.openFile(filePath)
        else:
            self.closeFile()

        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.layout = QtWidgets.QHBoxLayout(self.centralWidget)
        self.centralWidget.layout.setSpacing(0)
        self.centralWidget.layout.setContentsMargins(0, 0, 0, 0)
        self.centralWidget.layout.addWidget(self.lineNumbers, 0)
        self.centralWidget.layout.addWidget(self.textField, 0)
        self.setCentralWidget(self.centralWidget)
        
        self._initMenu()
        
        firstUpdate = QTimer()
        firstUpdate.setInterval(10)
        firstUpdate.timeout.connect(self.onTextChanged)
        firstUpdate.start()
        
    def closeFile(self):
        self.fileContent = ""
        self.filePath = None
        self.setWindowTitle("[No file] - adEdit")
        self.hashOnDisk = ""
        self.lengthOnDisk = 0
        
    def openFile(self, filePath):
        self.filePath = abspath(filePath)
        self.messageBroker = MessageBroker(self)
        
        document = self.textField.document()
        
        selector = LanguageSelector()
        self.language = selector.selectForFilePath(self.filePath)
        
        handle = open(self.filePath, "r")
        self.fileContent = handle.read()

        if self.language != None:
            assert isinstance(self.language, Language)
            self.syntaxTree = self.language.parse(self.fileContent)
            self.highlighter = self.language.syntaxHighlighter(document, self.syntaxTree)
        
        self.hashOnDisk = hashlib.md5(self.fileContent.encode()).hexdigest()
        self.lengthOnDisk = len(self.fileContent)
        
        document.setPlainText(self.fileContent)
        
        self.updateTitle()
        
    def saveFile(self):
        handle = open(self.filePath, "w")
        handle.write(self.fileContent)
        self.hashOnDisk = hashlib.md5(self.fileContent.encode()).hexdigest()
        self.lengthOnDisk = len(self.fileContent)
        self.updateTitle()

    def updateTitle(self):
        textHash = hashlib.md5(self.fileContent.encode()).hexdigest()
        modified = (len(self.fileContent) != self.lengthOnDisk) or (textHash != self.hashOnDisk)

        if modified:
            self.setWindowTitle("* %s (%s) - adEdit" % (
                basename(self.filePath), 
                dirname(self.filePath)
            ))
        else:
            self.setWindowTitle("%s (%s) - adEdit" % (
                basename(self.filePath), 
                dirname(self.filePath)
            ))
        
    def presentSelf(self):
        self.activateWindow()
        self.setFocus()
        
    def onUpdate(self, rect, dy):
        self.lineNumbers.onUpdate(rect, dy)
        
    def onTextChanged(self):
        self.fileContent = self.textField.document().toPlainText()
        self.updateTitle()
        contentWidth = self.textField.contentWidth()
        contentHeight = self.textField.contentHeight()
        
        contentWidth = min(contentWidth, 800)
        contentHeight = min(contentHeight, 800)
        
        contentWidth = max(contentWidth, 275)
        contentHeight = max(contentHeight, 150)
        
        # print([contentWidth, contentHeight])
        
        self.setMinimumWidth(contentWidth)
        self.setMinimumHeight(contentHeight)
        
        if contentWidth >= 800:
            contentWidth = 16777215
        
        if contentHeight >= 800:
            contentHeight = 16777215
            
        self.setMaximumWidth(contentWidth)
        self.setMaximumHeight(contentHeight)
        
        afterUpdate = QTimer()
        afterUpdate.setInterval(10)
        afterUpdate.timeout.connect(self._afterTextChanged)
        afterUpdate.start()

        text = self.textField.document().toPlainText()

        self.syntaxTree = self.language.parse(text)
        if isinstance(self.highlighter, LanguageFromSyntaxTreeHighlighter):
            self.highlighter.updateSyntaxTree(self.syntaxTree)

    def onTextInserted(self, text, position, added):
        inserted = text[position:position+added]

        if inserted == "\n":
           lines = text.split("\n")
           lineNumber = text[:position].count("\n")
           
           oldLine = lines[lineNumber]

           indentionMatch = re.match(r'^(\s+)[^\s]?', oldLine)

           if indentionMatch != None:
               indention = indentionMatch.group(1)
               self.textField.insertTextAt(position+added, indention)
               
    def onSelectionChanged(self, position, anchor, text):
        if self.highlighter != None:
            self.highlighter.updateSelection(text)
            
    def showOpenFilePicker(self):
        (filePath, fileTypeDescr) = QtWidgets.QFileDialog.getOpenFileName(
            self, 
            "Open File", 
            dirname(self.filePath),
            "Text files (*.*)"
        )
        
        bashScript = "/home/gerrit/workspace/Privat/adEdit/run.sh"
        
        os.system(f"nohup {bashScript} '{filePath}' 2>&1 > {bashScript}.log")
        
    def openGitGui(self):
        os.system(f"git gui")
        
    def _afterTextChanged(self):
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)
        self.setMaximumWidth(16777215)
        self.setMaximumHeight(16777215)
        
    def _initMenu(self):
        
        menuBar = self.menuBar()

        ########
        ### FILE
        fileMenu = menuBar.addMenu('File')
        
        openAction = fileMenu.addAction('Open')
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open')
        openAction.triggered.connect(self.showOpenFilePicker)
        
        saveAction = fileMenu.addAction('Save')
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save')
        saveAction.triggered.connect(self.saveFile)
        
        quitAction = fileMenu.addAction('Quit')
        quitAction.setShortcut('Ctrl+Q')
        quitAction.setStatusTip('Quit')
        quitAction.triggered.connect(self.close)
        
        ########
        ### EDIT
        editMenu = menuBar.addMenu('Edit')
        
        deleteLineAction = editMenu.addAction('Delete line')
        deleteLineAction.setShortcut('Ctrl+D')
        deleteLineAction.triggered.connect(self.textField.deleteCurrentLines)

        indentInAction = editMenu.addAction('Indent in')
        indentInAction.triggered.connect(self.textField.indentIn)

        indentOutAction = editMenu.addAction('Indent out')
        indentOutAction.triggered.connect(self.textField.indentOut)

        ##########
        ### SEARCH
        searchMenu = menuBar.addMenu('Search')
        
        searchInFileAction = searchMenu.addAction('Search in this File')
        
        replaceInFileAction = searchMenu.addAction('Replace Text in this File')
        
        searchInProjectAction = searchMenu.addAction('Search in Project')
        
        #######
        ### GIT
        gitMenu = menuBar.addMenu('Git')
        
        gitGuiAction = gitMenu.addAction('git gui')
        gitGuiAction.triggered.connect(self.openGitGui)
        
        #############
        ### DEBUGGING
        debuggingMenu = menuBar.addMenu('Debugging')
        
        self.setMenuBar(menuBar)
        
        menuBar.show()
        
        ############
        ### LANGUAGE
        if self.language != None:
            languageMenu = menuBar.addMenu(self.language.name())