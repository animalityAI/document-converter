import os
from pathlib import Path
import ebooklib
from ebooklib import epub
from pypdf import PdfReader
from docx import Document
import mammoth
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from .utils.formatting import apply_formatting, create_style

class DocumentConverter:
    def __init__(self, input_path, output_dir=None):
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir) if output_dir else self.input_path.parent / 'converted'
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def batch_convert(input_dir, output_format, output_dir=None, max_workers=4):
        """
        Convert all supported files in a directory.
        """
        input_dir = Path(input_dir)
        if not output_dir:
            output_dir = input_dir / 'converted'
        
        # Get all supported files
        supported_extensions = {'.pdf', '.epub', '.docx', '.txt'}
        files_to_convert = [
            f for f in input_dir.rglob("*") 
            if f.suffix.lower() in supported_extensions
        ]
        
        if not files_to_convert:
            print(f"No supported files found in {input_dir}")
            return
        
        # Create progress bar
        pbar = tqdm(total=len(files_to_convert), desc="Converting files")
        
        def convert_file(file_path):
            try:
                converter = DocumentConverter(file_path, output_dir)
                if output_format == 'txt':
                    converter.convert_to_txt()
                elif output_format == 'epub':
                    converter.convert_to_epub()
                elif output_format == 'mobi':
                    converter.convert_to_mobi()
                pbar.update(1)
                return None
            except Exception as e:
                return (file_path, str(e))
        
        # Convert files in parallel
        failed_conversions = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(convert_file, files_to_convert)
            for result in results:
                if result is not None:
                    failed_conversions.append(result)
        
        pbar.close()
        
        # Report results
        total = len(files_to_convert)
        success = total - len(failed_conversions)
        print(f"\nConversion complete!")
        print(f"Successfully converted: {success}/{total} files")
        
        if failed_conversions:
            print("\nFailed conversions:")
            for file_path, error in failed_conversions:
                print(f"- {file_path.name}: {error}")

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
            if item.