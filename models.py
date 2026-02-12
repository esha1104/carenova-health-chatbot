"""
Pydantic schemas for API request/response validation.
Ensures type safety and auto-generates OpenAPI docs.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SymptomRequest(BaseModel):
    """Input: Initial symptom description"""
    symptoms: str = Field(..., min_length=5, max_length=1000, description="User's symptom description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": "I have a persistent cough and chest pain"
            }
        }


class FollowupQuestionsRequest(BaseModel):
    """Input: Generate adaptive follow-up questions"""
    symptoms: str = Field(..., min_length=5, max_length=1000, description="User's symptom description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": "I have a persistent cough and chest pain"
            }
        }


class FollowupQuestionsResponse(BaseModel):
    """Output: Generated follow-up questions"""
    questions: List[str] = Field(..., description="List of follow-up questions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "questions": [
                    "How long have you had this cough?",
                    "Is the chest pain constant or intermittent?",
                    "Do you have difficulty breathing?"
                ]
            }
        }


class AnalysisRequest(BaseModel):
    """Input: Analyze symptoms + answers"""
    initial_symptoms: str = Field(..., min_length=5, max_length=1000)
    followup_answers: List[str] = Field(default_factory=list, max_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "initial_symptoms": "I have a persistent cough and chest pain",
                "followup_answers": [
                    "For 2 weeks",
                    "It comes and goes",
                    "Yes, especially when I take a deep breath"
                ]
            }
        }


class AnalysisResponse(BaseModel):
    """Output: Comprehensive symptom analysis"""
    severity: str = Field(..., description="Mild | Moderate | Severe")
    confidence: str = Field(..., description="Confidence score as percentage")
    possible_conditions: List[str] = Field(..., description="2-4 possible conditions")
    explanation: List[str] = Field(..., description="Why symptoms match conditions")
    home_care_tips: List[str] = Field(..., description="Safe home care advice")
    when_to_see_doctor: List[str] = Field(..., description="Warning signs requiring medical attention")
    disclaimer: str = Field(..., description="Medical disclaimer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "Moderate",
                "confidence": "78%",
                "possible_conditions": ["Bronchitis", "Pneumonia", "GERD"],
                "explanation": ["Persistent cough + chest pain commonly seen in..."],
                "home_care_tips": ["Rest", "Stay hydrated", "Use humidifier"],
                "when_to_see_doctor": ["If cough persists > 3 weeks", "If fever > 101°F"],
                "disclaimer": "This is not a medical diagnosis. Consult a healthcare professional."
            }
        }


class HealthResponse(BaseModel):
    """Output: Health check status"""
    status: str = Field(..., description="healthy | degraded | unhealthy")
    message: str = Field(..., description="Status message")
    models_loaded: bool = Field(..., description="LLM and embeddings models available")
    vector_db_ready: bool = Field(..., description="Chroma vector database accessible")
