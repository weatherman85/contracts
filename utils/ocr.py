import pytesseract
from pdf2image import convert_from_bytes
import tempfile
import tabula
from unidecode import unidecode
import os

class OCRProcessor:
    def __init__(self):
        pass

    def replace_table_references(self, text, tables):
        # Define a placeholder for table references
        placeholder = "TABLE_REFERENCE"

        # Iterate over each table and replace its content with the placeholder
        for table_idx, table in enumerate(tables):
            # Assuming the table content is in a list of strings
            table_content = [row.strip() for row in table]  # Adjust this according to your table structure
            table_text = "\n".join(table_content)

            # Replace the table content in the text with the placeholder
            text = text.replace(table_text, f"{placeholder}_{table_idx + 1}")

        return text

    def __call__(self, contract, extract_tables=False):
        if contract.file_path.lower().endswith('.pdf'):
            with open(contract.file_path, 'rb') as f:
                pdf_bytes = f.read()
            images = convert_from_bytes(pdf_bytes)
            ocr_results = []
            bbox_info = []  
            tables = []
            for image in images:
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                ocr_text = unidecode(pytesseract.image_to_string(image))
                ocr_results.append(ocr_text)
                bbox_info.append(ocr_data)
                if extract_tables:
                    temp_dir = tempfile.mkdtemp()
                    ocr_pdf_path = os.path.join(temp_dir, f"tmp.pdf")
                    pdf_data = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
                    with open(ocr_pdf_path, 'wb') as f:
                         f.write(pdf_data)
                     # Extract tables from each OCR'd PDF
                    tables_in_page = tabula.read_pdf(ocr_pdf_path, pages='all')
                    tables.extend(tables_in_page)
                    # Remove temporary files
                    os.remove(ocr_pdf_path)
                    os.rmdir(temp_dir)

            text = ''.join(ocr_results)
            
            # Replace table content with placeholders
            text_with_table_references = self.replace_table_references(text, tables)

            contract.page_count = len(images)
            contract.raw = text_with_table_references
            contract.bbox_info = bbox_info  
            contract.tables = tables
        else:
            raise ValueError("OCR processing is supported only for PDF files.")
        
        return contract
