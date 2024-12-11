import os
from pathlib import Path
import ebooklib
from ebooklib import epub
from pypdf import PdfReader
from docx import Document
import mammoth
from bs4 import BeautifulSoup
from .utils.formatting import apply_formatting, create_style
import glob
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import concurrent.futures
import uuid

class DocumentConverter:
    def __init__(self, input_path):
        self.input_path = Path(input_path)
        self.output_dir = self.input_path.parent / 'converted'
        os.makedirs(self.output_dir, exist_ok=True)

    def convert_to_epub(self):
        content = self._extract_content()
        
        # Create epub book with proper metadata
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(self.input_path.stem)
        book.set_language('en')
        
        # Add more metadata
        book.add_metadata('DC', 'description', f'Converted from {self.input_path.name}')
        book.add_metadata('DC', 'creator', 'Document Converter')
        book.add_metadata('DC', 'publisher', 'Document Converter')
        book.add_metadata('DC', 'source', str(self.input_path))

        # Add CSS
        style = create_style()
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)

        # Split content into chapters if it's long
        chunks = self._split_into_chapters(content)
        chapters = []
        
        for i, chunk in enumerate(chunks, 1):
            # Create chapter
            c = epub.EpubHtml(title=f'Chapter {i}', 
                             file_name=f'chapter_{i:02d}.xhtml',
                             lang='en')
            c.content = self._create_chapter_html(chunk)
            c.add_item(nav_css)
            
            book.add_item(c)
            chapters.append(c)

        # Add navigation files
        book.toc = [(epub.Section(f'Chapter {i+1}'), [c]) for i, c in enumerate(chapters)]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Create spine
        book.spine = ['nav'] + chapters
        
        output_path = self.output_dir / f"{self.input_path.stem}.epub"
        epub.write_epub(str(output_path), book, {})
        return output_path

    def _create_chapter_html(self, content):
        return f'''
        <?xml version="1.0" encoding="UTF-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
        <head>
            <title>{self.input_path.stem}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body>
            {content}
        </body>
        </html>
        '''

    def _split_into_chapters(self, content):
        # Split content into manageable chunks (around 50KB each)
        MAX_CHUNK_SIZE = 50000
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > MAX_CHUNK_SIZE and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(para)
            current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [content]

    def _extract_from_pdf(self):
        reader = PdfReader(self.input_path)
        text = []
        
        for page in reader.pages:
            content = page.extract_text()
            # Clean up common PDF conversion issues
            content = content.replace('\x0c', '\n\n')  # Form feed
            content = content.replace('\r\n', '\n')    # Windows line endings
            content = '\n'.join(line.strip() for line in content.split('\n'))
            text.append(content)

        return '\n\n'.join(text)

    # ... (rest of the methods remain the same) ...
