import re

from pypdf import PdfReader
import json

reader = PdfReader("data/справка.pdf")

data = {}
for index, page in enumerate(reader.pages):
    text = page.extract_text()
    text = re.sub(r"\s+", " ", text)
    data[f"page_{index + 1}"] = text

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)