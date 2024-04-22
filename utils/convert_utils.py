import os
import json
import subprocess
import uuid
import logging
import glob
from copy import deepcopy
from pathlib import Path
from pdf2image import convert_from_path
import tempfile

def run_system_command(cmd:str,ignore:bool=False):
    """
    Call a system command.  Ignore=True to ignore errors"""
    logging.debug(f"Running system command = {cmd}")
    result = subprocess.run(cmd.split(),stderr=subprocess.PIPE,stdout=subprocess.PIPE)
    if not ignore:
        assert result.returncode == 0, f"Error running {cmd}"
    try:
        result = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        result = result.stdout.decode("unicode_escape")
    return result

def pdf_to_images(pdf_fn,config):
    """pdftoppm to create image files"""
    logging.debug("Converting pdf to images")
    file_list = []
    pages = convert_from_path(pdf_fn)
    temp_dir = tempfile.mkdtemp()
    for count, page in enumerate(pages):
        page.save(os.path.join(temp_dir, f'out{count}.jpg'), 'JPEG')
        file_list.append(os.path.join(temp_dir, f'out{count}.jpg'))
    return file_list

def images_to_pdf(image_fn,config):
    """tesseract to OCR the images back into single pdf"""
    logging.debug("Converting image to pdf")
    file_path = os.path.dirname(image_fn)
    if file_path:
        os.chdir(file_path)
    cmd = f"tessearct -c textonly_pdf=1 {image_fn} OCR --psm 1 pdf"
    _ = run_system_command(cmd)
    return os.path.join(file_path,"OCR.pdf"),config

def convert_to_images_pdf(pdf_fn,config):
    """Convert to images and then back to single pdf"""
    image_fn, new_config = pdf_to_images(pdf_fn,config)
    pdf_fn,new_config = images_to_pdf(image_fn,new_config)
    return pdf_fn, new_config