import streamlit as st
import requests
import json
from requests.auth import HTTPBasicAuth
import datetime
from dotenv import load_dotenv
import os
import sys

# --- Project setup ---
load_dotenv()

# Add project root to sys.path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import MongoDB collections
try:
    from server.config.db import reports_collection
except ModuleNotFoundError:
    st.error("Could not import server.config.db. Ensure your folder structure is correct.")

# --- Configuration ---
API_URL = os.getenv("API_URL")

st.set_page_config(
    page_title="Medical Report Diagnosis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session state defaults ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "auth" not in st.session_state:
    st.session_state.auth = None

# --- API Functions ---

def signup_user(username, password, role):
    try:
        response = requests.post(
            f"{API_URL}/auth/signup",
            json={"username": username, "password": password, "role": role}
        )
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"detail": response.text}
        return response.status_code, data
    except requests.exceptions.ConnectionError:
        return 503, {"detail": "Server is unavailable. Please try again later."}

def authenticate_user(username, password):
    try:
        response = requests.get(
            f"{API_URL}/auth/login",
            auth=HTTPBasicAuth(username, password)
        )
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"detail": response.text}
        return response.status_code, data
    except requests.exceptions.ConnectionError:
        return 503, {"detail": "Server is unavailable. Please try again later."}

def upload_report(auth, files):
    try:
        headers = {'accept': 'application/json'}
        files_data = [('files', (file.name, file.getvalue(), file.type)) for file in files]
        response = requests.post(
            f"{API_URL}/reports/upload",
            auth=auth,
            files=files_data,
            headers=headers
        )
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"detail": response.text}
        return response.status_code, data
    except requests.exceptions.ConnectionError:
        return 503, {"detail": "Server is unavailable. Please try again later."}

def get_diagnosis(auth, doc_id, question):
    try:
        data = {
            'doc_id': doc_id,
            'question': question
        }
        response = requests.post(
            f"{API_URL}/diagnosis/from_report",
            auth=auth,
            data=data  # send as form data, not JSON
        )
        try:
            json_data = response.json()
        except requests.exceptions.JSONDecodeError:
            json_data = {"detail": f"Invalid response: {response.text}"}

        return response.status_code, json_data

    except requests.exceptions.ConnectionError:
        return 503, {"detail": "Server is unavailable. Please try again later."}

def get_doctor_diagnosis(auth, patient_name):
    try:
        response = requests.get(
            f"{API_URL}/diagnosis/by_patient_name",
            auth=auth,
            params={'patient_name': patient_name}
        )
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"detail": response.text}
        return response.status_code, data
    except requests.exceptions.ConnectionError:
        return 503, {"detail": "Server is unavailable. Please try again later."}

# --- Sidebar / Authentication ---
st.sidebar.title("Navigation")
st.sidebar.markdown("---")

if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.auth = None
        st.rerun()
else:
    st.sidebar.header("Login")
    login_username = st.sidebar.text_input("Username", key="login_username")
    login_password = st.sidebar.text_input("Password", type="password", key="login_password")
    if st.sidebar.button("Login"):
        if login_username and login_password:
            status_code, data = authenticate_user(login_username, login_password)
            if status_code == 200:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.session_state.role = data.get("role", "")
                st.session_state.auth = HTTPBasicAuth(login_username, login_password)
                st.sidebar.success("Logged in successfully!")
                st.rerun()
            else:
                st.sidebar.error(f"Login failed: {data.get('detail', 'Unknown error')}")
        else:
            st.sidebar.warning("Please enter a username and password.")

    st.sidebar.header("Signup")
    signup_username = st.sidebar.text_input("New Username", key="signup_username")
    signup_password = st.sidebar.text_input("New Password", type="password", key="signup_password")
    signup_role = st.sidebar.selectbox("Role", ["patient", "doctor"], key="signup_role")
    if st.sidebar.button("Signup"):
        if signup_username and signup_password:
            status_code, data = signup_user(signup_username, signup_password, signup_role)
            if status_code == 200:
                st.sidebar.success("User created successfully! You can now log in.")
            else:
                st.sidebar.error(f"Signup failed: {data.get('detail', 'Unknown error')}")
        else:
            st.sidebar.warning("Please fill in all fields.")

