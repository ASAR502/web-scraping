import os
import requests
from bs4 import BeautifulSoup
import pdf2image
import pytesseract
from PIL import Image
import json
from pathlib import Path

def fetch_pdfs_from_site(url="http://jmicoe.in/", folder="pdfs"):
    """Download all PDFs from the website"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all PDF links
        pdf_links = soup.find_all("a", href=lambda x: x and x.endswith(".pdf"))

        # Create folder if it doesn't exist
        os.makedirs(folder, exist_ok=True)

        downloaded_pdfs = []
        
        for link in pdf_links:
            pdf_url = link.get("href")
            if not pdf_url.startswith("http"):
                pdf_url = url.rstrip("/") + "/" + pdf_url.lstrip("/")

            pdf_name = pdf_url.split("/")[-1]
            pdf_path = os.path.join(folder, pdf_name)

            # Skip if already downloaded
            if os.path.exists(pdf_path):
                print(f"Skipping already downloaded: {pdf_name}")
                downloaded_pdfs.append(pdf_path)
                continue

            # Download the PDF
            print(f"Downloading: {pdf_name}")
            r = requests.get(pdf_url, stream=True)
            with open(pdf_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            downloaded_pdfs.append(pdf_path)

        print("✅ All PDFs downloaded successfully.")
        return downloaded_pdfs
        
    except Exception as e:
        print(f"❌ Error downloading PDFs: {e}")
        return []

def pdf_to_images(pdf_path, output_folder="images"):
    """Convert PDF pages to images using multiple fallback methods"""
    try:
        # Create output folder for images
        pdf_name = Path(pdf_path).stem
        image_folder = os.path.join(output_folder, pdf_name)
        os.makedirs(image_folder, exist_ok=True)
        
        print(f"Converting {pdf_path} to images...")
        
        # Method 1: Try pdf2image first
        try:
            pages = pdf2image.convert_from_path(
                pdf_path,
                dpi=300,  # Higher DPI for better OCR accuracy
                fmt='PNG'
            )
            
            image_paths = []
            for i, page in enumerate(pages):
                image_path = os.path.join(image_folder, f"page_{i+1}.png")
                page.save(image_path, 'PNG')
                image_paths.append(image_path)
                
            print(f"✅ Created {len(image_paths)} images from {pdf_path}")
            return image_paths
            
        except Exception as pdf2image_error:
            print(f"⚠️ pdf2image failed: {pdf2image_error}")
            print("🔄 Trying alternative method with PyMuPDF...")
            
            # Method 2: Fallback to PyMuPDF (fitz)
            try:
                import fitz  # PyMuPDF
                
                doc = fitz.open(pdf_path)
                image_paths = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # Render page to image
                    mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    image_path = os.path.join(image_folder, f"page_{page_num+1}.png")
                    pix.save(image_path)
                    image_paths.append(image_path)
                
                doc.close()
                print(f"✅ Created {len(image_paths)} images from {pdf_path} using PyMuPDF")
                return image_paths
                
            except ImportError:
                print("❌ PyMuPDF not installed. Installing...")
                import subprocess
                subprocess.check_call(["pip", "install", "PyMuPDF"])
                print("✅ PyMuPDF installed. Please restart the script.")
                return []
                
            except Exception as fitz_error:
                print(f"❌ PyMuPDF also failed: {fitz_error}")
                return []
        
    except Exception as e:
        print(f"❌ Error converting PDF to images: {e}")
        return []

def extract_text_from_image(image_path):
    """Extract text from image using OCR"""
    try:
        # Configure Tesseract for better accuracy
        custom_config = r'--oem 3 --psm 6'
        
        # Open and process image
        image = Image.open(image_path)
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(image, config=custom_config)
        
        return text.strip()
        
    except Exception as e:
        print(f"❌ Error extracting text from {image_path}: {e}")
        return ""

def process_pdfs_to_text(pdf_folder="pdfs", output_folder="extracted_text"):
    """Process all PDFs: convert to images and extract text"""
    # Create output folder for extracted text
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    all_extracted_data = {}
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        pdf_name = Path(pdf_file).stem
        
        print(f"\n🔄 Processing: {pdf_file}")
        
        # Convert PDF to images
        image_paths = pdf_to_images(pdf_path)
        
        if not image_paths:
            continue
            
        # Extract text from each image
        extracted_pages = {}
        for i, image_path in enumerate(image_paths):
            print(f"Extracting text from page {i+1}...")
            text = extract_text_from_image(image_path)
            
            if text:
                extracted_pages[f"page_{i+1}"] = text
                
        # Save extracted text
        if extracted_pages:
            all_extracted_data[pdf_name] = extracted_pages
            
            # Save individual PDF text to file
            text_file = os.path.join(output_folder, f"{pdf_name}_extracted.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                for page_num, page_text in extracted_pages.items():
                    f.write(f"=== {page_num.upper()} ===\n")
                    f.write(page_text)
                    f.write("\n\n" + "="*50 + "\n\n")
            
            print(f"✅ Extracted text saved to: {text_file}")
    
    # Save all extracted data as JSON
    json_file = os.path.join(output_folder, "all_extracted_data.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_extracted_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ All extracted data saved to: {json_file}")
    return all_extracted_data

def search_text_in_pdfs(search_term, extracted_data):
    """Search for specific text across all extracted PDF data"""
    results = {}
    
    for pdf_name, pages in extracted_data.items():
        pdf_results = []
        
        for page_name, text in pages.items():
            if search_term.lower() in text.lower():
                # Find the context around the search term
                lines = text.split('\n')
                matching_lines = []
                
                for i, line in enumerate(lines):
                    if search_term.lower() in line.lower():
                        # Get context (2 lines before and after)
                        start = max(0, i-2)
                        end = min(len(lines), i+3)
                        context = '\n'.join(lines[start:end])
                        matching_lines.append({
                            'line_number': i+1,
                            'context': context.strip()
                        })
                
                if matching_lines:
                    pdf_results.append({
                        'page': page_name,
                        'matches': matching_lines
                    })
        
        if pdf_results:
            results[pdf_name] = pdf_results
    
    return results

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Tesseract
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ Tesseract is installed")
    except Exception as e:
        print(f"❌ Tesseract not found: {e}")
        print("📋 Please install Tesseract:")
        print("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("   - macOS: brew install tesseract")
        print("   - Linux: sudo apt-get install tesseract-ocr")
    
    # Check Poppler
    try:
        import pdf2image
        # Try to convert a dummy PDF to test poppler
        print("✅ pdf2image is installed")
    except ImportError:
        print("❌ pdf2image not installed: pip install pdf2image")
    
    # Check PyMuPDF as fallback
    try:
        import fitz
        print("✅ PyMuPDF is available as fallback")
    except ImportError:
        print("⚠️ PyMuPDF not installed (fallback option): pip install PyMuPDF")
    
    print("\n📋 If you're still having issues with Poppler:")
    print("   - Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases")
    print("   - macOS: brew install poppler")
    print("   - Linux: sudo apt-get install poppler-utils")
    print("   - Or use conda: conda install -c conda-forge poppler")

def main():
    """Main function to orchestrate the entire process"""
    print("🚀 Starting PDF scraping and text extraction process...")
    
    # Check dependencies first
    check_dependencies()
    
    # Step 1: Download PDFs from website
    print("\n📥 Step 1: Downloading PDFs...")
    downloaded_pdfs = fetch_pdfs_from_site()
    
    if not downloaded_pdfs:
        print("❌ No PDFs downloaded. Exiting.")
        return
    
    # Step 2: Convert PDFs to images and extract text
    print("\n🔤 Step 2: Converting PDFs to images and extracting text...")
    extracted_data = process_pdfs_to_text()
    
    if not extracted_data:
        print("❌ No text extracted. Exiting.")
        return
    
    # Step 3: Example search functionality
    print("\n🔍 Step 3: Example search functionality...")
    search_term = input("Enter a term to search for (or press Enter to skip): ").strip()
    
    if search_term:
        search_results = search_text_in_pdfs(search_term, extracted_data)
        
        if search_results:
            print(f"\n📋 Search results for '{search_term}':")
            for pdf_name, results in search_results.items():
                print(f"\n📄 PDF: {pdf_name}")
                for result in results:
                    print(f"  📑 {result['page']}:")
                    for match in result['matches']:
                        print(f"    Line {match['line_number']}: {match['context'][:100]}...")
        else:
            print(f"❌ No results found for '{search_term}'")
    
    print("\n✅ Process completed successfully!")

if __name__ == "__main__":
    main()