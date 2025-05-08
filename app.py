# Streamlit App: Cálculo de IBUTG com Dendogramas e Boxplots
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from timezonefinder import TimezoneFinder
import pytz
import io
import os
import math
from datetime import datetime
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.preprocessing import StandardScaler

st.set_page_config(layout="wide")
st.title("Análise de IBUTG com Gráficos e Dendogramas")

uploaded_modelo = st.file_uploader("📄 Envie a planilha modelo (.xlsx) com as abas Planilha 1, 2, 3 e 4:", type="xlsx")
uploaded_csvs = st.file_uploader("📄 Envie os arquivos CSV do INMET:", type="csv", accept_multiple_files=True)

nomes_estacoes = {"outono": "Outono", "inverno": "Inverno", "primavera": "Primavera", "verão": "Verão"}
nomes_meses = {
    "janeiro": "Janeiro", "fevereiro": "Fevereiro", "março": "Março", "abril": "Abril",
    "maio": "Maio", "junho": "Junho", "julho": "Julho", "agosto": "Agosto",
    "setembro": "Setembro", "outubro": "Outubro", "novembro": "Novembro", "dezembro": "Dezembro"
}

# Funções
def criar_dendograma_entre_grupos(df, grupo_coluna):
    pivot = df.pivot_table(index=grupo_coluna, columns="Hora", values="IBUTG", aggfunc="mean")
    pivot = pivot.dropna(axis=0, how="any")
    if pivot.shape[0] < 2:
        return None
    scaled = StandardScaler().fit_transform(pivot)
    linked = linkage(scaled, method='ward')
    fig, ax = plt.subplots(figsize=(10, 6))
    dendrogram(linked, labels=pivot.index, leaf_rotation=90)
    plt.title(f"Dendograma de {grupo_coluna}s com base no IBUTG")
    plt.ylabel("Distância Euclidiana")
    plt.xlabel(grupo_coluna)
    return fig

