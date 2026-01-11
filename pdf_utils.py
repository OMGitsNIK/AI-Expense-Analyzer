import fitz  # PyMuPDF
import getpass
from pathlib import Path


def unlock_pdf(pdf_path: str, password: str = None) -> fitz.Document:
    """
    Open and unlock a PDF file, prompting for password if needed.
    
    Args:
        pdf_path: Path to the PDF file
        password: Optional password (if None, will prompt if needed)
        
    Returns:
        Unlocked PyMuPDF Document object
        
    Raises:
        ValueError: If password is incorrect or file cannot be opened
    """
    
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    
    # Check if PDF is encrypted
    if not doc.is_encrypted:
        return doc
    
    # If password provided, try it
    if password:
        if doc.authenticate(password):
            print("✅ Password accepted")
            return doc
        else:
            doc.close()
            raise ValueError("❌ Incorrect password provided")
    
    # Prompt user for password (up to 3 attempts)
    for attempt in range(3):
        password = getpass.getpass(f"🔑 Enter PDF password (attempt {attempt + 1}/3): ")
        
        if doc.authenticate(password):
            print("✅ Password accepted")
            return doc
        else:
            print(f"❌ Incorrect password (attempt {attempt + 1}/3)")
    
    # All attempts failed
    doc.close()
    raise ValueError("❌ Failed to unlock PDF after 3 attempts")

def save_unlocked_pdf(doc: fitz.Document, output_path: str):
    """
    Save an unlocked PDF without password protection.
    
    Args:
        doc: PyMuPDF Document object
        output_path: Path to save unlocked PDF
    """
    doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
    print(f"💾 Unlocked PDF saved to: {output_path}")


def pdf_to_temp_unlocked(pdf_path: str, password: str = None) -> str:
    """
    Create a temporary unlocked version of a password-protected PDF.
    
    Args:
        pdf_path: Path to original PDF
        password: Optional password
        
    Returns:
        Path to temporary unlocked PDF
    """
    from pathlib import Path
    import tempfile
    
    # Open and unlock
    doc = unlock_pdf(pdf_path, password)
    
    # Create temp file
    temp_path = Path(tempfile.gettempdir()) / f"unlocked_{Path(pdf_path).name}"
    
    # Save unlocked version
    doc.save(str(temp_path), encryption=fitz.PDF_ENCRYPT_NONE)
    doc.close()
    
    print(f"Temporary unlocked PDF: {temp_path}")
    return str(temp_path)
