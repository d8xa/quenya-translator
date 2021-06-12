from .structs import Document, TextSpan, PATTERNS, Language
from .tools import *
import re
import pandas as pd

class DocumentMatcher():
    def process(self, target):
        docs = [Document(t) for t in target]
        for doc in docs: DocumentMatcher._populate(doc)
        return docs

    def _populate(document):
        """Set initial fields for document"""
        # chapters 
        document.has_chapter_headings = re.search(PATTERNS.chapters.find.any, document.raw) is not None

        # preamble/body split
        m = PATTERNS.preamble.bounds.search(document.raw) # search first chapter title
        assert m is not None, "no preamble separator found in document."
        document.preamble = TextSpan(document, span=slice(0, m.span()[0]))
        document.body = TextSpan(document, span=slice(m.span()[1], None))
        
        
        
class ParagraphMatcher():
    """Matches paragraphs inside each document."""
    
    def process(self, target):
        for doc in target:
            assert doc.body is not None, "Document body is not set."
            spans = ParagraphMatcher._get_paragraph_spans(doc)
            doc.paragraphs = [TextSpan(doc, span) for span in spans]
            
        return target

    def _get_paragraph_spans(document):
        """Finds paragraphs in the document."""
        inverse_spans = [m.span() for m in re.finditer(PATTERNS.paragraphs.sep, document.body.text)]
        spans = spans_between(inverse_spans, len(document.body.text), offset=document.body.span.start)

        spans = trim_spans(
            spans, document.raw, 
            left_patterns=[PATTERNS.paragraphs.ltrim],
            right_patterns=[PATTERNS.paragraphs.rtrim]
        )
        spans = drop_whitespace_spans(spans, document.raw)

        return spans

class VerseMatcher():
    """Matches verses inside each paragraph for each document."""
    
    def process(self, target):
        for doc in target:
            verses = []
            for paragraph in doc.paragraphs:
                matches = [m for m in PATTERNS.verses.sep.finditer(paragraph.text)]
                if len(matches)==0:
                    verses.append([])
                    continue
                spans = [m.span() for m in matches]
                spans = drop_ignored_spans(
                    spans, paragraph.text, 
                    patterns=[PATTERNS.verses.sep_ignore]
                ) # drop spans which overlap with ignored content (e.g. in brackets)
                spans = spans_between(
                    spans, 
                    length=len(paragraph.text), 
                    offset=paragraph.span.start
                )
                spans = trim_spans(
                    spans, doc.raw,
                    left_patterns=[PATTERNS.verses.ltrim],
                    right_patterns=[PATTERNS.verses.rtrim]
                )
                spans = drop_whitespace_spans(spans, doc.raw)
                verses.append([TextSpan(paragraph, span) for span in spans])
                
            doc.verses = verses
        
        return target

    
class ParagraphLanguageTagger():
    """Tags each paragraph TextSpan object with the respective language.
    This assumes correctly matched paragraphs (i.e. the same number of 
    paragraphs for each language).
    """
    def process(self, target):
        self.validate_input(target)
        
        for doc in target:
            for i,par in enumerate(doc.paragraphs):
                par.tags["lang"] = Language.QUENYA if i%2==0 else Language.ENGLISH
                    
        return target

    def validate_input(self, target):
        """Check if any required attributes are not set."""
        
        fstr = "%s are not set for at least one of the documents."
        assert all([doc.paragraphs is not None for doc in target]), fstr % "Paragraphs"


class VerseLanguageTagger():
    """Tags each verse TextSpan object with the respective language of the surrounding paragraph (i.e. the parent TextSpan)."""
    def process(self, target):
        self.validate_input(target)
        
        for doc in target:
            for i,par in enumerate(doc.paragraphs):
                for verse in doc.verses[i]:
                    verse.tags["lang"] = par.tags["lang"]
                    
        return target
    
    def validate_input(self, target):
        """Check if any required attributes are not set."""
        
        fstr = "%s are not set for at least one of the documents."
        assert all([doc.paragraphs is not None for doc in target]), fstr % "Paragraphs"
        assert all([doc.verses is not None for doc in target]), fstr % "Verses"
        assert all([all(["lang" in p.tags for p in doc.paragraphs]) for doc in target]), fstr % "Paragraph language tags"

                   

