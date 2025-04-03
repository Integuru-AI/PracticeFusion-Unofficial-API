from datetime import datetime, timedelta
from fastapi import File, UploadFile
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal


class CreatePatientRequest(BaseModel):
    birthDate: str = Field(
        ...,
        pattern=r"^(0[1-9]|1[0-2])/([0-2][0-9]|3[01])/\d{4}$",
        description="Format: MM/DD/YYYY",
    )
    emailAddress: EmailStr
    firstName: str
    lastName: str
    gender: Literal["Male", "Female", "Unknown"]
    mobilePhone: str = Field(
        ..., pattern=r"^\(\d{3}\) \d{3}-\d{4}$", description="Format: (XXX) XXX-XXXX"
    )
    mobilePhoneCountry: Optional[str] = Field(
        "USA", pattern=r"^[A-Z]{3}$", description="3-letter country code (default: USA)"
    )
    postalCode: str = Field(..., pattern=r"^\d{5}$", description="5-digit postal code")
    streetAddress1: str
    streetAddress2: Optional[str] = ""


class DocumentUploadRequest(BaseModel):
    files: List[UploadFile]
    firstName: str
    lastName: str


class PatientSchedulerParticipant(BaseModel):
    chiefComplaint: str = Field("")
    firstName: str
    lastName: str


class AppointmentRequest(BaseModel):
    facilityName: Optional[str] = None
    appointmentType: Literal[
        "Wellness Exam",
        "Follow-Up Visit",
        "Nursing Only",
        "Urgent Visit",
        "New Patient Visit",
        "Video Visit",
        "Procedure",
    ]
    schedulerEventParticipants: List[PatientSchedulerParticipant]
    lastModifiedByProvider: Optional[str] = None
    startAtDateTimeUtc: datetime
    endAtDateTimeUtc: Optional[datetime] = None
    insuranceCoverageTypeCode: Optional[str] = "Unins"
    paymentDate: Optional[datetime] = Field(default_factory=datetime.now)

    def __init__(self, **data):
        super().__init__(**data)
        if not self.endAtDateTimeUtc:
            self.endAtDateTimeUtc = self.startAtDateTimeUtc + timedelta(minutes=30)


class GetAppointmentsRequest(BaseModel):
    facilityName: Optional[str] = None
    startTime: datetime
    endTime: datetime


class SchedulerEventPurposeType(BaseModel):
    schedulerEventPurposeTypeGuid: str


class PatientAppointment(BaseModel):
    practiceGuid: str
    schedulerEventGuid: str
    schedulerEventPurposeType: SchedulerEventPurposeType
    schedulerEventParticipants: List[dict]
    lastModifiedByProviderGuid: str
    startAtDateTimeUtc: datetime
    endAtDateTimeUtc: datetime
    scheduleDepartmentGuid: str
    scheduleDepartmentCode: str
    scheduleDepartmentName: str
    insuranceCoverageTypeCode: Optional[str] = "Unins"
    paymentMethodCode: Optional[str] = "CASH"
    paymentStatusCode: Optional[str] = "UNKNOWN"
    paymentDate: datetime = Field(default_factory=datetime.now)
    amountDueSourceCode: Optional[str] = "NONE"
    previousConfirmationState: Optional[bool] = False
    appointmentConfirmed: Optional[bool] = False
    appointmentConfirmationNotes: Optional[str] = ""
    intakeFormGuids: List[str] = []
    disableIntakeForm: Optional[bool] = True


class UpdateAppointmentRequest(BaseModel):
    patientAppointment: PatientAppointment


class MedicationRequest(BaseModel):
    searchCriteria: str
    drugNameOrNdc: str


class PatientTranscriptRequest(BaseModel):
    patientNameOrParticipantGuid: str
    transcriptGuid: Optional[str] = None
    facilityNameOrGuid: Optional[str] = None
    eventDisplayName: Optional[
        Literal[
            "Office Visit",
            "Nurse Visit",
            "Telemedicine Visit",
            "Home Visit",
            "Orders Only",
            "Nursing Home Visit",
            "Email Encounter",
            "Letter",
        ]
    ] = None
    healthConcernNote: Optional[str] = None
    chiefComplaint: Optional[str] = None
    subjectiveNote: Optional[str] = None
    objectiveNote: Optional[str] = None
    assessmentNote: Optional[str] = None
    planNote: Optional[str] = None
    carePlanNotes: Optional[str] = None
    medication: Optional[List[MedicationRequest]] = None
    providerNameOrGuid: Optional[str] = None
