import re
import pandas as pd
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

pattern_1 = (re.compile(r"(?:(?:word|term|phrase)?\s+|[:,\.]\s*|^)?(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018)(?P<term>[^\"\u0093\u0094\u0022\u0060{2}\u0091\u0092\u201C\u201D|\'{2}\u2019{2}\u2018\u2019]{1,75})(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}\u2018\u2019|\u2019\u2018|[\s,])\s+(?:will\s+mean|will\s+be\s+defined|shall\s+be\s+defined|shall\s+have\s+the\s+meaning|will\s+have\s+the\s+meaning|includes?|shall\s+mean|means|shallmean|rneans|significa|shall\s+for\s+purposes|have\s+meaning|has\s+the\s+meaning|referred\s+to|known\s+as|refers\s+to|shall\s+refer\s+to|as\s+used|for\s+purposes|shall\s+be\s+deemed\s+to|may\s+be\s+used|is\s+hereby\s+changed\s+to|is\s+defined|shall\s+be\s+interpreted|means\s+each\s+of\s+|is\s+a\s+reference\s+to)(?:\s|[,:]\s){1,2}"),"trigger words/qoutes")
pattern_2 = (re.compile(r"((?:each(?:,)?\s+)?(?:(?:the|a|an)\s+)?(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018)(?P<term>[^\"\u0093\u0094\u0022\u0060{2}\u0091\u0092\u201C\u201D|\'{2}\u2019{2}\u2018\u2019]{1,75}}?)\.?(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018))"),"each qoutes")
pattern_3 = (re.compile(r"\(\s?[the]{3}\s(\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018)(?P<term>[^\"\u0093\u0094\u0022\u0060{2}\u0091\u0092\u201C\u201D|\'{2}\u2019{2}\u2018\u2019]{1,75})(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}\u2018\u2019|\u2019\u2018|[\s,])"),"defined before")
pattern_4 = (re.compile(r"((?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018)(?P<term>[^\"\u0093\u0094\u0022\u0060{2}\u0091\u0092\u201C\u201D|\'{2}\u2019{2}\u2018\u2019]{1,75})(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018)):[\s]"),"qoutes no trigger")
pattern_5 = (re.compile(r"(?:(?:called|herein|herein\s+as|collectively\s+as|individually\s+as|together\s+with|referred\s+to\s+as|being|shall\s+be|definition\s+as|known\s+as|designated\s+as|hereinafter|hereinafter\s+as|hereafter|hereafter\s+as|in\s+this\s+section|in\s+this\s+paragraph|individually|collectively)[\s+,]{1,2})(?:(?:the|a|an)\s+)?(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018)(?P<term>[^\"\u0093\u0094\u0022\u0060{2}\u0091\u0092\u201C\u201D|\'{2}\u2019{2}\u2018\u2019]{1,75}?)(?:\"|\u0093|\u0094|\u0022|\u0060{2}|\u0091|\u0092|\u201C|\u201D|\'{2}|\u2019{2}|\u2018\u2019|\u2019\u2018)"),"trigger qoutes term")
patterns = [pattern_3,pattern_1,pattern_2,pattern_4,pattern_5]
triggers = ['will mean','will be defined','shall be defined','shall have the meaning','will have the meaning','includes',
            'shall mean','means','shallmean','rneans','significa','shall for purposes','have meaning','has the meaning',
            'referred to','known as','refers to','shall refer to','as used','for purposes','shall be deemed to','may be used',
            'is hereby changed to','is defined','shall be interpreted','means each of','is a reference to',"a reference to"]

def definition_finder(text:str):
    sents = sent_tokenize(text)
    terms = []
    glossary = []
    undefined = []
    for sent in sents: ##check with segments for better context in QA??
        text = re.sub(r"\s+",' ',sent).strip()
        #text = clean(sent.text,lower=False,no_line_breaks=True)
        # loop through patters to identify terms
        for ptn in patterns:
            matches = re.finditer(ptn[0],text)
            # look through matches
            if not matches == None:
                # get start and end character positions of term
                for match in matches:
                    term,start,end = match.group('term'),match.start('term'),match.end('term')
                    term = re.sub('[^0-9a-zA-Z\s]+', '', term)
                    try:
                        if term.lower() not in [term.lower() for term in terms]:
                            #split sentence at term
                                split_sent = text.split(term,1) 
                                for trigger in triggers:
                                    #check if trigger exists after term
                                    if split_sent[1].find(trigger) != -1:
                                        # grab definition as remaining phrase after trigger
                                        definition = split_sent[1].split(trigger,1)[1].strip()
                                        # add to list of terms
                                        terms.append(term)
                                        # add term and definition to glossary
                                        glossary.append((term,definition,text))
                                        break
                    except: 
                        continue
                    try:
                        if term.lower() not in [term.lower() for term in terms]:  
                        # check if def pattern is "term:"
                            split_sent = text.split(term,1)   
                            if split_sent[1][1] == ":":
                                # grab definition as remaining phrase after :
                                definition = split_sent[1].split(":",1)[1].strip()
                                # add to list of terms
                                terms.append(term)
                                # add term and definition to glossary
                                glossary.append((term,definition,text))
                                break
                            else:
                                break
                    except: 
                        continue
                    # check if prior step found a definition if yes, break loop
                    try:
                        if term.lower() not in [term.lower() for term in terms]:
                            # check if term is all uppercase, implying accronym
                            if term.isupper():
                                # get length of term and chunk sentence into n-grams of that length
                                term_len = len(term)
                                split_sent = text.split(term,1)
                                candidates = [split_sent[0].split()[i:i+term_len] for i in range(0, len(split_sent[0]), term_len)]
                                #get letters to check against chunks
                                for candidate in candidates:
                                    candidate_accro = ''.join(word[0] for word in candidate)
                                    if candidate_accro == term:
                                        terms.append(term)
                                        glossary.append((term,' '.join(word for word in candidate),text))
                        else:
                            break
                    except: continue
    return pd.DataFrame(glossary,columns=["Term","Definition","Text"])
