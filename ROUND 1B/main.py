import os
import json
import fitz # PyMuPDF
from datetime import datetime
import re # For regular expressions, useful for parsing text

# Define paths as they will be inside the Docker container
INPUT_ROOT_DIR = "/app/input" # This will now be the root where collection folders live
OUTPUT_DIR = "/app/output"
INPUT_JSON_FILENAME = "input.json" # Still the name of the input file

def extract_sections_from_text(text_content, document_filename):
    """
    A more sophisticated function to extract logical sections from raw text.
    For this example, we'll use a very simple heuristic:
    - Lines that are entirely uppercase or start with a capital letter and are short might be headings.
    - We'll group subsequent text under these "headings".
    - Each page will also be considered a potential "section" if no clear headings are found.
    """
    sections = []
    current_section_title = "Introduction/General Information"
    current_section_text = []
    current_page_number = 1 # We'll update this based on page markers

    lines = text_content.split('\n')
    
    for line in lines:
        # Check for page markers
        page_match = re.match(r'---\s*Page\s*(\d+)\s*---', line.strip())
        if page_match:
            if current_section_text: # Save previous section before moving to new page
                sections.append({
                    "document": document_filename,
                    "section_title": current_section_title,
                    "page_number": current_page_number,
                    "text_content": "\n".join(current_section_text).strip()
                })
            current_page_number = int(page_match.group(1))
            current_section_title = f"Content from Page {current_page_number}" # Default if no heading
            current_section_text = []
            continue

        stripped_line = line.strip()
        if not stripped_line: # Skip empty lines
            continue

        # Simple heuristic for potential headings: short, all caps, or starts with capital and looks like a title
        # This is a *very* basic heuristic and will need refinement for real PDFs.
        if (len(stripped_line) < 80 and stripped_line.isupper() and len(stripped_line.split()) < 10) or \
           (len(stripped_line) < 80 and stripped_line[0].isupper() and stripped_line.endswith('.') == False and len(stripped_line.split()) < 10):
            if current_section_text: # Save previous section
                sections.append({
                    "document": document_filename,
                    "section_title": current_section_title,
                    "page_number": current_page_number,
                    "text_content": "\n".join(current_section_text).strip()
                })
            current_section_title = stripped_line
            current_section_text = []
        else:
            current_section_text.append(stripped_line)
    
    # Add the last section
    if current_section_text:
        sections.append({
            "document": document_filename,
            "section_title": current_section_title,
            "page_number": current_page_number,
            "text_content": "\n".join(current_section_text).strip()
        })
    
    return sections

def rank_and_filter_sections(sections, job_to_be_done_task, persona_role):
    """
    Ranks sections based on relevance to the job_to_be_done and persona.
    Optimized for HR professional and form management documents.
    """
    ranked_sections = []
    
    job_keywords = job_to_be_done_task.lower().split()
    persona_keywords = persona_role.lower().split()
    
    # General relevant terms for HR and form management
    general_keywords = ["form", "forms", "fillable", "onboarding", "compliance", "signature", 
                        "e-signature", "sign", "request", "create", "manage", "edit", 
                        "convert", "export", "share", "pdf", "document", "digital", 
                        "workflow", "template", "review", "privacy", "security", "ai",
                        "human resources", "hr"]

    all_keywords = list(set(job_keywords + persona_keywords + general_keywords))

    for section in sections:
        score = 0
        section_text_lower = section.get("text_content", "").lower()
        section_title_lower = section.get("section_title", "").lower()

        # Score based on keyword presence
        for keyword in all_keywords:
            if keyword in section_title_lower:
                score += 10 # Higher score for title matches
            if keyword in section_text_lower:
                score += 2 # Score for text matches

        doc_name_lower = section["document"].lower()

        # Dynamic boosting based on document content/title strongly related to HR/forms
        if "fill and sign" in doc_name_lower or "request e-signatures" in doc_name_lower:
            score += 40 # Highest boost for direct form/signature relevance
        elif "create and convert" in doc_name_lower or "edit" in doc_name_lower:
            score += 30 # High boost for creation/editing tools
        elif "generative ai" in doc_name_lower:
            score += 20 # Moderate boost for AI tools
        elif "share" in doc_name_lower or "export" in doc_name_lower:
            score += 15 # Boost for related workflows
        elif "test your acrobat" in doc_name_lower or "pdf sharing checklist" in doc_name_lower:
            score += 10 # Boost for general Acrobat/PDF tips

        # Additional boosts for section titles indicating key topics
        if "form" in section_title_lower or "signature" in section_title_lower or "onboarding" in section_title_lower:
            score += 15
        if "compliance" in section_title_lower or "security" in section_title_lower or "privacy" in section_title_lower:
            score += 10


        section["relevance_score"] = score
        ranked_sections.append(section)

    ranked_sections.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    final_extracted_sections = []
    # Take top 10 relevant sections, only if score is positive
    for i, sec in enumerate(ranked_sections):
        if sec["relevance_score"] > 0 and i < 10:
            final_extracted_sections.append({
                "document": sec["document"],
                "section_title": sec["section_title"],
                "importance_rank": i + 1,
                "page_number": sec["page_number"]
            })
    
    return final_extracted_sections, ranked_sections # Return both for potential subsection analysis

