import pdfplumber
import unicodedata

with pdfplumber.open("app/data/mh-cet-cap-1.pdf") as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        if "Sardar Patel" in text or "3014" in text:
            print(f"\n--- Page {page_num} contains suspect college ---")
            for line in text.split("\n"):
                print(f"> {unicodedata.normalize('NFKC', line)}")
