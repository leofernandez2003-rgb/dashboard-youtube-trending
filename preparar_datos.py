# preparar_datos.py
# ============================================================
#  Limpieza y segmentacion del dataset de YouTube (Certamen 2)
#  -> genera data/youtube_limpio_muestra.csv para el dashboard
#
#  Se ejecuta UNA vez en el computador (no en Streamlit Cloud):
#     python preparar_datos.py
#
#  Necesita en la carpeta raw/ los archivos originales de Kaggle:
#     MX_youtube_trending_data.csv, US_youtube_trending_data.csv,
#     MX_category_id.json, US_category_id.json
# ============================================================
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

ruta = "raw/"

# ── 1. Cargar los archivos de cada pais ──────────────────────
mx = pd.read_csv(ruta + "MX_youtube_trending_data.csv")
us = pd.read_csv(ruta + "US_youtube_trending_data.csv")
mx["country"] = "MX"
us["country"] = "US"
df = pd.concat([mx, us], ignore_index=True)
print(f"Filas originales: {len(df)}")

# ── 2. Tipos de datos ────────────────────────────────────────
df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce")
df["trending_date"] = pd.to_datetime(df["trending_date"], errors="coerce")

# ── 3. Nombre de la categoria (desde los JSON) ───────────────
nombres_categoria = {}
for archivo in ["MX_category_id.json", "US_category_id.json"]:
    with open(ruta + archivo) as f:
        datos_json = json.load(f)
    for item in datos_json["items"]:
        nombres_categoria[int(item["id"])] = item["snippet"]["title"]
df["categoria"] = df["categoryId"].astype(int).map(nombres_categoria).fillna("Sin dato")

# ── 4. Decisiones de limpieza (iguales al Certamen 2) ────────
# Decision 1: eliminar duplicados (mismo video, dia y pais)
df = df.drop_duplicates(subset=["video_id", "trending_date", "country"], keep="last")
# Decision 2: eliminar videos con 0 vistas
df = df[df["view_count"] > 0]
# Decision 3: eliminar videos publicados despues de su dia en tendencias
df = df[df["publishedAt"].dt.tz_localize(None).dt.normalize() <= df["trending_date"].dt.tz_localize(None)]
print(f"Filas despues de limpiar: {len(df)}")

# ── 5. Variables nuevas ──────────────────────────────────────
df["likes_pct"] = df["likes"] / df["view_count"] * 100
df["comentarios_pct"] = df["comment_count"] / df["view_count"] * 100
df["trending_date"] = df["trending_date"].dt.tz_localize(None)
df["publishedAt"] = df["publishedAt"].dt.tz_localize(None)
df["anio"] = df["trending_date"].dt.year
df["anio_mes"] = df["trending_date"].dt.strftime("%Y-%m")
df["dia_semana"] = df["trending_date"].dt.day_of_week
df["dias_a_tendencia"] = (df["trending_date"] - df["publishedAt"].dt.normalize()).dt.days

# ── 6. Segmentacion K-Means (codigo del Certamen 2) ──────────
variables_cluster = ["view_count", "likes_pct", "comentarios_pct"]

# Se segmenta hasta el percentil 99 de cada variable
datos_cluster = df.copy()
for col in variables_cluster:
    p99 = df[col].quantile(0.99)
    datos_cluster = datos_cluster[datos_cluster[col] <= p99]

escalador = StandardScaler()
datos_escalados = escalador.fit_transform(datos_cluster[variables_cluster])

# Metodo del codo: se guarda la inercia de k = 1 a 8 para graficarla en la app
inercias = []
for k in range(1, 9):
    modelo = KMeans(n_clusters=k, random_state=42, n_init=5)
    modelo.fit(datos_escalados)
    inercias.append(modelo.inertia_)
pd.DataFrame({"k": range(1, 9), "inercia": inercias}).to_csv("data/codo.csv", index=False)

# k = 4 elegido por el metodo del codo
modelo_final = KMeans(n_clusters=4, random_state=42, n_init=10)
modelo_final.fit(datos_escalados)
datos_cluster["cluster"] = modelo_final.labels_

# Nombre de cada segmento segun su perfil (asi no depende del numero que da K-Means):
# el de mas vistas = "Alcance masivo"; los otros 3 se ordenan por % de likes
perfil = datos_cluster.groupby("cluster")[variables_cluster].mean()
masivo = perfil["view_count"].idxmax()
resto = perfil.drop(masivo).sort_values("likes_pct")
nombres_cluster = {
    masivo: "Alcance masivo",
    resto.index[0]: "Interaccion baja",
    resto.index[1]: "Interaccion media",
    resto.index[2]: "Interaccion muy alta",
}
datos_cluster["segmento"] = datos_cluster["cluster"].map(nombres_cluster)
df["segmento"] = datos_cluster["segmento"]
df["segmento"] = df["segmento"].fillna("Fuera de segmentacion (> P99)")
print(df["segmento"].value_counts())

# ── 7. Muestra para el dashboard (el archivo completo supera 25 MB) ──
columnas_app = ["video_id", "title", "channelTitle", "categoria", "country",
                "publishedAt", "trending_date", "anio", "anio_mes", "dia_semana",
                "dias_a_tendencia", "view_count", "likes", "comment_count",
                "likes_pct", "comentarios_pct", "segmento"]
muestra = df[columnas_app].sample(100000, random_state=42)
muestra["likes_pct"] = muestra["likes_pct"].round(3)
muestra["comentarios_pct"] = muestra["comentarios_pct"].round(4)
muestra.to_csv("data/youtube_limpio_muestra.csv", index=False)
print(f"Muestra guardada: {len(muestra)} filas")
