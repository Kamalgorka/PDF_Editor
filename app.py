import os
import fitz
import streamlit as st

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Easy PDF Editor",
    page_icon="📄",
    layout="wide"
)

# =========================
# FOLDERS
# =========================
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f7f8fc 0%, #eef2f7 100%);
    }

    .main-title {
        font-size: 3rem;
        font-weight: 800;
        color: #1f2937;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }

    .sub-title {
        text-align: center;
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 30px;
    }

    .hero-card {
        background: #ffffff;
        border-radius: 24px;
        padding: 32px 28px 22px 28px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 24px;
    }

    .mini-badge {
        display: inline-block;
        background: #fff3ee;
        color: #ff6b3d;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 8px 14px;
        border-radius: 999px;
        margin-bottom: 14px;
    }

    .section-card {
        background: #ffffff;
        border-radius: 22px;
        padding: 22px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-top: 18px;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }

    .section-note {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }

    .metric-box {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 16px 18px;
        text-align: center;
    }

    .metric-number {
        font-size: 1.4rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 4px;
    }

    .metric-label {
        color: #6b7280;
        font-size: 0.9rem;
    }

    div[data-testid="stFileUploader"] {
        background: #fff;
        border-radius: 18px;
        padding: 12px;
        border: 1px dashed #d1d5db;
    }

    div[data-testid="stDownloadButton"] button,
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 14px;
        padding: 0.7rem 1rem;
        font-weight: 700;
        border: none;
    }

    div[data-testid="stButton"] button {
        background: linear-gradient(90deg, #ff6b3d 0%, #ff845c 100%);
        color: white;
        box-shadow: 0 8px 18px rgba(255, 107, 61, 0.22);
    }

    div[data-testid="stButton"] button:hover {
        background: linear-gradient(90deg, #f35f31 0%, #ff7d52 100%);
        color: white;
    }

    div[data-testid="stDownloadButton"] button {
        background: #111827;
        color: white;
    }

    div[data-testid="stDownloadButton"] button:hover {
        background: #000000;
        color: white;
    }

    .footer-note {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 24px;
        margin-bottom: 10px;
    }

    .stExpander {
        border-radius: 16px !important;
        border: 1px solid #e5e7eb !important;
        background: #ffffff !important;
    }

    @media (max-width: 768px) {
        .main-title {
            font-size: 2.2rem;
        }
        .hero-card {
            padding: 22px 16px 16px 16px;
        }
    }
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
def int_to_rgb(color_int):
    if color_int is None:
        return (0, 0, 0)
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return (r / 255, g / 255, b / 255)


def find_cloud_font(pdf_font_name: str):
    if not pdf_font_name:
        return None

    font_name = pdf_font_name.lower()
    font_dir = "fonts"

    if "times" in font_name or "serif" in font_name:
        candidates = [
            "LiberationSerif-Regular.ttf",
            "LiberationSerif-Bold.ttf"
        ]
    elif "arial" in font_name or "helvetica" in font_name or "sans" in font_name:
        candidates = [
            "LiberationSans-Regular.ttf",
            "LiberationSans-Bold.ttf"
        ]
    elif "courier" in font_name or "mono" in font_name:
        candidates = [
            "LiberationMono-Regular.ttf"
        ]
    else:
        candidates = [
            "LiberationSans-Regular.ttf",
            "LiberationSerif-Regular.ttf"
        ]

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

    # clear original text area
    clear_rect = fitz.Rect(x0, y0 - 1, x1 + 5, y1 + 2)
    page.draw_rect(clear_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

    color_rgb = int_to_rgb(color_int)
    font_file = find_cloud_font(font_name)

    # allow writing in wider area
    page_width = page.rect.width
    write_rect = fitz.Rect(x0, y0 - 1, page_width - 20, y1 + 2)

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

        page.draw_rect(write_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        size_try -= 0.5

    # final fallback
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


# =========================
# UI HEADER
# =========================
st.markdown("""
<div class="hero-card">
    <div class="mini-badge">📄 Smart PDF Utility</div>
    <div class="main-title">Easy PDF Editor</div>
    <div class="sub-title">
        Edit computer-generated PDFs with cleaner layout, mobile-friendly experience, and downloadable output.
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# UPLOAD SECTION
# =========================
st.markdown("""
<div class="section-card">
    <div class="section-title">Upload PDF</div>
    <div class="section-note">Supported format: PDF only • Best results on computer-generated PDFs</div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose your PDF file", type=["pdf"], label_visibility="collapsed")

# =========================
# MAIN APP
# =========================
if uploaded_file:
    input_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("PDF uploaded successfully.")

    lines = extract_lines(input_path)

    if not lines:
        st.error("No editable text found in this PDF.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{len(lines)}</div>
            <div class="metric-label">Detected Lines</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">PDF</div>
            <div class="metric-label">{uploaded_file.name}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">Ready</div>
            <div class="metric-label">For Editing</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <div class="section-title">Edit Detected Lines</div>
        <div class="section-note">Expand a line, update the text, then generate the edited PDF.</div>
    </div>
    """, unsafe_allow_html=True)

    edits = []

    for i, line in enumerate(lines):
        title_text = line["text"][:80] + ("..." if len(line["text"]) > 80 else "")
        with st.expander(f"Page {line['page'] + 1} • Line {i + 1} • {title_text}"):
            info1, info2 = st.columns(2)
            with info1:
                st.caption(f"Detected font: {line['font']}")
            with info2:
                st.caption(f"Detected size: {round(line['size'], 2)}")

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

    st.markdown("""
    <div class="section-card">
        <div class="section-title">Final Output</div>
        <div class="section-note">Generate the updated PDF and download it instantly.</div>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"Total changed lines: {len(edits)}")

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

else:
    st.markdown("""
    <div class="section-card">
        <div class="section-title">How it works</div>
        <div class="section-note">
            1. Upload a PDF<br>
            2. Expand and edit the detected text lines<br>
            3. Generate and download the updated PDF
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="footer-note">Built for quick PDF text updates on desktop and mobile.</div>', unsafe_allow_html=True)
