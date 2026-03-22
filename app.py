import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
import requests

nltk.download("stopwords")

st.set_page_config(layout="wide")

st.title("Dashboard de Reclamações - ReclameAqui")

# =============================
# CARREGAR DADOS
# =============================

df = pd.read_csv("reclamacoes_tratado.csv")

# =============================
# VARIÁVEIS DERIVADAS
# =============================

df["tamanho_texto"] = df["DESCRICAO"].astype(str).apply(len)

# =============================
# FILTROS
# =============================

st.sidebar.header("Filtros")

estado = st.sidebar.multiselect(
    "Estado",
    options=df["ESTADO"].dropna().unique(),
    default=df["ESTADO"].dropna().unique()
)

status = st.sidebar.multiselect(
    "Status",
    options=df["STATUS"].unique(),
    default=df["STATUS"].unique()
)

texto_min, texto_max = st.sidebar.slider(
    "Tamanho do texto",
    int(df["tamanho_texto"].min()),
    int(df["tamanho_texto"].max()),
    (int(df["tamanho_texto"].min()), int(df["tamanho_texto"].max()))
)

df_filtrado = df[
    (df["ESTADO"].isin(estado)) &
    (df["STATUS"].isin(status)) &
    (df["tamanho_texto"].between(texto_min, texto_max))
]

# =============================
# MÉTRICAS (CORRIGIDO)
# =============================

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total de Reclamações", len(df_filtrado))

col2.metric("Resolvidas", len(df_filtrado[df_filtrado["STATUS"] == "resolvido"]))

col3.metric("Respondidas", len(df_filtrado[df_filtrado["STATUS"] == "respondida"]))

col4.metric("Em Réplica", len(df_filtrado[df_filtrado["STATUS"] == "em replica"]))

col5.metric("Não Respondidas", len(df_filtrado[df_filtrado["STATUS"] == "nao respondida"]))

col6.metric("Não Resolvidas", len(df_filtrado[df_filtrado["STATUS"] == "nao resolvido"]))

st.divider()

# =============================
# SÉRIE TEMPORAL (CORRIGIDO)
# =============================

st.subheader("Evolução das Reclamações")

serie = df_filtrado.groupby(["ANO","MES"]).size().reset_index(name="quantidade")

serie["data"] = pd.to_datetime(
    serie["ANO"].astype(str) + "-" + serie["MES"].astype(str)
)

serie["media_movel"] = serie["quantidade"].rolling(3).mean()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=serie["data"],
    y=serie["quantidade"],
    name="Reclamações"
))

fig.add_trace(go.Scatter(
    x=serie["data"],
    y=serie["media_movel"],
    name="Média Móvel"
))

st.plotly_chart(fig, use_container_width=True)

# =============================
# MAPA DO BRASIL (CORRIGIDO)
# =============================

st.subheader("Mapa de Reclamações por Estado")

url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson = requests.get(url).json()

mapa = df_filtrado.groupby("ESTADO").size().reset_index(name="quantidade")

fig_mapa = px.choropleth(
    mapa,
    geojson=geojson,
    locations="ESTADO",
    featureidkey="properties.sigla",
    color="quantidade",
    color_continuous_scale="Blues"
)

fig_mapa.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig_mapa, use_container_width=True)

# =============================
# PARETO (CORRIGIDO)
# =============================

st.subheader("Estados com Mais Reclamações")

pareto = df_filtrado.groupby("ESTADO").size().reset_index(name="quantidade")
pareto = pareto.sort_values(by="quantidade", ascending=False)

fig_pareto = px.bar(
    pareto,
    x="ESTADO",
    y="quantidade"
)

st.plotly_chart(fig_pareto, use_container_width=True)

# =============================
# STATUS (OK)
# =============================

st.subheader("Distribuição de Status")

status_count = df_filtrado["STATUS"].value_counts().reset_index()
status_count.columns = ["STATUS","quantidade"]

fig_status = px.pie(
    status_count,
    names="STATUS",
    values="quantidade"
)

st.plotly_chart(fig_status, use_container_width=True)

# =============================
# BOXPLOT
# =============================

st.subheader("Tamanho das Reclamações por Status")

fig_box = px.box(
    df_filtrado,
    x="STATUS",
    y="tamanho_texto"
)

st.plotly_chart(fig_box, use_container_width=True)

# =============================
# WORDCLOUD
# =============================

st.subheader("Palavras mais Frequentes")

stop_words = set(stopwords.words("portuguese"))

texto = " ".join(df_filtrado["DESCRICAO"].astype(str))

wordcloud = WordCloud(
    width=800,
    height=400,
    stopwords=stop_words,
    background_color="white"
).generate(texto)

fig, ax = plt.subplots()

ax.imshow(wordcloud)
ax.axis("off")

st.pyplot(fig)

# =============================
# DEBUG
# =============================

st.write("Total original:", len(df))
st.write("Total filtrado:", len(df_filtrado))

# streamlit run app.py