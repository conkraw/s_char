import streamlit as st
from docx import Document
from docx.shared import Pt
import os

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text):
    doc = Document()
    
    for line in text.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = 'Arial'
        run.font.size = Pt(9)
        p.paragraph_format.space_after = Pt(0)  # No space after paragraph
        p.paragraph_format.space_before = Pt(0)  # No space before paragraph
        p.paragraph_format.line_spacing = Pt(12)  # Single spacing

    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Function to combine diagnosis documents with formatted input text
def combine_notes(assess_text, diagnoses):
    doc = Document()
    
    # Assessment section
    assessment_paragraph = doc.add_paragraph()
    assessment_run = assessment_paragraph.add_run("ASSESSMENT:\n")
    assessment_run.bold = True
    assessment_run.underline = True
    assessment_run.font.name = 'Arial'
    assessment_run.font.size = Pt(9)
    assessment_run.paragraph_format.space_after = Pt(0)
    
    # Add the assessment text with formatting
    assessment_content = doc.add_paragraph(assess_text)
    for run in assessment_content.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)
    assessment_content.paragraph_format.space_after = Pt(0)
    assessment_content.paragraph_format.space_before = Pt(0)
    assessment_content.paragraph_format.line_spacing = Pt(12)

    # Plan section
    plan_paragraph = doc.add_paragraph()
    plan_run = plan_paragraph.add_run("PLAN:")
    plan_run.bold = True
    plan_run.underline = True
    plan_run.font.name = 'Arial'
    plan_run.font.size = Pt(9)
    plan_paragraph.paragraph_format.space_after = Pt(0)  # No space after PLAN heading
    plan_paragraph.paragraph_format.space_before = Pt(0)  # No space before PLAN heading

    for i, diagnosis in enumerate(diagnoses, start=1):
        diagnosis_doc_path = f"{diagnosis.lower().replace(' ', '')}.docx"
        if os.path.exists(diagnosis_doc_path):
            # Add the diagnosis header
            diagnosis_paragraph = doc.add_paragraph(f"{i}). {diagnosis}")
            diagnosis_paragraph.runs[0].font.size = Pt(9)
            diagnosis_paragraph.runs[0].font.name = 'Arial'
            diagnosis_paragraph.paragraph_format.space_after = Pt(0)  # No space after diagnosis
            diagnosis_paragraph.paragraph_format.space_before = Pt(0)  # No space before diagnosis
            diagnosis_paragraph.paragraph_format.line_spacing = Pt(12)  # Single spacing

            # Add the content from the diagnosis document
            diagnosis_doc = Document(diagnosis_doc_path)
            for para in diagnosis_doc.paragraphs:
                new_paragraph = doc.add_paragraph(para.text)
                for run in new_paragraph.runs:
                    run.font.name = 'Arial'
                    run.font.size = Pt(9)
                new_paragraph.paragraph_format.space_after = Pt(0)  # No space after diagnosis content
                new_paragraph.paragraph_format.space_before = Pt(0)  # No space before diagnosis content
                new_paragraph.paragraph_format.line_spacing = Pt(12)  # Single spacing

    output_path = "combined_note.docx"
    doc.save(output_path)
    return output_path

# Title of the app
st.title("Note Management App")

# Sidebar for navigation
#option = st.sidebar.selectbox("Choose an option:", ["New Note", "Update Note"])

#if option == "New Note":
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

