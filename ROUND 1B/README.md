# 📄 Adobe Hackathon 2025 – Round 1B: Persona-Driven Document Intelligence

## 🌟 Overview
This solution analyzes **multiple PDFs** and extracts **relevant sections** tailored to a given **persona** and their **job-to-be-done**.  
The system prioritizes sections using **TF-IDF similarity ranking** and outputs a **structured JSON** with metadata, extracted sections, and refined content analysis.

---

## 🧩 Key Features
- **Persona-based content filtering** – Ranks PDF sections by relevance to persona + task
- **Importance Ranking** – Assigns priority scores to extracted sections
- **Multi-document Support** – Handles 3–10 PDFs per run
- **Offline & Lightweight** – CPU-only execution, ≤1GB model size
- **Structured Output** – JSON format with metadata, extracted sections, and analysis

---

## 📂 Project Structure
```

ROUND 1B/
├── Dockerfile            #Docker configuration
├── main.py               # Main Python script
├── requirements.txt      # Python dependencies
├── README.md             #This is the new README file for Round 1B
├── input/                #Contains input PDF(s)
│   ├── collection1/
│   │   ├── input.json
│   │   ├── South of France - Cities.pdf
│   │   ├── South of France - Cuisine.pdf
│   │   ├── South of France - History.pdf
│   │   ├── South of France - Restaurants and Hotels.pdf
│   │   ├── South of France - Things to Do.pdf
│   │   ├── South of France - Tips and Tricks.pdf
│   │   └── South of France - Traditions and Culture.pdf
│   ├── collection2/
│   │   ├── input.json
│   │   ├── Breakfast Ideas.pdf
│   │   ├── Dinner Ideas - Mains_1.pdf
│   │   ├── Dinner Ideas - Mains_2.pdf
│   │   ├── Dinner Ideas - Mains_3.pdf
│   │   ├── Dinner Ideas - Sides_1.pdf
│   │   ├── Dinner Ideas - Sides_2.pdf
│   │   ├── Dinner Ideas - Sides_3.pdf
│   │   ├── Dinner Ideas - Sides_4.pdf
│   │   └── Lunch Ideas.pdf
│   └── collection3/
│       ├── input.json
│       ├── Learn Acrobat - Create and Convert_1.pdf
│       ├── Learn Acrobat - Create and Convert_2.pdf
│       ├── Learn Acrobat - Edit_1.pdf
│       ├── Learn Acrobat - Edit_2.pdf
│       ├── Learn Acrobat - Export_1.pdf
│       ├── Learn Acrobat - Export_2.pdf
│       ├── Learn Acrobat - Fill and Sign.pdf
│       ├── Learn Acrobat - Generative AI_1.pdf
│       ├── Learn Acrobat - Generative AI_2.pdf
│       ├── Learn Acrobat - Request e-signatures_1.pdf
│       ├── Learn Acrobat - Request e-signatures_2.pdf
│       ├── Learn Acrobat - Share_1.pdf
│       ├── Learn Acrobat - Share_2.pdf
│       ├── Test Your Acrobat Exporting Skills.pdf
│       └── The Ultimate PDF Sharing Checklist.pdf
└── output/
    ├── collection1_output.json   (Generated after running Docker for collection1)
    ├── collection2_output.json   (Generated after running Docker for collection2)
    └── collection3_output.json   (Generated after running Docker for collection3)

````

---

## 📝 Input Format
**File:** `input.json`
```json
{
  "challenge_info": {
    "challenge_id": "round_1b_002",
    "test_case_name": "travel_planner_case"
  },
  "documents": [
    {"filename": "South of France - Cities.pdf", "title": "Cities"},
    {"filename": "South of France - Cuisine.pdf", "title": "Cuisine"}
  ],
  "persona": {
    "role": "Travel Planner"
  },
  "job_to_be_done": {
    "task": "Plan a trip of 4 days for a group of 10 college friends."
  }
}
````

---

## 📝 Output Format

**File:** `collection1_output.json`

```json
{
  "metadata": {
    "input_documents": ["South of France - Cities.pdf", "South of France - Cuisine.pdf"],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends.",
    "processing_timestamp": "2025-07-10T15:31:22.632389"
  },
  "extracted_sections": [
    {
      "document": "South of France - Cities.pdf",
      "section_title": "Comprehensive Guide to Major Cities in the South of France",
      "importance_rank": 1,
      "page_number": 1
    }
  ],
  "subsection_analysis": [
    {
      "document": "South of France - Cities.pdf",
      "refined_text": "Detailed content extracted from the relevant section...",
      "page_number": 1
    }
  ]
}
```

---

````
Similarly for collection2 and collection3

---


```

---

## ⚙️ Installation & Execution

### 1️⃣ Build Docker Image

Run this command inside the project folder:

```bash
docker build --platform linux/amd64 -t persona-doc-processor .
```

### 2️⃣ Run the Container

#### **Windows PowerShell (VS Code default)**

```powershell
docker run --rm -v "${PWD}/input:/app/input:ro" -v "${PWD}/output:/app/output" --network none persona-doc-processor
```

#### **Windows CMD**

```cmd
docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output:/app/output" --network none persona-doc-processor
```

#### **Linux / Mac**

```bash
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none persona-doc-processor
```

---

## 🏃 Execution Flow

1. Place **PDF files** and `challenge1b_input.json` inside the `input/` folder
2. Run the Docker container using the commands above
3. Processed output (`challenge1b_output.json`) will be available in the `output/` folder

---

## 🚀 Performance

* **Runtime:** ≤ 60 seconds (tested on 3–10 PDFs)
* **Model size:** ≤ 1GB
* **Environment:** CPU-only, AMD64 architecture

---

## 📌 Notes

* No **hardcoding** – works for any persona/task/documents
* No **internet access** – completely offline
* Fully **generic** – adaptable to research, business, education use cases

