# Aplicativo Streamlit para Análise de IBUTG

Este app realiza:
- Cálculo do IBUTG com vento corrigido
- Boxplots por estação e mês
- Dendogramas com verificação contra gráficos nulos
- Exportação de planilha preenchida e gráficos .png 300dpi

## Rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar no Streamlit Community Cloud
1. Suba os arquivos para um repositório no GitHub
2. Defina `Main file path` como `app.py`
