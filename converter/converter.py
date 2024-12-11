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
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DocumentConverter:
    def __init__(self, input_path):
        self.input_path = Path(input_path)
        self.output_dir = self.input_path.parent / 'converted'
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"Initializing converter for {input_path}")
        logging.info(f"Output directory: {self.output_dir}")

    def convert_to_epub(self):
        try:
            logging.info(f"Starting conversion of {self.input_path}")
            content = self._extract_content()
            
            if not content.strip():
                raise ValueError(f"No content extracted from {self.input_path}")
            
            logging.info("Creating EPUB book")
            book = epub.EpubBook()
            book.set_identifier(str(uuid.uuid4()))
            book.set_title(self.input_path.stem)
            book.set_language('en')
            
            logging.info("Adding metadata")
            book.add_metadata('DC', 'description', f'Converted from {self.input_path.name}')
            book.add_metadata('DC', 'creator', 'Document Converter')
            
            logging.info("Adding CSS")
            style = create_style()
            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/nav.css",
                media_type="text/css",
                content=style
            )
            book.add_item(nav_css)

            logging.info("Processing content")
            chunks = self._split_into_chapters(content)
            logging.info(f"Created {len(chunks)} chapters")
            
            chapters = []
            for i, chunk in enumerate(chunks, 1):
                logging.info(f"Processing chapter {i}")
                c = epub.EpubHtml(
                    title=f'Chapter {i}',
                    file_name=f'chapter_{i:02d}.xhtml',
                    lang='en'
                )
                c.content = self._create_chapter_html(chunk)
                c.add_item(nav_css)
                book.add_item(c)
                chapters.append(c)

            logging.info("Adding navigation")
            book.toc = [(epub.Section(f'Chapter {i+1}'), [c]) for i, c in enumerate(chapters)]
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ['nav'] + chapters

            output_path = self.output_dir / f"{self.input_path.stem}.epub"
            logging.info(f"Writing EPUB to {output_path}")
            epub.write_epub(str(output_path), book, {})
            
            logging.info("Conversion completed successfully")
            return output_path
            
        except Exception as e:
            logging.error(f"Error converting {self.input_path}: {str(e)}")
            raise

def convert_file(input_file, output_format):
    try:
        logging.info(f"Converting {input_file} to {output_format}")
        converter = DocumentConverter(input_file)
        if output_format == 'epub':
            return converter.convert_to_epub()
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    except Exception as e:
        logging.error(f"Error converting {input_file}: {str(e)}")
        return f"Error: {str(e)}"

def batch_convert(input_pattern, output_format, max_workers=4):
    files = glob.glob(input_pattern)
    if not files:
        logging.error(f"No files found matching pattern: {input_pattern}")
        print(f"No files found matching pattern: {input_pattern}")
        return

    logging.info(f"Found {len(files)} files to convert")
    print(f"Found {len(files)} files to convert")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        with tqdm(total=len(files), desc="Converting files") as pbar:
            future_to_file = {
                executor.submit(convert_file, file, output_format): file 
                for file in files
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append((file, result))
                except Exception as e:
                    results.append((file, f"Error: {str(e)}"))
                pbar.update(1)

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
    parser.add_argument('--to', choices=['epub'], required=True,
                      help='Output format')
    parser.add_argument('--workers', type=int, default=4,
                      help='Number of parallel conversions (default: 4)')
    parser.add_argument('--verbose', action='store_true',
                      help='Show detailed progress')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    batch_convert(args.input_pattern, args.to, args.workers)

if __name__ == "__main__":
    main()