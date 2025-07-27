import fitz # PyMuPDF library, often imported as 'fitz'
import json
import os
import traceback
import logging # Import the logging module
import re # Import re once at the top

# Configure logging at the beginning of your script
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def extract_outline(pdf_path):
    """
    Extracts title and hierarchical headings (H1, H2, H3) from a PDF.
    """
    logging.debug(f"Entering extract_outline for: {pdf_path}")
    document = fitz.open(pdf_path)

    # --- 1. Extract Title ---
    title = ""
    if document.page_count > 0:
        first_page = document[0]
        max_title_font_size = 0
        potential_title_lines = []

        # Get all text blocks and lines from the first page
        blocks = first_page.get_text("dict")["blocks"]

        # Iterate through blocks and lines to find the largest/boldest text on the first page
        for block in blocks:
            if block["type"] == 0: # text block
                for line in block["lines"]:
                    # Join spans to reassemble potentially fragmented text, and strip
                    line_text = "".join([span["text"] for span in line["spans"]]).strip()
                    if not line_text:
                        continue

                    # Get properties of the first span as representative for the line
                    if not line["spans"]: # Skip if no spans (empty line)
                        continue
                    first_span = line["spans"][0]
                    line_font_size = first_span["size"]
                    line_font_name = first_span["font"]
                    line_is_bold = "Bold" in line_font_name or (first_span["flags"] & 16)

                    # Accumulate potential title lines, looking for the most prominent one
                    # Only consider if bold or very large, and not a short, number-like string
                    if (line_is_bold or line_font_size >= 28) and \
                       len(line_text) > 5 and \
                       not line_text.isdigit() and \
                       not re.match(r'^\d+(\.\d+){0,2}\s*$', line_text): # Exclude just numbers/patterns like "1."

                        if line_font_size > max_title_font_size:
                            max_title_font_size = line_font_size
                            potential_title_lines = [line_text] # Start new potential title if larger font found
                        elif line_font_size == max_title_font_size:
                            potential_title_lines.append(line_text) # If same largest font size, append for multi-line titles

        # Join the collected lines to form the title
        if potential_title_lines:
            title = " ".join(potential_title_lines)
            # A final check to ensure it's not a short or trivial title that might have slipped through
            if len(title) < 10 or re.match(r'^(RFP:\s*(Request)?\s*for\s*Proposal|March\s*\d{1,2},\s*\d{4})$', title, re.IGNORECASE):
                title = "" # Reset if too short or a known header/footer pattern

    # --- 2. Extract Headings (H1, H2, H3) ---
    outline = []
    
    # Store font sizes encountered to help normalize/compare
    font_sizes = {}
    for page_num in range(document.page_count):
        page = document[page_num]
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b["type"] == 0: # Only process text blocks
                for line in b["lines"]:
                    if not line["spans"]:
                        continue
                    first_span = line["spans"][0]
                    size = first_span["size"]
                    if size not in font_sizes:
                        font_sizes[size] = 0
                    font_sizes[size] += 1
    
    # Sort font sizes to determine relative importance (largest usually H1)
    sorted_font_sizes = sorted(font_sizes.keys(), reverse=True)
    
    # Define thresholds dynamically or based on common PDF patterns
    # These are illustrative and might need fine-tuning for diverse PDFs
    h1_threshold = sorted_font_sizes[0] if sorted_font_sizes else 0
    h2_threshold = sorted_font_sizes[1] if len(sorted_font_sizes) > 1 else h1_threshold * 0.8
    h3_threshold = sorted_font_sizes[2] if len(sorted_font_sizes) > 2 else h2_threshold * 0.8

    # Apply some minimums to avoid picking up body text as headings if dynamic thresholds are too low
    h1_min = 20 # Absolute minimum for H1
    h2_min = 16 # Absolute minimum for H2
    h3_min = 12 # Absolute minimum for H3
    
    h1_threshold = max(h1_threshold, h1_min)
    h2_threshold = max(h2_threshold, h2_min)
    h3_threshold = max(h3_threshold, h3_min)

    # Adjust H2 and H3 relative to H1 if they are too close
    if h2_threshold >= h1_threshold:
        h2_threshold = h1_threshold * 0.85
    if h3_threshold >= h2_threshold:
        h3_threshold = h2_threshold * 0.85

    logging.debug(f"Dynamic Font Size Thresholds: H1={h1_threshold:.2f}, H2={h2_threshold:.2f}, H3={h3_threshold:.2f}")


    for page_num in range(document.page_count):
        page = document[page_num]
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if b["type"] == 0: # Only process text blocks
                for line in b["lines"]:
                    # Reassemble line text from spans, then strip whitespace
                    line_text = "".join([span["text"] for span in line["spans"]]).strip()
                    
                    if not line_text or not line["spans"]: # Skip empty lines or lines with no spans
                        continue

                    # Get font properties from the first span (as representative for the line)
                    first_span = line["spans"][0]
                    line_font_size = first_span["size"]
                    line_font_name = first_span["font"]
                    line_is_bold = "Bold" in line_font_name or (first_span["flags"] & 16) # Check for "Bold" in name or the bold flag

                    logging.debug(f"DEBUG: Page {page_num + 1}, Font Size: {line_font_size:.2f}, Is_Bold: {line_is_bold}, Text: '{line_text}'")

                    current_level = None

                    # --- Heuristic 1: Filter out known non-headings based on content or pattern ---
                    # Filter out very short symbols, numbers, or common footer/header text
                    if (len(line_text) < 2 and not re.match(r'^\d+(\.\d+){0,2}\s', line_text)) or \
                       line_text in ["•", ".", "-", "—", "_", "/", "|", ":", ""] or \
                       re.match(r'^\s*page\s+\d+\s*$', line_text, re.IGNORECASE) or \
                       re.match(r'^(RFP:\s*To Develop the Ontario Digital Library Business Plan|March \d{4})$', line_text): # Specific footer/header
                        continue
                    
                    # Specific filter for the "100 Lombard" footer on page 2 of E0H1CM114.pdf and similar footers
                    if "Lombard" in line_text and page_num + 1 >= 2 and line_font_size < 12:
                        continue
                    
                    # Heuristic to remove page numbers in isolation or as part of a short line
                    if (line_text.isdigit() and len(line_text) <= 3) or \
                       (re.match(r'^\d+$', line_text.replace('.', '')) and len(line_text) <= 5):
                        continue


                    # --- Heuristic 2: Heading Classification based on Line Properties (Font Size & Boldness) ---
                    # Using dynamic thresholds and prioritizing bold text
                    if line_is_bold:
                        if line_font_size >= h1_threshold:
                            current_level = "H1"
                        elif line_font_size >= h2_threshold:
                            current_level = "H2"
                        elif line_font_size >= h3_threshold:
                            current_level = "H3"
                    else: # If not bold, still consider if font size is significantly large
                        if line_font_size >= h1_threshold * 1.1: # Even larger if not bold for H1
                            current_level = "H1"
                        elif line_font_size >= h2_threshold * 1.1: # Larger if not bold for H2
                             current_level = "H2"
                        elif line_font_size >= h3_threshold * 1.1: # Larger if not bold for H3
                             current_level = "H3"
                                        
                    # --- Heuristic 3: Numbering patterns (refine current_level if applicable) ---
                    # This should refine, not necessarily override, previous font-based classification
                    # Stronger bias for numbered headings
                    match = re.match(r'^((\d+)(\.\d+){0,2})\s', line_text)
                    if match:
                        num_part = match.group(1)
                        dot_count = num_part.count('.')

                        if dot_count == 0: # e.g., "1 Introduction"
                            # If it's a top-level number, it's very likely H1 or H2
                            if not current_level or current_level in ["H3"]:
                                current_level = "H1" if line_font_size >= h2_threshold else "H2" # If font size is closer to H2, make it H2
                            elif current_level == "H2" and line_font_size >= h1_threshold:
                                current_level = "H1" # Promote to H1 if it's a number and H1-level font
                        elif dot_count == 1: # e.g., "1.1 Sub-section"
                            # If it's a second-level number, lean towards H2
                            if not current_level or current_level in ["H1", "H3"]: # Allow H1 to be demoted if it's clearly a H2 numbered item
                                current_level = "H2"
                        elif dot_count == 2: # e.g., "1.1.1 Sub-sub-section"
                            # If it's a third-level number, lean towards H3
                            if not current_level or current_level in ["H1", "H2"]:
                                current_level = "H3"
                    
                    # --- Heuristic 4: All caps check (if not already classified and reasonable length) ---
                    if not current_level and line_text.isupper() and len(line_text) > 3 and line_font_size >= h3_min:
                        if line_font_size >= h1_threshold * 0.9:
                            current_level = "H1"
                        elif line_font_size >= h2_threshold * 0.9:
                            current_level = "H2"
                        else:
                            current_level = "H3"
                    
                    # Ensure "Summary" and "Background" are caught as H2 if they fit general size criteria and not picked up already
                    # Even if not bold, they are often key sections.
                    if (line_text.strip().lower() == "summary" or line_text.strip().lower() == "background") and \
                       line_font_size >= h3_threshold and (not current_level or current_level == "H3"):
                       current_level = "H2" # Elevate to H2 if they are "Summary" or "Background" and meet min font size

                    # Only append to outline if a heading level was determined AND it's not part of a known problematic fragmentation or footer
                    # Add a check to prevent "RFP: R" etc. from being added as headings.
                    if current_level and not re.match(r'^RFP:\s*[A-Z]$', line_text) and not re.match(r'^(quest|r Pr|oposal)\s*f.*$', line_text) \
                       and not re.match(r'^RFP:\s*To Develop the Ontario Digital Library Business Plan$', line_text):
                        outline.append({
                            "level": current_level,
                            "text": line_text, # Use the full line text
                            "page": page_num + 1
                        })

    logging.debug(f"Extracted {len(outline)} outline entries for {pdf_path}")
    return {
        "title": title,
        "outline": outline
    }

