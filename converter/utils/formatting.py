def create_style():
    return '''
        body {
            font-family: Arial, sans-serif;
            margin: 5%;
            text-align: justify;
        }
        h1, h2, h3 { 
            color: #333;
            margin-top: 1em;
        }
        .bold { font-weight: bold; }
        .italic { font-style: italic; }
        .underline { text-decoration: underline; }
        .center { text-align: center; }
        .right { text-align: right; }
        .indent { text-indent: 2em; }
    '''

def apply_formatting(content):
    formatted_content = f'''
    <html>
        <head>
            <link rel="stylesheet" href="style/nav.css"/>
        </head>
        <body>
            {_process_content(content)}
        </body>
    </html>
    '''
    return formatted_content

def _process_content(content):
    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    
    formatted_paragraphs = []
    for para in paragraphs:
        if not para.strip():
            continue
            
        # Basic heuristic for headers
        if len(para.strip()) < 100 and para.isupper():
            formatted_paragraphs.append(f"<h1>{para}</h1>")
        else:
            formatted_paragraphs.append(f"<p>{para}</p>")
    
    return '\n'.join(formatted_paragraphs)