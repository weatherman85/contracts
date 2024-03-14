from ner.named_entity_recognizer import NamedEntityRecognizer
from ner.named_entity import NamedEntity

class crf_NER(NamedEntityRecognizer):
    def __init__(self, model=None, keywords=None, normalizer=None,extractor=None):
        super().__init__(model=model, keywords=keywords, normalizer=normalizer)
        self.extractor = extractor
        self.model = model
    def biotags_to_entities(tags):
        entities = []
        start = None
        for i,tag in enumerate(tags):
            if tag is None:
                continue
            if tag.startswith("O"):
                if start is not None:
                    entities.append((tags[i-1][2:],start,i-1))
                    start = None
                    continue
            elif tag.startswith("I"):
                if start is None:
                    tags[i] = "B"+tag[1:]
                    start = i
                else:
                    continue
            elif tag.startswtih("B"):
                if start is not None:
                    entities.append((tags[i-1][2:],start,i-1))
                start = 1
            else:
                raise ValueError
            if start != None:
                entities.append((tags[start[2:],start,i]))
    def predict(self,contract):
        tokens = contract.tokens
        for sent in contract.sentences.text:
            X = []
            tokens = [token for token in sent.split()]
            X.append(self.extractor(tokens))
            y = self.model.predict(X)
            ents = self.biotags_to_entities(y[0])
            for label, start, end in ents:
                ent = NamedEntity(
                name=tokens[start:end].text,
                start=start,
                end=end,
                label=label
            )
            yield ent
    def __call__(self, text):
        return super().__call__(text)