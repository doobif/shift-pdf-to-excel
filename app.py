import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
from openpyxl import Workbook

st.set_page_config(page_title="Shift PDF → Excel Converter", layout="centered")

st.title("ממיר דו\"ח משמרות לקובץ אקסל")

st.write("העלה קובץ PDF של המשמרות והכנס את שם העובד")

worker_name = st.text_input("שם העובד")
uploaded_pdf = st.file_uploader("העלאת קובץ PDF", type=["pdf"])

def parse_pdf(pdf_file):
    text = ""
    tables = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
            t = page.extract_tables()
            for tbl in t:
                if tbl:
                    tables.extend(tbl)

    return text, tables

def extract_header_info(text):
    # Phone number
    phone_match = re.search(r"05\d{8}", text)
    phone = phone_match.group(0) if phone_match else "לא נמצא"

    # Month title, e.g. “משמרות נובמבר 2025”
    month_match = re.search(r"משמרות\s+\S+\s+\d{4}", text)
    month_title = month_match.group(0) if month_match else "חודש לא ידוע"

    return phone, month_title

def clean_table_rows(rows):
    clean = []
    for r in rows:
        if len(r) >= 4 and all(r):
            week, shift, date, hours = r[0], r[1], r[2], r[3]
            # Accept only valid hour rows
            if re.search(r"\d", str(hours)):
                clean.append([week, shift, date, hours])
    return clean

if uploaded_pdf and worker_name:
    text, raw_rows = parse_pdf(uploaded_pdf)
    phone, month_title = extract_header_info(text)

    cleaned = clean_table_rows(raw_rows)

    df = pd.DataFrame(cleaned, columns=["מספר שבוע", "סוג משמרת", "תאריך", "כמות שעות"])

    total_shifts = len(df)
    total_hours = df["כמות שעות"].astype(int).sum()

    # Create Excel
    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = month_title

    ws.append([f"{month_title} - {worker_name}"])
    ws.append([f"טלפון: {phone}"])
    ws.append([])

    ws.append(["מספר שבוע", "סוג משמרת", "תאריך", "כמות שעות"])

    for _, row in df.iterrows():
        ws.append(list(row.values))

    ws.append([])
    ws.append([f"סך הכל משמרות: {total_shifts}"])
    ws.append([f"סך הכל שעות: {total_hours}"])

    wb.save(output)
    output.seek(0)

    st.success("הקובץ מוכן להורדה!")
    st.download_button(
        label="📥 הורדת קובץ אקסל",
        data=output,
        file_name=f"{month_title}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

