import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from fpdf import FPDF
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="MinaOperAI - Fast2Mine Edition", layout="wide")
st.title("🚀 MinaOperAI - Análise de Ciclos Fast2Mine")
st.markdown("**Por Diego Salim Mapa** – Ex-gerente Tico-Tico & Fast2Mine | BH, 2026")

uploaded_file = st.file_uploader("Suba sua exportação Fast2Mine (Excel/CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        # Leitura com skiprows para ignorar cabeçalho extra
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, sheet_name=0, skiprows=1)

        # Limpeza básica: converter datas se necessário
        if 'Data Início' in df.columns:
            df['Data Início'] = pd.to_datetime(df['Data Início'], errors='coerce')

        st.success(f"Carregado! {len(df)} ciclos detectados. Colunas: {', '.join(df.columns)}")

        st.subheader("Prévia dos ciclos")
        st.dataframe(df.head(10))

        # Dashboard adaptado para Fast2Mine
        st.subheader("Dashboard Avançado - Ciclos de Frota")

        date_col = 'Data Início' if 'Data Início' in df.columns else None
        mass_col = 'Massa (tons)' if 'Massa (tons)' in df.columns else None
        ciclo_col = 'Tempo de Ciclo (min)' if 'Tempo de Ciclo (min)' in df.columns else None
        fila_col = 'Tempo Fila Carregamento (min)' if 'Tempo Fila Carregamento (min)' in df.columns else None
        vazio_col = 'Tempo Vazio (min)' if 'Tempo Vazio (min)' in df.columns else None

        if date_col and mass_col:
            df_group = df.groupby(pd.Grouper(key=date_col, freq='D'))[mass_col].sum().reset_index()
            fig_prod = px.line(df_group, x=date_col, y=mass_col, title='Produção Diária (Massa Total)')
            st.plotly_chart(fig_prod)

        if ciclo_col:
            fig_ciclo = px.histogram(df, x=ciclo_col, title='Distribuição de Tempo de Ciclo (min)')
            st.plotly_chart(fig_ciclo)

        if fila_col:
            fig_fila = px.box(df, y=fila_col, title='Tempo de Fila Carregamento (min) - Gargalos')
            st.plotly_chart(fig_fila)

        # Métricas rápidas
        st.subheader("Métricas Rápidas (estilo Fast2Mine)")
        col1, col2, col3 = st.columns(3)
        if mass_col:
            total_mass = df[mass_col].sum()
            col1.metric("Total Massa Movimentada", f"{total_mass:,.0f} tons")
        if ciclo_col:
            media_ciclo = df[ciclo_col].mean()
            col2.metric("Tempo Médio Ciclo", f"{media_ciclo:.1f} min")
        if fila_col:
            media_fila = df[fila_col].mean()
            col3.metric("Tempo Médio Fila Carreg.", f"{media_fila:.1f} min")

        # IA com dados resumidos (evita limite de tokens)
        st.subheader("Pergunte à IA (gerente de frota Fast2Mine)")
        query = st.text_input("Ex: 'Análise de ciclos de carga: onde está o gargalo?'")

        if st.button("Analisar") and query:
            with st.spinner("Analisando..."):
                # Resumo inteligente para caber no prompt
                summary = f"""
                Resumo da planilha Fast2Mine ({len(df)} ciclos):
                - Total massa movimentada: {df.get(mass_col, pd.Series([0])).sum():,.0f} tons
                - Tempo médio ciclo: {df.get(ciclo_col, pd.Series([0])).mean():.1f} min
                - Tempo médio fila carregamento: {df.get(fila_col, pd.Series([0])).mean():.1f} min
                - Tempo médio vazio: {df.get(vazio_col, pd.Series([0])).mean():.1f} min
                - Turnos únicos: {df['Turno'].unique().tolist() if 'Turno' in df.columns else 'N/A'}
                - Equipamentos comuns: {df['Caminhão'].value_counts().head(5).to_dict() if 'Caminhão' in df.columns else 'N/A'}
                - Média por turno: {df.groupby('Turno')[mass_col].mean().to_dict() if 'Turno' in df.columns and mass_col else 'N/A'}
                """

                prompt = f"""
                Você é gerente de frota com experiência em Fast2Mine Mining Control.
                Resumo dos dados:
                {summary}

                Pergunta: {query}

                Responda prático em português:
                - Use os números do resumo.
                - Foque em gargalos (fila, ciclo longo, ociosidade).
                - Sugestões reais: ajuste dispatch, manutenção, negociação diesel, otimização turno.
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.7
                )
                st.markdown("**Resposta da IA:**")
                st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Erro ao processar: {e}. Tente remover linhas vazias ou verificar formato.")
else:
    st.info("Suba a exportação do Fast2Mine. Skiprows=1 aplicado para pular cabeçalho extra.")