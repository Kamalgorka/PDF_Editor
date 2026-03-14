import os
import fitz
import streamlit as st

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def int_to_rgb(color_int):
    if color_int is None:
        return (0, 0, 0)
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return (r / 255, g / 255, b / 255)


def find_windows_font(pdf_font_name: str):
    if not pdf_font_name:
        return None

    font_name = pdf_font_name.lower()
    font_dir = r"C:\Windows\Fonts"

    candidates = []

    if "times" in font_name:
        candidates = ["times.ttf", "times new roman.ttf", "timesbd.ttf", "timesi.ttf"]
    elif "arial" in font_name or "helvetica" in font_name:
        candidates = ["arial.ttf", "arialbd.ttf", "ariali.ttf"]
    elif "calibri" in font_name:
        candidates = ["calibri.ttf", "calibrib.ttf", "calibrii.ttf"]
    elif "cambria" in font_name:
        candidates = ["cambria.ttf", "cambriab.ttf", "cambriai.ttf"]
    elif "courier" in font_name:
        candidates = ["cour.ttf", "courbd.ttf", "couri.ttf"]
    else:
        candidates = ["arial.ttf", "calibri.ttf", "times.ttf"]

    for c in candidates:
        p = os.path.join(font_dir, c)
        if os.path.exists(p):
            return p
    return None


def extract_lines(pdf_path):
    doc = fitz.open(pdf_path)
    data = []

    for page_num, page in enumerate(doc):
        text_dict = page.get_text("dict")

        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                spans = []
                line_text = ""

                for span in line["spans"]:
                    txt = span["text"]
                    if txt.strip():
                        line_text += txt
                        spans.append({
                            "text": txt,
                            "font": span.get("font", ""),
                            "size": span.get("size", 10),
                            "color": span.get("color", 0),
                            "bbox": span["bbox"]
                        })

                if spans and line_text.strip():
                    x0 = min(s["bbox"][0] for s in spans)
                    y0 = min(s["bbox"][1] for s in spans)
                    x1 = max(s["bbox"][2] for s in spans)
                    y1 = max(s["bbox"][3] for s in spans)

                    data.append({
                        "page": page_num,
                        "text": line_text,
                        "bbox": (x0, y0, x1, y1),
                        "font": spans[0]["font"],
                        "size": spans[0]["size"],
                        "color": spans[0]["color"]
                    })

    doc.close()
    return data


def redraw_line(page, bbox, new_text, font_name, font_size, color_int):
    x0, y0, x1, y1 = bbox

    # cover original text area only
    clear_rect = fitz.Rect(x0, y0 - 1, x1 + 5, y1 + 2)
    page.draw_rect(clear_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

    color_rgb = int_to_rgb(color_int)
    font_file = find_windows_font(font_name)

    # allow writing in a wider area till near page end
    page_width = page.rect.width
    write_rect = fitz.Rect(x0, y0 - 1, page_width - 20, y1 + 2)

    # first try: keep original size
    size_try = font_size
    min_size = max(8, font_size - 2)

    while size_try >= min_size:
        try:
            if font_file:
                result = page.insert_textbox(
                    write_rect,
                    new_text,
                    fontsize=size_try,
                    fontfile=font_file,
                    color=color_rgb,
                    align=0
                )
            else:
                result = page.insert_textbox(
                    write_rect,
                    new_text,
                    fontsize=size_try,
                    fontname="Times-Roman",
                    color=color_rgb,
                    align=0
                )

            if result >= 0:
                return True

        except Exception:
            pass

        # clean writing area before retry
        page.draw_rect(write_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        size_try -= 0.5

    # final fallback: direct baseline write
    try:
        baseline_y = y1 - 2
        if font_file:
            page.insert_text(
                (x0, baseline_y),
                new_text,
                fontsize=font_size,
                fontfile=font_file,
                color=color_rgb
            )
        else:
            page.insert_text(
                (x0, baseline_y),
                new_text,
                fontsize=font_size,
                fontname="Times-Roman",
                color=color_rgb
            )
        return True
    except Exception:
        return False    


def create_edited_pdf(input_pdf_path, output_pdf_path, edits):
    doc = fitz.open(input_pdf_path)

    for edit in edits:
        page = doc[edit["page"]]
        redraw_line(
            page=page,
            bbox=edit["bbox"],
            new_text=edit["new_text"],
            font_name=edit["font"],
            font_size=edit["size"],
            color_int=edit["color"]
        )

    doc.save(output_pdf_path)
    doc.close()


st.set_page_config(page_title="Style-Aware PDF Editor", layout="wide")
st.title("Style-Aware PDF Editor")
st.caption("Computer-generated PDFs only")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    input_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("PDF uploaded successfully.")

    lines = extract_lines(input_path)

    if not lines:
        st.error("No editable text found in this PDF.")
        st.stop()

    st.subheader("Edit Lines")
    edits = []

    for i, line in enumerate(lines):
        with st.expander(f"Page {line['page'] + 1} | Line {i + 1} | {line['text'][:80]}"):
            st.write(f"Detected font: {line['font']}")
            st.write(f"Detected size: {round(line['size'], 2)}")

            new_text = st.text_input(
                f"Edit Line {i + 1}",
                value=line["text"],
                key=f"line_{i}"
            )

            if new_text != line["text"]:
                edits.append({
                    "page": line["page"],
                    "bbox": line["bbox"],
                    "font": line["font"],
                    "size": line["size"],
                    "color": line["color"],
                    "new_text": new_text
                })

    st.write(f"Total changed lines: {len(edits)}")

    if st.button("Generate Edited PDF"):
        output_path = os.path.join(OUTPUT_FOLDER, f"edited_{uploaded_file.name}")
        create_edited_pdf(input_path, output_path, edits)

        with open(output_path, "rb") as f:
            st.download_button(
                label="Download Edited PDF",
                data=f,
                file_name=f"edited_{uploaded_file.name}",
                mime="application/pdf"
            )

        st.success("Edited PDF created successfully.")
