import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_UNDERLINE

# Function to create a Word document with specific font settings
def create_word_doc(text):
    doc = Document()
    
    # Split the text to handle "ASSESSMENT:" and "PLAN:"
    sections = text.split('\n')
    for section in sections:
        if section.startswith("ASSESSMENT:"):
            p = doc.add_paragraph()
            run = p.add_run(section)
            run.bold = True
            run.underline = True
            run.font.name = 'Arial'
            run.font.size = Pt(9)
        elif section.startswith("PLAN:"):
            p = doc.add_paragraph()
            run = p.add_run(section)
            run.bold = True
            run.underline = True
            run.font.name = 'Arial'
            run.font.size = Pt(9)
        else:
            p = doc.add_paragraph()
            run = p.add_run(section)
            run.font.name = 'Arial'
            run.font.size = Pt(9)

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

