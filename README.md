# 🏥 Medical Report Diagnosis

A **FastAPI + Streamlit** application that allows patients to upload medical reports and receive AI-powered diagnoses. Reports are processed with **Google Gemini embeddings**, stored in **Pinecone**, and accessible by doctors for review.

🌐 **Backend:** [https://medical-diagnosis-exua.onrender.com](https://medical-diagnosis-exua.onrender.com)  
🌐 **Frontend (Streamlit):** [https://medical-diagnosis-vjv3tcbabymxenzdqspyr5.streamlit.app/](https://medical-diagnosis-vjv3tcbabymxenzdqspyr5.streamlit.app/)

## 🚀 Features

- 🔑 Role-based Authentication (Doctor / Patient)  
- 📄 PDF Report Upload & Text Extraction  
- 🧠 AI Diagnosis using **Google Gemini**  
- 📦 Vector Storage in Pinecone (3072-dim)  
- 🗄 MongoDB for reports & diagnosis history  
- 💻 Streamlit frontend for easy access  

## ⚙️ Tech Stack

- **Frontend:** Streamlit  
- **Backend:** FastAPI  
- **Database:** MongoDB  
- **Vector DB:** Pinecone  
- **Embeddings & LLM:** Google Gemini  

## ▶️ Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/medical-report-diagnosis.git
cd medical-report-diagnosis
pip install -r requirements.txt
