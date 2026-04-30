"""Generate PDF from markdown using fpdf2 - Robust approach."""
import re
from fpdf import FPDF

def sanitize(text):
    """Replace all non-latin1 characters."""
    replacements = {
        '\u2014': '--', '\u2013': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '-',
        '\u2192': '->', '\u2190': '<-', '\u25ba': '>', '\u25b6': '>',
        '\u2502': '|', '\u251c': '|', '\u2514': '|', '\u2500': '-',
        '\u250c': '+', '\u2510': '+', '\u2518': '+', '\u2524': '|',
        '\u252c': '+', '\u2534': '+', '\u253c': '+', '\u00a0': ' ',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', errors='replace').decode('latin-1')

def strip_md(text):
    """Remove markdown formatting."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return sanitize(text)

def write_text(pdf, text, size=9, style="", h=5):
    """Write text with automatic X reset."""
    pdf.set_x(10)  # Always reset to left margin
    pdf.set_font("Helvetica", style, size)
    pdf.multi_cell(pdf.w - 20, h, text)

def main():
    with open("project_explanation.md", "r", encoding="utf-8") as f:
        content = f.read()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.alias_nb_pages()

    in_code = False
    lines = content.split("\n")

    for line in lines:
        line_s = sanitize(line)
        stripped = line_s.strip()

        # Code block toggle
        if stripped.startswith("```"):
            in_code = not in_code
            pdf.ln(2)
            continue

        # Inside code block
        if in_code:
            pdf.set_x(10)
            pdf.set_font("Courier", size=7)
            pdf.set_fill_color(240, 240, 240)
            safe = line_s[:95] if len(line_s) > 95 else line_s
            pdf.cell(pdf.w - 20, 4, safe, 0, 1, fill=True)
            continue

        # Table separator - skip
        if re.match(r'^\|[\s\-:|]+\|$', stripped):
            continue

        # Table row
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if cells:
                pdf.set_x(10)
                pdf.set_font("Helvetica", size=7)
                col_w = (pdf.w - 20) / len(cells)
                for cell_text in cells:
                    safe = strip_md(cell_text)[:45]
                    pdf.cell(col_w, 5, safe, 1)
                pdf.ln()
            continue

        # Horizontal rule
        if stripped in ("---", "***", "- - -"):
            pdf.set_draw_color(200, 200, 200)
            y = pdf.get_y()
            pdf.line(10, y, pdf.w - 10, y)
            pdf.ln(4)
            continue

        # H1
        if stripped.startswith("# ") and not stripped.startswith("## "):
            pdf.ln(4)
            text = strip_md(re.sub(r'^#+\s*', '', stripped))
            write_text(pdf, text, size=16, style="B", h=7)
            pdf.set_draw_color(79, 134, 237)
            pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
            pdf.ln(3)
            continue

        # H2
        if stripped.startswith("## ") and not stripped.startswith("### "):
            pdf.ln(3)
            text = strip_md(re.sub(r'^#+\s*', '', stripped))
            write_text(pdf, text, size=13, style="B", h=6)
            pdf.ln(2)
            continue

        # H3
        if stripped.startswith("### ") and not stripped.startswith("#### "):
            pdf.ln(2)
            text = strip_md(re.sub(r'^#+\s*', '', stripped))
            write_text(pdf, text, size=11, style="B", h=5)
            pdf.ln(1)
            continue

        # H4
        if stripped.startswith("#### "):
            pdf.ln(1)
            text = strip_md(re.sub(r'^#+\s*', '', stripped))
            write_text(pdf, text, size=10, style="BI", h=5)
            pdf.ln(1)
            continue

        # Empty line
        if not stripped:
            pdf.ln(2)
            continue

        # Bullet or numbered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = strip_md(stripped[2:])
            write_text(pdf, "  - " + text)
            continue

        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            text = strip_md(m.group(2))
            write_text(pdf, "  " + m.group(1) + ". " + text)
            continue

        # Normal paragraph
        text = strip_md(stripped)
        write_text(pdf, text)

    pdf.output("project_explanation.pdf")
    print("PDF generated successfully: project_explanation.pdf")

if __name__ == "__main__":
    main()
