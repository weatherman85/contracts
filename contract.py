from typing import List, Union, Dict, Generator
from tokenization.tokenizer import Tokenizer
from tokenization.sentence import SentenceTokenizer
from tokenization.segments import SectionSegmenter
from utils.clean_text import TextCleaner
from definitions.definitions import DefinitionFinder

class Contract(object):
    def __init__(self, 
                 text: str,
                 tokens=None,
                 sentences=None,
                 segments=None,
                 segment_count=0,
                 glossary=None,
                 table_of_contents=None,
                 ents=None):
        self.text = text
        self.raw = text
        self.char_length = len(self.text)
        self.tokens = tokens
        self.sentences = sentences
        self.segments = segments
        self.segment_count = segment_count
        self.glossary = glossary
        self.table_of_contents = table_of_contents
        self.ents = ents
     
class ContractPipeline:
    def __init__(self,defaults=True):
        if defaults:
            tokenizer = Tokenizer(default=True)
            section_segmenter = SectionSegmenter()
            sentence_tokenizer = SentenceTokenizer()
            pre_process = TextCleaner()
            definitions = DefinitionFinder()
            
            self.pipeline = [
                {"component":pre_process,"name":"clean_text","params":{"lower":False, 
                                                                       "remove_num":False, 
                                                                       "add_stop_words":None, 
                                                                       "remove_stop_words":None}},
                {"component":tokenizer,"name":"tokenizer"},
                {"component":sentence_tokenizer,"name":"sentence_tokenizer"},
                {"component":section_segmenter,"name":"section_segmenter"},
                {"component":definitions,"name":"definition_finder"}
            ]
        else:
            self.pipeline = []

    def add_pipe(self, component, name=None, before=None, after=None,params=None):
        """
        Add a processing component to the pipeline.

        Args:
        - component (callable): The processing component.
        - name (str): Name to identify the component.
        - before (str): Add the component before an existing component with this name.
        - after (str): Add the component after an existing component with this name.
        """
        if params:
            pipe_item = {"component": component, "name": name,"params":params}
        else:
            pipe_item = {"component": component, "name": name}
        if before and after:
            raise ValueError("Specify either 'before' or 'after', not both.")
        elif before:
            index = next((i for i, item in enumerate(self.pipeline) if item["name"] == before), None)
            if index is not None:
                self.pipeline.insert(index, pipe_item)
            else:
                raise ValueError(f"Component '{before}' not found in the pipeline.")
        elif after:
            index = next((i for i, item in enumerate(self.pipeline) if item["name"] == after), None)
            if index is not None:
                self.pipeline.insert(index + 1, pipe_item)
            else:
                raise ValueError(f"Component '{after}' not found in the pipeline.")
        else:
            self.pipeline.append(pipe_item)
            
    def __call__(self, text):
        contract = Contract(text)
        for item in self.pipeline:
            component = item["component"]
            params = item.get("params", {})
            contract = component(contract,**params)

        return contract
