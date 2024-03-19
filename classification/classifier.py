class Classifier:
    def __init__(self, model=None, attribute=None, positive_class=None):
        self.model = model
        self.attribute = attribute
        self.positive_class = positive_class

    def predict(self, text, method, text_range=None):
        raise NotImplementedError("Subclasses must implement the predict method.")

    def __call__(self, contract, batch_size=5, text_range=None):
        results = self.predict(contract, batch_size, text_range)

        if self.positive_class != "multi":
            for label, score, text in results:
                if label == self.positive_class:
                    # Update the specified attribute dynamically
                    setattr(contract, self.attribute, text)
                    break
        else:
            best_score = float('-inf')
            for label, score, text in results:
                if score > best_score:
                    best_score = score
                    best_label = label
            if best_score != float('-inf'):
                setattr(contract, self.attribute, best_label)

        return contract