# --- Main Page ---
st.title("👨‍⚕️ GenAI-Powered Medical Diagnosis")
st.markdown("Use your medical reports to get AI-powered diagnoses and allow doctors to view patient records.")

if not st.session_state.logged_in:
    st.info("Please log in or sign up to use the application.")
else:
    if st.session_state.role == "patient":
        st.header("Patient Dashboard")
        st.markdown("---")

        st.subheader("Upload Your Report")
        with st.form("upload_form"):
            uploaded_files = st.file_uploader(
                "Choose medical report files (PDF or TXT)",
                type=["pdf", "txt"],
                accept_multiple_files=True
            )
            upload_submitted = st.form_submit_button("Upload Reports")
            if upload_submitted and uploaded_files:
                with st.spinner("Uploading and processing reports..."):
                    status_code, data = upload_report(st.session_state.auth, uploaded_files)
                    if status_code == 200:
                        st.success(f"Reports uploaded successfully! Document ID: `{data.get('doc_id', '')}`")
                        st.session_state.doc_id = data.get('doc_id')
                    else:
                        st.error(f"Upload failed: {data.get('detail', 'Unknown error')}")

        st.markdown("---")

        st.subheader("Get a Diagnosis")
        if 'doc_id' in st.session_state:
            with st.form("diagnosis_form"):
                diagnosis_doc_id = st.text_input("Document ID", value=st.session_state.doc_id)
                diagnosis_question = st.text_area(
                    "Question for diagnosis model:",
                    "Please provide a diagnosis based on my report."
                )
                diagnosis_submitted = st.form_submit_button("Get Diagnosis")
                if diagnosis_submitted:
                    with st.spinner("Generating diagnosis..."):
                        status_code, data = get_diagnosis(
                            st.session_state.auth,
                            diagnosis_doc_id,
                            diagnosis_question
                        )
                        if status_code == 200:
                            st.success("Diagnosis Generated!")
                            st.subheader("Diagnosis Result")
                            st.write(data.get("diagnosis", "No diagnosis provided."))
                            st.subheader("Sources")
                            st.json(data.get("sources", []))
                        else:
                            st.error(f"Diagnosis failed: {data.get('detail', 'Unknown error')}")
        else:
            st.info("Please upload a report first to get a Document ID.")

    elif st.session_state.role == "doctor":
        st.header("Doctor Dashboard")
        st.markdown("---")

        st.subheader("View Patient Diagnosis History")
        with st.form("doctor_form"):
            patient_name_input = st.text_input("Enter Patient's Username:")
            view_submitted = st.form_submit_button("View Diagnosis Records")
            if view_submitted:
                with st.spinner(f"Fetching diagnosis records for {patient_name_input}..."):
                    status_code, data = get_doctor_diagnosis(st.session_state.auth, patient_name_input)
                    if status_code == 200:
                        if not data:
                            st.info(f"No diagnosis records found for {patient_name_input}.")
                        else:
                            st.success(f"Found {len(data)} diagnosis record(s).")
                            for record in data:
                                st.info(f"Record ID: {record.get('_id')}")
                                st.write(f"Date: {datetime.datetime.fromtimestamp(record.get('timestamp',0)).strftime('%Y-%m-%d %H:%M:%S')}")
                                st.write(f"Document ID: {record.get('doc_id','')}")
                                st.write(f"Question: {record.get('question','')}")
                                st.subheader("Diagnosis Answer")
                                st.markdown(record.get('answer',''))
                                st.subheader("Sources")
                                sources = record.get("sources", [])
                                if sources:
                                    for source in sources:
                                        st.write(f"- {source}")
                                else:
                                    st.write("No sources found.")
                                st.markdown("---")
                    else:
                        st.error(f"Failed to fetch records: {data.get('detail', 'Unknown error')}")

    else:
        st.warning("Your role is not recognized. Please contact support.")
