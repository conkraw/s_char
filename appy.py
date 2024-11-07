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

# Function to fetch both physical exam days and diagnosis files
def fetch_data():
    # Fetch physical exam days from GitHub
    url_exam = "https://raw.githubusercontent.com/conkraw/s_char/master/physicalexam.txt"
    try:
        response_exam = requests.get(url_exam)
        if response_exam.status_code == 200:
            physical_exam_days = response_exam.text.splitlines()
        else:
            st.error("Error fetching physical exam days.")
            physical_exam_days = []
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching physical exam days: {e}")
        physical_exam_days = []

    # Dynamically list available diagnosis documents in the current directory
    available_docs = [f[:-5] for f in os.listdir('.') if f.endswith('.docx')]
    formatted_conditions = [format_diagnosis_name(doc) for doc in available_docs]

    # Create a mapping for formatted names to original filenames
    diagnosis_mapping = {format_diagnosis_name(doc): doc for doc in available_docs}

    return physical_exam_days, formatted_conditions, diagnosis_mapping

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text):
    doc = Document()
    
    for line in text.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = 'Arial'
        run.font.size = Pt(9)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
    
    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Function to combine diagnosis documents with formatted input text
def combine_notes(assess_text, diagnoses, free_text_diag=None, free_text_plan=None, physical_exam_day=None):
    doc = Document()
    
    # Add Objective section if a physical exam day is selected
    if physical_exam_day:
        objective_paragraph = doc.add_paragraph()
        objective_run = objective_paragraph.add_run("OBJECTIVE:")
        objective_run.bold = True
        objective_run.underline = True
        objective_run.font.name = 'Arial'
        objective_run.font.size = Pt(9)
        objective_paragraph.paragraph_format.space_after = Pt(0)
        objective_paragraph.paragraph_format.space_before = Pt(0)
        
        # Add the selected physical exam day below "OBJECTIVE"
        doc.add_paragraph(f"Physical Exam Day: {physical_exam_day}")
    
    # Add Assessment section
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

# Fetch both the diagnoses and physical exam days from GitHub
physical_exam_days, formatted_conditions, diagnosis_mapping = fetch_data()

# Sort the formatted conditions alphabetically
sorted_conditions = sorted(formatted_conditions)

selected_conditions = st.multiselect("Choose diagnoses:", sorted_conditions)

assessment_text = st.text_area("Enter Assessment:")

# Add the selection input for physical exam day
if physical_exam_days:
    selected_exam_day = st.selectbox("Select Physical Examination Day:", physical_exam_days)
else:
    selected_exam_day = None

if st.button("Submit New Note"):
    if selected_conditions and assessment_text and room_number:
        combined_file = combine_notes(assessment_text, selected_conditions, physical_exam_day=selected_exam_day)
        file_name = f"{room_number}.docx"
        with open(combined_file, "rb") as f:
            st.download_button("Download Combined Note", f, file_name=file_name)
    else:
        st.error("Please fill out all fields.")


