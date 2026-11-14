#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps
from pypdf import PdfReader


def render_pdf(path: Path, output_dir: Path, write_pages: bool = True):
    document = pdfium.PdfDocument(str(path))
    page_dir = output_dir / path.stem
    if write_pages:
        page_dir.mkdir(parents=True, exist_ok=True)
    thumbs, coverage = [], []
    for index, page in enumerate(document):
        image = page.render(scale=1.4).to_pil().convert("RGB")
        if write_pages:
            image.save(page_dir / f"page-{index + 1}.png")
        gray = image.convert("L").resize((160, 220))
        nonwhite = sum(gray.histogram()[:248])
        coverage.append(round(nonwhite / (160 * 220), 4))
        width = 420
        height = int(image.height * width / image.width)
        thumbs.append(ImageOps.expand(image.resize((width, height)), border=3, fill="gray"))
    cols = 2
    rows = (len(thumbs) + cols - 1) // cols
    cell_w = max(image.width for image in thumbs)
    cell_h = max(image.height for image in thumbs)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (230, 230, 230))
    for index, image in enumerate(thumbs):
        sheet.paste(image, ((index % cols) * cell_w, (index // cols) * cell_h))
    contact = output_dir / f"{path.stem}_contact.jpg"
    sheet.save(contact, quality=92)
    reader = PdfReader(str(path))
    text_lengths = [len(page.extract_text() or "") for page in reader.pages]
    return {
        "pdf": str(path),
        "pages": len(document),
        "bytes": path.stat().st_size,
        "contact_sheet": str(contact),
        "ink_coverage": coverage,
        "text_lengths": text_lengths,
        "warnings": [
            f"page {i + 1} may be nearly blank" for i, value in enumerate(coverage) if value < 0.008
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Render homework PDFs and create visual QA contact sheets.")
    parser.add_argument("pdfs", nargs="+", help="Question and answer PDFs")
    parser.add_argument("--output-dir", required=True, help="Directory for rendered QA images")
    parser.add_argument("--contact-only", action="store_true", help="Save only contact sheets and the JSON report; omit per-page PNGs")
    args = parser.parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for value in args.pdfs:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        reports.append(render_pdf(path, output_dir, write_pages=not args.contact_only))
    report_path = output_dir / "qa_report.json"
    report_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report_path)


if __name__ == "__main__":
    main()
