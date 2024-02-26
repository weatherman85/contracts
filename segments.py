import re
from typing import Generator
from titles import find_segment_titles,score_title 
from utils.clean_text import clean_text

class DocumentSegment:
    def __init__(self,
                 start: int = 0,
                 end: int = 0,
                 title: str = '',
                 title_start: int = 0,
                 title_end: int = 0,
                 text: str = '',
                 section: str = '',
                 subsection:str=''):
        self.start = start
        self.end = end
        self.section = section
        self.title = title
        self.title_start = title_start
        self.title_end = title_end
        self.subsection = subsection
        self.text = text

    def __str__(self):
        return f'{self.title} [{self.start}: {self.end}]'

    def __eq__(self, other):
        if not isinstance(other, DocumentSegment):
            return NotImplemented

        return self.start == other.start and self.end == other.end \
               and self.title == other.title and self.title_start == other.title_start \
               and self.title_end == other.title_end and self.text == other.text

# Constants for regex patterns
COMBINED_PATTERN = re.compile(r"""
    ^([SECTIONsection]{7})?\s*(?P<section>[IVX\d]+(?:\.[IVX\d]+)*(?:(?=\s|$)|\.))\s*(?P<title>[A-Z\d][^\r\n]*?)(=$|[^\w\s\-])(?:\.|\s|$)(?!\d+\.\d+)
    | ^(ARTICLE|article)\s(\d+):?(.*)$
    | (\s+IN\s+WITNESS\s+WHEREOF)|(\s+Signed\s+by\s+the\s+Parties\s+)
    | ^(Schedule|Appendix|Addendum|Annex|Exhibit|Annexure)
""", re.MULTILINE | re.VERBOSE | re.IGNORECASE)

def get_segments(text: str):
    prev_start = None
    accumulated_text = ""    
    #for title_pattern in title_patterns:
    for match in COMBINED_PATTERN.finditer(text):
        #print(match.group())
        start, end = match.span()
        title_score = score_title(match.group(0), start)
        if title_score >= 5:
            #print(match.group())
            # Yield the accumulated text if any
            if accumulated_text:
                yield accumulated_text
                accumulated_text = ""            
            # Yield the current text
            if prev_start:
                yield text[prev_start:start]
            elif start != 0:
                yield text[0:start]
            prev_start = start
        else:
            # Accumulate text with a score under 5
            accumulated_text += text[end: start]
    # Yield the remaining accumulated text
    if accumulated_text:
        yield accumulated_text
    # Yield the remaining text after the last match if any
    if prev_start:
        yield text[prev_start:]


def get_segment_spans(text: str, return_text: bool = True) -> Generator:
    _start_index_counter = 0
    segment_tokenizer = get_segments
    for segment_text in get_segments(text):
        try:
            start_index = _start_index_counter + text[_start_index_counter:].index(segment_text)
            end_index = start_index + len(segment_text)
            _start_index_counter = end_index
        except:
            print(segment_text)
        try:
            title_start, title_end, section_title, subsection, title = find_segment_titles(segment_text)
        except IndexError:
            title_start = title_end =section_title= subsection= title = None

        res = DocumentSegment(
            start=start_index,
            end=end_index,
            title=title,
            title_start=title_start,
            title_end=title_end,
            section=section_title,
            subsection=subsection
        )
        if return_text:
            res.text = clean_text(
                segment_text,lower=False, 
                remove_num=False, 
                add_stop_words=None, 
                remove_stop_words=None)[title_end:].lstrip()
        yield res

class Map(dict):
    """
    Example:
    m = Map(some_dict)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

        self.objectify(self)

    def objectify(self, a_dict):
        for key, val in a_dict.items():
            if isinstance(val, dict):
                a_dict[key] = Map(val)

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super().__delitem__(key)
        del self.__dict__[key]