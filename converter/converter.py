import os
from pathlib import Path
import ebooklib
from ebooklib import epub
from pypdf import PdfReader
from docx import Document
import mammoth
from bs4 import BeautifulSoup
from .utils.formatting import apply_formatting, create_style

class DocumentConverter:
    def __init__(self, input_path):
        self.input_path = Path(input_path)
        self.output_dir = self.input_path.parent / 'converted'
        os.makedirs(self.output_dir, exist_ok=True)

    def convert_to_txt(self):
        content = self._extract_content()
        output_path = self.output_dir / f"{self.input_path.stem}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_path

    def convert_to_epub(self):
        content = self._extract_content()
        
        # Create epub book
        book = epub.EpubBook()
        book.set_identifier(f'id_{self.input_path.stem}')
        book.set_title(self.input_path.stem)
        book.set_language('en')

        # Add CSS
        style = create_style()
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)

        # Create chapter
        chapter = epub.EpubHtml(title='Chapter 1', file_name='chap_01.xhtml')
        chapter.content = apply_formatting(content)
        
        book.add_item(chapter)
        book.spine = ['nav', chapter]
        
        output_path = self.output_dir / f"{self.input_path.stem}.epub"
        epub.write_epub(str(output_path), book)
        return output_path

    def convert_to_mobi(self):
        epub_path = self.convert_to_epub()
        output_path = self.output_dir / f"{self.input_path.stem}.mobi"
        
        os.system(f'ebook-convert "{epub_path}" "{output_path}"')
        return output_path

    def _extract_content(self):
        suffix = self.input_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._extract_from_pdf()
        elif suffix == '.epub':
            return self._extract_from_epub()
        elif suffix == '.docx':
            return self._extract_from_docx()
        elif suffix == '.txt':
            return self._extract_from_txt()
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _extract_from_pdf(self):
        reader = PdfReader(self.input_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def _extract_from_epub(self):
        book = epub.read_epub(str(self.input_path))
        text = ""
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + "\n"
        return text

    def _extract_from_docx(self):
        result = mammoth.convert_to_html(self.input_path)
        soup = BeautifulSoup(result.value, 'html.parser')
        return soup.get_text()

    def _extract_from_txt(self):
        with open(self.input_path, 'r', encoding='utf-8') as f:
            return f.read()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert documents between formats')
    parser.add_argument('input_file', help='Path to input file')
    parser.add_argument('--to', choices=['txt', 'epub', 'mobi'], 
                      required=True, help='Output format')
    
    args = parser.parse_args()
    
    converter = DocumentConverter(args.input_file)
    
    if args.to == 'txt':
        output_path = converter.convert_to_txt()
    elif args.to == 'epub':
        output_path = converter.convert_to_epub()
    elif args.to == 'mobi':
        output_path = converter.convert_to_mobi()
        
    print(f"Converted file saved to: {output_path}")

if __name__ == "__main__":
    main()