import streamlit as st
from docx import Document
from docx.shared import Pt
import os
import re
import requests

# Function to fetch and format diagnosis names
def format_diagnosis_name(diagnosis):
    diagnosis = diagnosis.replace('_', ' ')
    formatted_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', diagnosis)
    formatted_name = formatted_name.title()
    return formatted_name

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

# Function to combine all sections into a single note
def combine_notes(assess_text, critical_care_reason, diagnoses, free_text_diag=None, free_text_plan=None, physical_exam_day=None, ros_file=None):
    doc = Document()

    # Add the introductory statement at the top (italicized, Arial, font size 9)
    intro_paragraph = doc.add_paragraph()
    intro_run = intro_paragraph.add_run(
        "I personally examined the patient separately and discussed the case with the resident/physician assistant and with any services involved in a multidisciplinary fashion. I agree with the resident/physician's assistant documentation with any exceptions noted below:"
    )
    intro_run.italic = True
    intro_run.font.name = 'Arial'
    intro_run.font.size = Pt(9)
    intro_paragraph.paragraph_format.space_after = Pt(0)
    intro_paragraph.paragraph_format.space_before = Pt(0)

    last_paragraph = doc.add_paragraph()  # Add an empty paragraph
    last_paragraph.paragraph_format.space_after = Pt(0)  # Set space after to a small value (6 pt)

    # Add Review of Systems section first (if ROS file is selected)
    if ros_file:
        ros_paragraph = doc.add_paragraph()
        ros_run = ros_paragraph.add_run("REVIEW OF SYSTEMS:")
        ros_run.bold = True
        ros_run.underline = True
        ros_run.font.name = 'Arial'
        ros_run.font.size = Pt(9)
        ros_paragraph.paragraph_format.space_after = Pt(0)
        ros_paragraph.paragraph_format.space_before = Pt(0)
        
        # Fetch the content of the selected ROS file
        ros_doc = fetch_file_content('ros', ros_file)
        
        # Add the fetched content under the REVIEW OF SYSTEMS section
        if ros_doc:
            for para in ros_doc.paragraphs:
                new_paragraph = doc.add_paragraph()
                
                # Split the paragraph text by the target phrases and apply formatting to those specific phrases
                text = para.text
                text_chunks = []
                
                # Check and split for "OVERNIGHT EVENTS"
                if "OVERNIGHT EVENTS" in text:
                    text_chunks.extend(text.split("OVERNIGHT EVENTS"))
                    text_chunks.insert(1, "OVERNIGHT EVENTS")
                else:
                    text_chunks.append(text)

                # Now handle applying bold/underline to "OVERNIGHT EVENTS" and "SUBJECTIVE"
                formatted_text = []
                for chunk in text_chunks:
                    if chunk == "OVERNIGHT EVENTS":
                        # Apply bold and underline only to "OVERNIGHT EVENTS"
                        run = new_paragraph.add_run(chunk)
                        run.bold = True
                        run.underline = True
                    elif "SUBJECTIVE" in chunk:
                        # Apply bold and underline to "SUBJECTIVE"
                        run = new_paragraph.add_run(chunk)
                        run.bold = True
                        run.underline = True
                    else:
                        # For normal text, just add as-is
                        run = new_paragraph.add_run(chunk)
                    run.font.name = 'Arial'
                    run.font.size = Pt(9)
                
                new_paragraph.paragraph_format.space_after = Pt(0)
                new_paragraph.paragraph_format.space_before = Pt(0)

            last_paragraph = doc.add_paragraph()  # Add an empty paragraph
            last_paragraph.paragraph_format.space_after = Pt(0)  # Set space after to a small value (6 pt)
            
            for run in last_paragraph.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(9)

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
        physical_exam_doc = fetch_file_content('physicalexam', physical_exam_day)
        
        # Add the fetched content under the OBJECTIVE section
        if physical_exam_doc:
            for para in physical_exam_doc.paragraphs:
                new_paragraph = doc.add_paragraph(para.text)
                new_paragraph.paragraph_format.space_after = Pt(0)
                new_paragraph.paragraph_format.space_before = Pt(0)
                for run in new_paragraph.runs:
                    run.font.name = 'Arial'
                    run.font.size = Pt(9)
            
            last_paragraph = doc.add_paragraph()  # Add an empty paragraph
            last_paragraph.paragraph_format.space_after = Pt(0)  # Set space after to a small value (6 pt)
            
            for run in last_paragraph.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(9)

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

    # Add the "Why Critical Care" dropdown selection after assessment
    critical_care_paragraph = doc.add_paragraph()
    critical_care_run = critical_care_paragraph.add_run("WHY CRITICAL CARE:")
    critical_care_run.bold = True
    critical_care_run.underline = True
    critical_care_run.font.name = 'Arial'
    critical_care_run.font.size = Pt(9)
    critical_care_paragraph.paragraph_format.space_after = Pt(0)
    critical_care_paragraph.paragraph_format.space_before = Pt(0)

    critical_care_options = [
        "The patient requires critical care services due to the continuous management of invasive respiratory as well as hemodynamic support, which if not provided, would be life threatening to the patient.",
        "The patient requires critical care services due to the high risk of neurologic decompensation which could result in airway loss and respiratory failure, which is life threatening to the patient.",
        "The patient requires critical care services for management of the patient's airway and invasive mechanical respiratory support without which would be life threatening to the patient.",
        "The patient requires critical care services for management of the patient's airway and non-invasive mechanical respiratory support without which would be life threatening to the patient.",
        "The patient requires critical care services as the patient is at high risk of withdrawal, and thus requires intensive care monitoring."
    ]
    
    selected_critical_care = st.selectbox("Why Critical Care:", critical_care_options)
    
    critical_care_content = doc.add_paragraph(selected_critical_care)
    for run in critical_care_content.runs:
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
                new_paragraph.paragraph_format.space_after = Pt(0)
                
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