def refine_subsection_text(section_text, job_to_be_done_task):
    """
    Refines section text based on the job_to_be_done, making it cleaner and
    more readable by removing extraneous newlines and ensuring proper stripping.
    """
    # 1. Handle ligatures (like \ufb00 for 'ff')
    cleaned_text = section_text.replace('\ufb00', 'ff')
    cleaned_text = cleaned_text.replace('\ufb01', 'fi') # Common fi ligature
    cleaned_text = cleaned_text.replace('\ufb02', 'fl') # Common fl ligature

    # 2. Remove bullet points (\u2022)
    cleaned_text = cleaned_text.replace('\u2022', '')

    # 3. Remove all non-ASCII characters
    cleaned_text = cleaned_text.encode('ascii', 'ignore').decode('ascii')

    # Aggressively replace multiple newlines with a single space and strip overall
    # This helps in creating cleaner "sentences" before splitting
    cleaned_text = re.sub(r'\s*\n\s*', ' ', cleaned_text).strip()
    
    sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    relevant_sentences = []
    task_keywords = job_to_be_done_task.lower().split()

    # Enhanced keyword check for sentence relevance related to HR/Forms
    extended_task_keywords = list(set(task_keywords + ["form", "fillable", "signature", "e-signature", "onboarding", "compliance", "create", "manage", "edit", "pdf", "document"]))


    for sentence in sentences:
        stripped_sentence = sentence.strip() # Ensure each individual sentence is stripped
        if any(keyword in stripped_sentence.lower() for keyword in extended_task_keywords):
            relevant_sentences.append(stripped_sentence)
    
    if relevant_sentences:
        refined_text = " ".join(relevant_sentences)
        refined_text = refined_text.strip() # Final strip to catch any leading/trailing spaces
        if len(refined_text) > 500: # Truncate if too long
            refined_text = refined_text[:497] + "..."
        return refined_text
    else:
        # Fallback if no relevant sentences found, ensure it's also stripped
        if len(cleaned_text) > 500:
            return cleaned_text[:497] + "..."
        return cleaned_text.strip()


