from bs4 import BeautifulSoup
import trafilatura
import re
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_and_convert(filepath):
    with open(filepath, 'r') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')

    for script in soup(["script", "style"]):
        script.extract()

    for element in soup(['nav', 'footer', 'aside']):
        element.decompose()

    for element in soup.find_all(class_=['ad', 'advertisement', 'tracking']):
        element.decompose()

    markdown = trafilatura.extract(
        str(soup),
        output_format='markdown'
    )

    return markdown

def clean_whitespaces_markdown(markdown):
    """Clean up markdown spacing"""
    # Remove multiple blank lines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    # Remove trailing whitespace
    markdown = '\n'.join(line.rstrip() for line in markdown.split('\n'))

    # Ensure single newline at end
    markdown = markdown.rstrip() + '\n'

    return markdown

def validate_markdown(markdown):
    """Validate markdown quality"""
    issues = []

    # Check for HTML remnants
    if '<' in markdown and '>' in markdown:
        issues.append("HTML tags detected")

    # Check for broken links
    if '[' in markdown and ']()' in markdown:
        issues.append("Empty link detected")

    # Check for excessive code blocks
    code_block_count = markdown.count('``')
    if code_block_count % 2 != 0:
        issues.append("Unclosed code block")

    return len(issues) == 0, issues


def process_file(html_path):
    """Process single HTML file"""
    try:
        markdown = clean_and_convert(html_path)
        # html = Path(html_path).read_text(encoding='utf-8')
        # markdown = trafilatura.extract(
        #     html,
        #     output_format='markdown',
        #     include_links=True,
        #     include_images=False
        # )

        if markdown:
            # Normalize
            markdown = clean_whitespaces_markdown(markdown)

            # Validate
            is_valid, issues = validate_markdown(markdown)
            if not is_valid:
                logger.warning(f"{html_path}: {', '.join(issues)}")

            # Save
            output_path = Path(str(html_path).replace('.html', '.md'))
            output_path.write_text(markdown, encoding='utf-8')

            return True

        return False

    except Exception as e:
        logger.error(f"Error processing {html_path}: {e}")
        return False
    
def batch_convert(input_dir, max_workers=4):
    """Convert all HTML files in directory"""
    html_files = list(Path(input_dir).rglob('*.html'))
    logger.info(f"Found {len(html_files)} HTML files")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, html_files))

    success_count = sum(results)
    logger.info(f"Successfully converted {success_count}/{len(html_files)} files")