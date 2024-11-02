import streamlit as st

# Title of the app
st.title("Note Management App")

# Sidebar for navigation
option = st.sidebar.selectbox("Choose an option:", ["New Note", "Update Note"])

if option == "New Note":
    st.header("Create a New Note")
    note_text = st.text_area("Enter your note text here:")
    if st.button("Submit"):
        st.success("New note created!")
        st.write(note_text)

elif option == "Update Note":
    st.header("Update an Existing Note")
    paragraph_text = st.text_area("Enter the text for the note you want to update:")

    if st.button("Submit"):
        if paragraph_text:
            # Options for replacement
            options = ["Continue", "Will continue", "We will continue", "We shall continue"]
            selected_option = st.selectbox("Select a phrase to replace:", options)

            # Replacement options
            replacement = st.selectbox("Select a replacement phrase:", options)

            # Perform replacement
            updated_text = paragraph_text.replace(selected_option, replacement)

            # Display the updated note
            st.subheader("Updated Note:")
            st.write(updated_text)
        else:
            st.error("Please enter some text to update.")
