import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from fpdf import FPDF
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

load_dotenv()

# Senha do app
APP_PASSWORD = os.getenv("APP_PASSWORD", "mina2026")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====================== LOGIN ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login - MinaOperAI")
    st.markdown("**Por Diego Salim Mapa** – Engenheiro de Minas + MBA Data Science | BH, 2026")
    
    password = st.text_input("Digite a senha para acessar:", type="password")
    
    if st.button("Entrar"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.success("Login realizado!")
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# ====================== APP ======================
st.set_page_config(page_title="MinaOperAI - Fast2Mine", layout="wide")
st.title("🚀 MinaOperAI - Análise de Ciclos Fast2Mine")
st.markdown("**Por Diego Salim Mapa** – Engenheiro de Minas + MBA Data Science | BH, 2026")

uploaded_file = st.file_uploader("📤 Suba sua exportação do Fast2Mine (Excel ou CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, sheet_name=0, skiprows=1)

        if 'Data Início' in df.columns:
            df['Data Início'] = pd.to_datetime(df['Data Início'], errors='coerce')

        st.success(f"✅ Carregado! {len(df):,} ciclos.")

        st.subheader("Prévia")
        st.dataframe(df.head(10))

        # Métricas
        st.subheader("Métricas Rápidas")
        col1, col2, col3 = st.columns(3)
        if 'Massa (tons)' in df.columns:
            col1.metric("Total Massa", f"{df['Massa (tons)'].sum():,.0f} tons")
        if 'Tempo de Ciclo (min)' in df.columns:
            col2.metric("Tempo Médio Ciclo", f"{df['Tempo de Ciclo (min)'].mean():.1f} min")
        if 'Tempo Fila Carregamento (min)' in df.columns:
            col3.metric("Tempo Médio Fila", f"{df['Tempo Fila Carregamento (min)'].mean():.1f} min")

        # IA
        st.subheader("Pergunte à IA")
        query = st.text_input("Ex: 'Onde está o gargalo nos ciclos?'")

        if st.button("Analisar") and query:
            with st.spinner("Analisando..."):
                summary = f"Total ciclos: {len(df)}\nTotal massa: {df.get('Massa (tons)', pd.Series([0])).sum():,.0f} tons"
                prompt = f"Você é gerente de frota Fast2Mine. Resumo: {summary}\nPergunta: {query}\nResponda prático em português."
                response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], max_tokens=600)
                st.write(response.choices[0].message.content)

        # PDF
        if st.button("Gerar PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Relatório MinaOperAI", ln=1, align='C')
            pdf.output("relatorio.pdf")
            with open("relatorio.pdf", "rb") as f:
                st.download_button("Baixar PDF", f, "relatorio.pdf")

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("Suba sua planilha do Fast2Mine para começar.")