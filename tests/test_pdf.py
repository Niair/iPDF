import fitz

pdf_path = "data/uploads/b2812dd2_Resume.pdf"

print("=" * 60)
print("Testing PDF...")
print("=" * 60)

doc = fitz.open(pdf_path)
print(f"\nPages: {len(doc)}")

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text("text")
    print(f"\nPage {page_num + 1}:")
    print(f"  Text length: {len(text)} characters")
    if len(text) > 0:
        print(f"  Preview: {text[:100]}...")
    else:
        print("  ⚠️ NO TEXT FOUND (image-based PDF)")

doc.close()

print("\n" + "=" * 60)
if len(text) == 0:
    print("DIAGNOSIS: This is a SCANNED/IMAGE-BASED PDF")
    print("SOLUTION: Use OCR (pytesseract)")
else:
    print("DIAGNOSIS: Normal text-based PDF")
print("=" * 60)
