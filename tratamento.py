import pandas as pd
import numpy as np
import unicodedata
import re

def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')

pd.set_option("display.max_columns", None)

df = pd.read_csv("RECLAMEAQUI_HAPVIDA.csv")

df.head()
df.info()
df.shape
df.describe()
df.isnull().sum()


#tratamento de nulos
df = df.dropna(subset=["DESCRICAO", "TEMA"])
df["LOCAL"] = df["LOCAL"].fillna("nao informado")

# isso aq resolve o problema do local nulo
df = df[df["LOCAL"].str.match(r"^[A-Za-zÀ-ÿ\s]+ - [A-Z]{2}$", na=False)]


#padronização de texto
df["TEMA"] = df["TEMA"].str.lower().str.strip()

df["STATUS"] = df["STATUS"].str.lower().str.strip()
df["STATUS"] = df["STATUS"].apply(remover_acentos)

df["LOCAL"] = df["LOCAL"].str.lower().str.strip()

df["DESCRICAO"] = df["DESCRICAO"].astype(str)
df["DESCRICAO"] = df["DESCRICAO"].str.lower().str.strip()

#remove caracteres estranhos
df["DESCRICAO"] = df["DESCRICAO"].apply(
    lambda x: re.sub(r"[^a-zà-ÿ\s]", "", x)
)
#remove muitos espaços
df["DESCRICAO"] = df["DESCRICAO"].apply(
    lambda x: re.sub(r"[^a-zà-ÿ\s]", "", x)
)

df["CATEGORIA"] = df["CATEGORIA"].str.lower().str.strip()


#conversão de tipos
df["ANO"] = df["ANO"].astype(int)
df["MES"] = df["MES"].astype(int)
df["DIA"] = df["DIA"].astype(int)
df["SEMANA_DO_ANO"] = df["SEMANA_DO_ANO"].astype(int)
df["DIA_DA_SEMANA"] = df["DIA_DA_SEMANA"].astype(int)

df["TEMPO"] = pd.to_datetime(df["TEMPO"], errors="coerce")


#separa cidade e estado
df[["CIDADE", "ESTADO"]] = df["LOCAL"].str.split(" - ", expand=True)

df["CIDADE"] = df["CIDADE"].str.upper().str.strip()
df["ESTADO"] = df["ESTADO"].str.upper().str.strip()


#remove as duplicatas
df = df.drop_duplicates()


df.to_csv("reclamacoes_tratado.csv", index=False)

print("Dataset tratado salvo com sucesso!")