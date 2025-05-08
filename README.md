# Aplicativo Streamlit para Análise de IBUTG

Este aplicativo realiza:
- Cálculo do IBUTG com vento corrigido
- Conversão automática UTC -> horário local
- Boxplots por estação e mês com limites configuráveis
- Dendogramas com base em estatísticas de IBUTG

## Uso no Streamlit Community Cloud
1. Crie um repositório no GitHub
2. Faça upload dos arquivos do projeto
3. No campo 'Main file path', use: `app.py`

## Rodando localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```
