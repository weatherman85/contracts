import re
from typing import Generator
from titles import find_segment_titles,score_title 
from utils.clean_text import clean_text
from street_endings import street_endings
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

TITLE_PATTERNS = [
    re.compile(r'\b(?:section|part|chapter|article)\s*[IVXLCDMivxlcdm]+(?:\s*[-–]\s*[IVXLCDMivxlcdm]+)?\b', re.IGNORECASE),
    re.compile(r'\b(?:sub\s*[-–]?\s*section|subsection)\s*[A-Za-z0-9]+\b', re.IGNORECASE),
    re.compile(r'\b(?:[IVXLCDMivxlcdm]+\.\s*)+[A-Za-z0-9]+\b'),
    re.compile(r'^([SECTIONsection]{7})?\s*(?P<section>[IVX\d]+(?:\.[IVX\d]+)*(?:(?=\s|$)|\.))\s*(?P<title>[A-Z\d][^\r\n]*?)(=$|[^\w\s\-])(?:\.|\s|$)(?!(?:(?:\d{1,5}\s+[A-Za-z.,]+(?:\s+[A-Za-z.,]+)*)|(?:[A-Za-z.,]+\s*\d{1,5}(?:[A-Za-z.,]+\s*\d{1,5})*)))(?!%)'),
    re.compile(r'^(ARTICLE|article)\s*(?P<section>[IVX\d]+(?:\.[IVX\d]+)*):?\s*(?P<title>.*)$'),
    re.compile(r'(IN\s+WITNESS\s+WHEREOF)'),
    re.compile(r'(Signed\s+by\s+the\s+Parties\s+)'),
    re.compile(r'^(Schedule|Appendix|Addendum|Annex|Exhibit|Annexure)\s.*$'),
    re.compile(r'^(?:Dear\s(.+?)|(Ladies\sand\sGentlemen:))'),
    re.compile(r'\n^(Best\sregards|Sincerely|Yours\ssincerely|Kind\sregards|Very\struly\syours)'),
]

def identify_sections(text):
    sections = []
    current_section = {"start": 0, "end": 0, "title_start": 0, "title_end": 0, "section": None, "sub_section": None}

    lines = text.split('\n')
    text_index = 0

    for index, line in enumerate(lines):
        for pattern in TITLE_PATTERNS:
            match = pattern.match(line)
            if match:
                if not any(ending in match.group() for ending in street_endings):
                    current_section["end"] = text_index
                    sections.append(current_section.copy())
                    current_section["start"] = text_index
                    if 'title' in pattern.groupindex and match.group("title"):
                        current_section["title"] = match.group("title").strip()
                        current_section["title_start"] = text_index + match.start("title")
                        current_section["title_end"] = text_index + match.end("title")
                    else:
                        current_section["title"] = ""
                        current_section["title_start"] = text_index
                        current_section["title_end"] = text_index
                    if 'section' in pattern.groupindex and match.group("section"):
                        section_str = match.group("section")
                        section_split = section_str.split(".", 1)
                        current_section["section"] = section_split[0].rstrip(".")
                        current_section["subsection"] = section_split[1].rstrip(".") if len(section_split) > 1 else None
                    else:
                        current_section["section"] = None
                        current_section["subsection"] = None
        text_index += len(line) + 1  # Add 1 for the newline character

    # Set the end of the last section after the loop
    current_section["end"] = len(text)
    sections.append(current_section)

    return sections

def get_segments(text: str) -> Generator:
    sections = identify_sections(text)

    for section in sections:
       yield DocumentSegment(
            start=section.get("title_start", 0),
            end=section.get("title_end", len(text)),
            title=section.get("title", None),
            title_start=section.get("title_start", None),
            title_end=section.get("title_end", None),
            section=section.get("section", None),
            subsection=section.get("subsection", None),
            text=clean_text(
                text[section.get("title_end", section.get("startsailp")):section.get("end", len(text))],
                lower=False,
                remove_num=False, 
                add_stop_words=None, 
                remove_stop_words=None).lstrip(".").lstrip("\n")
        )