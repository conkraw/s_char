import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_UNDERLINE

# Function to create a Word document with specific font settings
def create_word_doc(text):
    doc = Document()
    
    # Add "Assessment" section with bold and underline
    assessment = doc.add_paragraph()
    assessment_run = assessment.add_run("ASSESSMENT: ")
    assessment_run.bold = True
    assessment_run.underline = True
    assessment_run.font.name = 'Arial'
    assessment_run.font.size = Pt(9)
    
    # Add the assessment text
    assessment.add_run(text)  # Add the note text here
    
    # Add "Plan" section with bold and underline
    plan = doc.add_paragraph()
    plan_run = plan.add_run("PLAN: ")
    plan_run.bold = True
    plan_run.underline = True
    plan_run.font.name = 'Arial'
    plan_run.font.size = Pt(9)
    
    # Add the plan text
    plan.add_run(text)  # Add the note text here
    
    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

st.title("Update Note")

# Text area for the note to be updated
paragraph_text = st.text_area("Enter the text for the note you want to update:")

# Options for replacement
options = ["Continue", "Will continue", "We will continue", "We shall continue"]

# Dropdowns for selecting phrases
selected_option = st.selectbox("Select a phrase to replace:", options)
replacement = st.selectbox("Select a replacement phrase:", options)

if st.button("Replace"):
    if paragraph_text:
        # Perform replacement
        updated_text = paragraph_text.replace(selected_option, replacement)

        # Display the updated note
        st.subheader("Updated Note:")
        st.write(updated_text)

        # Create and download button for the updated note
        word_file = create_word_doc(updated_text)
        with open(word_file, "rb") as f:
            st.download_button("Download Updated Note", f, file_name="updated_note.docx")
    else:
        st.error("Please enter some text to update.")

