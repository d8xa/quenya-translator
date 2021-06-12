import re


def trim_span(span, text, left_patterns=[], right_patterns=[]):
    """Trim the span left and right with the supplied patterns."""
    newspan = slice(span.start, span.stop)
    
    for pattern in left_patterns:
        m = pattern.match(text[newspan])
        if m is not None:
            if newspan.start is None:
                newspan = slice(m.span()[1], newspan.stop)
            else:
                newspan = slice(newspan.start+m.span()[1], newspan.stop)


    for pattern in right_patterns:
        m = pattern.search(text[newspan]) # search, bc. match is anchored at start
        if m is not None:
            if newspan.stop is None: 
                newspan = slice(newspan.start, -m.span()[1]-m.span()[0])
            else:
                newspan = slice(newspan.start, newspan.stop-(m.span()[1]-m.span()[0]))
            
    return newspan

def trim_spans(spans, text, left_patterns=[], right_patterns=[]):
    """Trim the spans left and right with the supplied patterns."""
    return [trim_span(span, text, left_patterns, right_patterns) for span in spans]

def drop_whitespace_spans(spans, text):
    """Drop spans which are None, empty, or whitespace."""
    return [span for span in spans
            if not (not text[span] or text[span].isspace())]

def drop_ignored_spans(spans, text, patterns=[]):
    """Drop spans which are fully contained in one of the ignored spans"""
    ignored_spans = []
    for pattern in patterns:
        ignored_spans.extend([m.span() for m in re.finditer(pattern, text)])
    
    if len(ignored_spans)==0: 
        return spans # no overlap found
    
    keep = []
    for span in spans:
        drop = False
        for ignored in ignored_spans:
            if span[0]>=ignored[0] and span[1]<=ignored[1]:
                drop = True
                break # don't search for other overlaps; continue with next span.
        if not drop:
            keep.append(span)
    
    return keep
    
    
def spans_between(spans, length, offset=0):
    """Returns the spans before, after and between the given spans."""
    if len(spans)==0: return spans
    result = spans
    if len(spans)==1:
        result = [(0,spans[0][0]), (spans[0][1],length)]
    else:
        result = [(a[1], b[0]) for a,b in zip(spans[:-1], spans[1:])]
        if spans[0][0] != 0:
            # if there is content before the first span, include it.
            result = [(0,spans[0][0])] + result
        if spans[-1][1] != length:
            # if there is content after the last span, include it.
            result = result +[(spans[-1][1],length)]

    return [slice(a+offset, b+offset) for (a,b) in result]