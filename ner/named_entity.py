class NamedEntity:
    def __init__(self, name=None, normalized = None, label=None, start=0, end=0):
        self.name = name
        self.normalized = normalized
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