import streamlit as st
from contract import ContractPipeline
from ner.clf_ner import CLF_NER
from ner.regex_ner import RegexNER
from normalization.date_normalizer import DateNorm
from normalization.gov_normalizer import GovNorm
from normalization.lang_normalizer import LangNorm
from normalization.entity_normalizer import EntityNormalizer
from classification.transformer_classifier import TransformersClassifier
from classification.sklearn_classifier import SklearnClassifier
from ner.transformer_ner import TransformersNER
import pandas as pd
from io import StringIO
import os
from streamlit_pdf_viewer import pdf_viewer
from utils.generate_annotations import generate_annotations
import json
from datetime import date
from pathlib import Path

tooltip_css = """
<style>
    .tooltip {
    position: absolute;
    visibility: hidden;
    width: 700px;
    background-color: #333;
    color: #fff;
    text-align: left;
    border-radius: 8px;
    padding: 8px;
    z-index: 1;
    top: 100%; /* Change to top instead of bottom */
    left: calc(100% - 150px); /* Adjust the left position */
    opacity: 0;
    transition: opacity 0.3s;
}

.highlighted:hover .tooltip {
    visibility: visible;
    opacity: 1;
}
</style>
"""

st.set_page_config(page_title="Visualize Contract Data")
st.title("Visualize Contract Data")
st.write(tooltip_css, unsafe_allow_html=True)

text_file = st.file_uploader("Upload a text version of your Contract")

st.sidebar.title('Configure Contract Pipeline')
language_classifier = st.sidebar.checkbox("Document Language Classifier (Linear SVM)")
governing_law = st.sidebar.checkbox("Governing Law (BERT)")
effective_date = st.sidebar.checkbox("Effective Dates (Regex)")
currency = st.sidebar.checkbox("Currency (Regex)")
document_type = st.sidebar.checkbox("Document Type Classifier (Linear SVM)")
legal_entities = st.sidebar.checkbox("Counterparties and Signatories (BERT)")

def annotate_entities(text, section_start, entities):
    highlighted_text = ""
    entity_infos = []  # Store entity information for retrieval
    current_position = 0
    for entity in entities:
        start = entity.start - section_start
        end = entity.end - section_start
        entity_text = text[start:end]
        entity_info = {
            "start": start,
            "end": end,
            "label": entity.label,
            "normalized": entity.normalized,
            "lei":None,
            "address":None
        }
        if entity.lei_info is not None:
            lei = entity.lei_info["lei"]
            headquarters_address = ", ".join(entity.lei_info["entity"]["headquartersAddress"]["addressLines"])
            headquarters_address += f', {entity.lei_info["entity"]["headquartersAddress"]["city"]}, {entity.lei_info["entity"]["headquartersAddress"]["region"]}, {entity.lei_info["entity"]["headquartersAddress"]["country"]}, {entity.lei_info["entity"]["headquartersAddress"]["postalCode"]}'
            entity_info["lei"] = lei
            entity_info["address"] = headquarters_address        
            highlighted_text += text[current_position:start]
            highlighted_text += f'<span class="highlighted" data-entity="{len(entity_infos)}" ' \
                                f'style="background-image: linear-gradient(90deg, #aa9cfc, #fc9ce7); ' \
                                f'cursor: pointer; position: relative;">' \
                                f'{entity_text}<span class="tooltip">' \
                                f'<span class="tooltip-text">Entity Type: {entity.label}<br>Normalized Text: {entity.normalized}<br>Legal Entity Identifier:{entity_info["lei"]}<br>Headquarters:{entity_info["address"]}</span>' \
                                f'</span></span>'
        else:
            highlighted_text += text[current_position:start]
            highlighted_text += f'<span class="highlighted" data-entity="{len(entity_infos)}" ' \
                                f'style="background-image: linear-gradient(90deg, #aa9cfc, #fc9ce7); ' \
                                f'cursor: pointer; position: relative;">' \
                                f'{entity_text}<span class="tooltip">' \
                                f'<span class="tooltip-text">Entity Type: {entity.label}<br>Normalized Text: {entity.normalized}</span>' \
                                f'</span></span>'
        current_position = end
        entity_infos.append(entity_info)
    
    highlighted_text += text[current_position:]
    
    return highlighted_text, entity_infos

