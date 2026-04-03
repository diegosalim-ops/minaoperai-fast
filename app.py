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

        if 'Data Início' in df.columns:
            df['Data Início'] = pd.to_datetime(df['Data Início'], errors='coerce')

        st.success(f"✅ Carregado! {len(df):,} ciclos encontrados.")

        st.subheader("Prévia dos dados")
        st.dataframe(df.head(10))

        # ====================== SELEÇÃO DE COLUNAS ======================
        st.subheader("🎯 Escolha as colunas para análise")

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        date_cols = [col for col in df.columns if 'Data' in col or 'data' in col.lower()]

        col_x = st.selectbox("Coluna X (geralmente Data ou Tempo)", 
                             options=date_cols + numeric_cols, 
                             index=0 if date_cols else 0)

        col_y = st.selectbox("Coluna Y (o que você quer analisar)", 
                             options=numeric_cols, 
                             index=0)

        remove_outliers = st.checkbox("Remover outliers da coluna Y", value=False)

        if remove_outliers and col_y in df.columns:
            Q1 = df[col_y].quantile(0.25)
            Q3 = df[col_y].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            df = df[(df[col_y] >= lower) & (df[col_y] <= upper)]
            st.info(f"Outliers removidos. Restaram {len(df):,} registros.")

        # ====================== GRÁFICOS ======================
        st.subheader("📊 Gráficos Gerados")

        figures = []  # Vamos guardar os gráficos para o PDF

        if col_x and col_y:
            # Gráfico de Linha
            if col_x in date_cols:
                df_group = df.groupby(pd.Grouper(key=col_x, freq='D'))[col_y].mean().reset_index()
                fig_line = px.line(df_group, x=col_x, y=col_y, title=f"{col_y} ao longo do tempo")
                st.plotly_chart(fig_line, use_container_width=True)
                figures.append(("Linha", fig_line))

            # Scatter Plot
            fig_scatter = px.scatter(df, x=col_x, y=col_y, title=f"{col_y} vs {col_x}")
            st.plotly_chart(fig_scatter, use_container_width=True)
            figures.append(("Scatter", fig_scatter))

            # Box Plot
            fig_box = px.box(df, y=col_y, title=f"Box Plot - {col_y}")
            st.plotly_chart(fig_box, use_container_width=True)
            figures.append(("Box Plot", fig_box))

            # Histograma
            fig_hist = px.histogram(df, x=col_y, title=f"Distribuição de {col_y}")
            st.plotly_chart(fig_hist, use_container_width=True)
            figures.append(("Histograma", fig_hist))

        # ====================== IA ======================
        st.subheader("💬 Pergunte à IA")
        query = st.text_input("Ex: 'Onde está o maior gargalo?' ou 'Sugestões para reduzir tempo de ciclo'")

        ia_response = None
        if st.button("Analisar com IA") and query:
            with st.spinner("Analisando..."):
                summary = f"""
                Total registros: {len(df)}
                Coluna analisada: {col_y}
                Média: {df[col_y].mean():.2f}
                Mínimo: {df[col_y].min():.2f} | Máximo: {df[col_y].max():.2f}
                """
                prompt = f"Você é gerente de frota experiente em Fast2Mine.\nResumo: {summary}\nPergunta: {query}\nResponda prático em português."
                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=700
                )
                ia_response = response.choices[0].message.content
                st.write(ia_response)

        # ====================== GERAR PDF COM GRÁFICOS E ANÁLISE ======================
        if st.button("📄 Gerar PDF Completo (com gráficos e análise)"):
            with st.spinner("Gerando PDF..."):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Relatório MinaOperAI - Fast2Mine", ln=1, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
                pdf.cell(0, 10, f"Total de ciclos: {len(df)}", ln=1)
                pdf.cell(0, 10, f"Coluna analisada: {col_y}", ln=1)
                pdf.ln(5)

                # Métricas
                if col_y in df.columns:
                    pdf.cell(0, 10, f"Média de {col_y}: {df[col_y].mean():.2f}", ln=1)
                    pdf.cell(0, 10, f"Mínimo: {df[col_y].min():.2f} | Máximo: {df[col_y].max():.2f}", ln=1)

                pdf.ln(10)

                # Adicionar gráficos no PDF
                for title, fig in figures:
                    # Converter Plotly para imagem
                    img_bytes = fig.to_image(format="png")
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 10, title, ln=1, align='C')
                    pdf.ln(5)
                    # Salvar temporariamente e inserir
                    with open("temp_img.png", "wb") as f:
                        f.write(img_bytes)
                    pdf.image("temp_img.png", x=10, y=30, w=180)
                    os.remove("temp_img.png")

                # Adicionar resposta da IA
                if ia_response:
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, "Análise da IA", ln=1)
                    pdf.ln(5)
                    pdf.set_font("Arial", size=11)
                    pdf.multi_cell(0, 8, ia_response)

                pdf.output("relatorio_minaoperai.pdf")

                with open("relatorio_minaoperai.pdf", "rb") as f:
                    st.download_button(
                        label="📥 Baixar PDF Completo",
                        data=f,
                        file_name="relatorio_minaoperai.pdf",
                        mime="application/pdf"
                    )

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("👆 Suba sua planilha do Fast2Mine para começar.")

st.caption("MinaOperAI • Desenvolvido por Diego Salim Mapa")