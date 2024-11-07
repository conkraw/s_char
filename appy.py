import streamlit as st
from docx import Document
from docx.shared import Pt
import os
import re
import requests

# Function to format diagnosis names
def format_diagnosis_name(diagnosis):
    diagnosis = diagnosis.replace('_', ' ')
    formatted_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', diagnosis)
    formatted_name = formatted_name.title()
    return formatted_name

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text):
    doc = Document()

    # First, add the "OBJECTIVE:" as the first section
    objective_paragraph = doc.add_paragraph()
    objective_run = objective_paragraph.add_run("OBJECTIVE:")
    objective_run.bold = True
    objective_run.underline = True
    objective_run.font.name = 'Arial'
    objective_run.font.size = Pt(9)
    
    # Add a space after the title to separate it from the content
    objective_paragraph.paragraph_format.space_after = Pt(0)
    objective_paragraph.paragraph_format.space_before = Pt(0)

    # Now, add the rest of the content after "OBJECTIVE:"
    for line in text.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = 'Arial'
        run.font.size = Pt(9)

        # Set paragraph spacing to ensure single line spacing
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)

    # Save the document
    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Function to fetch the raw content of a Word document directly from GitHub (via raw URL)
def read_github_doc(github_url):
    response = requests.get(github_url)
    if response.status_code == 200:
        with open("temp_document.docx", 'wb') as f:
            f.write(response.content)
        
        # Load the document and extract text
        doc = Document("temp_document.docx")
        document_text = ""
        for para in doc.paragraphs:
            document_text += para.text + '\n'
        os.remove("temp_document.docx")  # Clean up the temporary file
        return document_text
    else:
        st.error(f"Error downloading the document from GitHub. Status Code: {response.status_code}")
        return None

# Function to fetch the list of .docx files from the GitHub repository
def get_github_docs_list(github_repo, folder_path):
    url = f"https://api.github.com/repos/{github_repo}/contents/{folder_path}"
    response = requests.get(url)
    
    if response.status_code == 200:
        files = response.json()
        # Filter only .docx files
        doc_files = [file['name'] for file in files if file['name'].endswith('.docx')]
        return doc_files
    else:
        st.error(f"Failed to fetch files from GitHub repository. Status Code: {response.status_code}")
        return []

