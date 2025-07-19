import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import tempfile
import matplotlib.pyplot as plt
import io

def generate_png(dataframe, cgpa, total_credits):
    fig, ax = plt.subplots(figsize=(6, len(dataframe)*0.5 + 2))
    ax.axis('tight')
    ax.axis('off')

    summary_row = pd.DataFrame([{"SGPA": f"CGPA: {cgpa:.2f}", "Credits": f"Total Credits: {total_credits}"}])
    summary_df = pd.concat([dataframe, summary_row], ignore_index=True)

    table = ax.table(cellText=summary_df.values, colLabels=summary_df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf




def generate_pdf(dataframe, cgpa, total_credits):
    # Create a temporary file
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp_file.name, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CGPA Calculator Results")

    # Prepare table data including summary
    table_data = [list(dataframe.columns)] + dataframe.values.tolist()
    table_data.append(["", ""])  # Blank row
    table_data.append(["Total Credits", f"{total_credits}"])
    table_data.append(["CGPA", f"{cgpa:.2f}"])

    table = Table(table_data, colWidths=[200, 200])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(style)

    # Calculate table size and position
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 300)

    c.save()
    return tmp_file.name

st.set_page_config(page_title="CGPA Calculator", layout="centered")
st.title("   CGPA Calculator , devloped by Vansh")

# Initialize session state
if "sgpa_list" not in st.session_state:
    st.session_state.sgpa_list = []
    st.session_state.credits_list = []

# ---- Form for better UX ----
with st.form("entry_form", clear_on_submit=True):
    sgpa = st.number_input("🎯 Enter SGPA (0 - 10)", min_value=0.0, max_value=10.0, step=0.1, format="%.2f")
    credit = st.number_input("🎒 Enter Credits", min_value=0.0, step=0.5, format="%.1f")
    submitted = st.form_submit_button("➕ Add Semester")

    if submitted:
        st.session_state.sgpa_list.append(sgpa)
        st.session_state.credits_list.append(credit)
        st.success(f"Added: SGPA = {sgpa}, Credits = {credit}")

# ---- Display Semester List ----
if st.session_state.sgpa_list:
    st.subheader("📋 Semester Entries")
    df = pd.DataFrame({
        "SGPA": st.session_state.sgpa_list,
        "Credits": st.session_state.credits_list
    })
    st.dataframe(df, use_container_width=True)

    # CGPA Calculation
    total_weighted = sum(s * c for s, c in zip(st.session_state.sgpa_list, st.session_state.credits_list))
    total_credits = sum(st.session_state.credits_list)
    cgpa = total_weighted / total_credits if total_credits > 0 else 0
    st.success(f" Your CGPA is: **{cgpa:.2f}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Remove Last Semester"):
            st.session_state.sgpa_list.pop()
            st.session_state.credits_list.pop()
            st.info("Last Semester removed.")
    with col2:
        if st.button("🧹 Clear All"):
            st.session_state.sgpa_list.clear()
            st.session_state.credits_list.clear()
            st.warning("All Semesters cleared.")

    # ---- Export Options ----
    st.markdown("### 📤 Export Your Results")
    export_format = st.selectbox("Select format to export:", ["CSV", "XLSX", "TXT", "PDF", "PNG (table image)"])

    if st.button("⬇️ Export Now"):
        filename = f"cgpa_export.{export_format.lower()}"

        # Prepare dataframe with summary rows
        summary_df = pd.DataFrame({
            "SGPA": ["--", f"CGPA: {cgpa:.2f}"],
            "Credits": [f"Total Credits: {total_credits}", "--"]
        })
        export_df = pd.concat([df, summary_df], ignore_index=True)

        if export_format == "CSV":
            csv = export_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, file_name=filename, mime="text/csv")

        elif export_format == "XLSX":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                export_df.to_excel(writer, index=False, sheet_name="CGPA")
                writer.close()
            st.download_button("Download XLSX", output.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        elif export_format == "TXT":
            text_data = export_df.to_string(index=False)
            st.download_button("Download TXT", text_data.encode(), file_name=filename, mime="text/plain")

        elif export_format == "PDF":
            pdf_path = generate_pdf(export_df, cgpa, total_credits)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button("Download PDF", pdf_bytes, file_name=filename, mime="application/pdf")
        
        elif export_format == "PNG (table image)":
            png_buf = generate_png(df, cgpa, total_credits)
            st.download_button("Download PNG", png_buf, file_name=filename, mime="image/png")
