import streamlit as st
from docx import Document
from docx.shared import Pt
import os

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text):
    doc = Document()
    
    # Split input text into lines
    for line in text.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        
        # Set font properties
        run.font.name = 'Arial'
        run.font.size = Pt(9)

        # Set single spacing
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = Pt(12)

    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Function to combine diagnosis documents with formatted input text
def combine_notes(assess_text, diagnoses):
    doc = Document()
    
    # Add Assessment
    assessment_paragraph = doc.add_paragraph()
    assessment_run = assessment_paragraph.add_run(f"ASSESSMENT:\n{assess_text}\n")
    assessment_run.bold = True
    assessment_run.underline = True

    # Add Plan heading
    plan_paragraph = doc.add_paragraph()
    plan_run = plan_paragraph.add_run("PLAN:")
    plan_run.bold = True
    plan_run.underline = True
    doc.add_paragraph()  # Add a blank line after the PLAN heading

    # Add diagnosis documents in order
    for i, diagnosis in enumerate(diagnoses, start=1):
        # Load the corresponding diagnosis document
        diagnosis_doc_path = f"{diagnosis.lower().replace(' ', '')}.docx"  # Ensure proper file naming
        if os.path.exists(diagnosis_doc_path):
            # Add numbered diagnosis without extra lines or symbols
            doc.add_paragraph(f"{i}. {diagnosis}")  # Format without any additional symbols
            # Load the diagnosis document
            diagnosis_doc = Document(diagnosis_doc_path)
            for para in diagnosis_doc.paragraphs:
                # Add each paragraph from the diagnosis document
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
    
    # Multi-select for medical conditions
    conditions = ["Acute Hypoxemic Respiratory Failure", "Sepsis", "Hyponatremia"]
    selected_conditions = st.multiselect("Choose diagnoses:", conditions)
    
    # Text area for assessment
    assessment_text = st.text_area("Enter Assessment:")
    
    if st.button("Submit New Note"):
        if selected_conditions and assessment_text:
            # Combine notes with selected diagnoses
            combined_file = combine_notes(assessment_text, selected_conditions)
            st.success("New note created!")

            # Download button for the combined note
            with open(combined_file, "rb") as f:
                st.download_button("Download Combined Note", f, file_name="combined_note.docx")
        else:
            st.error("Please fill out all fields.")

elif option == "Update Note":
    # Implement your update note functionality here as before
    pass


