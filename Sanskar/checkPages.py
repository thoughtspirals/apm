import pdfplumber
with pdfplumber.open("app/data/mh-cet-cap-1.pdf") as pdf:
    print(len(pdf.pages))  # should show correct number of pages (e.g., 5000)
