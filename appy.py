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

def fetch_files_from_github(folder_name, fetch_diagnoses=True):
    url = f"https://api.github.com/repos/conkraw/s_char/contents/{folder_name}"
    files = []

    try:
        # Send GET request to GitHub API to fetch contents of the folder
        response = requests.get(url)
        
        if response.status_code == 200:
            # Parse the response JSON
            response_files = response.json()
            for file in response_files:
                # Filter out only .docx files, adjust for diagnosis folder
                if file['name'].endswith('.docx') and (fetch_diagnoses or folder_name in ["physicalexam", "ros"]):
                    files.append(file['name'])
        else:
            st.error(f"Failed to fetch files: Status code {response.status_code}")
            st.write(response.text)  # Display the response content for debugging
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching files: {e}")
        st.write(str(e))  # Display the exception details for debugging
    
    return files

# Function to download and extract content from a document (for diagnosis fetching)
def fetch_file_content(folder_name, file_name, fetch_diagnosis=True):
    url = f"https://raw.githubusercontent.com/conkraw/s_char/master/{folder_name}/{file_name}"
    
    try:
        # If the folder is diagnoses, proceed to fetch it
        if fetch_diagnosis:
            response = requests.get(url)
            if response.status_code == 200:
                # Save and process the .docx file
                with open(file_name, "wb") as f:
                    f.write(response.content)
                doc = Document(file_name)
                content = "\n".join([para.text for para in doc.paragraphs])
                os.remove(file_name)
                return doc  # Return the Document object, not just plain text
            else:
                st.error(f"Failed to fetch content: Status code {response.status_code}")
                return None
        else:
            return None  # Return None for ROS and physical exam files if not needed
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching content: {e}")
        return None

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

def combine_notes(assess_text, critical_care_reason, diagnoses, free_text_diag=None, free_text_plan=None, physical_exam_day=None, ros_file=None, critical_care_time=None):
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

    # Add "OVERNIGHT EVENTS:" section
    overnight_paragraph = doc.add_paragraph()
    overnight_header_run = overnight_paragraph.add_run("OVERNIGHT EVENTS:")
    overnight_header_run.bold = True
    overnight_header_run.underline = True
    overnight_header_run.font.name = 'Arial'
    overnight_header_run.font.size = Pt(9)
    overnight_content_run = overnight_paragraph.add_run(" No acute events were noted overnight.")
    overnight_content_run.font.name = 'Arial'
    overnight_content_run.font.size = Pt(9)
    overnight_paragraph.paragraph_format.space_after = Pt(6)
    overnight_paragraph.paragraph_format.space_before = Pt(6)

    # Add "SUBJECTIVE" header and ROS content
    if ros_file != "None.docx":
        ros_paragraph = doc.add_paragraph()
        
        # Add SUBJECTIVE heading (bold, underline)
        ros_run = ros_paragraph.add_run("SUBJECTIVE: ")
        ros_run.bold = True
        ros_run.underline = True
        ros_run.font.name = 'Arial'
        ros_run.font.size = Pt(9)

        ros_paragraph.paragraph_format.space_after = Pt(0)
        ros_paragraph.paragraph_format.space_before = Pt(0)
        
        # Fetch the content of the selected ROS file
        ros_doc = fetch_file_content('ros', ros_file)

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

                new_paragraph.paragraph_format.space_after = Pt(6)
                new_paragraph.paragraph_format.space_before = Pt(0)

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

    # Add Assessment section
    assessment_paragraph = doc.add_paragraph()
    assessment_run = assessment_paragraph.add_run("ASSESSMENT:")
    assessment_run.bold = True
    assessment_run.underline = True
    assessment_run.font.name = 'Arial'
    assessment_run.font.size = Pt(9)
    assessment_paragraph.paragraph_format.space_after = Pt(0)
    assessment_paragraph.paragraph_format.space_before = Pt(6)

    assessment_content = doc.add_paragraph(assess_text)
    for run in assessment_content.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)

    # Add the "Why Critical Care" dropdown selection after assessment only if it's not empty
    if critical_care_reason != "":
        critical_care_paragraph = doc.add_paragraph()
        critical_care_run = critical_care_paragraph.add_run("CLINICAL INDICATIONS FOR CRITICAL CARE SERVICES:")
        critical_care_run.bold = True
        critical_care_run.underline = True
        critical_care_run.font.name = 'Arial'
        critical_care_run.font.size = Pt(9)
        critical_care_paragraph.paragraph_format.space_after = Pt(0)
        critical_care_paragraph.paragraph_format.space_before = Pt(0)

        critical_care_content = doc.add_paragraph(critical_care_reason)
        for run in critical_care_content.runs:
            run.font.name = 'Arial'
            run.font.size = Pt(9)

    # Add plan if exists
    if free_text_plan:
        plan_paragraph = doc.add_paragraph("PLAN:")
        plan_paragraph.bold = True
        plan_paragraph.underline = True
        plan_paragraph.font.name = 'Arial'
        plan_paragraph.font.size = Pt(9)

    # Save the generated document
    doc.save("Combined_Note.docx")

    # Return the file path to the user
    return "Combined_Note.docx"


# Call this function when you have the proper selections and inputs:
# combine_notes(assess_text, critical_care_reason, diagnoses, free_text_diag, free_text_plan, physical_exam_day, ros_file, critical_care_time)
