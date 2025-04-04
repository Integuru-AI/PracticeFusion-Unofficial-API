# **PracticeFusion-API**  
This project integrates with **Practice Fusion** to manage patient appointments, encounter summaries, and SOAP notes. It allows users to create, update, and retrieve medical records efficiently.  

---

## **Endpoints**  

### **Authentication & Credentials**  
- **POST** `/practicefusion/add-creds` – Add And Authorize Creds  

### **Patient Management**  
- **POST** `/practicefusion/create-patient` – Create Patient  

### **Documents**  
- **POST** `/practicefusion/upload-documents` – Upload Documents  

### **Appointments**  
- **POST** `/practicefusion/create-appointment` – Create Appointment  
- **PUT** `/practicefusion/get-appointments` – Get Appointments List  
- **POST** `/practicefusion/update-appointment` – Update Appointment  

### **Encounter Summaries & SOAP Notes**  
- **GET** `/practicefusion/encounter-summaries` – Get Encounter Summaries  
- **POST** `/practicefusion/add-or-edit-soap-notes` – Add or Edit SOAP Notes  

---

## **Installation**  
This API is designed to be integrated into a [larger project](https://github.com/Unofficial-APIs/Integrations).  

---

## **Info**  
This unofficial API is built by **[Integuru.ai](https://integuru.ai/)**. We take custom requests for new platforms or additional features for existing platforms. We also offer hosting and authentication services.  

If you have requests or want to work with us, reach out at **richard@taiki.online**.  

Here's a **[complete list](https://github.com/Integuru-AI/APIs-by-Integuru)** of unofficial APIs built by Integuru.ai.  
This repo is part of our integrations package: **[GitHub Repo](https://github.com/Integuru-AI/Integrations)**.