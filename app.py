import streamlit as st
from docx import Document
from docx.shared import Pt

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text):
    doc = Document()
    
    sections = text.split('\n')
    for section in sections:
        p = doc.add_paragraph()
        run = p.add_run(section)
        
        # Set font properties
        run.font.name = 'Arial'
        run.font.size = Pt(10)

        # Check for "ASSESSMENT:" and "PLAN:" to apply bold and underline
        if section.startswith("ASSESSMENT:"):
            run.bold = True
            run.underline = True
        elif section.startswith("PLAN:"):
            run.bold = True
            run.underline = True

        # Set single spacing
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = Pt(12)

    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Title of the app
st.title("Note Management App")

st.header("Update an Existing Note")

room_input = st.text_input("Enter Room Number:")
paragraph_text = st.text_area("Enter the text for the note you want to update:")

options = ["Continue", "Will continue", "We will continue", "We shall continue"]

# Columns for the selectboxes
col1, col2 = st.columns(2)

with col1:
    selected_option = st.selectbox("Select a phrase to replace:", options)

with col2:
    replacement = st.selectbox("Select a replacement phrase:", options)

if st.button("Replace"):
    if paragraph_text:
        # Perform replacement
        updated_text = paragraph_text.replace(selected_option, replacement)
        word_file = create_word_doc(updated_text)
        
        # Ensure room input is valid for filename
        if room_input:
            file_name = f"u_{room_input}.docx"
        else:
            file_name = "updated_note.docx"

        with open(word_file, "rb") as f:
            st.download_button("Download Updated Note", f, file_name=file_name)
    else:
        st.error("Please enter some text to update.")

