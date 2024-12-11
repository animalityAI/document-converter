# Document Converter

A Python tool for converting documents between different formats while preserving formatting.

## Features

- Convert between PDF, EPUB, DOCX, and TXT formats
- Preserve text formatting
- Support for various document structures
- Command-line interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/animalityAI/document-converter.git
cd document-converter
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Calibre (required for MOBI conversion):
- Download from: https://calibre-ebook.com/download

## Usage

```bash
# Convert PDF to EPUB
python -m converter input.pdf --to epub

# Convert DOCX to MOBI
python -m converter document.docx --to mobi

# Convert EPUB to TXT
python -m converter book.epub --to txt
```

## License

MIT