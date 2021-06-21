from enum import Enum
import re


class FullStruct:
    def __init__(self, kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                fs = FullStruct(value)
                self.__dict__.update({key: fs})
            else:
                self.__dict__.update({key: value})
                
                
class Pipeline():
    def __init__(self, steps=[]):
        self.steps = steps
    
    def process(self, X):
        Xt = X
        for name,step in self.steps:
            Xt = step.process(Xt)
        return Xt
    


class Document():
    """Represents a document."""
    def __init__(self, text: str):
        self.raw = text
        self.body = None
        self.preamble = None
        self.has_chapter_headings = None
        self.paragraphs = None
        self.chapters = None
        self.verses = None


class TextSpan():
    """Represents a span in the parent object"""
    def __init__(self, parent, span, tags=None):
        self.parent = parent
        self.span = span
        #self.number
        self.tags = {} if tags is None else tags

    @property
    def text(self):
        parent = self.parent
        while not hasattr(parent, "raw"):
            if not hasattr(parent, "parent"):
                raise KeyError("Parent is root, but has no raw text field.")
            parent = parent.parent
        return parent.raw[self.span]


    def __repr__(self):
        if len(self.text)>30:
            text = self.text.replace("\t", "\\t").replace("\n", "\\n")[:27]
        else: text = self.text[:30]
        return f"TextSpan(text=\"{text}\"{'...' if len(self.text)>30 else ''}, span={self.span})"
    
    def __str__(self):
        return self.text
    
class Language(Enum):
    QUENYA = 0
    ENGLISH = 1
    
    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name
    
    
PATTERNS = FullStruct({
    "preamble" : {"bounds" : re.compile(r'\s*\n+\s*-+\s*\n+\s*', flags=re.I)}, #
    "chapters" : {
        #"sep" : re.compile(r"\s*RANTA.*\n\s*"), # not (yet) in use.
        "find" : {
            "any" : re.compile(r"^(?:RANTA|CHAPTER).*$", flags=re.M+re.I), #
        },
    },
    "paragraphs" : {
        "sep" : re.compile(r"\s*(?:\n[\t ]*){2,}(?:(?:RANTA|CHAPTER|SSS)\s+\d+\s*)?\s*(?=\S)", flags=re.I), #
        "ltrim" : re.compile(r"^\s*(?:(?:RANTA|CHAPTER|SSS)\s*\d+\s*)?\s+\b", flags=re.I), #
        "rtrim" : re.compile(r"\s+$", flags=re.I) #
    },
    "verses" : {
        #"number" : re.compile(r"\W(\d+)[^\n]\w", flags=re.I+re.M), # not (yet) in use.
        "sep" : re.compile(r"\s*\d+\s+(?=\S)", flags=re.I+re.S), #
        "ltrim" : re.compile(r"^\s+", flags=re.I), #
        "rtrim" : re.compile(r"\s+$", flags=re.I), #
#        "sep_ignore" : re.compile(r"\[(?:[^\]\d]*\d+[^\]\d]+|[^\]\d]+\d+[^\]\d]*)\]") #
        "sep_ignore" : re.compile(r"\[[^\]]*\d+\s+[^\]]*\]"), #
        "cleanup" : re.compile(r"\[[^\]]*\]|\*|[\t\n]+") #
    },
})