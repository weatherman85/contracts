from typing import List, Union, Dict, Generator
import spacy
from sentence import *
from segments import *
from utils.clean_text import clean_text
import pandas as pd
from definitions import Glossary

nlp = spacy.blank("en")

class Contract(object):
    def __init__(self, text: str):
        self.text = clean_text(text, lower=False, remove_num=False, add_stop_words=None, remove_stop_words=None)
        self.raw = text
        self.char_length = len(self.text)
        self.tokens = [token for token in nlp.tokenizer(self.text)]
        self.sentences = Sentences(self.tokens)
        self.segments = self.extract_segments()
        self.segment_count = len(self.segments)
        self.glossary = Glossary(self.sentences)
        self.table_of_contents = self.create_table_of_contents()
        #self.word_count = len(self.tokens)
        #self.sent_count = len(self.sentences)
        self.num_pages = 0      

    def create_table_of_contents(self):
        return [(segment.section, segment.subsection, segment.title) for segment in self.segments]

    def extract_segments(self):
        sections = list(get_segment_spans(self.text))
        self.segments = sections
        return sections
        

    