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

# ====================== CONFIGURAÇÃO ======================
load_dotenv()

# Senha do app (pode ser alterada ou colocada em Secrets)
APP_PASSWORD = os.getenv("APP_PASSWORD", "mina2026")  # Senha padrão para teste local

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====================== LOGIN ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login - MinaOperAI")
    st.markdown("**Por Diego Salim Mapa** – Ex-gerente Tico-Tico & Fast2Mine | BH, 2026")
    
    password = st.text_input("Digite a senha para acessar:", type="password")
    
    if st.button("Entrar"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Senha incorreta. Tente novamente.")
    st.stop()  # Para o app até o login

# ====================== APP PRINCIPAL ======================
st.set_page_config(page_title="MinaOperAI - Fast2Mine", layout="wide")
st.title("🚀 MinaOperAI - Análise de Ciclos Fast2Mine")
st.markdown("**Por Diego Salim Mapa** – Ex-gerente Tico-Tico & Fast2Mine | Belo Horizonte, 2026")

uploaded_file = st.file_uploader("📤 Suba sua exportação do Fast2Mine (Excel ou CSV)", 
                                 type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        # Lê a planilha pulando as linhas de cabeçalho extras
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, sheet_name=0, skiprows=1)

        # Conversão de data
        if 'Data Início' in df.columns:
            df['Data Início'] = pd.to_datetime(df['Data Início'], errors='coerce')

        st.success(f"✅ Planilha carregada com sucesso! {len(df):,} ciclos detectados.")

        st.subheader("Prévia dos dados")
        st.dataframe(df.head(10))

        # ====================== DASHBOARD ======================
        st.subheader("📊 Dashboard Avançado")

        date_col = 'Data Início' if 'Data Início' in df.columns else None
        mass_col = 'Massa (tons)' if 'Massa (tons)' in df.columns else None
        ciclo_col = 'Tempo de Ciclo (min)' if 'Tempo de Ciclo (min)' in df.columns else None
        fila_col = 'Tempo Fila Carregamento (min)' if 'Tempo Fila Carregamento (min)' in df.columns else None

        col1, col2, col3, col4 = st.columns(4)
        if mass_col:
            col1.metric("Total Massa Movimentada", f"{df[mass_col].sum():,.0f} tons")
        if ciclo_col:
            col2.metric("Tempo Médio de Ciclo", f"{df[ciclo_col].mean():.1f} min")
        if fila_col:
            col3.metric("Tempo Médio Fila", f"{df[fila_col].mean():.1f} min")
        col4.metric("Total Ciclos", f"{len(df):,}")

        # Gráficos
        if date_col and mass_col:
            df_daily = df.groupby(pd.Grouper(key=date_col, freq='D'))[mass_col].sum().reset_index()
            fig1 = px.line(df_daily, x=date_col, y=mass_col, title="Produção Diária (Massa Total)")
            st.plotly_chart(fig1, use_container_width=True)

        if ciclo_col:
            fig2 = px.histogram(df, x=ciclo_col, title="Distribuição do Tempo de Ciclo (min)")
            st.plotly_chart(fig2, use_container_width=True)

        if fila_col:
            fig3 = px.box(df, y=fila_col, title="Tempo de Fila no Carregamento (min)")
            st.plotly_chart(fig3, use_container_width=True)

        # ====================== IA ======================
        st.subheader("💬 Pergunte à IA (Gerente de Frota Fast2Mine)")
        query = st.text_input("Exemplo: 'Onde está o maior gargalo?', 'Sugestões para reduzir ociosidade', 'Análise de ciclos'")

        if st.button("Analisar com IA") and query:
            with st.spinner("Analisando dados como gerente experiente..."):
                # Resumo para evitar limite de tokens
                summary = f"""
                Resumo da planilha Fast2Mine ({len(df)} ciclos):
                - Total massa: {df.get(mass_col, pd.Series([0])).sum():,.0f} tons
                - Tempo médio ciclo: {df.get(ciclo_col, pd.Series([0])).mean():.1f} min
                - Tempo médio fila carregamento: {df.get(fila_col, pd.Series([0])).mean():.1f} min
                - Turnos presentes: {df['Turno'].unique().tolist() if 'Turno' in df.columns else 'N/A'}
                """

                prompt = f"""
                Você é um gerente de operações de frota com muita experiência em Fast2Mine no Quadrilátero Ferrífero.
                Resumo dos dados:
                {summary}

                Pergunta do usuário: {query}

                Responda de forma clara, prática e direta em português, como um parceiro experiente.
                Use números do resumo e dê sugestões reais (otimização de dispatch, redução de fila, manutenção, etc.).
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.7
                )
                st.markdown("**Resposta da IA:**")
                st.write(response.choices[0].message.content)

        # ====================== EXPORT PDF ======================
        st.subheader("📄 Exportar Relatório PDF com Gráficos")
        if st.button("Gerar PDF Completo"):
            with st.spinner("Gerando PDF com gráficos..."):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Relatório MinaOperAI - Análise Fast2Mine", ln=1, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
                pdf.cell(0, 10, f"Total de ciclos: {len(df):,}", ln=1)

                if mass_col:
                    pdf.cell(0, 10, f"Total massa movimentada: {df[mass_col].sum():,.0f} tons", ln=1)
                if ciclo_col:
                    pdf.cell(0, 10, f"Tempo médio de ciclo: {df[ciclo_col].mean():.1f} min", ln=1)

                # Adiciona gráfico de produção no PDF
                if date_col and mass_col:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    df_daily = df.groupby(pd.Grouper(key=date_col, freq='D'))[mass_col].sum()
                    ax.plot(df_daily.index, df_daily.values, marker='o')
                    ax.set_title("Produção Diária")
                    ax.set_xlabel("Data")
                    ax.set_ylabel("Toneladas")
                    plt.xticks(rotation=45)
                    plt.tight_layout()

                    buf = BytesIO()
                    fig.savefig(buf, format="png", dpi=200)
                    buf.seek(0)
                    plt.close(fig)

                    pdf.add_page()
                    pdf.image(buf, x=10, y=20, w=180)

                pdf.output("relatorio_minaoperai.pdf")

                with open("relatorio_minaoperai.pdf", "rb") as f:
                    st.download_button(
                        label="📥 Baixar PDF Completo",
                        data=f,
                        file_name="relatorio_minaoperai.pdf",
                        mime="application/pdf"
                    )

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        st.info("Dica: Certifique-se de que a planilha tem as colunas esperadas do Fast2Mine.")

else:
    st.info("👆 Suba sua planilha de exportação do Fast2Mine para começar a análise.")

st.caption("MinaOperAI • Desenvolvido por Diego Salim Mapa")