# 🎓 College Suggester API

This is a FastAPI-based backend application that parses CAP round cutoff PDFs of engineering colleges in Maharashtra, extracts college and branch data, and stores it in a PostgreSQL database. It then suggests colleges to students based on their entrance exam scores.

---

## 📌 Features

- 📄 Parses PDF files containing CAP round cutoff data.
- 🏫 Extracts unique college names, codes, and statuses.
- 🗃️ Stores structured data in a PostgreSQL database.
- 📊 Suggests colleges based on previous year cutoffs.
- ⚙️ Clean and scalable API design using FastAPI.

---

## 📁 Folder Context

This project resides in the `Sanskar/` folder and is part of a collaborative internship repository. It is isolated from the `students/` folder where apps made by teammates are present.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.11
- **Database**: PostgreSQL
- **PDF Parsing**: PyMuPDF (fitz), Regular Expressions (regex)
- **ORM**: SQLAlchemy
- **Other Tools**: Uvicorn, Pydantic

---

## 🚀 How to Run

1. Navigate into this folder:
   ```bash
   cd Sanskar
2. Create and activate a virtual environment:   
   ```bash
   python -m venv venv
   source venv/bin/activate        # For Windows: venv\Scripts\activate
3. Install requirement:
   ```bash
   pip install -r requirements.txt
4. Set up PostgreSQL and update your database URL in database.py:
   ```bash
   DATABASE_URL = "postgresql://username:password@localhost:5432/your_db_name"
5. Run the FastAPI app:
   ```bash
   uvicorn main:app --reload
6. Open your browser at:
   ```bash
   http://127.0.0.1:8000/docs
to test and expore the api with swagger UI

## ⚙️ How It Works

- Parses PDFs line-by-line using **pdfplumber**.
- Extracts valid college data using **regex pattern matching**.
- Skips duplicates using a composite uniqueness check on `(code, name, status)`.
- Stores confirmed entries into a **PostgreSQL** database using **SQLAlchemy ORM**.
- Suggests colleges based on cutoff data mapped to user-entered scores *(feature in progress)*.

