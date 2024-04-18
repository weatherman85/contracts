from ner.named_entity import Entities

class NamedEntityRecognizer:
    def __init__(self, rules=None, keywords=None, normalizer=None):
        """Initialize the NamedEntityRecognizer.

        Args:
            rules (list): List of rules for entity recognition.
            keywords (list): List of keywords for filtering.
            normalizer (Normalizer): Object for normalizing entity names.
        """
        self.entities = Entities()
        self.rules = rules
        self.keywords = keywords
        self.normalizer = normalizer

    def find_entities(self, contract):
        entity_idxs = set()
        if contract.ents is not None:
            self.entities = contract.ents
            entity_idxs.update(range(ent.start, ent.end) for ent in contract.ents)

        for segment in contract.segments:
            text = segment.text
            title = segment.title

            if self.keywords and title and any(keyword in title.lower().split() for keyword in self.keywords):
                entities = self.predict(text)
            elif not self.keywords:
                entities = self.predict(text)
            else:
                entities = []

            for ent in entities:
                start, end = ent.start + segment.start, ent.end + segment.start
                overlapped = any(idx in entity_idxs for idx in range(start, end))

                if not overlapped:
                    entity_idxs.update(range(start, end))
                    ent.start, ent.end = start, end

                    # Find tokens corresponding to the entity's start and end positions
                    entity_tokens = [token for token in contract.tokens if token.idx >= start and token.idx + len(token.text) <= end]
                    
                    # Extract bounding boxes corresponding to the tokens
                    entity_bboxes = [token._.bbox for token in entity_tokens]

                    # Associate bounding boxes with the entity
                    ent.bbox_span = entity_bboxes

                    if self.normalizer:
                        ent.normalized = self.normalizer.process(ent)
                    self.entities.append(ent)

        return self.entities

    def predict(self, text):
        raise NotImplementedError("Subclasses must implement the predict method.")
   
    
    def __call__(self, contract):
        """Process the contract to find entities.

        Args:
            contract (Contract): The contract object to process.

        Returns:
            Entities: The processed entities.
        """
        self.entities = Entities()
        self.find_entities(contract)
        contract.ents = self.entities
        return contract
