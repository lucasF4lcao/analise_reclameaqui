import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
import requests
import plotly.express as px
import unicodedata

nltk.download("stopwords")

st.set_page_config(layout="wide")

st.title("Dashboard de Reclamações - ReclameAqui")

url = "https://raw.githubusercontent.com/lucasF4lcao/analise_reclameaqui/main/datasets/reclamacoes_tratado.csv"
df = pd.read_csv(url)

df["tamanho_texto"] = df["DESCRICAO"].astype(str).apply(len)

df["data_completa"] = pd.to_datetime(
    df["ANO"].astype(str) + "-" + df["MES"].astype(str) + "-01"
)

# função para normalizar texto
def normalizar(texto):
    if pd.isna(texto):
        return ""
    return unicodedata.normalize('NFKD', str(texto))\
        .encode('ascii', 'ignore')\
        .decode('utf-8')\
        .lower()

# normalizar cidade
if "CIDADE" in df.columns:
    df["CIDADE"] = df["CIDADE"].apply(normalizar)

# filtros
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

if "CIDADE" in df.columns:
    municipio = st.sidebar.multiselect(
        "Município",
        options=df["CIDADE"].dropna().unique(),
        default=df["CIDADE"].dropna().unique()
    )
else:
    municipio = df["ESTADO"]

texto_min, texto_max = st.sidebar.slider(
    "Tamanho do texto",
    int(df["tamanho_texto"].min()),
    int(df["tamanho_texto"].max()),
    (int(df["tamanho_texto"].min()), int(df["tamanho_texto"].max()))
)

st.sidebar.subheader("Busca Inteligente")
busca = st.sidebar.text_input("Digite um problema (ex: entrega, cobrança)")

df_filtrado = df[
    (df["ESTADO"].isin(estado)) &
    (df["STATUS"].isin(status)) &
    (df["tamanho_texto"].between(texto_min, texto_max))
]

if "CIDADE" in df.columns:
    df_filtrado = df_filtrado[df_filtrado["CIDADE"].isin(municipio)]

if busca:
    palavras_busca = normalizar(busca).split()

    df_filtrado = df_filtrado[
        df_filtrado["DESCRICAO"].astype(str).apply(
            lambda x: all(p in normalizar(x) for p in palavras_busca)
        )
    ]

    st.info(f"Mostrando resultados para: '{busca}'")

    total = len(df_filtrado)
    nao_resolvidas = len(df_filtrado[df_filtrado["STATUS"] == "nao resolvido"])

    if total > 0:
        st.success(
            f"Foram encontradas {total} reclamações. "
        )
    else:
        st.warning("Nenhuma reclamação encontrada.")

# métricas
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total de Reclamações", len(df_filtrado))
col2.metric("Resolvidas", len(df_filtrado[df_filtrado["STATUS"] == "resolvido"]))
col3.metric("Respondidas", len(df_filtrado[df_filtrado["STATUS"] == "respondida"]))
col4.metric("Em Réplica", len(df_filtrado[df_filtrado["STATUS"] == "em replica"]))
col5.metric("Não Respondidas", len(df_filtrado[df_filtrado["STATUS"] == "nao respondida"]))
col6.metric("Não Resolvidas", len(df_filtrado[df_filtrado["STATUS"] == "nao resolvido"]))

st.divider()

if busca:
    st.subheader("Exemplos de Reclamações")

    exemplos = df_filtrado[["ID", "DESCRICAO"]].dropna().head(5)

    for _, row in exemplos.iterrows():
        st.markdown(f"### 🧾 Reclamação {row['ID']}")
        st.write(row["DESCRICAO"])
        st.divider()

# série temporal
st.subheader("Evolução das Reclamações")

tipo_tempo = st.radio("Visualização", ["Mensal", "Semanal"])

if tipo_tempo == "Mensal":
    serie = df_filtrado.groupby(["ANO","MES"]).size().reset_index(name="quantidade")
    serie["data"] = pd.to_datetime(
        serie["ANO"].astype(str) + "-" + serie["MES"].astype(str)
    )
