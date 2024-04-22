import os
import json
import logging
import chardet
import textract
from .convert_utils import *

def convert_image_to_text(input_fn:str,config):
    pth = os.path.dirname(input_fn)
    if pth:
        os.chdir(pth)
    cmd = f"tesseract {input_fn} - --psm 1"
    return run_system_command(cmd),config

def convert_to_text(input_fn:str,input_fmt:str,config:dict):
    """
    Convert input document to txt
    Config options:
    -convert_as_image: imput_fmt:pdf, convert to images, convert images to pdf, then extract
    """
    if input_fmt == "xml":
        input_fmt = "htm"
    if input_fmt in ["png","jpg","jpeg"]:
        output,new_config = convert_image_to_text(input_fn,config)
        return output
    
    if input_fmt != "pdf":
        try:
            output = textract.process(input_fn,extension=input_fmt).decode("utf8")
        except UnicodeDecodeError:
            logging.degub("Decoding error -- attempting to detect encoding")
            with open(input_fn,"rb") as file_in:
                input_bytes = file_in.read()
            enc = chardet.detect(input_bytes)["encoding"]
            if enc is None:
                raise Exception("Encoding could not be detected")
            input_data = input_bytes.decode(enc,errors="replace")
            tmp_fn = f"{input_fn}.decoded"
            with open(tmp_fn,"w",encoding="utf-8") as file_out:
                file_out.write(input_data)
            output = textract.process(tmp_fn,extension=input_fmt).decode("utf8")
            logging.debug("Input successfully converted to utf-8")
        return output
    
    if config["convert_as_image"]:
        input_fn,config = convert_to_images_pdf(input_fn,config)
    os.chdir(os.path.dirname(input_fn))
    cmd = f"pdftotext -f {config['first_page']} -l {config['last_page']} {input_fn}"
    result = run_system_command(cmd)
    return result