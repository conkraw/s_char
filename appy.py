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

def read_docx_from_url(url):
    # Ensure the URL starts with https:// or http://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url  # Default to https if not present

    response = requests.get(url)
    doc = Document(BytesIO(response.content))
    content = []
    for para in doc.paragraphs:
        content.append(para.text)
    return '\n'.join(content)

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
    
    # Instead of saving to a file, save it to a BytesIO buffer
    doc_buffer = BytesIO()
    doc.save(doc_buffer)
    doc_buffer.seek(0)  # Rewind buffer to the beginning
    return doc_buffer

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
    
    # Fetch and add the ROS content under the SUBJECTIVE section
    if ros_file != "None" and ros_file in ros_files:
        ros_paragraph = doc.add_paragraph()
        
        # Add SUBJECTIVE heading (bold, underline)
        ros_run = ros_paragraph.add_run("SUBJECTIVE: ")
        ros_run.bold = True
        ros_run.underline = True
        ros_run.font.name = 'Arial'
        ros_run.font.size = Pt(9)
        
        ros_paragraph.paragraph_format.space_after = Pt(0)
        ros_paragraph.paragraph_format.space_before = Pt(0)
        
        # Fetch the content of the selected ROS file using read_docx_from_url
        ros_url = ros_files[ros_file]  # Get the URL from the dictionary
        ros_content = read_docx_from_url(ros_url)
        
        # Ensure the ROS content is being fetched correctly
        if ros_content:
            # Add the ROS content to the document as paragraphs
            for line in ros_content.split("\n"):
                ros_run = ros_paragraph.add_run(line)
                ros_run.font.name = 'Arial'
                ros_run.font.size = Pt(9)
                ros_paragraph.add_run("\n")  # Ensure each line is on a new line
        
    # Add the Assessment section
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

    # Append Critical Care Time if provided
    if critical_care_time:
        doc.add_paragraph(f"Critical Care Time: {critical_care_time}")

    # Save the final document to a BytesIO buffer
    doc_buffer = BytesIO()
    doc.save(doc_buffer)
    doc_buffer.seek(0)  # Rewind buffer to the beginning
    return doc_buffer

# Create Streamlit app to generate and download the combined notes
def app():
    st.title("Medical Note Generator")

    # Input data for the note (replace with actual input in the real app)
    assess_text = st.text_area("Enter the assessment text:")
    critical_care_reason = st.text_area("Enter the critical care reason:")
    diagnoses = st.multiselect("Select diagnoses", ["Diagnosis 1", "Diagnosis 2", "Diagnosis 3"])
    free_text_diag = st.text_input("Free text diagnosis:")
    free_text_plan = st.text_area("Free text plan:")
    physical_exam_day = st.date_input("Physical exam day")
    ros_file = st.selectbox("Select ROS file", ["None"] + ros_files)  # Assuming ros_files is available
    critical_care_time = st.text_input("Critical care time:")
    
    # Combine the notes into a Word document
    if st.button("Generate Note"):
        doc_buffer = combine_notes(
            assess_text, critical_care_reason, diagnoses, free_text_diag, 
            free_text_plan, physical_exam_day, ros_file, critical_care_time
        )
        
        # Streamlit download button
        st.download_button(
            label="Download Combined Note",
            data=doc_buffer,
            file_name="combined_note.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# Run the Streamlit app
if __name__ == "__main__":
    app()


