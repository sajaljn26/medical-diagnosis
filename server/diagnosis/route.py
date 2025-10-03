from fastapi import APIRouter, Depends, Form, HTTPException
from ..auth.route import authenticate
from .query import diagnosis_report
from ..config.db import reports_collection, diagnosis_collection
import time

router=APIRouter(prefix="/diagnosis",tags=["diagnosis"])

import logging

@router.post("/from_report")
async def diagnos(user=Depends(authenticate), doc_id: str = Form(...), question: str = Form(default="Please provide a diagnosis based on my report")):
    report = reports_collection.find_one({"doc_id": doc_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if user["role"] == "patient" and report["uploader"] != user["username"]:
        raise HTTPException(status_code=406, detail="You cannot access another user's report")

    if user["role"] == "patient":
        try:
            res = await diagnosis_report(user["username"], doc_id, question)
        except Exception as e:
            logging.exception("Diagnosis generation failed")
            raise HTTPException(status_code=500, detail=f"Diagnosis generation failed: {str(e)}")

        diagnosis_collection.insert_one({
            "doc_id": doc_id,
            "requester": user["username"],
            "question": question,
            "answer": res.get("diagnosis"),
            "sources": res.get("sources", []),
            "timestamp": time.time()
        })
        return res

    if user["role"] in ("doctor", "admin"):
        raise HTTPException(status_code=407, detail="Doctors cannot access this endpoint")

    raise HTTPException(status_code=408, detail="Unauthorized action")



@router.get("/by_patient_name")
async def get_patient_diagnosis(patient_name: str, user=Depends(authenticate)):
    # Only doctors can view a patient's diagnosis
    if user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access this endpoint")
        
    diagnosis_records = diagnosis_collection.find({"requester": patient_name})
    if not diagnosis_records:
        raise HTTPException(status_code=404, detail="No diagnosis found for this patient")
        
    # Convert cursor to a list of dictionaries, excluding the internal _id field
    records_list = []
    for record in diagnosis_records:
        record["_id"] = str(record["_id"]) # Convert ObjectId to string for JSON serialization
        records_list.append(record)
        
    return records_list