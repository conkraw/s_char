import streamlit as st
from docx import Document
from docx.shared import Pt
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# Function to read the content of a .docx file from a URL
def read_docx_from_url(url, headers):
    response = requests.get(url, headers=headers)
    doc = Document(BytesIO(response.content))
    content = []
    for para in doc.paragraphs:
        content.append(para.text)
    return '\n'.join(content)

# Function to fetch the list of .docx files from a GitHub directory
def get_github_files(github_repo_url, directory, headers):
    api_url = f"{github_repo_url}/contents/{directory}"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Will raise an error for invalid responses
        files = response.json()

        docx_files = []
        for file in files:
            if file['name'].endswith('.docx'):
                raw_url = file['download_url']
                docx_files.append({'name': file['name'], 'url': raw_url})

        return docx_files
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching files from GitHub: {e}")
        return []

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text, ros_text, physical_exam_text):
    doc = Document()

    # The specific phrase to add at the top of the document
    intro_text = (
        "I personally examined the patient separately and discussed the case with the resident/physician assistant "
        "and with any services involved in a multidisciplinary fashion. I agree with the resident/physician's assistant "
        "documentation with any exceptions noted below:"
    )

    # Add the introductory text as a paragraph, italicized, with Arial font and size 9
    intro_paragraph = doc.add_paragraph()
    intro_run = intro_paragraph.add_run(intro_text)
    intro_run.italic = True  # Set the intro text to be italicized
    intro_run.font.name = 'Arial'  # Set the font to Arial
    intro_run.font.size = Pt(9)   # Set the font size to 9

    # Add a line break after the introductory statement
    doc.add_paragraph()  # This adds a blank line after the intro text

    # Add ROS if selected
    if ros_text:
        ros_paragraph = doc.add_paragraph()
        ros_run = ros_paragraph.add_run("Review of Systems:\n" + ros_text)
        ros_run.font.name = 'Arial'
        ros_run.font.size = Pt(10)
        doc.add_paragraph()  # Add a blank line after ROS

    # Add Physical Exam (always required)
    physical_exam_paragraph = doc.add_paragraph()
    physical_exam_run = physical_exam_paragraph.add_run("Physical Exam:\n" + physical_exam_text)
    physical_exam_run.font.name = 'Arial'
    physical_exam_run.font.size = Pt(10)
    doc.add_paragraph()  # Add a blank line after Physical Exam

    # Process the rest of the text passed into the function
    sections = text.split('\n')
    for section in sections:
        p = doc.add_paragraph()
        run = p.add_run(section)

        # Set font properties for the rest of the document
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

# Use session state to manage the text area content
if 'paragraph_text' not in st.session_state:
    st.session_state.paragraph_text = ""

st.session_state.paragraph_text = st.text_area("Enter the text for the note you want to update:", value=st.session_state.paragraph_text)

# GitHub Repo URL and authentication headers
github_repo_url = "https://api.github.com/repos/conkraw/s_char"
github_token = st.text_input("Enter your GitHub Personal Access Token (optional, for increased rate limit):")
headers = {"Authorization": f"token {github_token}"} if github_token else {}

# Fetch available ROS and Physical Exam files from GitHub using ThreadPoolExecutor for concurrent fetching
with ThreadPoolExecutor() as executor:
    ros_future = executor.submit(get_github_files, github_repo_url, "ros", headers)
    physical_exam_future = executor.submit(get_github_files, github_repo_url, "physicalexam", headers)

    ros_files = ros_future.result()
    physical_exam_files = physical_exam_future.result()

# Debug: Check if Physical Exam files are being fetched
st.write(f"ROS Files: {ros_files}")
st.write(f"Physical Exam Files: {physical_exam_files}")

# Handle case where no Physical Exam files are fetched
if not physical_exam_files:
    st.error("No Physical Exam files found in the repository.")

# Dropdowns for selecting ROS and Physical Exam files
ros_options = [f["name"] for f in ros_files]
physical_exam_options = [f["name"] for f in physical_exam_files]

ros_selection = st.selectbox("Select ROS file:", ros_options)
physical_exam_selection = st.selectbox("Select Physical Exam file:", physical_exam_options)

# Allow the user to input their text for replacement
options = ["Continue", "Will continue", "We will continue", "We shall continue"]
col1, col2 = st.columns(2)

with col1:
    selected_option = st.selectbox("Select a phrase to replace:", options)

with col2:
    replacement = st.selectbox("Select a replacement phrase:", options)

# Construct the URLs for the selected files
ros_url = next(f["url"] for f in ros_files if f["name"] == ros_selection)
physical_exam_url = next(f["url"] for f in physical_exam_files if f["name"] == physical_exam_selection)

ros_text = read_docx_from_url(ros_url, headers)  # Fetch the content of ROS file
physical_exam_text = read_docx_from_url(physical_exam_url, headers)  # Fetch the content of Physical Exam file

if st.button("Replace"):
    if st.session_state.paragraph_text:
        # Perform replacement
        updated_text = st.session_state.paragraph_text.replace(selected_option, replacement)
        
        # Create the Word document
        word_file = create_word_doc(updated_text, ros_text, physical_exam_text)
        
        # Ensure room input is valid for filename
        if room_input:
            file_name = f"u_{room_input}.docx"
        else:
            file_name = "updated_note.docx"

        with open(word_file, "rb") as f:
            st.download_button("Download Updated Note", f, file_name=file_name)

        # Clear the text area
        st.session_state.paragraph_text = ""  # Clear the text area
        st.success("Replacement done! Text area cleared.")
    else:
        st.error("Please enter some text to update.")



