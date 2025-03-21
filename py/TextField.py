

from PySide6 import QtCore, QtWidgets, QtGui

class TextField(QtWidgets.QPlainTextEdit):
    
    def __init__(self, parent):
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        
        self.parent = parent
        
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        
        self.document().setDefaultFont(QtGui.QFont("Mono"))
        
        self.updateRequest.connect(self.onUpdateRequest)
        self.textChanged.connect(self.onTextChanged)
        
    def onUpdateRequest(self, rect, dy):
        # print([rect, dy])
        self.parent.onUpdate(rect, dy)
        
    def onTextChanged(self):
        self.parent.onTextChanged()
        
    def contentWidth(self):
        doc = self.document()
        block = doc.firstBlock()
        lastBlock = doc.lastBlock()
        biggestWidth = 0
        while type(block) is QtGui.QTextBlock:
            width = len(block.text()) * 10
            # print([width])
            # width = self.blockBoundingRect(block).width()
            if width > biggestWidth:
                biggestWidth = width
            if block == lastBlock:
                break
            block = block.next()
        return biggestWidth + 24
        
    def contentHeight(self):
        doc = self.document()
        block = doc.firstBlock()
        charHeight = self.blockBoundingRect(block).height()
        return doc.lineCount() * charHeight + 32
