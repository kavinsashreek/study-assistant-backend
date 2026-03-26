import fitz
import re
import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import tempfile

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set Poppler path
POPPLER_PATH = r'C:\poppler\poppler-25.12.0\Library\bin'


def extract_text_from_pdf(file_path: str) -> str:
    """
    Smart PDF reader that tries normal reading first.
    If that fails (scanned PDF), uses OCR automatically!
    """
    print(f"📄 Trying normal text extraction...")

    # First try normal text extraction
    full_text = ""
    pdf_document = fitz.open(file_path)

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        page_text = page.get_text()
        full_text += f"\n[Page {page_number + 1}]\n{page_text}"

    pdf_document.close()
    full_text = clean_text(full_text)

    # Check if we got enough text
    word_count = len(full_text.split())
    print(f"📊 Normal extraction: {word_count} words found")

    if word_count >= 50:
        print("✅ Normal text extraction successful!")
        return full_text

    # Not enough text — use OCR!
    print("🔍 Scanned PDF detected! Switching to OCR mode...")
    return extract_text_with_ocr(file_path)


def preprocess_image(image):
    """
    Improves image quality before OCR.
    Better image = better OCR accuracy!
    """
    # Convert to grayscale
    image = image.convert('L')

    # Increase size for better accuracy
    width, height = image.size
    image = image.resize((width * 2, height * 2), Image.LANCZOS)

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Sharpen the image
    image = image.filter(ImageFilter.SHARPEN)

    # Make it black and white (binarize)
    image = image.point(lambda x: 0 if x < 140 else 255, '1')

    return image


def extract_text_with_ocr(file_path: str) -> str:
    """
    Uses OCR to read text from scanned PDF images.
    Preprocesses images for better accuracy.
    """
    try:
        from pdf2image import convert_from_path

        print("🖼️ Converting PDF pages to images...")

        # Convert PDF pages to high quality images
        pages = convert_from_path(
            file_path,
            dpi=400,  # Higher DPI = better quality
            poppler_path=POPPLER_PATH
        )

        print(f"📑 Found {len(pages)} pages, running OCR...")

        full_text = ""

        for page_number, page_image in enumerate(pages):
            print(f"🔍 OCR processing page {page_number + 1}/{len(pages)}...")

            # Preprocess image for better OCR
            processed_image = preprocess_image(page_image)

            # Run OCR with better settings
            custom_config = r'--oem 3 --psm 6 -l eng'
            page_text = pytesseract.image_to_string(
                processed_image,
                config=custom_config
            )

            # Clean up common OCR mistakes
            page_text = fix_ocr_errors(page_text)

            full_text += f"\n[Page {page_number + 1}]\n{page_text}"

        full_text = clean_text(full_text)
        word_count = len(full_text.split())

        print(f"✅ OCR complete! Extracted {word_count} words")

        return full_text

    except Exception as e:
        raise ValueError(
            f"OCR failed: {str(e)}\n"
            "Please make sure Tesseract and Poppler are installed correctly!"
        )


def fix_ocr_errors(text: str) -> str:
    """
    Fixes common OCR mistakes.
    For example: '0' instead of 'O', '1' instead of 'l' etc.
    """
    # Fix common character substitutions
    fixes = {
        r'\b0\b': 'O',      # Standalone 0 → O
        r'l1': 'li',         # l1 → li
        r'\bI\b(?!\s)': 'I', # Keep capital I
    }

    # Remove garbage characters that OCR sometimes produces
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\'\"\n\+\=\/\%\#\@]', ' ', text)

    # Fix multiple spaces
    text = re.sub(r' +', ' ', text)

    # Fix lines that are too short (likely OCR noise)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Keep lines with at least 3 characters
        if len(line.strip()) >= 3:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def clean_text(text: str) -> str:
    """Cleans up extracted text."""
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 30) -> list[str]:
    """Cuts text into smaller searchable chunks."""
    words = text.split()
    print(f"📊 Total words found: {len(words)}")

    if len(words) == 0:
        return []

    chunks = []
    start_index = 0

    while start_index < len(words):
        end_index = start_index + chunk_size
        chunk_words = words[start_index:end_index]
        chunk = ' '.join(chunk_words)

        if len(chunk_words) > 10:
            chunks.append(chunk)

        start_index += (chunk_size - overlap)

    return chunks


def process_pdf(file_path: str) -> dict:
    """Main function that processes any PDF automatically."""
    print(f"📄 Processing PDF: {file_path}")

    full_text = extract_text_from_pdf(file_path)

    print(f"📝 Total extracted: {len(full_text)} characters")

    if not full_text or len(full_text.strip()) < 50:
        raise ValueError(
            "Could not extract text from this PDF. "
            "Please try a different file."
        )

    chunks = chunk_text(full_text)

    print(f"✅ Extracted {len(full_text)} characters")
    print(f"✅ Created {len(chunks)} chunks")

    if len(chunks) == 0:
        raise ValueError(
            "Could not create chunks from this PDF. "
            "Please try a TXT file instead."
        )

    return {
        "full_text": full_text,
        "chunks": chunks,
        "total_characters": len(full_text),
        "total_chunks": len(chunks)
    }