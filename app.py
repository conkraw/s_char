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
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = Pt(12)

    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Function to combine diagnosis documents with formatted input text
def combine_notes(assess_text, diagnoses):
    doc = Document()
    
    assessment_paragraph = doc.add_paragraph()
    assessment_run = assessment_paragraph.add_run("ASSESSMENT:\n")
    assessment_run.bold = True
    assessment_run.underline = True
    doc.add_paragraph(assess_text)

    plan_paragraph = doc.add_paragraph()
    plan_run = plan_paragraph.add_run("PLAN:")
    plan_run.bold = True
    plan_run.underline = True
    doc.add_paragraph()  # Add a blank line after the PLAN heading

    for i, diagnosis in enumerate(diagnoses, start=1):
        diagnosis_doc_path = f"{diagnosis.lower().replace(' ', '')}.docx"
        if os.path.exists(diagnosis_doc_path):
            doc.add_paragraph(f"{i}). {diagnosis}")
            diagnosis_doc = Document(diagnosis_doc_path)
            for para in diagnosis_doc.paragraphs:
                doc.add_paragraph(para.text)

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

    # Allow user to order selected conditions
    ordered_conditions = st.multiselect("Order your selections (drag to reorder):", 
                                         options=selected_conditions, 
                                         default=selected_conditions)
    
    assessment_text = st.text_area("Enter Assessment:")
    
    if st.button("Submit New Note"):
        if ordered_conditions and assessment_text:
            combined_file = combine_notes(assessment_text, ordered_conditions)
            st.success("New note created!")

            with open(combined_file, "rb") as f:
                st.download_button("Download Combined Note", f, file_name="combined_note.docx")
        else:
            st.error("Please fill out all fields.")

elif option == "Update Note":
    # Implement your update note functionality here as before
    pass