# Function to combine diagnosis documents with formatted input text
def combine_notes(physical_exam_text, assess_text, diagnoses, free_text_diag=None, free_text_plan=None):
    doc = Document()

    # First, add the "OBJECTIVE:" section
    doc.add_paragraph("OBJECTIVE:", style='Heading 1')

    # Physical Exam Section (first)
    if physical_exam_text:
        physical_exam_paragraph = doc.add_paragraph()
        run = physical_exam_paragraph.add_run(physical_exam_text)  # Adding the content as a run
        run.font.name = 'Arial'  # Set font for the run
        run.font.size = Pt(9)  # Set font size for the run
        physical_exam_paragraph.paragraph_format.space_before = Pt(0)
        physical_exam_paragraph.paragraph_format.space_after = Pt(0)

    # Assessment Section (second)
    assessment_paragraph = doc.add_paragraph()
    assessment_run = assessment_paragraph.add_run("ASSESSMENT:")
    assessment_run.bold = True
    assessment_run.underline = True
    assessment_run.font.name = 'Arial'
    assessment_run.font.size = Pt(9)
    assessment_paragraph.paragraph_format.space_after = Pt(0)
    assessment_paragraph.paragraph_format.space_before = Pt(0)
    
    assessment_content = doc.add_paragraph(assess_text)
    for run in assessment_content.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)

    # Plan Section (third)
    plan_paragraph = doc.add_paragraph()
    plan_run = plan_paragraph.add_run("PLAN:")
    plan_run.bold = True
    plan_run.underline = True
    plan_run.font.name = 'Arial'
    plan_run.font.size = Pt(9)
    plan_paragraph.paragraph_format.space_after = Pt(0)
    plan_paragraph.paragraph_format.space_before = Pt(0)

    # Add selected diagnoses (from the list)
    for i, diagnosis in enumerate(diagnoses, start=1):
        diagnosis_key = diagnosis.lower().replace(' ', '_') + '.docx'
        
        # Construct the raw URL for the diagnosis document from your GitHub repo
        diagnosis_url = f"https://raw.githubusercontent.com/conkraw/s_char/main/diagnoses/{diagnosis_key}"
        
        # Download and add diagnosis content if it exists
        diagnosis_text = read_github_doc(diagnosis_url)
        if diagnosis_text:
            diagnosis_paragraph = doc.add_paragraph()
            diagnosis_run = diagnosis_paragraph.add_run(f"{i}). {diagnosis}")
            diagnosis_run.font.size = Pt(9)
            diagnosis_run.font.name = 'Arial'
            diagnosis_paragraph.paragraph_format.space_before = Pt(0)
            diagnosis_paragraph.paragraph_format.space_after = Pt(0) 
            
            # Add diagnosis text
            for para in diagnosis_text.split("\n"):
                new_paragraph = doc.add_paragraph(para)
                new_paragraph.paragraph_format.space_before = Pt(0)
                new_paragraph.paragraph_format.space_after = Pt(0)  # No space after diagnosis content
                
                for run in new_paragraph.runs:
                    run.font.name = 'Arial'
                    run.font.size = Pt(9)

    # Append free-text diagnosis and plan if provided
    if free_text_diag and free_text_plan:
        doc.add_paragraph()  # Add a blank line
        doc.add_paragraph(f"Free Text Diagnosis: {free_text_diag}")
        doc.add_paragraph(f"Plan: {free_text_plan}")

    output_path = "combined_note.docx"
    doc.save(output_path)
    return output_path

# Title of the app
st.title("Note Management App")

# Header for the New Note section
st.header("Create a New Note")

# Input for room number
room_number = st.text_input("Enter Room Number:")

# GitHub repo info
github_repo = "conkraw/s_char"  # Replace with your actual GitHub repository
folder_path = "physicalexam"  # Folder in your GitHub repo containing the exam documents

# Fetch the list of available documents from GitHub
available_exam_docs = get_github_docs_list(github_repo, folder_path)

# Allow user to select a physical exam document from the available list
if available_exam_docs:
    selected_exam = st.selectbox("Select a Physical Exam Document:", available_exam_docs)
else:
    st.warning("No exam documents found in the specified folder.")

# Fetch the content of the selected physical exam document
physical_exam_text = None
if selected_exam:
    github_url = f"https://raw.githubusercontent.com/{github_repo}/main/{folder_path}/{selected_exam}"
    physical_exam_text = read_github_doc(github_url)

# Dynamically list available diagnosis documents in the current directory
available_docs = [f[:-5] for f in os.listdir('.') if f.endswith('.docx') and f != selected_exam]  # Exclude selected exam doc
formatted_conditions = [format_diagnosis_name(doc) for doc in available_docs]

# Sort the formatted conditions alphabetically
sorted_conditions = sorted(formatted_conditions)

# Create a mapping for formatted names to original filenames
diagnosis_mapping = {format_diagnosis_name(doc): doc for doc in available_docs}

selected_conditions = st.multiselect("Choose diagnoses:", sorted_conditions)

# Input for assessment
assessment_text = st.text_area("Enter Assessment:")

if st.button("Submit New Note"):
    if selected_conditions and assessment_text and room_number:
        combined_file = combine_notes(physical_exam_text, assessment_text, selected_conditions)  # Add free_text_diag, free_text_plan if needed
        file_name = f"{room_number}.docx"
        with open(combined_file, "rb") as f:
            st.download_button("Download Combined Note", f, file_name=file_name)
    else:
        st.error("Please fill out all fields.")



