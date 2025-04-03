from datetime import datetime, timezone
import aiohttp
from fake_useragent import UserAgent
from fastapi import HTTPException
from fastapi.logger import logger
from fastapi.responses import JSONResponse
from helpers.classes.network_requester import NetworkRequester
from integrations.practicefusion.practicefusion_login_utils import PF_URLS_MAP
from submodule_integrations.models.integration import Integration
from submodule_integrations.practicefusion.models.models import (
    AppointmentRequest,
    CreatePatientRequest,
    DocumentUploadRequest,
    GetAppointmentsRequest,
    MedicationRequest,
    PatientTranscriptRequest,
    UpdateAppointmentRequest,
)
from submodule_integrations.utils.errors import (
    IntegrationAPIError,
)


class PracticeFusionIntegration(Integration):
    def __init__(self, user_agent: str = UserAgent().chrome):
        super().__init__("practicefusion")
        self.user_agent = user_agent
        self.network_requester: NetworkRequester = None
        self.url = "https://static.practicefusion.com"
        self.cookies: str = None
        self.bearer_auth: str = None

    @classmethod
    async def create(
        cls,
        cookies: str,
        authorization: str,
        network_requester=None,
    ):
        """
        Initialize the integration with required configurations.

        Args:
            - cookies (str): Cookies to include in network requests.
            - authorization (str): The JWT token needed to authorize requests
            -  network_requester (optional): A custom network requester instance. Defaults to None.
        """
        instance = cls()
        instance.network_requester = network_requester

        instance.cookies = cookies
        instance.bearer_auth = authorization
        return instance

    async def _make_request(self, method: str, url: str, **kwargs):
        """
        Make a network request to the specified URL using the given HTTP method.

        Args:
            * method (str): The HTTP method (e.g., GET, POST).
            * url (str): The URL to send the request to.
            * **kwargs: Additional parameters for the request.

        Returns:
            * The response object from the request.
        """
        if self.network_requester:
            response = await self.network_requester.request(method, url, **kwargs)
            return response
        else:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    return await self._handle_response(response)

    async def _handle_response(self, response: aiohttp.ClientResponse):
        """
        Handle the response from a network request, raising exceptions for errors.

        Args:
            * response (aiohttp.ClientResponse): The response object.

        Returns:
            * str | Any: Parsed JSON response if successful.

        Raises:
            * `IntegrationAuthError`: If the response status is 401.
            * `IntegrationAPIError`: For other API errors.
        """
        response_json = {}
        try:
            response_json = await response.json()
        except Exception:
            response_json = {
                "error": {"message": "Unknown error", "code": str(response.status)}
            }

        if 200 <= response.status < 204:
            return response_json
        if response.status == 204:
            return

        error_message = response_json.get("error", {}).get("message", "Unknown error")
        error_code = response_json.get("error", {}).get("code", str(response.status))

        logger.debug(f"{response.status} - {response_json}")

        if response.status >= 400 and response.status < 500:
            raise HTTPException(status_code=response.status, detail=response_json)
        elif response.status >= 500:
            raise IntegrationAPIError(
                self.integration_name,
                f"Downstream server error (translated to HTTP 501): {error_message}",
                501,
                error_code,
            )
        else:
            raise IntegrationAPIError(
                self.integration_name,
                f"{error_message} (HTTP {response.status})",
                response.status,
                error_code,
            )

    async def _setup_headers(self):
        """
        Set up headers for network requests.

        Returns:
            * dict: Headers for the network request.
        """
        _headers = {
            "User-Agent": self.user_agent,
            "Cookie": self.cookies,
            "Authorization": self.bearer_auth,
            "Sec-Ch-Ua": "'Chromium';v='134', 'Not:A-Brand';v='24', 'Google Chrome';v='134'",
        }
        return _headers

    async def create_patient(self, request: CreatePatientRequest):
        """
        Create a new patient on PF

        Params:
        ------
            * request (`CreatePatientRequest`): request body
                                                containing information
                                                needed from the user to
                                                create patient

        returns:
        -------
            * create_patient_response (`JSONResponse`): response body
                                                        containing crucial
                                                        information regarding
                                                        the created patient
                                                        such as unique Ids etc.
        """
        logger.debug("Creating patient commenced")
        headers = await self._setup_headers()
        postal_url = PF_URLS_MAP["postalCode"].format(postalCode=request.postalCode)
        logger.debug(f"Verifying postal code for: {request.postalCode}")
        postal_data: dict = await self._make_request("GET", postal_url, headers=headers)
        logger.debug("Constructing patient payload")
        patient_payload = {
            "patient": {
                "birthDate": request.birthDate,
                "emailAddress": request.emailAddress,
                "firstName": request.firstName,
                "gender": request.gender,
                "isActive": True,
                "isUserOfEmail": True,
                "isUserOfMobilePhone": True,
                "mobilePhone": request.mobilePhone,
                "mobilePhoneCountry": request.mobilePhoneCountry,
                "lastName": request.lastName,
                "preferredMethodOfCommunicationOption": "1",
                "primaryAddress": {
                    "city": postal_data.get("city"),
                    "country": "",
                    "moveInDate": "",
                    "moveOutDate": "",
                    "notes": "",
                    "postalCode": request.postalCode,
                    "state": postal_data.get("stateProvince"),
                    "streetAddress1": request.streetAddress1,
                    "streetAddress2": request.streetAddress2,
                },
                "previousAddress": {
                    "city": "",
                    "country": "",
                    "moveInDate": "",
                    "moveOutDate": "",
                    "notes": "",
                    "postalCode": "",
                    "state": "",
                    "streetAddress1": "",
                    "streetAddress2": "",
                },
                "ethnicities": ["0a306a4e-6217-4a50-a47f-888c53c9b193"],
                "races": ["f051a797-87bf-468f-99e3-217f2b5eb6dc"],
                "raceOptions": [],
                "birthSequence": 1,
                "isMultipleBirth": False,
            },
            "patientPreferences": {
                "medicationHistoryConsentPreference": "2",
                "preferredPharmacy": None,
            },
            "patientContacts": [],
            "patientSocialHistory": {
                "raceEthnicity": [
                    {
                        "displayOrder": 1,
                        "hierarchicalCode": "PF1",
                        "hierarchicalRootParent": "",
                        "isDefault": True,
                        "isExcluded": False,
                        "isExclusive": True,
                        "name": "Provider did not ask",
                        "type": "Ethnicity",
                        "optionGuid": "0a306a4e-6217-4a50-a47f-888c53c9b193",
                    },
                    {
                        "displayOrder": 1,
                        "hierarchicalCode": "PF1",
                        "hierarchicalRootParent": "",
                        "isDefault": True,
                        "isExcluded": False,
                        "isExclusive": True,
                        "name": "Provider did not ask",
                        "type": "Race",
                        "optionGuid": "f051a797-87bf-468f-99e3-217f2b5eb6dc",
                    },
                ]
            },
            "generateNewPatientRecordNumber": True,
        }

        logger.debug("Submitting create patient request...")
        create_patient_response = await self._make_request(
            "PUT", PF_URLS_MAP["create_patient"], json=patient_payload, headers=headers
        )
        logger.debug(f"Patient: {request.firstName} created successfully")
        return JSONResponse(create_patient_response)

    async def check_for_conflicts(
        self,
        provider_guid: str,
        facility_guid: str,
        start_at: datetime,
        end_at: datetime,
    ):
        logger.debug("Checking for conflicts")
        start_at_str = start_at.strftime("%Y-%m-%dT%H:%M")
        end_at_str = end_at.strftime("%Y-%m-%dT%H:%M")

        params = {
            "providerGuid": provider_guid,
            "facilityGuid": facility_guid,
            "startDateTimeFlt": start_at_str,
            "endDateTimeFlt": end_at_str,
        }

        headers = await self._setup_headers()

        data = await self._make_request(
            "GET", PF_URLS_MAP["conflicts"], params=params, headers=headers
        )

        if data.get("conflictsExist", False):
            logger.debug("Conflicts found.")
            raise HTTPException(
                status_code=400,
                detail="Conflicts exist with the selected time. Please select a different time.",
            )

        logger.debug("No conflicts thus far")
        return True

    async def upload_document(self, request: DocumentUploadRequest):
        logger.debug(f"Uploading {len(request.files)} file(s)")
        headers = await self._setup_headers()
        search_payload = {
            "matchAll": True,
            "firstName": request.firstName,
            "lastName": request.lastName,
        }
        logger.debug(f"Searching for patient {request.firstName} {request.lastName} ")
        search_response = await self._make_request(
            "POST", PF_URLS_MAP["search_patient"], json=search_payload, headers=headers
        )

        if len(search_response.get("patients")) < 1:
            raise HTTPException(
                status_code=404, detail="Patient not found.", error_code="client_error"
            )

        patient_id = search_response["patients"][0]["patientPracticeGuid"]

        logger.debug("Patient found. Patient Id extracted successfully.")

        uploaded_documents = []

        logger.debug("File(s) uploading commenced")
        for upload_file in request.files:
            form = aiohttp.FormData()
            form.add_field(
                "documents",
                await upload_file.read(),
                filename=upload_file.filename,
                content_type=upload_file.content_type,
            )

            upload_response = await self._make_request(
                "POST", PF_URLS_MAP["upload_document"], data=form, headers=headers
            )

            upload_data = upload_response[0]

            # Update document metadata
            metadata_payload = {
                "documentGuid": upload_data["documentGuid"],
                "binaryStorageGuid": upload_data["binaryStorageGuid"],
                "comments": None,
                "documentDateTimeUtc": upload_data["documentDateTimeUtc"],
                "documentName": upload_data["documentName"],
                "documentStatus": upload_data["documentStatus"],
                "documentTypeId": upload_data["documentTypeId"],
                "documentTypeName": upload_data["documentTypeName"],
                "fileSize": upload_data["fileSize"],
                "isDocumentTypeActive": upload_data["isDocumentTypeActive"],
                "isDocumentUnrecoverable": upload_data["isDocumentUnrecoverable"],
                "isReadyForDownload": upload_data["isReadyForDownload"],
                "isSigned": upload_data["isSigned"],
                "mimeType": upload_data["mimeType"],
                "originalFileExtension": upload_data["originalFileExtension"],
                "patientPracticeGuid": patient_id,
                "transcriptGuids": [],
            }

            metadata_response = await self._make_request(
                "PUT",
                PF_URLS_MAP["update_document_meta"],
                json=metadata_payload,
                headers=headers,
            )

            uploaded_documents.append(metadata_response)

        logger.debug("File(s) uploaded successfully")
        return JSONResponse(content={"uploaded_files": uploaded_documents})

    async def create_appointment(self, request: AppointmentRequest):
        logger.debug(
            f"Creating appointment for {request.schedulerEventParticipants[0].firstName} {request.schedulerEventParticipants[0].lastName}"
        )
        headers = await self._setup_headers()
        logger.debug("Fetching available appointment types")
        appointment_types_response = await self._make_request(
            "GET", PF_URLS_MAP["appointment_types"], headers=headers
        )

        appointment_type = next(
            (
                item
                for item in appointment_types_response
                if item["name"] == request.appointmentType
            ),
            None,
        )

        if not appointment_type:
            logger.debug(f"Appointment type {request.appointmentType} not found. ")
            raise HTTPException(status_code=404, detail="Appointment type not found.")

        logger.debug(f"Appointment type {request.appointmentType} found. ")

        appointment_type_guid = appointment_type["id"]

        patient_search_payload = {
            "matchAll": True,
            "firstName": request.schedulerEventParticipants[0].firstName,
            "lastName": request.schedulerEventParticipants[0].lastName,
        }
        logger.debug(
            f"Searching for patient: {patient_search_payload['firstName']} {patient_search_payload['lastName']}"
        )
        patient_search_response = await self._make_request(
            "POST",
            PF_URLS_MAP["search_patient"],
            json=patient_search_payload,
            headers=headers,
        )

        if len(patient_search_response.get("patients")) < 1:
            raise HTTPException(status_code=404, detail="Patient not found.")

        patient_id = patient_search_response["patients"][0]["patientPracticeGuid"]

        logger.debug("Patient found. Id extracted successfully.")

        provider_guid = (
            "d744609f-1bab-4e11-89bd-680e8d19a397"  # default provider ID (anurag)
        )

        if request.lastModifiedByProvider:
            logger.debug("Custom Provider was given. Getting list of providers")
            provider_data = await self._make_request(
                "GET",
                PF_URLS_MAP["provider"],
                headers=headers,
            )

            provider = next(
                (
                    item
                    for item in provider_data
                    if item["providerName"] == request.lastModifiedByProvider
                ),
                None,
            )

            if not provider:
                logger.debug(f"Provider {request.lastModifiedByProvider} not found. ")
                raise HTTPException(status_code=404, detail="Provider not found.")

            provider_guid = provider["providerGuid"]
            logger.debug(f"Custome provider: {request.lastModifiedByProvider} found")

        facility_guid = "68cc1f4c-0378-424f-9d12-e3ee0ab9b4be"  # default facility ID (Silicon beach medical center)
        practice_guid = "f6f290f1-968a-4900-a7a0-5500ce2a30f7"  # default practice GUID (Silicon beach medical center)

        if request.facilityName:
            logger.debug("Fetching facility GUID ")
            facility_data = await self._make_request(
                "GET",
                PF_URLS_MAP["facility"],
                headers=headers,
            )

            facility = next(
                (
                    item
                    for item in facility_data
                    if item["name"] == request.facilityName
                ),
                None,
            )

            if not facility:
                logger.debug(f"Facility '{request.facilityName}' not found. ")
                raise HTTPException(status_code=404, detail="Facility not found.")

            facility_guid = facility["facilityGuid"]
            practice_guid = facility["practiceGuid"]
            logger.debug(f"Facility '{request.facilityName}' found. ")

        scheduler_event_participants = [
            {
                "schedulerEventParticipantTypeId": 3,  # Patient
                "participantGuid": patient_id,
                "chiefComplaint": request.schedulerEventParticipants[0].chiefComplaint,
            },
            {
                "schedulerEventParticipantTypeId": 2,  # Facility
                "participantGuid": facility_guid,
            },
            {
                "schedulerEventParticipantTypeId": 1,  # Provider
                "participantGuid": provider_guid,
            },
        ]

        appointment_payload = {
            "patientAppointment": {
                "practiceGuid": practice_guid,
                "schedulerEventPurposeType": {
                    "schedulerEventPurposeTypeGuid": appointment_type_guid
                },
                "schedulerEventParticipants": scheduler_event_participants,
                "lastModifiedByProviderGuid": provider_guid,
                "startAtDateTimeUtc": request.startAtDateTimeUtc.isoformat(),
                "endAtDateTimeUtc": request.endAtDateTimeUtc.isoformat(),
                "insuranceCoverageTypeCode": request.insuranceCoverageTypeCode,
                "paymentDate": (
                    request.paymentDate.isoformat()
                    if request.paymentDate
                    else datetime.now().isoformat()
                ),
                "startAtDateTimeFlt": request.startAtDateTimeUtc.isoformat(),
                "endAtDateTimeFlt": request.endAtDateTimeUtc.isoformat(),
                "appointmentConfirmationNotes": "",
                "intakeFormGuids": [],
                "disableIntakeForm": True,
            }
        }

        await self.check_for_conflicts(
            provider_guid,
            facility_guid,
            request.startAtDateTimeUtc,
            request.endAtDateTimeUtc,
        )

        logger.debug("Making request to create appointment with payload")

        create_appointment_response = await self._make_request(
            "POST",
            PF_URLS_MAP["create_appointment"],
            json=appointment_payload,
            headers=headers,
        )

        logger.debug("Appointment created successfully.")

        return JSONResponse(create_appointment_response)

    async def get_combined_events(self, request: GetAppointmentsRequest):
        logger.debug("Fetching list of appointments")
        headers = await self._setup_headers()
        facility_name = "SILICON BEACH MEDICAL CENTER"
        practice_guid = "f6f290f1-968a-4900-a7a0-5500ce2a30f7"
        facility_guid = "68cc1f4c-0378-424f-9d12-e3ee0ab9b4be"

        if request.facilityName:
            logger.debug("Using user-provided facility name")
            facility_name = request.facilityName
            logger.debug("Fetching list of facilities")
            facility_data = await self._make_request(
                "GET", PF_URLS_MAP["facility"], headers=headers
            )
            facility_match = next(
                (f for f in facility_data if f["name"] == (request.facilityName)),
                None,
            )

            if not facility_match:
                logger.debug(f"Facility '{request.facilityName}' not found. ")
                raise HTTPException(status_code=404, detail="Facility not found.")

            logger.debug(f"Facility match found for: {request.facilityName}")

            practice_guid = facility_match["practiceGuid"]
            facility_guid = facility_match["facilityGuid"]
            logger.debug(f"Extracted practice_guid and facility_guid")

        logger.debug("Fetching providers list")
        provider_data = await self._make_request(
            "GET", PF_URLS_MAP["provider"], headers=headers
        )
        provider_guid_list = [
            p["providerGuid"] for p in provider_data if p.get("providerGuid")
        ]
        logger.debug("Provider guid list populated successfully")

        payload = {
            "practiceDetailName": facility_name.upper(),
            "practiceGuid": practice_guid,
            "providerGuidList": provider_guid_list,
            "facilityGuid": facility_guid,
            "startMinimumDateTimeUtc": request.startTime.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "startMaximumDateTimeUtc": request.endTime.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "includePinnedPatientNote": True,
        }

        logger.debug("Making PUT request for combined events")
        appointments_response = await self._make_request(
            "PUT", PF_URLS_MAP["combined_event"], json=payload, headers=headers
        )
        logger.debug("Appointments fetched successfully")
        return JSONResponse(appointments_response)

    async def update_appointment_details(self, request: UpdateAppointmentRequest):
        logger.debug(
            f"Updating appointment details for id: {request.patientAppointment.schedulerEventGuid}"
        )

        request_url = f"{PF_URLS_MAP["create_appointment"]}/{request.patientAppointment.schedulerEventGuid}"
        headers = await self._setup_headers()
        payload = request.model_dump(mode="json")
        payload["patientAppointment"][
            "startAtDateTimeFlt"
        ] = request.patientAppointment.startAtDateTimeUtc.isoformat()
        payload["patientAppointment"][
            "endAtDateTimeFlt"
        ] = request.patientAppointment.endAtDateTimeUtc.isoformat()

        logger.debug("Making PUT request to update appointment")
        update_response = await self._make_request(
            "PUT", request_url, json=payload, headers=headers
        )
        logger.debug("Appointment updated successfully")
        return JSONResponse(update_response)

    ########-----------A bunch of helper methods --------####################
    def is_guid(self, value: str) -> bool:
        return len(value) == 36 and value.count("-") == 4

    async def get_participant_guid_from_name(
        self, firstname: str, lastname: str, headers: dict
    ) -> str:
        search_payload = {
            "matchAll": True,
            "firstName": firstname,
            "lastName": lastname,
        }
        response = await self._make_request(
            "POST",
            PF_URLS_MAP["search_patient"],
            json=search_payload,
            headers=headers,
        )

        if len(response.get("patients")) < 1:
            raise HTTPException(status_code=404, detail="Patient not found.")

        return response["patients"][0]["patientPracticeGuid"]

    async def get_facility_guid_from_name(
        self, facilityname: str, headers: dict
    ) -> str:
        response = await self._make_request(
            "GET", PF_URLS_MAP["facility"], headers=headers
        )
        facility = next((f for f in response if f["name"] == facilityname), None)
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found.")
        return facility["facilityGuid"]

    async def get_encounter_guid_from_display_name(
        self, displayName: str, headers: dict
    ) -> str:
        logger.debug("Making GET request to fetch list of encounter event types")
        response = await self._make_request(
            "GET", PF_URLS_MAP["encounter_event_type"], headers=headers
        )
        event = next(
            (e for e in response.get("events", []) if e["displayName"] == displayName),
            None,
        )
        return (
            event["eventTypeGuid"] if event else "9381cfbf-373b-418e-812c-e44b97835be4"
        )

    async def create_transcript(
        self, encounter_guid: str, participant_guid: str, facility_guid: str, headers
    ) -> dict:
        payload = {
            "encounterTypeEncounterEventTypeGuid": encounter_guid,
            "facilityGuid": facility_guid,
            "dateOfServiceLocal": datetime.now(timezone.utc).isoformat(),
        }
        url = PF_URLS_MAP["create_transcripts"].format(participantGuid=participant_guid)

        logger.debug("Making POST request to create transcript")
        return await self._make_request(
            "POST",
            url,
            json=payload,
            headers=headers,
        )

    async def create_health_concern(
        self, patient_practice_guid: str, healthConcernNote: str, headers
    ):
        logger.debug("Adding/Updating health concern to transcript")

        payload = {
            "patientPracticeGuid": patient_practice_guid,
            "healthConcernType": "Note",
            "healthConcernNote": healthConcernNote,
        }
        url = PF_URLS_MAP["health_concern"].format(
            patientPracticeGuid=patient_practice_guid
        )
        request_method = "POST"

        logger.debug("Checking if previous health concerns exist for patient")
        get_health_concerns_url = PF_URLS_MAP["health_concerns"].format(
            patientPracticeGuid=patient_practice_guid
        )

        health_concern_data = await self._make_request(
            "GET", get_health_concerns_url, headers=headers
        )

        if (
            health_concern_data.get("patientHealthConcerns", None)
            and len(health_concern_data.get("patientHealthConcerns")) > 0
        ):
            logger.debug("Patient has previous health concerns. Extracting guid...")
            patientHealthConcernGuid = health_concern_data["patientHealthConcerns"][0][
                "patientHealthConcernGuid"
            ]
            payload["patientHealthConcernGuid"] = patientHealthConcernGuid
            url = f"{url}/{patientHealthConcernGuid}"
            request_method = "PUT"

        logger.debug(f"Making {request_method} request for health concern")
        await self._make_request(
            request_method,
            url,
            json=payload,
            headers=headers,
        )

    async def update_transcript_field(
        self,
        patient_practice_guid: str,
        transcript_guid: str,
        field: str,
        value: str,
        headers,
    ):
        logger.debug(f"Adding/updating {field} to transcript")
        url = PF_URLS_MAP["update_transcript"].format(
            patientPracticeGuid=patient_practice_guid, transcriptGuid=transcript_guid
        )
        payload = {field: value}
        logger.debug("Making PATCH request")
        await self._make_request(
            "PATCH",
            url,
            json=payload,
            headers=headers,
        )

    def format_rich_text(self, text: str | None) -> str | None:
        return f'<div class="pf-rich-text"><p>{text}</p></div>' if text else None

    async def update_care_plan_notes(
        self,
        patient_practice_guid: str,
        transcript_guid: str,
        carePlanNotes: str,
        headers: dict,
    ):
        logger.debug("Adding/updating care plan note")
        transcript_events_url = PF_URLS_MAP["transcript_events"].format(
            patientPracticeGuid=patient_practice_guid, transcriptGuid=transcript_guid
        )
        logger.debug("Making GET request to fetch transcript events list")
        response = await self._make_request(
            "GET", transcript_events_url, headers=headers
        )
        care_plan_event = next(
            (
                e
                for e in response.get("transcriptEvents")
                if e["eventType"]["displayName"] == "Care plan"
            ),
            None,
        )

        if not care_plan_event:
            raise HTTPException(status_code=404, detail="Care plan event not found.")

        logger.debug("Care plan event found")

        event_type_data = care_plan_event["eventType"]
        event_type_data["worksheetGuid"] = None

        payload = {
            "causedByGuid": None,
            "comments": f'<div class="pf-rich-text"><p>{carePlanNotes}</p></div>',
            "dueDate": None,
            "endDateTimeUtc": None,
            "eventType": event_type_data,
            "isNegated": care_plan_event["isNegated"],
            "lastModifiedAt": f"{datetime.now(timezone.utc).isoformat()}Z",
            "resultValue": None,
            "startDateTimeUtc": None,
            "status": "Documented",
            "transcriptEventGuid": care_plan_event["transcriptEventGuid"],
            "transcriptGuid": transcript_guid,
        }

        care_plan_url = PF_URLS_MAP["update_care_plan"].format(
            patientPracticeGuid=patient_practice_guid,
            transcriptEventGuid=care_plan_event["transcriptEventGuid"],
        )

        logger.debug("Making PUT request to update care plan notes")
        await self._make_request("PUT", care_plan_url, json=payload, headers=headers)

    async def process_medications(
        self,
        patient_practice_guid: str,
        transcript_guid: str,
        medication: list[MedicationRequest],
        providerNameOrGuid: str | None,
        headers,
    ):
        logger.debug("Adding/updating medications to transcript")
        provider_guid = "d744609f-1bab-4e11-89bd-680e8d19a397"  # Default would be Anurag for the time-being

        if providerNameOrGuid:
            logger.debug("Custom provider name or GUID supplied, using that instead")
            if self.is_guid(providerNameOrGuid):
                provider_guid = providerNameOrGuid
            else:
                provider_data = await self._make_request(
                    "GET", PF_URLS_MAP["provider"], headers=headers
                )
                provider = next(
                    (
                        p
                        for p in provider_data
                        if p["providerName"] == providerNameOrGuid
                    ),
                    None,
                )
                if not provider:
                    logger.debug(f"Provider: {providerNameOrGuid} not found")
                    raise HTTPException(
                        status_code=404,
                        detail=f"Provider {providerNameOrGuid} not found.",
                    )
                provider_guid = provider["providerGuid"]
                logger.debug("Provider guid extracted successfully.")

        for med in medication:
            logger.debug(f"Adding medication '{med.drugNameOrNdc}' to transcript")
            drug_search_url = PF_URLS_MAP["search_drug"].format(
                searchCriteria=med.searchCriteria
            )

            logger.debug("Making GET request to find possible drug matches")
            drug_data = await self._make_request(
                "GET",
                drug_search_url,
                headers=headers,
            )

            matched_drug = next(
                (
                    d
                    for d in drug_data
                    if d["drugName"].lower() == med.drugNameOrNdc.lower()
                    or d["ndc"] == med.drugNameOrNdc
                ),
                None,
            )
            if not matched_drug:
                logger.debug(f"Drug by name: {med.searchCriteria} not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"No matching drug found for {med.searchCriteria}",
                )

            interaction_url = PF_URLS_MAP["drug_interactions"].format(
                patientPracticeGuid=patient_practice_guid
            )
            logger.debug("Making POST request for interaction data for patient")
            interaction_payload = {
                "drugInputs": [
                    {**matched_drug, "patientPracticeGuid": patient_practice_guid}
                ]
            }
            interaction_data = await self._make_request(
                "POST",
                interaction_url,
                json=interaction_payload,
                headers=headers,
            )

            if any(
                interaction_data.get(key)
                for key in [
                    "drugInteractionAlerts",
                    "drugAllergyAlerts",
                    "drugAlertErrors",
                ]
            ):
                logger.debug(
                    f"Potential drug interactions or allergies may be present with drug: {matched_drug["drugName"]}"
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": f"Potential drug interactions or allergies detected between patient and drug:{matched_drug["drugName"]}.",
                        "alerts": {
                            "drugInteractionAlerts": interaction_data[
                                "drugInteractionAlerts"
                            ],
                            "drugAllergyAlerts": interaction_data["drugAllergyAlerts"],
                            "drugAlertErrors": interaction_data["drugAlertErrors"],
                        },
                    },
                )

            medication_payload = {
                "controlledSubstanceSchedule": None,
                "createdByProviderGuid": None,
                "createdDateTimeUtc": None,
                "diagnosisGuid": None,
                "doseForm": matched_drug["doseForm"],
                "drugName": matched_drug["drugName"],
                "genericName": matched_drug["genericName"],
                "isCompoundMedication": False,
                "isGeneric": matched_drug["isGeneric"],
                "isMedicalSupply": matched_drug["isMedicalSupply"],
                "isPending": False,
                "lastModifiedProviderGuid": None,
                "lastModifiedDateTimeUtc": None,
                "medicationComment": None,
                "medicationDiscontinuedReason": None,
                "medicationGuid": None,
                "ndc": matched_drug["ndc"],
                "patientPracticeGuid": patient_practice_guid,
                "productStrength": matched_drug["productStrength"],
                "providerGuid": provider_guid,
                "route": matched_drug["route"],
                "rxNormCui": matched_drug["rxNormCui"],
                "sig": {"patientDescription": None, "professionalDescription": None},
                "source": None,
                "startDateTime": None,
                "stopDateTime": None,
                "tradeDisplayName": None,
                "tradeName": matched_drug["tradeName"],
                "transcriptGuid": transcript_guid,
                "userGuid": None,
                "intent": None,
            }

            add_medication_url = PF_URLS_MAP["add_medication"].format(
                patientPracticeGuid=patient_practice_guid,
                transcriptGuid=transcript_guid,
            )

            logger.debug("Making POST request to add medication")
            medication_response = await self._make_request(
                "POST",
                add_medication_url,
                json=medication_payload,
                headers=headers,
            )
            medication_guid = medication_response["medicationGuid"]

            transcript_medication_payload = {
                "comment": None,
                "lastModifiedProviderGuid": None,
                "transcriptGuid": transcript_guid,
            }
            add_transcript_medication_url = PF_URLS_MAP[
                "add_transcript_medication"
            ].format(
                patientPracticeGuid=patient_practice_guid,
                medicationGuid=medication_guid,
            )
            logger.debug("Making POST request to associate medication with")
            await self._make_request(
                "POST",
                add_transcript_medication_url,
                json=transcript_medication_payload,
                headers=headers,
            )

    ########-----------End of a bunch of helper methods --------####################

    async def get_encounters(self, patientNameOrParticipantGuid: str):
        logger.debug(
            f"Fetching transcript summaries for patient: {patientNameOrParticipantGuid}"
        )
        headers = await self._setup_headers()

        logger.debug("Setting participant guid")
        participant_guid = (
            patientNameOrParticipantGuid
            if self.is_guid(patientNameOrParticipantGuid)
            else await self.get_participant_guid_from_name(
                firstname=patientNameOrParticipantGuid.split()[0],
                lastname=patientNameOrParticipantGuid.split()[-1],
                headers=headers,
            )
        )

        transcript_summaries_url = PF_URLS_MAP["transcript_summaries"].format(
            patientPracticeGuid=participant_guid
        )

        logger.debug("Making GET requrst to fetch summaries")
        transcripts_encounters = await self._make_request(
            "GET", transcript_summaries_url, headers=headers
        )

        logger.debug("Request successful")
        return JSONResponse(transcripts_encounters)

    async def create_soap_notes(self, request: PatientTranscriptRequest):
        logger.debug(
            f"{'Creating new soap notes' if not request.transcriptGuid else f'Updating transcript: {request.transcriptGuid}'}"
        )
        headers = await self._setup_headers()

        logger.debug("Setting participant guid")
        participant_guid = (
            request.patientNameOrParticipantGuid
            if self.is_guid(request.patientNameOrParticipantGuid)
            else await self.get_participant_guid_from_name(
                firstname=request.patientNameOrParticipantGuid.split()[0],
                lastname=request.patientNameOrParticipantGuid.split()[-1],
                headers=headers,
            )
        )

        logger.debug("Setting facility guid")
        facility_guid = "68cc1f4c-0378-424f-9d12-e3ee0ab9b4be"
        if request.facilityNameOrGuid:
            logger.debug("Custom facility name or guid supplied. Using that instead.")
            facility_guid = (
                request.facilityNameOrGuid
                if self.is_guid(request.facilityNameOrGuid)
                else await self.get_facility_guid_from_name(
                    request.facilityNameOrGuid, headers
                )
            )

        transcript_guid = request.transcriptGuid

        if not transcript_guid:
            logger.debug("Creating new transcript. Fetching encounter guid")
            encounter_guid = await self.get_encounter_guid_from_display_name(
                request.eventDisplayName, headers
            )

            logger.debug("Creating transcript in progresss...")
            transcript_data = await self.create_transcript(
                encounter_guid, participant_guid, facility_guid, headers
            )

            transcript_guid = transcript_data["transcript"]["transcriptGuid"]
            logger.debug("Transcript guid for new transcript extracted successfully")

        patient_practice_guid = participant_guid

        if request.healthConcernNote:
            await self.create_health_concern(
                patient_practice_guid, request.healthConcernNote, headers
            )

        fields = {
            "chiefComplaintNote": request.chiefComplaint,
            "subjectiveNote": self.format_rich_text(request.subjectiveNote),
            "objectiveNote": self.format_rich_text(request.objectiveNote),
            "assessmentNote": self.format_rich_text(request.assessmentNote),
            "planNote": self.format_rich_text(request.planNote),
        }

        for field, value in fields.items():
            if value:
                await self.update_transcript_field(
                    patient_practice_guid, transcript_guid, field, value, headers
                )

        if request.carePlanNotes:
            await self.update_care_plan_notes(
                patient_practice_guid, transcript_guid, request.carePlanNotes, headers
            )

        if request.medication:
            await self.process_medications(
                patient_practice_guid,
                transcript_guid,
                request.medication,
                request.providerNameOrGuid,
                headers,
            )

        logger.debug("Transcript added/updated successfully")

        return JSONResponse(
            {
                "status": True,
                "message": (
                    f"Encounter transcript with id: {transcript_guid} created successfully"
                    if not request.transcriptGuid
                    else f"Encounter transcript with id: {request.transcriptGuid} updated successfully"
                ),
            }
        )
