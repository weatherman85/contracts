import spacy
from unidecode import unidecode
import re
from spacy.lang.en import EnglishDefaults

nlp = spacy.load('en_core_web_md')
NORMALIZE_SPACE = re.compile(r"[\r\t\f\v  ]+")
NORMALIZE_NEWLINES = re.compile(r'(\n\s*)+')
REMOVE_NUM = re.compile(
    r"(?:^|(?<=[^\w,.]))[+–-]?(([1-9]\d{0,2}(,\d{3})+(\.\d*)?)|([1-9]\d{0,2}([ .]\d{3})+(,\d*)?)|(\d*?[.,]\d+)|\d+)(?:$|(?=\b))"
)

bad_double_qoutes = [
    "«",
    "‹",
    "»",
    "›",
    "„",
    "“",
    "‟",
    "”",
    "❝",
    "❞",
    "❮",
    "❯",
    "〝",
    "〞",
    "〟",
    "＂",
]

bad_single_quotes = ["‘", "‛", "’", "❛", "❜", "`", "´", "‘", "’"]

DOUBLE_QUOTE_REGEX = re.compile("|".join(bad_double_qoutes))
SINGLE_QUOTE_REGEX = re.compile("|".join(bad_single_quotes))
page_number_pattern = re.compile(r'\n+(\d+)\n{2,}', re.MULTILINE)
digit_word_pattern = re.compile(r'(\d)([A-Za-z])')  # Match a digit followed by a letter

class TextCleaner(object):
    def __init__(self):
        pass
    def __call__(self,
                 contract,
                lower:bool=True,
                remove_num:bool=True,
                add_stop_words:set=None,
                remove_stop_words:list=None) -> str:

        """Preproccessing of text prior to running through a function
        Args:
            text (str): the text to clean
            lower (bool, optional): Whether to return lowercase only. Defaults to True.
            remove_num (bool, optional): Whether to renove numbers completly . Defaults to True.
            add_stop_words (set, optional): Set of additional words to be added to list of stopwords. Defaults to None.
        Returns:
            str: cleaned up text
        """
        text = str(contract.raw)
        if lower:
            text = text.lower()
        text = unidecode(text)
        text = NORMALIZE_SPACE.sub(" ",text)
        text = page_number_pattern.sub("\n",text)
        text = NORMALIZE_NEWLINES.sub("\n",text)
        text = digit_word_pattern.sub(r"\1 \2",text) 
        text = self.fix_line_breaks(text)    
        if remove_num:
            text = REMOVE_NUM.sub('',text)
        if not add_stop_words == None:
            nlp.Defaults.stop_words |= add_stop_words
        if not remove_stop_words == None:
            for word in remove_stop_words:
                nlp.vocab[word].is_stop = False
        tokens = nlp.tokenizer(text)
        #text = ' '.join([token.text for token in tokens if (not token.is_space and not token.is_punct and not token.is_stop \
        #    and not len(token)==1) or token.is_digit])
        contract.text = text
        return contract
    
    def fix_line_breaks(self,text):
        # Split text into lines
        lines = text.split('\n')
        
        # Merge words that are split across lines
        cleaned_lines = []
        for i in range(len(lines)):
            # Check if the line is not empty and contains at least one character
            if lines[i] and lines[i][0].islower():
                # Merge with previous line if the current line starts with a lowercase letter
                cleaned_lines[-1] += lines[i]
            else:
                cleaned_lines.append(lines[i])
        
        # Join lines back into a single text
        cleaned_text = '\n'.join(cleaned_lines)
        
        return cleaned_text