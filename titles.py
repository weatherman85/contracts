import regex as re

def find_segment_titles(text):
    start, end, title, section,subsection = None, None, None, None,None

    SECTION_TITLE_RE1 = re.compile(r"""
        ^([SECTIONsection]{7})?\s*(?P<section>[IVX\d]+(?:\.[IVX\d]+)*(?:(?=\s|$)|\.))\s*(?P<title>[A-Z\d][^\r\n]*?)(?=$|[^\w\s\-])(?:\.|\s|$)(?!\d+\.\d+)
        """,re.MULTILINE | re.VERBOSE)
    ARTICLE_TITLE_PATTERN = re.compile(r'^(ARTICLE|article)\s(?P<section>\d+):?(?P<title>.*)$',re.MULTILINE | re.VERBOSE)
    title_patterns = [SECTION_TITLE_RE1, ARTICLE_TITLE_PATTERN]

    for ptn in title_patterns:
        matches = re.finditer(ptn, text)
        for match in matches:
            start, end = match.span()
            #print(match)
            #score title
            title_score = score_title(match.group(0),start)
            if title_score >=5:
                title = match.group('title').strip()                
                # Check if 'section' group is present in the match
                if 'section' in match.groupdict():
                    section = match.group('section')              
                    # Determine if it's a parent section or a subsection
                    section_split = section.split(".",1)
                    #print(section_split)
                    section = section_split[0]
                    subsection =  section_split[1] if len(section_split)>1 else None
                return start, end, section, subsection,title  # Return the pattern name along with section, title, start, and end positions

    return start, end, section, subsection,title  # Return None for the pattern name if no match is found

def score_title(title: str, start: int) -> int:
    # Set weights for features
    WEIGHTS = [15, 5, 10, 10, 15]
    # Check if title starts with a section number
    section_number = re.compile(r"^\d+\.|[XIV]{1,3}\.")
    # Check if title starts with an enumeration a) a. etc
    section_enum = re.compile(r"^(?P<letter_enum>\(?[a-zA-Z]{1,2}\)?\.?)|(?P<num_enum>\(\d{1,2}\)\.?)")
    # Check if title starts with Section/Article
    section_start = re.compile(r'^(?:S(ection|\s?ECTION)|Article|\s?RTICLE)?\s*(?:\d{1,2}\.)*\d{1,2}\.?')
    starts_number = 1 if section_number.match(title) else 0
    starts_enum = 1 if section_enum.match(title.lower()) else 0
    starts_section = 1 if section_start.match(title) else 0
    # Combine for title start features
    title_start = starts_number + starts_enum + starts_section
    # Check for reasonable length
    title_length = 1 if 2 <= len(title.split()) <= 6 else 0
    # Check position
    title_position = 1 if int(start) >= 3 else 0
    # Check typical schedule/appendix names
    schedule_list = ["schedule", "appendix", "addendum", "annex", "exhibit", "annexure"]
    title_schedule = 1 if any(term in title.lower() for term in schedule_list) else 0
    # Check case
    title_case = 1 if title.isupper() or title.istitle() else 0
    score = title_start * WEIGHTS[0] + title_length * WEIGHTS[1] + title_position * WEIGHTS[2] + title_schedule * WEIGHTS[3] + title_case * WEIGHTS[4]
    return score