def criar_boxplot_por_grupo(df, grupo_coluna, limites=None):
    if grupo_coluna == "Estação":
        ordem_grupos = ["Outono", "Inverno", "Primavera", "Verão"]
        n_colunas = 2
    else:
        ordem_grupos = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        n_colunas = 3

    letras = [chr(97 + i) + ") " for i in range(len(ordem_grupos))]
    grupos_legenda = {g: letras[i] + g for i, g in enumerate(ordem_grupos)}
    df['Grupo_Rotulado'] = df[grupo_coluna].map(grupos_legenda)

    n_linhas = -(-len(ordem_grupos) // n_colunas)
    fig, axes = plt.subplots(n_linhas, n_colunas, figsize=(6 * n_colunas, 5 * n_linhas), squeeze=False)

    for idx, grupo in enumerate(ordem_grupos):
        linha = idx // n_colunas
        coluna = idx % n_colunas
        ax = axes[linha][coluna]
        subset = df[df[grupo_coluna] == grupo]
        sns.boxplot(x="Hora", y="IBUTG", data=subset, ax=ax, palette="Set2")
        ax.set_title(grupos_legenda[grupo])
        ax.set_xlabel("Hora" if linha == n_linhas - 1 else "")
        ax.set_ylabel("IBUTG (°C)" if coluna == 0 else "")
        ax.set_ylim(10, 40)
        ax.set_yticks(range(10, 41, 5))
        ax.grid(axis='x', linestyle='--', alpha=0.4, which='major')
        ax.grid(axis='y', visible=False)
        if limites and grupo in limites:
            na = limites[grupo].get("NA")
            le = limites[grupo].get("LE")
            if na: ax.axhline(na, color="red", linestyle="--", linewidth=1, label="Nível de Ação")
            if le: ax.axhline(le, color="blue", linestyle="-.", linewidth=1, label="Limite de Exposição")

    for idx in range(len(ordem_grupos), n_linhas * n_colunas):
        fig.delaxes(axes[idx // n_colunas][idx % n_colunas])

    plt.tight_layout()
    return fig

if uploaded_modelo and uploaded_csvs:
    modelo_bytes = uploaded_modelo.read()
    modelo_stream = io.BytesIO(modelo_bytes)
    limites_df = pd.read_excel(io.BytesIO(modelo_bytes), sheet_name='Planilha 4')
    limites_est = {row['Estação']: {'NA': row['Nível de Ação'], 'LE': row['Limite de Exposição']} for _, row in limites_df.iterrows() if pd.notna(row['Nível de Ação']) or pd.notna(row['Limite de Exposição'])}

    for file in uploaded_csvs:
        df = pd.read_csv(file, sep=';', skiprows=8, encoding='latin1')
        df = df[[
            'DATA (YYYY-MM-DD)', 'HORA (UTC)',
            'TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)',
            'TEMPERATURA DO PONTO DE ORVALHO (°C)',
            'UMIDADE RELATIVA DO AR, HORARIA (%)',
            'VENTO, VELOCIDADE HORARIA (m/s)'
        ]]
        for col in df.columns[2:]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        lat, lon = None, None
        with io.StringIO(file.getvalue().decode('latin1')) as f:
            for _ in range(10):
                linha = f.readline().strip()
                if 'LATITUDE' in linha.upper(): lat = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))
                if 'LONGITUDE' in linha.upper(): lon = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))

        timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat))
        df['data_hora_utc'] = pd.to_datetime(df['DATA (YYYY-MM-DD)'] + ' ' + df['HORA (UTC)'], format='%Y-%m-%d %H:%M', utc=True)
        df['data_hora_local'] = df['data_hora_utc'].dt.tz_convert(timezone)
        df['hora_local'] = df['data_hora_local'].dt.hour
        df = df[(df['hora_local'] >= 8) & (df['hora_local'] <= 17)].copy()
        df['G'] = df['TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)']
        df['H'] = df['TEMPERATURA DO PONTO DE ORVALHO (°C)']
        df['I'] = df['UMIDADE RELATIVA DO AR, HORARIA (%)']
        df['J'] = df['VENTO, VELOCIDADE HORARIA (m/s)']
        K1 = 0.4
        ln_parte = math.log(1.5 / K1) / math.log(10 / K1)
        df['K_corrigido'] = df['J'] * ln_parte
        df['IBUTG'] = (
            0.511006 * df['G'] +
            0.400225 * df['H'] -
            0.0192126 * df['I'] -
            0.3899874 * df['K_corrigido'] +
            7.314762
        )
        df = df[df['IBUTG'] >= 0]
        df['Data'] = df['data_hora_local'].dt.date
        df['Hora'] = df['data_hora_local'].dt.strftime('%H:%M')
        df_plot = df[['Data', 'Hora', 'IBUTG']].copy()
        wb = load_workbook(modelo_stream)
        ws2 = wb['Planilha 2']
        ws3 = wb['Planilha 3']
        linha2 = 4
        linha3 = 2
        for _, row in df_plot.iterrows():
            ws2[f'D{linha2}'] = row['Data'].date()
            ws2[f'E{linha2}'] = row['Hora']
            ws2[f'O{linha2}'] = float(f"{row['IBUTG']:.4f}")
            ws3[f'A{linha3}'] = row['Data'].date()
            ws3[f'B{linha3}'] = row['Hora']
            ws3[f'C{linha3}'] = float(f"{row['IBUTG']:.2f}")
            linha2 += 1
            linha3 += 1

        excel_out = io.BytesIO()
        wb.save(excel_out)
        st.download_button("📥 Baixar Planilha Modelo Preenchida", excel_out.getvalue(), file_name="planilha_modelo_preenchida.xlsx")
        df_plot['Data'] = pd.to_datetime(df_plot['Data'])
        df_plot['Hora'] = df_plot['Hora'].str[:5]
        df_plot['Mês'] = df_plot['Data'].dt.month
        df_plot['Nome_Mês'] = df_plot['Mês'].map({i+1: m for i, m in enumerate(nomes_meses.values())})

        def estacao_ano(data):
            ano = data.year
            if datetime(ano, 3, 20) <= data <= datetime(ano, 6, 21): return "Outono"
            elif datetime(ano, 6, 22) <= data <= datetime(ano, 9, 21): return "Inverno"
            elif datetime(ano, 9, 22) <= data <= datetime(ano, 12, 21): return "Primavera"
            else: return "Verão"

        df_plot['Estação'] = df_plot['Data'].apply(estacao_ano)

        st.subheader("📊 Dendogramas")
        fig_est = criar_dendograma_entre_grupos(df_plot, "Estação")
        if fig_est is not None:
            st.pyplot(fig_est)
            buf_est = io.BytesIO()
            fig_est.savefig(buf_est, format="png", dpi=300)
            st.download_button("📥 Baixar Dendograma Estações (300dpi)", buf_est.getvalue(), file_name="dendograma_estacoes.png")
        else:
            st.warning("⚠️ Dendograma de estações não pôde ser gerado. Verifique se há dados suficientes.")
        buf_est = io.BytesIO()
        fig_est.savefig(buf_est, format="png", dpi=300)
        st.download_button("📥 Baixar Dendograma Estações (300dpi)", buf_est.getvalue(), file_name="dendograma_estacoes.png")
        fig_mes = criar_dendograma_entre_grupos(df_plot, "Nome_Mês")
        if fig_mes is not None:
            st.pyplot(fig_mes)
            buf_mes = io.BytesIO()
            fig_mes.savefig(buf_mes, format="png", dpi=300)
            st.download_button("📥 Baixar Dendograma Meses (300dpi)", buf_mes.getvalue(), file_name="dendograma_meses.png")
        else:
            st.warning("⚠️ Dendograma de meses não pôde ser gerado. Verifique se há dados suficientes.")
        buf_mes = io.BytesIO()
        fig_mes.savefig(buf_mes, format="png", dpi=300)
        st.download_button("📥 Baixar Dendograma Meses (300dpi)", buf_mes.getvalue(), file_name="dendograma_meses.png")

        st.subheader("📈 Boxplots por Estação")
        fig_box_est = criar_boxplot_por_grupo(df_plot, "Estação", limites_est)
        st.pyplot(fig_box_est)
        buf_box_est = io.BytesIO()
        fig_box_est.savefig(buf_box_est, format="png", dpi=300)
        st.download_button("📥 Baixar Boxplot Estações (300dpi)", buf_box_est.getvalue(), file_name="boxplot_estacoes.png")

        st.subheader("📈 Boxplots por Mês")
        fig_box_mes = criar_boxplot_por_grupo(df_plot, "Nome_Mês", limites_est)
        st.pyplot(fig_box_mes)
        buf_box_mes = io.BytesIO()
        fig_box_mes.savefig(buf_box_mes, format="png", dpi=300)
        st.download_button("📥 Baixar Boxplot Meses (300dpi)", buf_box_mes.getvalue(), file_name="boxplot_meses.png")
