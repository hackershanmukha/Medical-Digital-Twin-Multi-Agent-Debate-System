from app.db.base_class import Base
from app.models.user import User
from app.models.patient import Patient
from app.models.vitals import Vitals
from app.models.clinical import Condition, Allergy
from app.models.medication import Medication
from app.models.lab import LabReport
from app.models.debate import Debate

__all__ = [
    "Base",
    "User",
    "Patient",
    "Vitals",
    "Condition",
    "Allergy",
    "Medication",
    "LabReport",
    "Debate",
]