def run_document_analysis():
    print(f"[{os.getenv('HOSTNAME')}] Starting document analysis...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get the collection name from an environment variable
    collection_name = os.getenv('COLLECTION_TO_PROCESS')
    if not collection_name:
        print(f"[{os.getenv('HOSTNAME')}] ERROR: Please specify the collection to process using the 'COLLECTION_TO_PROCESS' environment variable.")
        print(f"[{os.getenv('HOSTNAME')}] Example: docker run -e COLLECTION_TO_PROCESS=collection1 ...")
        return

    # input.json path is now inside the collection folder
    input_json_path = os.path.join(INPUT_ROOT_DIR, collection_name, INPUT_JSON_FILENAME)
    
    if not os.path.exists(input_json_path):
        print(f"[{os.getenv('HOSTNAME')}] ERROR: {INPUT_JSON_FILENAME} not found at {input_json_path}. Please ensure it's in your collection folder.")
        return

    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        print(f"[{os.getenv('HOSTNAME')}] Successfully loaded {INPUT_JSON_FILENAME} from {collection_name} folder.")
    except json.JSONDecodeError as e:
        print(f"[{os.getenv('HOSTNAME')}] ERROR: Could not parse {INPUT_JSON_FILENAME} in {collection_name} folder: {e}")
        return

    persona_role = input_data.get("persona", {}).get("role", "N/A")
    job_task = input_data.get("job_to_be_done", {}).get("task", "N/A")
    documents_info = input_data.get("documents", [])
    
    # Set output filename based on collection name
    output_json_filename = f"{collection_name}_output.json"

    print(f"[{os.getenv('HOSTNAME')}] Persona Role: {persona_role}")
    print(f"[{os.getenv('HOSTNAME')}] Job to be done Task: {job_task}")
    print(f"[{os.getenv('HOSTNAME')}] Processing collection: {collection_name}")
    print(f"[{os.getenv('HOSTNAME')}] Output filename: {output_json_filename}")

    print(f"[{os.getenv('HOSTNAME')}] --- Extracting Text and Identifying Sections ---")
    all_raw_sections = [] # To store all sections with their raw text
    
    for doc_info in documents_info:
        filename = doc_info.get("filename")
        if not filename:
            continue

        # Construct doc_path within the specific collection folder
        doc_path = os.path.join(INPUT_ROOT_DIR, collection_name, filename)

        if not os.path.exists(doc_path):
            print(f"[{os.getenv('HOSTNAME')}] WARNING: Document '{filename}' not found at '{doc_path}'. Skipping.")
            continue

        try:
            doc_full_text = []
            doc = fitz.open(doc_path)
            print(f"[{os.getenv('HOSTNAME')}] Reading PDF: {filename} (Pages: {doc.page_count})")
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                doc_full_text.append(f"--- Page {page_num + 1} ---\n{text}") # Add page marker
            doc.close()
            
            # Extract sections from the full text of the document
            sections_from_doc = extract_sections_from_text("\n".join(doc_full_text), filename)
            all_raw_sections.extend(sections_from_doc)

        except Exception as e:
            print(f"[{os.getenv('HOSTNAME')}] ERROR processing {filename}: {e}")

    print(f"[{os.getenv('HOSTNAME')}] --- Section Identification Complete. Ranking Sections ---")
    
    # Pass persona_role to the ranking function
    final_extracted_sections_output, ranked_sections_with_text = rank_and_filter_sections(all_raw_sections, job_task, persona_role)

    print(f"[{os.getenv('HOSTNAME')}] --- Generating Subsection Analysis ---")
    subsection_analysis_output = []
    # Take the top 5 most important sections from ranked_sections_with_text for detailed analysis
    for i, section in enumerate(ranked_sections_with_text):
        if i < 5 and section["relevance_score"] > 0: # Ensure positive score for subsection analysis
            refined_text = refine_subsection_text(section["text_content"], job_task)
            subsection_analysis_output.append({
                "document": section["document"],
                "refined_text": refined_text,
                "page_number": section["page_number"]
            })
        elif section["relevance_score"] <= 0: # Stop if relevance drops to zero or negative
            break
        else:
            break # Stop after top 5 for efficiency in this example

    print(f"[{os.getenv('HOSTNAME')}] --- Creating Output JSON ---")
    output_data = {
        "metadata": {
            "input_documents": [d.get("filename") for d in documents_info],
            "persona": persona_role,
            "job_to_be_done": job_task,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": final_extracted_sections_output,
        "subsection_analysis": subsection_analysis_output
    }

    output_json_path = os.path.join(OUTPUT_DIR, output_json_filename)
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
        print(f"[{os.getenv('HOSTNAME')}] Successfully wrote output to {output_json_path}")
    except Exception as e:
        print(f"[{os.getenv('HOSTNAME')}] ERROR writing output: {e}")

    print(f"[{os.getenv('HOSTNAME')}] Document analysis finished.")


if __name__ == "__main__":
    run_document_analysis()