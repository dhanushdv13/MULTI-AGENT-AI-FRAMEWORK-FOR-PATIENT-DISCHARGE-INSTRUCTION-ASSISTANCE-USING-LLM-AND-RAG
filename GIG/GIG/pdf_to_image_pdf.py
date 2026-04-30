"""
PDF to Image-PDF Converter - STANDALONE UTILITY

Converts any PDF (native text or scanned) into a new PDF where each page
is rendered as an image. Useful for:
- Ensuring consistent display across different PDF viewers
- Creating "flattened" PDFs that can't be easily edited
- Testing OCR pipelines with known-good images

Fast: Uses PyMuPDF, renders at configurable DPI, processes in parallel.
"""
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF


def render_page_to_image(page_num: int, pdf_path: str, dpi: int = 150) -> dict:
    """
    Render a single PDF page to an image (runs in thread pool).
    Returns: {page_num, pixmap_data, width, height}
    """
    pdf_doc = fitz.open(pdf_path)
    page = pdf_doc[page_num]
    
    # Render at specified DPI (150 = web quality, 200 = high quality, 300 = print quality)
    zoom = dpi / 72  # 72 is PDF's native DPI
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Extract pixmap data (PNG format, in-memory)
    img_data = pix.tobytes("png")
    width, height = pix.width, pix.height
    
    pdf_doc.close()
    
    return {
        "page_num": page_num,
        "image_data": img_data,
        "width": width,
        "height": height,
    }


def convert_pdf_to_image_pdf(
    input_pdf: str,
    output_pdf: str = None,
    dpi: int = 150,
    max_workers: int = 4,
) -> str:
    """
    Convert a PDF to an image-based PDF (each page becomes an image).
    
    Args:
        input_pdf: Path to input PDF
        output_pdf: Path to output PDF (default: {input}_images.pdf)
        dpi: Resolution for rendering
             - 150 = web/screen quality, smaller file size
             - 200 = balanced quality
             - 300 = high quality, larger file size
        max_workers: Number of parallel rendering threads (default 4)
    
    Returns:
        Path to the generated image PDF
    """
    input_path = Path(input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")
    
    if output_pdf is None:
        output_pdf = input_path.parent / f"{input_path.stem}_images.pdf"
    output_path = Path(output_pdf)
    
    print("="*70)
    print("PDF TO IMAGE-PDF CONVERTER")
    print("="*70)
    print(f"Input:  {input_path.name}")
    print(f"Output: {output_path.name}")
    print(f"DPI:    {dpi}")
    print(f"Workers: {max_workers}")
    print()
    
    # Get page count
    pdf_doc = fitz.open(str(input_path))
    total_pages = len(pdf_doc)
    pdf_doc.close()
    
    print(f"Rendering {total_pages} pages...")
    start_time = time.time()
    
    # ── Render all pages in parallel ──────────────────────────────────
    pages_data = [None] * total_pages
    completed = 0
    
    with ThreadPoolExecutor(max_workers=min(max_workers, total_pages)) as executor:
        futures = {
            executor.submit(render_page_to_image, pn, str(input_path), dpi): pn
            for pn in range(total_pages)
        }
        for future in as_completed(futures):
            page_num = futures[future]
            try:
                result = future.result()
                pages_data[page_num] = result
                completed += 1
                print(f"  [{completed}/{total_pages}] Page {page_num + 1} rendered")
            except Exception as e:
                print(f"  [ERROR] Page {page_num + 1} failed: {e}")
                pages_data[page_num] = None
    
    render_time = time.time() - start_time
    print(f"\n✓ All pages rendered in {render_time:.1f}s")
    
    # ── Build new PDF from images ─────────────────────────────────────
    print("\nBuilding image-based PDF...")
    
    output_doc = fitz.open()  # Create new empty PDF
    
    for page_num, page_data in enumerate(pages_data):
        if page_data is None:
            print(f"  [WARN] Skipping page {page_num + 1} (rendering failed)")
            continue
        
        # Create a new page with the image dimensions
        # PyMuPDF uses points (72 DPI), so convert from image pixels
        page_w_pt = page_data["width"] * 72 / dpi
        page_h_pt = page_data["height"] * 72 / dpi
        
        new_page = output_doc.new_page(width=page_w_pt, height=page_h_pt)
        
        # Insert the image to fill the entire page
        rect = fitz.Rect(0, 0, page_w_pt, page_h_pt)
        new_page.insert_image(rect, stream=page_data["image_data"])
    
    # Save the output PDF
    output_doc.save(str(output_path), garbage=4, deflate=True)
    output_doc.close()
    
    total_time = time.time() - start_time
    output_size_mb = output_path.stat().st_size / (1024 * 1024)
    
    print(f"\n✓ Image PDF saved: {output_path.name}")
    print(f"  Size: {output_size_mb:.1f} MB")
    print(f"  Total time: {total_time:.1f}s")
    print("="*70)
    
    return str(output_path)


# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n")
    
    if len(sys.argv) < 2:
        print("USAGE:")
        print("  python pdf_to_image_pdf.py <input.pdf> [output.pdf] [dpi] [workers]")
        print()
        print("EXAMPLES:")
        print("  python pdf_to_image_pdf.py document.pdf")
        print("  python pdf_to_image_pdf.py document.pdf output.pdf")
        print("  python pdf_to_image_pdf.py document.pdf output.pdf 200")
        print("  python pdf_to_image_pdf.py document.pdf output.pdf 200 8")
        print()
        print("DPI OPTIONS:")
        print("  150 - Web/screen quality (default, smaller files)")
        print("  200 - Balanced quality")
        print("  300 - High quality (larger files)")
        print()
        sys.exit(1)
    
    # Parse arguments
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    dpi = int(sys.argv[3]) if len(sys.argv) >= 4 else 150
    workers = int(sys.argv[4]) if len(sys.argv) >= 5 else 4
    
    # Validate DPI
    if dpi < 72 or dpi > 600:
        print(f"WARNING: DPI {dpi} is unusual. Recommended range: 150-300")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Convert
    try:
        result = convert_pdf_to_image_pdf(input_file, output_file, dpi=dpi, max_workers=workers)
        print(f"\n✓ SUCCESS! Image PDF created: {result}\n")
    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
