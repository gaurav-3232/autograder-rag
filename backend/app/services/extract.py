import PyPDF2
from docx import Document
from io import BytesIO


class TextExtractor:
    @staticmethod
    def extract_from_pdf(file_data: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = BytesIO(file_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            
            return '\n'.join(text)
        except Exception as e:
            raise Exception(f"Failed to extract PDF text: {e}")
    
    @staticmethod
    def extract_from_docx(file_data: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(BytesIO(file_data))
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            raise Exception(f"Failed to extract DOCX text: {e}")
    
    @staticmethod
    def extract_from_txt(file_data: bytes) -> str:
        """Extract text from TXT file."""
        try:
            return file_data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_data.decode('latin-1')
            except Exception as e:
                raise Exception(f"Failed to decode text file: {e}")
    
    @staticmethod
    def extract_text(file_data: bytes, filename: str) -> str:
        """Extract text based on file extension."""
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        extractors = {
            'pdf': TextExtractor.extract_from_pdf,
            'docx': TextExtractor.extract_from_docx,
            'doc': TextExtractor.extract_from_docx,
            'txt': TextExtractor.extract_from_txt,
        }
        
        extractor = extractors.get(extension)
        if not extractor:
            raise ValueError(f"Unsupported file type: {extension}")
        
        return extractor(file_data)


text_extractor = TextExtractor()
