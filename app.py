
# Streamlit App de IBUTG com proteção para dendogramas nulos
import streamlit as st
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="wide")
st.title("Análise de IBUTG com Gráficos e Dendogramas")

st.subheader("Exemplo de Dendograma com Verificação")

# Simulação de gráfico inválido (None)
fig = None

if fig is not None:
    st.pyplot(fig)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300)
    st.download_button("📥 Baixar Gráfico", buf.getvalue(), file_name="grafico.png")
else:
    st.warning("⚠️ Dendograma não pôde ser gerado. Verifique os dados disponíveis.")
