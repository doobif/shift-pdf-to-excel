import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
from openpyxl import Workbook

st.set_page_config(page_title="Shift PDF → Excel Converter", layout="centered")
st.title("ממיר דו\"ח משמרות לקובץ אקסל")

worker_name = st.text_input("שם העובד")
uploaded_pdf = st.file_uploader("העלאת קובץ PDF", type=["pdf"])


def extract_text_lines(pdf_file):
    all_lines = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    clean = line.strip()
                    if clean:
                        all_lines.append(clean)
    return all_lines


def extract_header_info(lines):
    phone = "לא נמצא"
    month = "חודש לא ידוע"

    for line in lines:
        if re.fullmatch(r"05\d{8}", line):
            phone = line
        if line.startswith("משמרות "):
            month = line

    return phone, month


def extract_shifts(lines):
    shifts = []
    current = []

    # A valid shift item is detected by hour line: a pure number
    for line in lines:
        if re.fullmatch(r"\d{1,2}", line):  # hours
            current.append(line)
            if len(current) == 4:
                shifts.append(current)
                current = []
        else:
            # collect lines until 4 elements
            if len(current) < 3:  
                current.append(line)
            else:
                # if 3 items but next is not hours, reset
                current = []

    # Clean and format
    cleaned = []
    for s in shifts:
        if len(s) == 4:
            week, shift_type, date, hours = s
            cleaned.append([week, shift_type, date, hours])

    return cleaned


if uploaded_pdf and worker_name:
    lines = extract_text_lines(uploaded_pdf)
    phone, month_title = extract_header_info(lines)
    shift_rows = extract_shifts(lines)

    df = pd.DataFrame(shift_rows, columns=["מספר שבוע", "סוג משמרת", "תאריך", "כמות שעות"])
    df["כמות שעות"] = df["כמות שעות"].astype(int)

    total_shifts = len(df)
    total_hours = df["כמות שעות"].sum()

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


