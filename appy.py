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

# Function to fetch physical exam day files from GitHub repository
def fetch_physical_exam_days():
    url = "https://api.github.com/repos/conkraw/s_char/contents/physicalexam"
    physical_exam_days = []
    
    try:
        # Send GET request to GitHub API to fetch contents of the 'physicalexam' folder
        response = requests.get(url)
        
        if response.status_code == 200:
            # Parse the response JSON
            files = response.json()
            for file in files:
                # Filter out only .docx files (assuming they are the physical exam day files)
                if file['name'].endswith('.docx'):
                    physical_exam_days.append(file['name'])
        else:
            st.error(f"Failed to fetch physical exam days: Status code {response.status_code}")
            st.write(response.text)  # Display the response content for debugging
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching physical exam days: {e}")
        st.write(str(e))  # Display the exception details for debugging
    
    return physical_exam_days

# Function to download and extract content from a physical exam day document
def fetch_physical_exam_content(exam_file_name):
    url = f"https://raw.githubusercontent.com/conkraw/s_char/master/physicalexam/{exam_file_name}"
    try:
        # Download the physical exam document as raw content
        response = requests.get(url)
        
        if response.status_code == 200:
            # Save the content as a .docx file locally
            with open(exam_file_name, "wb") as f:
                f.write(response.content)
            
            # Now read the content from the local file
            exam_doc = Document(exam_file_name)
            content = "\n".join([para.text for para in exam_doc.paragraphs])
            os.remove(exam_file_name)  # Remove the local file after reading content
            return content
        else:
            st.error(f"Failed to fetch physical exam content: Status code {response.status_code}")
            return ""
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching physical exam content: {e}")
        return ""

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
        
        # Fetch the content of the selected physical exam day
        physical_exam_content = fetch_physical_exam_content(physical_exam_day)
        
        # Add the fetched content under the OBJECTIVE section
        if physical_exam_content:
            doc.add_paragraph(physical_exam_content)
    
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
physical_exam_days = fetch_physical_exam_days()

# Dynamically list available diagnosis documents in the current directory
available_docs = [f[:-5] for f in os.listdir('.') if f.endswith('.docx')]
formatted_conditions = [format_diagnosis_name(doc) for doc in available_docs]

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


