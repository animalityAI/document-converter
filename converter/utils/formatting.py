def create_style():
    return '''
        @namespace epub "http://www.idpf.org/2007/ops";

        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 5% 8%;
            text-align: justify;
            font-size: 1em;
        }

        h1, h2, h3 {
            text-align: left;
            line-height: 1.2;
            margin: 1em 0 0.5em;
            page-break-after: avoid;
        }

        h1 { font-size: 1.5em; }
        h2 { font-size: 1.3em; }
        h3 { font-size: 1.1em; }

        p {
            margin: 0.5em 0;
            text-indent: 1em;
        }

        .chapter {
            break-before: page;
        }
    '''

def _process_content(content):
    """Process content to create better HTML structure"""
    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    
    formatted_paragraphs = []
    current_section = []
    
    for para in paragraphs:
        if not para.strip():
            continue
            
        # Basic heuristics for headers
        para = para.strip()
        if len(para) < 100 and para.isupper():
            # If we have accumulated paragraphs, add them as a section
            if current_section:
                formatted_paragraphs.extend(current_section)
                current_section = []
            formatted_paragraphs.append(f"<h1>{para.title()}</h1>")
        elif len(para) < 200 and para.endswith(':'):
            # Potential subheading
            if current_section:
                formatted_paragraphs.extend(current_section)
                current_section = []
            formatted_paragraphs.append(f"<h2>{para}</h2>")
        else:
            # Regular paragraph
            current_section.append(f"<p>{para}</p>")
    
    # Add any remaining paragraphs
    if current_section:
        formatted_paragraphs.extend(current_section)
    
    return '\n'.join(formatted_paragraphs)

def apply_formatting(content):
    """Apply formatting to content and wrap in proper EPUB HTML structure"""
    processed_content = _process_content(content)
    return processed_content