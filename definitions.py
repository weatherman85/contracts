import re

class Definition:
    def __init__(self, term=None, definition=None, phrase=None, start=0, end=0):
        self.term = term
        self.definition = definition
        self.phrase = phrase
        self.start = start
        self.end = end       

class DefinitionPatterns:
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

class Definition:
    def __init__(self, term=None, 
                 definition=None, 
                 phrase=None, 
                 start=0, 
                 end=0):
        self.term = term
        self.definition = definition
        self.phrase = phrase
        self.start = start
        self.end = end

class Glossary:
    def __init__(self, sents):
        self.glossary = DefinitionFinder()(sents)
    @property
    def terms(self):
        return [definition.term for definition in self.glossary]            
    def __iter__(self):
        return iter(self.glossary)   
    
class DefinitionFinder(object):
    def __init__(self):
        pass
    def __call__(self,sents):
        glossary = []
        terms = set()

        for sent in sents:
            text = re.sub(r"\s+", ' ', sent.text).strip()

            for ptn in DefinitionPatterns.patterns:
                matches = re.finditer(ptn[0], text)

                for match in matches:
                    term, start, end = match.group('term'), match.start('term'), match.end('term')
                    term = re.sub('[^0-9a-zA-Z\s]+', '', term)
                    term_lower = term.lower()  # Convert term to lowercase

                    if term_lower not in terms:
                        try:
                            split_sent = text.split(term, 1)
                        except ValueError:
                            break
                        if len(split_sent) > 1:  # Check if there are enough elements
                            for trigger in DefinitionPatterns.triggers:
                                if split_sent[1].find(trigger) != -1:
                                    definition = split_sent[1].split(trigger, 1)[1].strip()
                                    terms.add(term_lower)
                                    glossary.append(Definition(term, definition, text, start, end))
                                    break
                                if term_lower not in terms and split_sent[1][1] == ":":
                                    definition = split_sent[1].split(":", 1)[1].strip()
                                    terms.add(term_lower)
                                    glossary.append(Definition(term, definition, text, start, end))
                                    break
                                if term_lower not in terms and term.isupper():
                                    term_len = len(term)
                                    split_sent = text.split(term, 1)
                                    candidates = [split_sent[0].split()[i:i + term_len] for i in range(0, len(split_sent[0]), term_len)]
                                    for candidate in candidates:
                                        candidate_accro = ''.join(word[0] for word in candidate)
                                        if candidate_accro == term:
                                            terms.add(term_lower)
                                            glossary.append(Definition(term, ' '.join(word for word in candidate), text, start, end))
                                            break
        return glossary
                                
