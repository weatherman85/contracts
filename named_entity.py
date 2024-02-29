import re

class NamedEntity:
    def __init__(self, name=None, label=None, start=0, end=0):
        self.name = name
        self.label = label
        self.start = start
        self.end = end


class Entities:
    def __init__(self, entities=None):
        self._entities = entities if entities is not None else []

    @property
    def ents(self):
        return [(ent.name, ent.label) for ent in self._entities]

    def __iter__(self):
        return iter(self._entities)

    def append(self, entity):
        self._entities.append(entity)


class RegexNER(object):
    def __init__(self):
        self.regexes = list()
        self.entities = Entities()

    def load_rules(self, rules):
        self.regexes.extend(rules)

    def load_raw_rules(self,rules):
        for rule in rules:
            if len(rule) == 2:
                regex_ = rule[0].strip()
                label_ = rule[1].strip()
                self.regexes.append((re.compile(regex_),label_))
                
    def __call__(self, doc):
        entity_idxs = set()
        
        if doc.ents is not None:
            self.entities = doc.ents
            entity_idxs.update(range(ent.start, ent.end) for ent in doc.ents)
        if not self.regexes:
            return self.entities  
        
        for regex, label in self.regexes:
            for match in regex.finditer(doc.text):
                start, end = match.span()
                overlapped = any(idx in entity_idxs for idx in range(start, end))

                if not overlapped:
                    entity_idxs.update(range(start, end))
                    ent = NamedEntity(
                        name=match.group(),
                        start=start,
                        end=end,
                        label=label
                    )
                    self.entities.append(ent)

        return self.entities
