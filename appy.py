import streamlit as st
from docx import Document
from docx.shared import Pt
import os
import re
import requests
from io import BytesIO

# Function to format diagnosis names
def format_diagnosis_name(diagnosis):
    diagnosis = diagnosis.replace('_', ' ')
    formatted_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', diagnosis)
    formatted_name = formatted_name.title()
    return formatted_name

# Function to fetch the physical exam day documents from GitHub (handling .docx files)
def fetch_physical_exam_docs():
    # GitHub raw file URL for the physical exam documents
    url = 'https://raw.githubusercontent.com/conkraw/s_char/main/physicalexam'
    response = requests.get(url)
    if response.status_code == 200:
        files = response.text.splitlines()  # Assuming the files are listed as plain text in the GitHub repo
        return files  # List of file names
    else:
        st.error(f"Error fetching files from GitHub. Status code: {response.status_code}")
        return []

# Function to fetch and process a .docx file from GitHub
def fetch_physical_exam_text(exam_file):
    url = f'https://raw.githubusercontent.com/conkraw/s_char/main/physicalexam/{exam_file}'
    response = requests.get(url)

    if response.status_code == 200:
        # Use BytesIO to load the .docx content into memory
        docx_file = BytesIO(response.content)
        doc = Document(docx_file)
        exam_text = "\n".join([para.text for para in doc.paragraphs])
        return exam_text
    else:
        st.error(f"Error fetching the selected physical exam document: {exam_file}")
        return ""

# Function to combine diagnosis documents with formatted input text
def combine_notes(physical_exam_text, assess_text, diagnoses, free_text_diag=None, free_text_plan=None):
    doc = Document()
    
    # Objective Section (Physical Exam)
    objective_paragraph = doc.add_paragraph()
    objective_run = objective_paragraph.add_run("OBJECTIVE:")
    objective_run.bold = True
    objective_run.underline = True
    objective_run.font.name = 'Arial'
    objective_run.font.size = Pt(9)
    objective_paragraph.paragraph_format.space_after = Pt(0)
    objective_paragraph.paragraph_format.space_before = Pt(0)
    
    # Add physical exam content
    objective_content = doc.add_paragraph(physical_exam_text)
    for run in objective_content.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)
    
    # Assessment section
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

    # Plan section
    plan_paragraph = doc.add_paragraph()
    plan_run = plan_paragraph.add_run("PLAN:")
    plan_run.bold = True
    plan_run.underline = True
    plan_run.font.name = 'Arial'
    plan_run.font.size = Pt(9)
    plan_paragraph.paragraph_format.space_after = Pt(0)
    plan_paragraph.paragraph_format.space_before = Pt(0)

    # Add selected diagnoses
    for i, diagnosis in enumerate(diagnoses, start=1):
        diagnosis_key = diagnosis.lower().replace(' ', '_') + '.docx'
        if os.path.exists(diagnosis_key):
            diagnosis_paragraph = doc.add_paragraph()
            diagnosis_run = diagnosis_paragraph.add_run(f"{i}). {diagnosis}")
            diagnosis_run.font.size = Pt(9)
            diagnosis_run.font.name = 'Arial'
            diagnosis_paragraph.paragraph_format.space_before = Pt(0)
            diagnosis_paragraph.paragraph_format.space_after = Pt(0) 
            
            diagnosis_doc = Document(diagnosis_key)
            for para in diagnosis_doc.paragraphs:
                new_paragraph = doc.add_paragraph(para.text)
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

# Fetch available physical exam documents from GitHub
exam_docs = fetch_physical_exam_docs()

# Let the user select a physical exam document
selected_exam = st.selectbox("Select Physical Exam Day:", exam_docs)

# Input for free text diagnosis and plan
assessment_text = st.text_area("Enter Assessment:")

if st.button("Submit New Note"):
    if selected_exam and assessment_text and room_number:
        # Fetch the physical exam content from GitHub
        physical_exam_text = fetch_physical_exam_text(selected_exam)
        if physical_exam_text:
            combined_file = combine_notes(physical_exam_text, assessment_text, [])
            file_name = f"{room_number}.docx"
            with open(combined_file, "rb") as f:
                st.download_button("Download Combined Note", f, file_name=file_name)
        else:
            st.error("Error fetching the physical exam document.")
    else:
        st.error("Please fill out all fields.")



