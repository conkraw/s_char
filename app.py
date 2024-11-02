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

# Sidebar for navigation
option = st.sidebar.selectbox("Choose an option:", ["New Note", "Update Note"])

if option == "New Note":
    st.header("Create a New Note")
    
    # Selection for medical condition
    condition = st.selectbox("Choose a condition:", 
                              ["Acute Hypoxemic Respiratory Failure", "Sepsis", "Hyponatremia"])
    
    # Text area for additional notes
    additional_notes = st.text_area("Enter any additional notes here:")
    
    if st.button("Submit New Note"):
        if condition:
            # Combine condition and additional notes for the note content
            note_text = f"{condition}\n{additional_notes}"
            st.success("New note created!")
            st.write(note_text)

            # Create and download button for the new note
            word_file = create_word_doc(note_text)
            with open(word_file, "rb") as f:
                st.download_button("Download New Note", f, file_name="new_note.docx")
        else:
            st.error("Please select a condition.")

elif option == "Update Note":
    st.header("Update an Existing Note")
    
    paragraph_text = st.text_area("Enter the text for the note you want to update:")

    options = ["Continue", "Will continue", "We will continue", "We shall continue"]
    selected_option = st.selectbox("Select a phrase to replace:", options)
    replacement = st.selectbox("Select a replacement phrase:", options)

    if st.button("Replace"):
        if paragraph_text:
            # Perform replacement
            updated_text = paragraph_text.replace(selected_option, replacement)

            # Display the updated note
            #st.subheader("Updated Note:")
            #st.write(updated_text)

            # Create and download button for the updated note
            word_file = create_word_doc(updated_text)
            with open(word_file, "rb") as f:
                st.download_button("Download Updated Note", f, file_name="updated_note.docx")
        else:
            st.error("Please enter some text to update.")

