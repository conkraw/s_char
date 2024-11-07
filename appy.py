import streamlit as st
from docx import Document
from docx.shared import Pt
import os
import re

# Helper function to format diagnosis names
def format_diagnosis_name(diagnosis):
    diagnosis = diagnosis.replace('_', ' ')
    formatted_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', diagnosis)
    return formatted_name.title()

# Helper function to apply font style and size to a paragraph
def apply_font(paragraph, font_name='Arial', font_size=Pt(9)):
    for run in paragraph.runs:
        run.font.name = font_name
        run.font.size = font_size

# Helper function to add a section header
def add_section_header(doc, section_title):
    section_paragraph = doc.add_paragraph()
    section_run = section_paragraph.add_run(section_title)
    section_run.bold = True
    section_run.underline = True
    apply_font(section_paragraph)
    section_paragraph.paragraph_format.space_after = Pt(0)
    section_paragraph.paragraph_format.space_before = Pt(0)
    return section_paragraph

# Function to fetch content from .docx files
def fetch_file_content(file_type, filename):
    try:
        doc = Document(filename)
        return doc
    except Exception as e:
        st.error(f"Error reading {file_type} file: {e}")
        return None

# Function to create a Word document with specific font settings and single spacing
def create_word_doc(text):
    doc = Document()
    for line in text.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        apply_font(p)  # Apply the font settings
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
    
    output_path = "updated_note.docx"
    doc.save(output_path)
    return output_path

# Function to combine all sections into a single note
def combine_notes(assess_text, critical_care_reason, diagnoses, free_text_diag=None, free_text_plan=None, physical_exam_day=None, ros_file=None):
    doc = Document()

    # Introductory statement
    intro_paragraph = doc.add_paragraph()
    intro_run = intro_paragraph.add_run(
        "I personally examined the patient separately and discussed the case with the resident/physician assistant and with any services involved in a multidisciplinary fashion. I agree with the resident/physician's assistant documentation with any exceptions noted below:"
    )
    intro_run.italic = True
    apply_font(intro_paragraph)
    
    # Add Review of Systems (ROS) if file provided
    if ros_file:
        add_section_header(doc, "REVIEW OF SYSTEMS:")
        ros_doc = fetch_file_content('ROS', ros_file)
        if ros_doc:
            for para in ros_doc.paragraphs:
                p = doc.add_paragraph(para.text)
                apply_font(p)
    
    # Add Objective section if physical exam file is provided
    if physical_exam_day:
        add_section_header(doc, "OBJECTIVE:")
        physical_exam_doc = fetch_file_content('Physical Exam', physical_exam_day)
        if physical_exam_doc:
            for para in physical_exam_doc.paragraphs:
                p = doc.add_paragraph(para.text)
                apply_font(p)

    # Add Assessment section
    add_section_header(doc, "ASSESSMENT:")
    assessment_paragraph = doc.add_paragraph(assess_text)
    apply_font(assessment_paragraph)

    # Add Critical Care section with dropdown selection
    add_section_header(doc, "WHY CRITICAL CARE:")
    critical_care_options = [
        "The patient requires critical care services due to the continuous management of invasive respiratory as well as hemodynamic support, which if not provided, would be life threatening to the patient.",
        "The patient requires critical care services due to the high risk of neurologic decompensation which could result in airway loss and respiratory failure, which is life threatening to the patient.",
        # (other options)
    ]
    selected_critical_care = st.selectbox("Clinical Indications for Critical Care Services:", critical_care_options)
    critical_care_paragraph = doc.add_paragraph(selected_critical_care)
    apply_font(critical_care_paragraph)

    # Add Plan section
    add_section_header(doc, "PLAN:")

    # Add selected diagnoses from files
    for i, diagnosis in enumerate(diagnoses, start=1):
        diagnosis_key = diagnosis.lower().replace(' ', '_') + '.docx'
        if os.path.exists(diagnosis_key):
            diagnosis_paragraph = doc.add_paragraph()
            diagnosis_run = diagnosis_paragraph.add_run(f"{i}). {diagnosis}")
            apply_font(diagnosis_paragraph)
            diagnosis_doc = Document(diagnosis_key)
            for para in diagnosis_doc.paragraphs:
                p = doc.add_paragraph(para.text)
                apply_font(p)
    
    # Append free-text diagnosis and plan if provided
    if free_text_diag and free_text_plan:
        doc.add_paragraph(f"Free Text Diagnosis: {free_text_diag}")
        doc.add_paragraph(f"Plan: {free_text_plan}")

    # Save and return document path
    output_path = "combined_note.docx"
    doc.save(output_path)
    return output_path

