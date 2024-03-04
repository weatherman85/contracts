from ner.named_entity import NamedEntity
from ner.named_entity_recognizer import NamedEntityRecognizer
import re

class RegexNER(NamedEntityRecognizer):
    def __init__(self, rules=None, keywords=None, normalizer=None):
        super().__init__(rules=rules, keywords=keywords, normalizer=normalizer)
        self.regexes = list()

    def load_rules(self, rules):
        self.regexes.extend(rules)

    def load_raw_rules(self, rules):
        for rule in rules:
            if len(rule) == 2:
                regex_ = rule[0].strip()
                label_ = rule[1].strip()
                self.regexes.append((re.compile(regex_), label_))

    def predict(self, text):
        for regex, label in self.regexes:
            for match in regex.finditer(text):
                start, end = match.span()
                ent = NamedEntity(
                    name=match.group(),
                    start=start,
                    end=end,
                    label=label
                )
                yield ent
                
    def __call__(self, text):
        return super().__call__(text)
