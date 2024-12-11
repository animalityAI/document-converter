import os
from pathlib import Path
from pypdf import PdfReader
import mammoth
from bs4 import BeautifulSoup
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

    def _extract_content(self):
        suffix = self.input_path.suffix.lower()
        if suffix == '.pdf':
            return self._extract_from_pdf()
        elif suffix == '.docx':
            return self._extract_from_docx_alternative()
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

    def _extract_from_docx_alternative(self):
        try:
            with open(self.input_path, "rb") as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                return result.value
        except Exception as e:
            raise ValueError(f"Error extracting text from DOCX: {e}")

    def _extract_from_txt(self):
        with open(self.input_path, 'r', encoding='utf-8') as f:
            return f.read()

def process_file(file_path, output_format):
    try:
        converter = DocumentConverter(file_path)
        if output_format == 'txt':
            output_path = converter.convert_to_txt()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        return f"\u2713 Success: {file_path} -> {output_path}"
    except Exception as e:
        return f"\u2717 Failed: {file_path} -> {e}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert documents between formats in parallel.')
    parser.add_argument('input_files', nargs='+', help='Paths to input files (supports wildcards).')
    parser.add_argument('--to', choices=['txt'], required=True, help='Output format')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers (default: 4).')

    try:
        args = parser.parse_args()
    except SystemExit as e:
        print("Error: Missing or incorrect arguments. Please specify input files and the '--to' option.")
        print("Example: python script.py 'input/*.pdf' --to txt")
        return

    input_files = []
    for pattern in args.input_files:
        input_files.extend(Path().glob(pattern))

    if not input_files:
        print("No files matched the input patterns.")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(tqdm(executor.map(lambda f: process_file(f, args.to), input_files), total=len(input_files)))

    for result in results:
        print(result)

if __name__ == "__main__":
    main()