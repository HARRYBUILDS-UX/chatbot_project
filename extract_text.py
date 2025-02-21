import fitz  # PyMuPDF for PDFs
from docx import Document
import pytesseract  # OCR
from pdf2image import convert_from_path  # Convert PDF to images for OCR

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF, with OCR fallback for scanned documents."""
    text = ""

    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                page_text = page.get_text("text")
                text += page_text + "\n"
        # If no text found, attempt OCR on images
        if not text.strip():
            images = convert_from_path(file_path)
            text = "\n".join(pytesseract.image_to_string(img) for img in images)

    except Exception as e:
        return f"Error extracting text from PDF: {e}"

    return text.strip() if text else "No readable text found in the PDF."

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip() if text else "No readable text found in the DOCX."
    except Exception as e:
        return f"Error extracting text from DOCX: {e}"
