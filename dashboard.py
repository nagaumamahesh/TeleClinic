# IMPORTS
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import db
import notifbot


# SETUP
st_autorefresh(2000)


# HELPER FUNCTIONS
def prescription_parser(dr_input: str) -> tuple:
    '''
    Parses the doctor's prescription and returns a list of dictionaries in the following format:
    [
        {
            "name": <medicine-name>,
            "days": <number-of-days>,
            "timings": [<morning>, <afternoon>, <night>]
        },
        ...
    ]
    '''
    symptoms, prescription = dr_input.split("\n\n")
    symptoms = symptoms.split("\n")[1:]
    prescription = prescription.split("\n")[1:]
    prescription = [medicine.split() for medicine in prescription]
    prescription = [
        {
            "name": prescription[0], 
            "days": int(prescription[1]), 
            "timings": [True if x == "O" else False for x in prescription[2].split("-")]
        } 
        for prescription in prescription]
    return symptoms, prescription

def appointment_over(telegram_id: int, dr_input: str) -> None:
    '''
    Marks the appointment as over and sends the prescription to the patient
    '''
    symptoms, prescription = prescription_parser(dr_input)
    notifbot.send_prescription_to_patient(telegram_id, prescription)
    db.create_consultation(telegram_id, symptoms, prescription)
    db.close_appointment(telegram_id)
    notifbot.send_queue_notif()


# PAGE RENDER
st.markdown("""
# ```Health-Centre Queue 🏥```
Used by the doctor to monitor the queue for the health centre appointments and log their prescriptions
""")

with st.expander("Usage"):
    st.markdown("""
    ```
    Enter the patient's prescription using the following format:
                
    Symptoms:
    <symptom-name>
                
    Medicines:
    <medicine-name> <number-of-days> <morning-afternoon-night>
    [X = Do not take medicine, O = Take Medicine]

    Example:
    
    Symptoms:
    High fever
    Body pain
    Dehydration
    
    Medicines:
    Dolo-650 2 O-X-O
    ORS 3 O-O-O
    ```
    """)

st.markdown("""
---
""")


for patient in db.get_active_appointments():
    with st.container():
        left, right = st.columns(2, gap = "small")
        with left:
            st.write("Name: ", patient['name'])
            st.write("Age: ", patient['age'])
            st.write("Sex: ", patient['sex'])
            st.write("Phone Number: ", patient['phone_no'])
            st.write("Time: ", patient['time'])
        
        with right:
            with st.form(key = str(patient['telegram_id'])):
                dr_input = st.text_area(value="Symptoms: \n\nMedicines: ", label = "Enter the patient presciption", placeholder = "Enter here")
                submitted = st.form_submit_button("Submit")

                if submitted and dr_input != "":
                    appointment_over(patient['telegram_id'], dr_input)