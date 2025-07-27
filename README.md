# 📘 Adobe Hackathon 2025 – Connecting the Dots Challenge

## 🏆 Overview
This repository contains solutions for **Round 1A** and **Round 1B** of the Adobe Hackathon 2025 – *Connecting the Dots*.  
The goal is to transform traditional PDFs into **intelligent, structured, and interactive** experiences.

---

## 🔹 Round 1A: Understand Your Document
**Mission:**  
Extract a **structured outline** (Title, H1, H2, H3) from a single PDF, including page numbers, and save it as JSON.

**Input:** PDF file (up to 50 pages)  
**Output:** JSON file with:
- Document title  
- Hierarchical headings (H1, H2, H3) with page numbers  

---

## 🔹 Round 1B: Persona-Driven Document Intelligence
**Mission:**  
Analyze **multiple PDFs** (3–10) based on a **persona** and their **job-to-be-done**, extract and rank relevant sections, and output a JSON with:
- Metadata (persona, task, documents, timestamp)  
- Extracted sections with importance ranking  
- Sub-section refined content analysis  

---

## 📂 Folder Structure
```

AdobeIndiaHackathon25/
├── ROUND 1A/   # Round 1A: Outline extraction
│   ├── Dockerfile
│   ├── main.py
│   ├── input/
│   └── output/
│
├── ROUND 1B/   # Round 1B: Persona-driven analysis
│   ├── Dockerfile
│   ├── main.py
│   ├── input/
│   └── output/
│
└── README.md

````

---

## ⚙️ How to Run

### 1. Build Docker Image
Inside each challenge folder (e.g., `ROUND 1A` or `ROUND 1B`):
```bash
docker build --platform linux/amd64 -t pdf-processor .
````

### 2. Run Container

#### **Windows PowerShell**

```powershell
docker run --rm -v "${PWD}/input:/app/input:ro" -v "${PWD}/output:/app/output" --network none pdf-processor
```

#### **Windows CMD**

```cmd
docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output:/app/output" --network none pdf-processor
```


## 🏁 Expected Outputs

* **Round 1A:** `filename.json` containing Title + H1/H2/H3 outline
* **Round 1B:** `collection_output.json` containing metadata, ranked sections, and refined text

---

## 🚀 Why This Matters

* PDF → Intelligent insights
* Structure → Context-driven search and recommendations
* Offline, fast, and lightweight solution for large-scale document understanding

---

*Adobe India Hackathon 2025 – Connecting the Dots Challenge*
