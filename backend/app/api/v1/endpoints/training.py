from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.services.training_service import training_service

router = APIRouter()

@router.get("/module/{module_id}")
async def get_training_module(module_id: int):
    """
    Fetches course material for the Agent Academy.
    """
    return training_service.get_module_content(module_id)

@router.post("/exam/submit")
async def submit_certification_exam(exam_data: Dict):
    """
    Submits answers for the 200-question final certification.
    """
    return training_service.evaluate_exam(exam_data["answers"])