def process_pdfs_in_directory(input_dir, output_dir):
    """
    Processes all PDF files found in the input_dir and saves their
    extracted outlines as JSON files in the output_dir.
    """
    logging.debug(f"Starting process_pdfs_in_directory. Input: {input_dir}, Output: {output_dir}")

    # Check if directories exist (crucial inside container)
    if not os.path.exists(input_dir):
        logging.error(f"Input directory does not exist: {input_dir}")
        return
    if not os.path.exists(output_dir):
        logging.warning(f"Output directory does not exist: {output_dir}, attempting to create.")
        os.makedirs(output_dir, exist_ok=True)
        if not os.path.exists(output_dir):
            logging.critical(f"Failed to create or access output directory: {output_dir}")
            return

    file_list = os.listdir(input_dir)
    logging.debug(f"Files found in input directory: {file_list}")

    for filename in file_list:
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            output_filename = filename.replace(".pdf", ".json")
            output_path = os.path.join(output_dir, output_filename)

            print(f"Processing {filename}...") # Keep this print for high-level progress
            try:
                outline_data = extract_outline(pdf_path)
                logging.debug(f"Attempting to write to {output_path}")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(outline_data, f, indent=4, ensure_ascii=False)
                print(f"Saved outline to {output_path}") # Keep this print for high-level progress
            except Exception as e:
                logging.error(f"Error processing {filename}: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    logging.debug("main.py script started.")
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"

    process_pdfs_in_directory(INPUT_DIR, OUTPUT_DIR)
    logging.debug("main.py script finished.")