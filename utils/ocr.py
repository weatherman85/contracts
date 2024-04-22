import tempfile
from unidecode import unidecode
import os
import subprocess
import logging
from copy import deepcopy
from pathlib import Path
from pdf2image import convert_from_path
import chardet
import textract
from shutil import rmtree
import PyPDF2

logging.basicConfig(level=logging.DEBUG)

class FileProcessor():
    def __init__(self):
        pass
       
    def __call__(self, contract):
        input_fn = ""
        try:
            input_fn, input_fmt = pre_process(contract.file_path)
            logging.debug(f"Preprocessed input file: {input_fn}, format: {input_fmt}")
            text,bbox,_ = convert_to_text(input_fn, input_fmt, config={"convert_as_image": True})
        except Exception as err:
            logging.error(f"An error occurred: {err}")
            raise err
        finally:
            if input_fn:
                rmtree(os.path.dirname(input_fn))  
             
        # contract.page_count = len(images)
        contract.raw = text
        contract.bbox_info = bbox  
        return contract

def run_system_command(cmd:str, ignore:bool=False):
    """
    Call a system command. Ignore=True to ignore errors
    """
    logging.debug(f"Running system command = {cmd}")
    result = subprocess.run(cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if not ignore:
        assert result.returncode == 0, f"Error running {cmd}"
    try:
        result = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        result = result.stdout.decode("unicode_escape")
    return result

def pdf_to_images(pdf_fn, config):
    """pdftoppm to create image files"""
    logging.debug("Converting pdf to images")
    file_list = []
    pth = os.path.dirname(pdf_fn)
    if pth:
        os.chdir(pth)
    pages = convert_from_path(pdf_fn)
    temp_dir = tempfile.mkdtemp()
    for count, page in enumerate(pages):
        page.save(os.path.join(temp_dir, f'out{count}.jpg'), 'JPEG')
        file_list.append(os.path.join(temp_dir, f'out{count}.jpg'))
    with open("file_list", "w") as f:
        f.write("\n".join(file_list))
    config["first_page"] = 1
    config["last_page"] = len(pages)
    return os.path.join(pth, "file_list"), config

def images_to_pdf(image_fn, config=None):
    """tesseract to OCR the images back into single pdf"""
    logging.debug("Converting image to pdf")
    file_path = os.path.dirname(image_fn)
    original_path = os.getcwd() 
    os.chdir(file_path) 
    cmd = f"tesseract -c textonly_pdf=1 {image_fn} OCR --psm 1 pdf"
    _ = run_system_command(cmd)
    pdf_path = os.path.join(file_path, "OCR.pdf")
    return pdf_path, config


def convert_to_images_pdf(pdf_fn, config=None):
    """Convert to images and then back to single pdf"""
    image_fn, new_config = pdf_to_images(pdf_fn, config)
    pdf_fn, new_config = images_to_pdf(image_fn, new_config)
    return pdf_fn, new_config

def convert_image_to_text(input_fn:str, config=None):
    original_path = os.getcwd()  # Store original current working directory
    pth = os.path.dirname(input_fn)
    if pth:
        os.chdir(pth)
    cmd = f"tesseract {input_fn} - --psm 1"
    result = run_system_command(cmd)  # Execute Tesseract command
    os.chdir(original_path)  # Return to the original current working directory
    return result, config

def convert_to_text(input_fn:str, input_fmt:str, config:dict=None):
    """
    Convert input document to txt
    Config options:
    - convert_as_image: input_fmt:pdf, convert to images, convert images to pdf, then extract
    
    """
    print(input_fn)
    bbox = []
    new_config = deepcopy(config)
    original_path = os.getcwd()  # Store original current working directory
    if input_fmt == "xml":
        input_fmt = "htm"
    if input_fmt in ["png", "jpg", "jpeg"]:
        output, new_config = convert_image_to_text(input_fn, config)
        return output, bbox, new_config
    
    if input_fmt == "txt":
        with open(input_fn, "r", encoding="utf-8") as f:
            output = f.read()
        return output,bbox,new_config
    if input_fmt != "pdf":
        try:
            output = textract.process(input_fn, extension=input_fmt).decode("utf-8")
        except UnicodeDecodeError:
            logging.debug("Decoding error -- attempting to detect encoding")
            with open(input_fn, "rb") as file_in:
                input_bytes = file_in.read()
            enc = chardet.detect(input_bytes)["encoding"]
            if enc is None:
                raise Exception("Encoding could not be detected")
            input_data = input_bytes.decode(enc, errors="replace")
            tmp_fn = f"{input_fn}.decoded"
            with open(tmp_fn, "w", encoding="utf-8") as file_out:
                file_out.write(input_data)
            output = textract.process(tmp_fn, extension=input_fmt).decode("utf-8")
            logging.debug("Input successfully converted to utf-8")
        return output, bbox, new_config
    
    if new_config["convert_as_image"]:
        input_fn, new_config = convert_to_images_pdf(input_fn, new_config)
    os.chdir(os.path.dirname(input_fn))
    # print(os.getcwd())
    # cmd = f"pdftotext -f {new_config['first_page']} -l {new_config['last_page']} {input_fn}"
    text,bbox = get_pdf_text(input_fn)
    os.chdir(original_path)  # Return to the original current working directory
    return text,bbox, new_config

def pre_process(input_file):
    inpt_file = open(input_file, "rb")
    temp_dir = tempfile.mkdtemp()
    parts = Path(input_file).name.rsplit(".", 1)
    if len(parts) == 2:
        ext = parts[1]
    input_fn = os.path.join(temp_dir, f"input.{ext}")
    with open(input_fn, "wb") as fid:
        fid.write(inpt_file.read())
    inpt_file.close()
    return input_fn, ext

def get_pdf_text(pdf_path):
    text_content = ''
    bbox_info = []
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text_content += page.extract_text()
            bbox_info.append(page.mediabox)
    return text_content.strip(), bbox_info