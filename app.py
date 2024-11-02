import streamlit as st
from docx import Document

# Function to create a Word document
def create_word_doc(text):
    doc = Document()
    doc.add_paragraph(text)
    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

st.title("Update Note")

# Text area for the note to be updated
paragraph_text = st.text_area("Enter the text for the note you want to update:")

if st.button("Submit"):
    if paragraph_text:
        # Options for replacement
        options = ["Continue", "Will continue", "We will continue", "We shall continue"]
        
        selected_option = st.selectbox("Select a phrase to replace:", options)
        replacement = st.selectbox("Select a replacement phrase:", options)

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

