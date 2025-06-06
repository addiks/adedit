
import re

from .AbstractSyntaxTree import ASTNode
from .ASTPatterns import NodePattern

### TOKENS

class Token(ASTNode):
    def __init__(self, language, tokenName, code, row, col, offset):
        super().__init__(language, code, row, col, offset, "token")
        self.tokenName = tokenName
        
    def __repr__(self):
        return "<[%d,%d]:%s:'%s'>" % (self.row, self.col, self.tokenName, self.code)
        
    def grammarKey(self):
        return self.tokenName

class TokenDef:
    def __init__(self, tokenName, code):
        self.tokenName = tokenName
        self.code = code

    def toToken(self, language, row, col, offset):
        return Token(
            language, 
            self.tokenName,
            self.code,
            row,
            col,
            offset
        )

### TOKEN MATCHER

class TokenMatcher:
    def lexNext(self, text): # return: (text, TokenDef|null)
        raise NotImplementedError
        
class KeywordsTokenMatcher(TokenMatcher):
    def __init__(self, keywords, language):
        self._keywords = keywords
        self._language = language

    def lexNext(self, text): # return: (text, TokenDef|None)
        token = None
        for keyword in self._keywords:
            if text[0:len(keyword)].upper() == keyword.upper():
                if not text[len(keyword):len(keyword)+1].isidentifier():
                    tokenName = "T_" + keyword.upper()
                    token = TokenDef(tokenName, keyword)
                    text = text[len(keyword):]
            
        return (text, token)

class LiteralTokenMatcher(TokenMatcher):
    def __init__(self, delimitter, tokenName):
        self._delimitter = delimitter
        self._tokenName = tokenName

    def lexNext(self, text): # return: (text, TokenDef|None)
        token = None
        if text[0] == self._delimitter:
            end = False
            index = 0
            while not end:
                index += 1
                if index >= len(text) or text[index] == self._delimitter:
                    end = True
            literal = text[0:index + 1]
            token = TokenDef(self._tokenName, literal)
            text = text[len(literal):]
        return (text, token)

class RegexMatcher(TokenMatcher):
    def __init__(self, pattern, tokenName, groupNo=0):
        self._pattern = pattern
        self._tokenName = tokenName
        self._groupNo = groupNo

    def lexNext(self, text): # return: (text, TokenDef|None)
        token = None
        rematch = re.match(self._pattern, text)
        if rematch != None:
            matchedText = rematch.group(self._groupNo)
            token = TokenDef(self._tokenName, matchedText)
            text = text[len(matchedText):]
        return (text, token)
        
class DirectTokenMatcher(TokenMatcher):
    def __init__(self, directTexts, tokenName):
        if type(directTexts) == str:
            directTexts = [directTexts]
        self._directTexts = directTexts
        self._tokenName = tokenName

    def lexNext(self, text): # return: (text, TokenDef|None)
        token = None
        for directText in self._directTexts:
            if text[0:len(directText)] == directText:
                token = TokenDef(self._tokenName, directText)
                text = text[len(directText):]
                break
        return (text, token)

### NODE PATTERNS

class TokenNodePattern(NodePattern):
    def __init__(self, tokenName):
        self._tokenName = tokenName

    def nodeKeys(self): # string
        return [self._tokenName]
        
    def producedNodeKey(self): # string
        return self._tokenName
        
    def matches(self, nodes, index):
        node = nodes[index]
        expected = self._tokenName
        if isinstance(node, Token):
            return node.tokenName == expected or node.code == expected
        return False
        
    def mutate(self, nodes, index):
        node = nodes[index]
        assert isinstance(node, Token)
        expected = self._tokenName
        assert node.tokenName == expected or node.code == expected
        return ([], index) # No mutation needed, the node is already the token
        