else:
    serie = df_filtrado.copy()
    serie["SEMANA"] = serie["data_completa"].dt.to_period("W").astype(str)
    serie = serie.groupby("SEMANA").size().reset_index(name="quantidade")
    serie["data"] = pd.to_datetime(serie["SEMANA"].str[:10])

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

# cruzamento
st.subheader("Status por Estado")

top_estados = df_filtrado["ESTADO"].value_counts().nlargest(10).index

cruzamento_estado = df_filtrado[df_filtrado["ESTADO"].isin(top_estados)] \
    .groupby(["ESTADO", "STATUS"]) \
    .size() \
    .reset_index(name="quantidade")

fig_estado = px.bar(
    cruzamento_estado,
    x="ESTADO",
    y="quantidade",
    color="STATUS",
    barmode="group",
    color_discrete_map={
        "resolvido": "green",
        "respondida": "blue",
        "em replica": "gold",
        "nao resolvido": "red",
        "nao respondida": "orange"
    }
)

fig_estado.update_layout(
    xaxis_tickangle=-45,
    height=500
)

st.plotly_chart(fig_estado, use_container_width=True)

# mapa do brasil
st.subheader("Mapa de Reclamações")

nivel_mapa = st.radio("Visualização do mapa", ["Estado", "Município"])

url_geo = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson = requests.get(url_geo).json()

if nivel_mapa == "Estado":
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

else:
    url_geo_cidades = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"
    geojson_cidades = requests.get(url_geo_cidades).json()

    for feature in geojson_cidades["features"]:
        feature["properties"]["name"] = normalizar(feature["properties"]["name"])

    mapa_cidades = df_filtrado.groupby("CIDADE").size().reset_index(name="quantidade")

    fig = px.choropleth(
        mapa_cidades,
        geojson=geojson_cidades,
        locations="CIDADE",
        featureidkey="properties.name",
        color="quantidade",
        color_continuous_scale="Blues"
    )

    fig.update_geos(fitbounds="locations", visible=False)

    st.plotly_chart(fig, use_container_width=True)

# pareto
st.subheader("Estados com Mais Reclamações")

pareto = df_filtrado.groupby("ESTADO").size().reset_index(name="quantidade")
pareto = pareto.sort_values(by="quantidade", ascending=False)

fig_pareto = px.bar(
    pareto,
    x="ESTADO",
    y="quantidade",
    color="quantidade",
    color_continuous_scale="Viridis"
)

st.plotly_chart(fig_pareto, use_container_width=True)

# status
st.subheader("Distribuição de Status")

status_count = df_filtrado["STATUS"].value_counts().reset_index()
status_count.columns = ["STATUS","quantidade"]

fig_status = px.pie(
    status_count,
    names="STATUS",
    values="quantidade",
    color="STATUS",
    color_discrete_map={
        "resolvido": "green",
        "respondida": "blue",
        "em replica": "gold",
        "nao resolvido": "red",
        "nao respondida": "orange"
    }
)

st.plotly_chart(fig_status, use_container_width=True)

# boxplot
st.subheader("Tamanho das Reclamações por Status")

fig_box = px.box(
    df_filtrado,
    x="STATUS",
    y="tamanho_texto",
    color="STATUS",
    color_discrete_map={
        "resolvido": "green",
        "respondida": "blue",
        "em replica": "gold",
        "nao resolvido": "red",
        "nao respondida": "orange"
    }
)

st.plotly_chart(fig_box, use_container_width=True)

# wordcloud
st.subheader("Palavras mais Frequentes")

stop_words = set(stopwords.words("portuguese"))

min_palavra = st.slider("Tamanho mínimo da palavra", 1, 10, 4)

palavras = []

for texto_individual in df_filtrado["DESCRICAO"].astype(str):
    for palavra in texto_individual.split():
        palavra = palavra.lower()
        if palavra not in stop_words and len(palavra) >= min_palavra:
            palavras.append(palavra)

texto_filtrado = " ".join(palavras)

wordcloud = WordCloud(
    width=800,
    height=400,
    background_color="white"
).generate(texto_filtrado)

fig, ax = plt.subplots()
ax.imshow(wordcloud)
ax.axis("off")

st.pyplot(fig)

# streamlit run app.py