import streamlit as st
from langchain.document_loaders import TextLoader
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=3000, chunk_overlap=0
)
draft_template = """You are a legal AI assitant that is an expert at identifying sections of legal agreements.  
I will be sending you a series of texts from an agreement and I want you to identify the character start and end of each section.
The response should be in a JSON format and should contain the following fields: character_start_position,character_end_position.
If the text sent does not seem to be a logicial start of conclusion to a section, please add a seperate field: "mid_segment" and return a value True.  
Identify the section title, section_number and sub_section_number if present.  An example of a subsection would be "2.2 Duties of Custodian".

Consider these patterns when identifying the sections

regex: {regex}

Do not include any other text in your response
       
Question: {question}"""

TITLE_PATTERNS = """
    (r'\b(?:section|part|chapter|article)\s*[IVXLCDMivxlcdm]+(?:\s*[-–]\s*[IVXLCDMivxlcdm]+)?\b',
    (r'\b(?:sub\s*[-–]?\s*section|subsection)\s*[A-Za-z0-9]+\b', 
    (r'\b(?:[IVXLCDMivxlcdm]+\.\s*)+[A-Za-z0-9]+\b'),
    (r'^([SECTIONsection]{7})?\s*(?P<section>[IVX\d]+(?:\.[IVX\d]+)*(?:(?=\s|$)|\.))\s*(?P<title>[A-Z\d][^\r\n]*?)(?=$|[^\w\s\-])(?:\.|\s|$)(?!(?:(?:\d{1,5}\s+[A-Za-z.,]+(?:\s+[A-Za-z.,]+)*)|(?:[A-Za-z.,]+\s*\d{1,5}(?:[A-Za-z.,]+\s*\d{1,5})*)))(?!%)'),
    (r'^(ARTICLE|article)\s*(?P<section>[IVX\d]+(?:\.[IVX\d]+)*):?\s*(?P<title>.*)$'),
    (r'(?P<title>IN\s+WITNESS\s+WHEREOF)'),
    (r'(?P<title>SIGNATURES)'),
    (r'(?P<title>Signed\s+by\s+the\s+Parties\s+)'),
    (r'^(?P<title>(Schedule|Appendix|Addendum|Annex|Exhibit|Annexure)\s.*)$'),
    (r'^(?:Dear\s(.+?)|(Ladies\sand\sGentlemen:))'),
    (r'\n^(Best\sregards|Sincerely|Yours\ssincerely|Kind\sregards|Very\struly\syours)'),
    (r'\bTABLE OF CONTENTS\b.*?(?=\b[A-Z]+\s+\d+\b|$)'"""


prompt = ChatPromptTemplate.from_template(draft_template)

model = ChatOpenAI(openai_api_key="")

chain = prompt | model | StrOutputParser()

