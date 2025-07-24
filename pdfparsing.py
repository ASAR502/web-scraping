import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import io

def extract_text_pdfplumber(pdf_path):
    """Extract text using pdfplumber with better error handling"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for i, page in enumerate(pdf.pages, 1):
                # Try different extraction methods
                page_text = page.extract_text()
                
                # If no text, try with different settings
                if not page_text or page_text.strip() == '':
                    page_text = page.extract_text(
                        x_tolerance=3,
                        y_tolerance=3,
                        layout=True,
                        x_density=7.25,
                        y_density=13
                    )
                
                if page_text and page_text.strip():
                    text += f"--- Page {i} ---\n{page_text}\n\n"
                else:
                    print(f"No text found on page {i}")
            
            return text if text.strip() else None
    except Exception as e:
        print(f"pdfplumber error: {str(e)}")
        return None

def extract_text_pypdf2(pdf_path):
    """Extract text using PyPDF2"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            
            for i, page in enumerate(pdf_reader.pages, 1):
                print(f"Processing page {i} with PyPDF2...")
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"--- Page {i} ---\n{page_text}\n\n"
            
            return text if text.strip() else None
    except Exception as e:
        print(f"PyPDF2 error: {str(e)}")
        return None

def extract_text_pymupdf(pdf_path):
    """Extract text using PyMuPDF (fitz)"""
    try:
        doc = fitz.open(pdf_path)
        text = ''
        
        for i in range(len(doc)):
            print(f"Processing page {i+1} with PyMuPDF...")
            page = doc[i]
            page_text = page.get_text()
            if page_text and page_text.strip():
                text += f"--- Page {i+1} ---\n{page_text}\n\n"
        
        doc.close()
        return text if text.strip() else None
    except Exception as e:
        print(f"PyMuPDF error: {str(e)}")
        return None

def extract_text_ocr(pdf_path):
    """Extract text using OCR (for image-based PDFs)"""
    try:
        doc = fitz.open(pdf_path)
        text = ''
        
        for i in range(len(doc)):
            print(f"Processing page {i+1} with OCR...")
            page = doc[i]
            
            # Convert page to image
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Use OCR to extract text
            page_text = pytesseract.image_to_string(img)
            if page_text and page_text.strip():
                text += f"--- Page {i+1} ---\n{page_text}\n\n"
        
        doc.close()
        return text if text.strip() else None
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return None

def extract_text_comprehensive(pdf_path):
    """Try multiple extraction methods"""
    if not os.path.exists(pdf_path):
        return f"Error: File not found at {pdf_path}"
    
    print(f"Attempting to extract text from: {pdf_path}")
    print("=" * 50)
    
    # Method 1: pdfplumber (your original method, enhanced)
    print("Trying pdfplumber...")
    text = extract_text_pdfplumber(pdf_path)
    if text:
        print("✓ Successfully extracted text with pdfplumber")
        return text
    
    # Method 2: PyPDF2
    print("\nTrying PyPDF2...")
    text = extract_text_pypdf2(pdf_path)
    if text:
        print("✓ Successfully extracted text with PyPDF2")
        return text
    
    # Method 3: PyMuPDF
    print("\nTrying PyMuPDF...")
    text = extract_text_pymupdf(pdf_path)
    if text:
        print("✓ Successfully extracted text with PyMuPDF")
        return text
    
    # Method 4: OCR (last resort for image-based PDFs)
    print("\nTrying OCR (this may take longer)...")
    text = extract_text_ocr(pdf_path)
    if text:
        print("✓ Successfully extracted text with OCR")
        return text
    
    return "Error: Unable to extract text using any method. The PDF might be corrupted or contain only images without text."

def analyze_pdf_structure(pdf_path):
    """Analyze PDF structure to understand why text extraction might fail"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print("\n" + "="*50)
            print("PDF ANALYSIS")
            print("="*50)
            
            for i, page in enumerate(pdf.pages, 1):
                chars = page.chars
                images = page.images
                
                print(f"\nPage {i}:")
                print(f"  - Characters found: {len(chars)}")
                print(f"  - Images found: {len(images)}")
                
                if len(chars) == 0 and len(images) > 0:
                    print(f"  - This appears to be an image-based page (requires OCR)")
                elif len(chars) > 0:
                    print(f"  - This page contains extractable text")
                
    except Exception as e:
        print(f"Analysis error: {str(e)}")

# Main execution
if __name__ == "__main__":
    pdf_path = "pdfs/samplereport.pdf"
    
    # First, analyze the PDF structure
    analyze_pdf_structure(pdf_path)
    
    # Then try to extract text
    result = extract_text_comprehensive(pdf_path)
    
    print("\n" + "="*50)
    print("EXTRACTION RESULT")
    print("="*50)
    
    if result.startswith("Error:"):
        print(result)
    else:
        print("Extracted text:")
        print("-" * 30)
        print(result[:1000] + "..." if len(result) > 1000 else result)  # Show first 1000 chars