class DataframeTransformer():
    """Converts the iterable to a dataframe with columns [text, language]."""
    def process(self, target):
        dfs = []
    
        for i, doc in enumerate(target):
            text = []
            lang = []
            I,J,K = [],[],[]
            for j in range(int(len(doc.paragraphs)/2)): # len always an even number >= 2.
                for k in range(len(doc.verses[j*2])):
                    for shift in range(2): # add both languages with same (i,j,k)
                        text.append(doc.verses[j*2+shift][k].text)
                        lang.append(doc.verses[j*2+shift][k].tags["lang"])
                        I.append(i)
                        J.append(j)
                        K.append(k)
                    
            df = pd.DataFrame({
                "text": text,
                "language": lang,
                "nr_doc": I,
                "nr_par": J,
                "nr_ver": K
            })

            dfs.append(df)
        
        df = pd.concat(dfs)
        df["nr_doc"] = df["nr_doc"] + 1
        df["nr_par"] = df["nr_par"] + 1
        df["nr_ver"] = df["nr_ver"] + 1

        return df.reset_index().drop("index", axis=1)          

    
class AnnotationRemover():
    """Removes all annotations in brackets from the text."""
    
    def process(self, target):
        self.validate_input(target)
        
        id_columns = [c for c in target.columns if c.startswith("nr")]

        # v1, takes very long.
        #target["text"] = target["text"].apply(
        #    lambda x: re.sub(PATTERNS.verses.annotation, "", x)
        #)
        #g = target.groupby(id_columns)
        #target = g.filter(predicate)
        
        # v2
        candidates = target.text.apply(
            lambda x: re.search(PATTERNS.verses.annotation, x) is not None
        ) # look up replacement candidate locations.
        target.loc[candidates, "text"] = target[candidates].text.apply(
            lambda x: re.sub(PATTERNS.verses.annotation, "", x)
        ) # replace text at candidates.
        # of candidates, check if any text field empty or whitespace only
        drop = target.loc[candidates].text.apply(lambda x:
            len(x)==0 # any text field empty
            or 
            re.search(r"\S", x) is None # any text field only whitespace
        )
        # for group keys in drop_keys, get indices of all group members in target:
        drop_keys = target.loc[candidates][drop].groupby(id_columns).groups.keys()
        group_keys = target.groupby(id_columns).groups
        drop_indices = pd.Int64Index([i for k in drop_keys for i in group_keys.get(k)])
                
        return target.drop(index=drop_indices)
        
    def validate_input(self, target):
        assert type(target) is pd.DataFrame, "input must be a DataFrame."
        assert "text" in target.columns, "input must have a column \'text\'."

    
####################
# Debugging classes:


class ParagraphMatchDebugger():
    """Returns the indices of documents with uneven numbers of paragraph matches."""
    
    def process(self, target):
        mismatches = []
        for i,doc in enumerate(target):
            if len(doc.paragraphs)%2==1:
                mismatches.append((i, 
                     len(doc.paragraphs[::2]), 
                     len(doc.paragraphs[1::2])
                ))
        return mismatches
    
    
class VerseMatchDebugger():
    
    def process(self, target):
        self.validate_input(target)
                   
        mismatches = []
        for i,doc in enumerate(target):
            qya_verses = doc.verses[::2]
            eng_verses = doc.verses[1::2]
            for j in range(len(qya_verses)):
                if len(qya_verses[j]) != len(eng_verses[j]):
                    mismatches.append((i, j, len(qya_verses[j]), len(eng_verses[j])))

        return mismatches
                   
                   
    def validate_input(self, target):
        fstr = f"Unbalanced number of verses (i.e. paragraphs) in one of the documents. Validate the previous pipeline steps with {ParagraphMatchDebugger.__qualname__} first and fix any mismatches."
        assert all([len(doc.verses)%2==0 for doc in doc]), fstr