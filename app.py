import streamlit as st
from docx import Document
from docx.shared import Pt
import os

# Function to set paragraph formatting for single spacing and font style
def set_paragraph_formatting(paragraph):
    paragraph.paragraph_format.space_after = Pt(0)  # No space after
    paragraph.paragraph_format.space_before = Pt(0)  # No space before
    paragraph.paragraph_format.line_spacing = Pt(12)  # Single spacing
    for run in paragraph.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text):
    doc = Document()
    
    for line in text.split('\n'):
        p = doc.add_paragraph(line)
        set_paragraph_formatting(p)

    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Function to combine diagnosis documents with formatted input text
def combine_notes(assess_text, diagnoses):
    doc = Document()
    
    # Assessment section
    assessment_paragraph = doc.add_paragraph("ASSESSMENT:")
    assessment_paragraph.bold = True
    assessment_paragraph.underline = True
    set_paragraph_formatting(assessment_paragraph)

    # Add the assessment text
    assessment_content = doc.add_paragraph(assess_text)
    set_paragraph_formatting(assessment_content)

    # Plan section
    plan_paragraph = doc.add_paragraph("PLAN:")
    plan_paragraph.bold = True
    plan_paragraph.underline = True
    set_paragraph_formatting(plan_paragraph)

    for i, diagnosis in enumerate(diagnoses, start=1):
        diagnosis_doc_path = f"{diagnosis.lower().replace(' ', '')}.docx"
        if os.path.exists(diagnosis_doc_path):
            # Add the diagnosis header
            diagnosis_paragraph = doc.add_paragraph(f"{i}). {diagnosis}")
            set_paragraph_formatting(diagnosis_paragraph)

            # Add the content from the diagnosis document
            diagnosis_doc = Document(diagnosis_doc_path)
            for para in diagnosis_doc.paragraphs:
                new_paragraph = doc.add_paragraph(para.text)
                set_paragraph_formatting(new_paragraph)

    output_path = "combined_note.docx"
    doc.save(output_path)
    return output_path

# Title of the app
st.title("Note Management App")

# Sidebar for navigation
option = st.sidebar.selectbox("Choose an option:", ["New Note", "Update Note"])

if option == "New Note":
    st.header("Create a New Note")
    
    conditions = ["Acute Hypoxemic Respiratory Failure", "Sepsis", "Hyponatremia"]
    selected_conditions = st.multiselect("Choose diagnoses:", conditions)
    
    assessment_text = st.text_area("Enter Assessment:")
    
    if st.button("Submit New Note"):
        if selected_conditions and assessment_text:
            combined_file = combine_notes(assessment_text, selected_conditions)
            st.success("New note created!")

            with open(combined_file, "rb") as f:
                st.download_button("Download Combined Note", f, file_name="combined_note.docx")
        else:
            st.error("Please fill out all fields.")

elif option == "Update Note":
    # Implement your update note functionality here as before
    pass


