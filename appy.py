import streamlit as st
from docx import Document
from docx.shared import Pt

# Simple function to create the Word document without file dependencies
def combine_notes_simple(assess_text, critical_care_reason):
    doc = Document()

    # Add a simple introductory statement
    intro_paragraph = doc.add_paragraph()
    intro_run = intro_paragraph.add_run("I personally examined the patient separately...")
    intro_run.italic = True
    intro_run.font.name = 'Arial'
    intro_run.font.size = Pt(9)
    intro_paragraph.paragraph_format.space_after = Pt(0)
    
    # Add "ASSESSMENT" section
    assessment_paragraph = doc.add_paragraph("ASSESSMENT:")
    assessment_paragraph.bold = True
    assessment_paragraph.underline = True
    assessment_paragraph.font.name = 'Arial'
    assessment_paragraph.font.size = Pt(9)
    
    assessment_content = doc.add_paragraph(assess_text)
    for run in assessment_content.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)
    
    # Add "Why Critical Care" section
    critical_care_paragraph = doc.add_paragraph("WHY CRITICAL CARE:")
    critical_care_paragraph.bold = True
    critical_care_paragraph.underline = True
    critical_care_paragraph.font.name = 'Arial'
    critical_care_paragraph.font.size = Pt(9)
    
    critical_care_content = doc.add_paragraph(critical_care_reason)
    for run in critical_care_content.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)
    
    # Save the document
    output_path = "combined_note.docx"
    doc.save(output_path)
    return output_path

# Streamlit UI
st.title("Clinical Note Management")

# Simple text inputs
assess_text = st.text_area("Enter Assessment:")
critical_care_reason = st.selectbox(
    "Why Critical Care?",
    [
        "The patient requires critical care services due to the continuous management of invasive respiratory...",
        "The patient requires critical care services due to the high risk of neurologic decompensation...",
        "The patient requires critical care services for management of the patient's airway and invasive mechanical respiratory support...",
        "The patient requires critical care services for management of the patient's airway and non-invasive mechanical respiratory support...",
        "The patient requires critical care services as the patient is at high risk of withdrawal..."
    ]
)

if st.button("Generate Note"):
    if assess_text and critical_care_reason:
        file_path = combine_notes_simple(assess_text, critical_care_reason)
        with open(file_path, "rb") as f:
            st.download_button("Download Combined Note", f, file_name="combined_note.docx")
    else:
        st.error("Please fill out all fields.")


