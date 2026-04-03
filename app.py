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

APP_PASSWORD = os.getenv("APP_PASSWORD", "mina2026")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====================== LOGIN ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login - MinaOperAI")
    st.markdown("**Por Diego Salim Mapa** – Engenheiro de Minas + MBA Data Science | BH, 2026")
    password = st.text_input("Digite a senha:", type="password")
    if st.button("Entrar"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.success("Login realizado!")
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# ====================== APP ======================
st.set_page_config(page_title="MinaOperAI", layout="wide")
st.title("🚀 MinaOperAI - Análise Fast2Mine")
st.markdown("**Por Diego Salim Mapa** – Engenheiro de Minas + MBA Data Science | BH, 2026")

uploaded_file = st.file_uploader("Suba sua exportação do Fast2Mine (Excel ou CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, skiprows=1)

        # Conversão de data
        if 'Data Início' in df.columns:
            df['Data Início'] = pd.to_datetime(df['Data Início'], errors='coerce')

        st.success(f"✅ Carregado com sucesso! {len(df):,} ciclos encontrados.")

        st.subheader("Prévia dos dados")
        st.dataframe(df.head(10))

        # ====================== DASHBOARD ======================
        st.subheader("📊 Dashboard")

        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        if 'Massa (tons)' in df.columns:
            col1.metric("Total Massa", f"{df['Massa (tons)'].sum():,.0f} tons")
        if 'Tempo de Ciclo (min)' in df.columns:
            col2.metric("Tempo Médio Ciclo", f"{df['Tempo de Ciclo (min)'].mean():.1f} min")
        if 'Tempo Fila Carregamento (min)' in df.columns:
            col3.metric("Tempo Médio Fila", f"{df['Tempo Fila Carregamento (min)'].mean():.1f} min")
        col4.metric("Total Ciclos", len(df))

        # Gráficos adaptados para sua planilha
        if 'Data Início' in df.columns and 'Massa (tons)' in df.columns:
            df_daily = df.groupby(pd.Grouper(key='Data Início', freq='D'))['Massa (tons)'].sum().reset_index()
            fig1 = px.line(df_daily, x='Data Início', y='Massa (tons)', title="Produção Diária (Massa Total)")
            st.plotly_chart(fig1, use_container_width=True)

        if 'Tempo de Ciclo (min)' in df.columns:
            fig2 = px.histogram(df, x='Tempo de Ciclo (min)', title="Distribuição do Tempo de Ciclo")
            st.plotly_chart(fig2, use_container_width=True)

        if 'Tempo Fila Carregamento (min)' in df.columns:
            fig3 = px.box(df, y='Tempo Fila Carregamento (min)', title="Tempo de Fila no Carregamento")
            st.plotly_chart(fig3, use_container_width=True)

        # ====================== IA ======================
        st.subheader("💬 Pergunte à IA")
        query = st.text_input("Ex: 'Onde está o maior gargalo?' ou 'Sugestões para reduzir fila'")

        if st.button("Analisar com IA") and query:
            with st.spinner("Analisando..."):
                summary = f"""
                Total ciclos: {len(df)}
                Total massa: {df.get('Massa (tons)', pd.Series([0])).sum():,.0f} tons
                Tempo médio ciclo: {df.get('Tempo de Ciclo (min)', pd.Series([0])).mean():.1f} min
                Tempo médio fila: {df.get('Tempo Fila Carregamento (min)', pd.Series([0])).mean():.1f} min
                """
                prompt = f"Você é gerente de frota experiente em Fast2Mine. Resumo: {summary}\nPergunta: {query}\nResponda prático em português com sugestões reais."
                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=700
                )
                st.write(response.choices[0].message.content)

        # ====================== PDF ======================
        if st.button("📄 Gerar PDF Completo"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Relatório MinaOperAI - Fast2Mine", ln=1, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
            pdf.cell(0, 10, f"Total ciclos: {len(df)}", ln=1)
            if 'Massa (tons)' in df.columns:
                pdf.cell(0, 10, f"Total massa: {df['Massa (tons)'].sum():,.0f} tons", ln=1)

            pdf.output("relatorio_minaoperai.pdf")
            with open("relatorio_minaoperai.pdf", "rb") as f:
                st.download_button("Baixar PDF", f, "relatorio_minaoperai.pdf")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("👆 Suba sua planilha de exportação do Fast2Mine para começar.")

st.caption("MinaOperAI • Desenvolvido por Diego Salim Mapa")