import re
import pdfplumber
import unicodedata
from sqlalchemy.orm import Session
from app.models import Cutoff, College
from app.database import engine
from datetime import datetime

def extract_cutoffs_from_pdf(file_path: str, db: Session):
    import unicodedata
    import re
    from datetime import datetime
    from collections import deque
    from app.models import Cutoff
    import pdfplumber

    with pdfplumber.open(file_path) as pdf:
        record_count = 0

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            tables = deque(page.extract_tables())
            course_blocks = []
            current_college = current_college_code = None

            # First pass to collect all college and course headers
            for line in lines:
                line = unicodedata.normalize("NFKC", line.strip())

                # First match course (9–10 digit), then fallback to college (4–6 digit)
                course_match = re.match(r"^(\d{9,10})\s*[-–—]?\s*(.+)", line)
                if course_match:
                    course_code = course_match.group(1).strip()
                    branch = course_match.group(2).strip()
                    print(f"📘 Detected Course: {branch} | Code: {course_code}")
                    course_blocks.append({
                        'college': current_college,
                        'college_code': current_college_code,
                        'course_code': course_code,
                        'branch': branch,
                    })
                    continue  # skip trying college match if already matched

                college_match = re.match(r"^(\d{4,6})\s*[-–—]?\s*(.+)", line)
                if college_match:
                    current_college_code = college_match.group(1).strip()
                    current_college = college_match.group(2).strip()
                    print(f"\n🏫 Detected College: {current_college} | Code: {current_college_code}")
                    continue


            # Now match each course to one table in sequence
            for block in course_blocks:
                if not tables:
                    print(f"⚠️ No table found for course {block['branch']} on page {page_num}")
                    continue

                table = tables.popleft()
                if not table or len(table) < 2:
                    continue

                # Build merged header
                raw_header_1 = table[0]
                raw_header_2 = table[1] if len(table) > 1 else None

                if raw_header_2:
                    while len(raw_header_2) < len(raw_header_1):
                        raw_header_2.append("")

                    merged_header = []
                    for c1, c2 in zip(raw_header_1, raw_header_2):
                        merged = f"{str(c1 or '').strip()}{str(c2 or '').strip()}"
                        merged_header.append(merged)
                else:
                    merged_header = raw_header_1

                # Extract categories
                categories = [
                    re.sub(r'\s+', '', cell.strip().upper())
                    for cell in merged_header[1:]  # Skip first 'Stage' col
                    if cell and re.search(r'[A-Z]', str(cell))
                ]

                print(f"📋 Page {page_num} | Categories: {categories} | Branch: {block['branch']}")

                for row in table[1:]:
                    if not row or not row[0]:
                        continue

                    stage_marker = row[0].strip()
                    values = row[1:]

                    for i, val in enumerate(values):
                        if i >= len(categories):
                            continue
                        cat = categories[i]
                        if not val:
                            continue

                        val_clean = val.strip().replace('\n', ' ')
                        match = re.match(r"(\d+)\s*\(?([\d.]+)\)?", val_clean)
                        if not match:
                            continue

                        rank = int(match.group(1))
                        percent = float(match.group(2))

                        gender = "female" if "L" in cat else "male"
                        level = (
                            "state" if "S" in cat
                            else "other" if "O" in cat
                            else "home"
                        )

                        # 1. Look up the College object using the code
                        college_obj = db.query(College).filter_by(
                            code=block['college_code'],
                            name=block['college']  # only if you're certain name is available
                        ).first()

                        if not college_obj:
                            print(f"❌ College not found in DB: {block['college']} ({block['college_code']})")
                            continue

                        # 2. Create Cutoff with the foreign key reference
                        cutoff = Cutoff(
                            college_id=college_obj.id,  # ✅ Assign FK ID here
                            college_code=block['college_code'],  # ✅ still useful for easier querying
                            branch=block['branch'],
                            course_code=block['course_code'],
                            category=cat,
                            rank=rank,
                            percent=percent,
                            gender=gender,
                            level=level,
                            stage=stage_marker,
                            year=datetime.now().year - 1
                        )
                        db.add(cutoff)

                        record_count += 1
                        print(f"✅ Page {page_num}: {stage_marker} | {cat} | Rank: {rank} | %: {percent}")

        print(f"\n🔍 Final Record Count Before Commit: {record_count}")
        db.commit()
        print("✅ All cutoffs saved.")

def extract_college_details(line):
    # Match exactly 5-digit college code followed by a hyphen and name
    match = re.match(r"^(\d{5})\s*-\s*(.+)", line)
    if match:
        code = match.group(1).strip()
        name = match.group(2).strip()
        return code, name
    return None, None


def load_college_data(pdf_lines, db: Session):
    colleges_to_add = []
    seen_colleges = set()
    SKIP_KEYWORDS = ["Polytechnic", "Diploma", "ITI", "MSBTE", "architecture", "POLYTECHNIC"]

    i = 0
    while i < len(pdf_lines) - 2:
        line = pdf_lines[i].strip()
        code, name = extract_college_details(line)

        if code and name:
            # Skip undesired college types
            if any(keyword.lower() in name.lower() for keyword in SKIP_KEYWORDS):
                print(f"⛔ Skipped (Invalid Type): [{code}] {name}")
                i += 1
                continue

            # Now safe to access i + 2
            status_line = pdf_lines[i + 2].strip()
            status_match = re.match(r"Status\s*:\s*(.+)", status_line, re.IGNORECASE)
            if status_match:
                full_status = status_match.group(1).strip()

                # Split into status and university
                if ' : ' in full_status:
                    status, university = full_status.split(' : ', 1)
                else:
                    status = full_status
                    university = None

                college_key = (code, name, status, university)
                if college_key not in seen_colleges:
                    colleges_to_add.append((code, name, status, university))
                    seen_colleges.add(college_key)
                    print(f"➕ Added College: [{code}] {name} ({status}) → {university}")
                else:
                    print(f"⏩ Skipped Duplicate: [{code}] {name} ({status}) → {university}")

                i += 3
                continue  # move to next block

        # move to next line if code/name not found
        i += 1

    # Preview all collected colleges
    print("\n📋 Collected Colleges:")
    for idx, (code, name, status, university) in enumerate(colleges_to_add, 1):
        print(f"{idx}. [{code}] {name} ({status}) → {university}")

    # Ask for confirmation
    confirm = input("\n✅ Commit this data to the database? (yes/no): ").strip().lower()
    if confirm in ('yes', 'y'):
        try:
            for code, name, status, university in colleges_to_add:
                college = College(code=code, name=name, status=status, university=university)
                db.add(college)
            db.commit()
            print("🎉 Data committed successfully.")
        except Exception as e:
            db.rollback()
            print("❌ Commit failed:", e)
    else:
        print("❌ Commit cancelled by user.")
