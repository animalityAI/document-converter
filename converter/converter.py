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

class DocumentConverter:
    def __init__(self, input_path):
        self.input_path = Path(input_path)
        self.output_dir = self.input_path.parent / 'converted'
        os.makedirs(self.output_dir, exist_ok=True)

    # ... (previous conversion methods remain the same) ...

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
    for file, result in results:
        if isinstance(result, Path):
            print(f"✓ {file} -> {result}")
        else:
            print(f"✗ {file}: {result}")

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