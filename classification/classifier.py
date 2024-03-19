class Classifier:
    def __init__(self, model=None, attribute=None, positive_class=None,normalizer=None):
        self.model = model
        self.attribute = attribute
        self.positive_class = positive_class
        self.normalizer = normalizer

    def predict(self, text, method, text_range=None):
        raise NotImplementedError("Subclasses must implement the predict method.")

    def __call__(self, contract, batch_size=5, text_range=None):
        results = self.predict(contract, batch_size, text_range)

        if self.positive_class != "multi":
            for label, score, text in results:
                if label == self.positive_class:
                    # Update the specified attribute dynamically
                    if self.normalizer:
                        setattr(contract, self.attribute, self.normalizer.process(text))
                    else:
                        setattr(contract, self.attribute, text)
                        break
        else:
            best_score = float('-inf')
            for label, score, text in results:
                if score > best_score:
                    best_score = score
                    best_label = label
            if best_score != float('-inf'):
                if self.normalizer:
                    setattr(contract, self.attribute, self.normalizer.process(best_label))
                else:
                    setattr(contract, self.attribute, best_label)

        return contract
