import re, string

class Sentence:
    def __init__(self, start=0, end=0, text=None):
        self.start = start
        self.end = end
        self.text = text

class Sentences:
    def __init__(self):
        self.sentences = []
    @property
    def text(self):
        return [sentence.text for sentence in self.sentences]
    def __iter__(self):
        return iter(self.sentences)
    def append(self, sentence):
        self.sentences.append(sentence)

class SentenceTokenizer:
    def __init__(self):
        self.newline_and_spaces = re.compile(r"\n[ \t]{2,}")
        self.two_more_newlines = re.compile(r"\n{2,}")
        self.terminators = ["...", ".", "!", "?", "\r\n", "\t"]
        self.quotes = ["'", "\""]
        self.sent_start_re = re.compile(f"^[0-9]|[A-Z]\w+")

    def is_potential_line_break(self, token):
        return token in self.terminators or self.newline_and_spaces.match(token) or self.two_more_newlines.match(token)

    def create_sentence(self, tokens, i, j):
        sentence_text = " ".join(tokens[i:j]).strip()

        # Remove space before punctuation marks
        sentence_text = re.sub(r'\s+([{}])'.format(re.escape(string.punctuation)), r'\1', sentence_text)

        return Sentence(start=i, end=j, text=sentence_text)

    def __call__(self,contract):
        text = contract.tokens
        tokens = [t.text for t in text if not t.is_space]
        len_tks = len(tokens)
        i, j = 0, 0
        sentences = Sentences()

        while j < len_tks:
            if self.is_potential_line_break(tokens[j]) or self.is_potential_line_break(tokens[j - 1] + tokens[j]):
                if tokens[j - 1].isdigit() or tokens[j - 2].isdigit():
                    j += 1
                    continue
                if self.newline_and_spaces.match(tokens[j]):
                    if j + 1 < len_tks and not self.sent_start_re.match(tokens[j + 1]):
                        j += 1
                        continue

                while j < len_tks and (
                        self.is_potential_line_break(tokens[j]) or
                        self.is_potential_line_break(tokens[j - 1] + tokens[j]) or
                        tokens[j] in self.quotes):
                    if tokens[j] in self.quotes and tokens[j] != tokens[j - 1]:
                        break  # Balanced quotes
                    j += 1

                sentences.append(self.create_sentence(tokens, i, j))
                i = j
            j += 1

        sentences.append(self.create_sentence(tokens, i, j))  # Handle the last sentence
        contract.sentences = sentences
        return contract
