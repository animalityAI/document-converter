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

def convert_file(input_file, output_format):
    """Convert a single file and return the result"""
    try:
        converter = DocumentConverter(input_file)
        if output_format == 'txt':
            return converter.convert_to_txt()
        elif output_format == 'epub':
            return converter.convert_to_epub()
        elif output_format == 'mobi':
            return converter.convert_to_mobi()
    except Exception as e:
        return f"Error converting {input_file}: {str(e)}"

def batch_convert(input_pattern, output_format, max_workers=4):
    """Convert multiple files matching the input pattern"""
    # Get list of files matching the pattern
    files = glob.glob(input_pattern)
    
    if not files:
        print(f"No files found matching pattern: {input_pattern}")
        return

    print(f"Found {len(files)} files to convert")
    
    # Convert files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a progress bar
        with tqdm(total=len(files), desc="Converting files") as pbar:
            # Submit all conversion tasks
            future_to_file = {
                executor.submit(convert_file, file, output_format): file 
                for file in files
            }
            
            # Process results as they complete
            results = []
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append((file, result))
                except Exception as e:
                    results.append((file, f"Error: {str(e)}"))
                pbar.update(1)
    
    # Print summary
    print("\nConversion Summary:")
    successful = 0
    failed = 0
    for file, result in results:
        if isinstance(result, Path):
            print(f"✓ {file} -> {result}")
            successful += 1
        else:
            print(f"✗ {file}: {result}")
            failed += 1
    
    print(f"\nTotal: {len(files)} files")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert documents between formats')
    parser.add_argument('input_pattern', help='Input file(s) pattern (e.g., "*.pdf", "docs/*.docx")')
    parser.add_argument('--to', choices=['txt', 'epub', 'mobi'], 
                      required=True, help='Output format')
    parser.add_argument('--workers', type=int, default=4,
                      help='Number of parallel conversions (default: 4)')
    
    args = parser.parse_args()
    
    batch_convert(args.input_pattern, args.to, args.workers)

if __name__ == "__main__":
    main()