def get_html(html, start, entities):
    highlighted_html, entity_info = annotate_entities(html, start, entities)
    for info in entity_info:
        if isinstance(info["normalized"], date):
            info["normalized"] = info["normalized"].strftime("%Y-%m-%d")
    entity_info_str = json.dumps(entity_info)
    WRAPPER = f"""
    <div id="annotated-text" style="white-space: pre-wrap; overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{highlighted_html}</div>
    """
    return WRAPPER.strip(), entity_info_str

def hash_func(obj: ContractPipeline) -> int:
    return obj 

@st.cache_resource(hash_funcs={ContractPipeline: hash_func})
def create_pipeline():
    contract_pipeline = ContractPipeline(defaults=True)
    if governing_law:
        gov_law_ner = CLF_NER(keywords=["law","jurisdicition","governing"],model="sguarnaccio/gov_law_clf_ner",normalizer=GovNorm())
        contract_pipeline.add_pipe(name="governing_law",component=gov_law_ner)
    if effective_date:
        effective_date_rules = [(r"(?:effective|dated) (?:as of|on)*? ((?:\d{1,2}[-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|Decmebter)?[a-z\s,.]*(?:\d{1,2}[-/th|st|nd|rd)\s,]*)+(?:\d{2,4})+)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated) (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated) (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated) (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(day)\s*(of)\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated) (?:as of|on)*? (January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated) (?:as of|on)*?  ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*of\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated) (?:as of|on)*?  (January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE")]
        eff_date_ner = RegexNER(normalizer=DateNorm())
        eff_date_ner.load_raw_rules(effective_date_rules)
        contract_pipeline.add_pipe(name="effective_date",component=eff_date_ner)
    if currency:
        currency_rules = [(r"(?P<currency>[\$£€¥₹]|(?:USD|US Dollar|GBP|British Pound|EUR|Euro|JPY|Japanese Yen|INR|Indian Rupee|CAD|Canadian Dollar|AUD|Australian Dollar|CHF|Swiss Franc|CNY|Chinese Yuan|SGD|Singapore Dollar|NZD|New Zealand Dollar|HKD|Hong Kong Dollar|SEK|Swedish Krona|NOK|Norwegian Krone|KRW|South Korean Won|MXN|Mexican Peso|BRL|Brazilian Real|TRY|Turkish Lira|ZAR|South African Rand|IDR|Indonesian Rupiah|MYR|Malaysian Ringgit|PHP|Philippine Peso|THB|Thai Baht|HUF|Hungarian Forint|CZK|Czech Koruna|ILS|Israeli New Shekel|PLN|Polish Złoty|DKK|Danish Krone|AED|United Arab Emirates Dirham|SAR|Saudi Riyal|RON|Romanian Leu|RUB|Russian Ruble|CLP|Chilean Peso|TWD|New Taiwan Dollar|ARS|Argentine Peso|COP|Colombian Peso|VND|Vietnamese Đồng|NGN|Nigerian Naira|UAH|Ukrainian Hryvnia|EGP|Egyptian Pound|QAR|Qatari Riyal|BDT|Bangladeshi Taka|PKR|Pakistani Rupee|PEN|Peruvian Sol))\s*(?P<amount>[0-9]+(?:[,.][0-9]{3})*(?:[,.][0-9]+)?)","currency")]
        currency_ner = RegexNER()
        currency_ner.load_raw_rules(currency_rules)
        contract_pipeline.add_pipe(name="currency",component=currency_ner)
    if document_type:
        document_type_classifier = SklearnClassifier(
        model= Path(__file__).parent /"classification/pretrained/document_type_model.pkl",
        method="lines",
        positive_class=1,
        attribute="document_type")
        document_type_classifier.model = document_type_classifier.model["Linear SVM"]["model"]
        contract_pipeline.add_pipe(name="document_type_classifier",component=document_type_classifier,params={"text_range":(0,15)})
    if language_classifier:
        language_classifier_model = SklearnClassifier(
            model= Path(__file__).parent /"classification/pretrained/document_language_model.pkl",
            attribute="language",
            method = "lines",
            positive_class="multi",
            normalizer=LangNorm()
        )
        model = language_classifier_model.model["Linear SVM"]

        language_classifier_model.model = model["model"]
        language_classifier_model.label_encoder = model["label_encoder"]
        contract_pipeline.add_pipe(
            name="language_classifier",
            component=language_classifier_model,
            before="tokenizer",
            params={"text_range":(0,50)})
    if legal_entities:
        le_ner = TransformersNER(keywords=["signature"],model="sguarnaccio/le_signatory",normalizer=EntityNormalizer())
        contract_pipeline.add_pipe(name="legal_entities",component=le_ner)
    return contract_pipeline

