import fitz, base64, json, urllib.request, re, sys, os

def ocr_page(doc, page_num, dpi=120):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
    body = json.dumps({"model":"deepseek-ocr","prompt":"OCR this image. Return only the recognized text.",
        "images":[b64],"stream":False,"options":{"temperature":0.0}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body, headers={"Content-Type":"application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return resp.get("response","").strip()

def ocr_page_mimo(doc, page_num, dpi=120):
    import os
    import tempfile
    from mimo_ocr import ocr_image

    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    pix.save(tmp_path)
    try:
        result = ocr_image(tmp_path)
    finally:
        os.unlink(tmp_path)
    return result.get("content", "").strip()

def ocr_pdf(pdf_path, pages=None, engine="deepseek"):
    doc = fitz.open(pdf_path)
    if pages is None: pages = range(len(doc))
    results = []
    for pn in pages:
        if engine == "mimo":
            text = ocr_page_mimo(doc, pn)
        else:
            text = ocr_page(doc, pn)
        chars = list(set(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text)))
        results.append({"page":pn,"text":text,"chars":chars})
    doc.close()
    return results

def encode_chars(chars, api_url="http://localhost:8000"):
    import urllib.request
    body = json.dumps({"chars":chars}).encode()
    req = urllib.request.Request(f"{api_url}/batch", data=body, headers={"Content-Type":"application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=300).read())
    return resp

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage: python ocr_pipeline.py <pdf_path> [page1 page2 ...] [--engine deepseek|mimo]")
        sys.exit(1)
    pdf = sys.argv[1]
    args = sys.argv[2:]
    engine = "deepseek"
    if "--engine" in args:
        idx = args.index("--engine")
        engine = args[idx+1]
        args = args[:idx] + args[idx+2:]
    pages = [int(a) for a in args] if args else None
    print(f"OCR: {pdf}")
    print(f"Engine: {engine}")
    texts = ocr_pdf(pdf, pages, engine=engine)
    for t in texts:
        print(f"  Page {t['page']}: {len(t['text'])} chars, {len(t['chars'])} unique")
    all_chars = list(set(c for t in texts for c in t["chars"]))
    print(f"Total unique chars: {len(all_chars)}")
    print("Encoding with CNBE...")
    results = encode_chars(all_chars)
    print(f"Encoded {len(results)} chars")
    for r in results[:3]:
        print(f"  {r['char']}: {r['cnbe']}")