@st.cache_resource
def run_pipeline(_pipeline,file_path):
    doc = _pipeline(file_path)
    return doc

if text_file is not None:
    st.session_state.counter = 1
    pipeline = create_pipeline()
    bytes_data = text_file.read()  # read the content of the file in binary
    file_path = f"tmp/{text_file.name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(text_file.getbuffer())
    doc = run_pipeline(pipeline,file_path)           
    segments = [(segment.section,segment.subsection,segment.title,segment.text,segment.start,segment.end) 
        for segment in doc.segments]
    annotations = generate_annotations(doc.ents)
    # print(annotations)
    viz = st.selectbox("Select option to visualize",
                ["Contract PDF",
                "Contract Metadata",
                "Contract Text",
                "Glossary",
                "Counterparties"])
    
    if viz == "Contract Metadata":
        st.header("Contract Metadata")
        st.text_input("Contract Type",doc.document_type)
        st.text_input("Contract Language",doc.language)
        st.text_area("Effective Dates",list(set([ent.normalized for ent in doc.ents if ent.label=="EFFECTIVE_DATE"])))
        st.text_area("Governing Law",list(set([ent.normalized for ent in doc.ents if ent.label=="gov_law"])))
    elif viz == "Contract Text":
        st.header("Contract Text")
        for section,subsection,title,section_text,section_start,section_end in segments:
            section_ents = []
            for ent in doc.ents:
                if section_start <= ent.start <= section_end:
                    section_ents.append(ent)
            with st.expander(f"{title}"):
                highlighted_html, entity_info_str = get_html(section_text, section_start, section_ents)
                st.markdown(highlighted_html, unsafe_allow_html=True)
    elif viz == "Glossary":
        definitions = [df for df in doc.glossary]
        for df in definitions:
            with st.expander(f"{df.term}"):
                st.markdown(f"{df.definition}",unsafe_allow_html=True)
    elif viz=="Counterparties":
        counterparties = list(set([ent for ent in doc.ents if ent.label=="legal_entity"]))
        for ent in counterparties:
            with st.expander(f"{ent.normalized}"):
                st.json(ent.lei_info)
    elif viz == "Contract PDF":
        # st.write(doc.bbox_info)
        # Display the current page
        page_container = st.empty()
        with page_container:
            pdf_viewer(file_path, pages_to_render=[st.session_state.counter])

        # Add buttons for navigation
        col1, col2 = st.columns(2)
        next_btn = col2.button("Next")
        back_btn = col1.button("Back")

        # Handle button clicks
        if next_btn:
            st.session_state.counter = min(st.session_state.counter + 1, 100 - 1)  # Prevent exceeding the total number of pages
        elif back_btn:
            st.session_state.counter = max(st.session_state.counter - 1, 0)  # Prevent going below the first page

        # Update the page display if the counter changed
        if next_btn or back_btn:
            page_container.empty()
            with page_container:
                pdf_viewer(file_path, pages_to_render=[st.session_state.counter])