# app.py
# ============================================================
#  DASHBOARD — YouTube Trending Mexico + Estados Unidos (2020-2024)
#  Visualizacion de la Informacion (UDD) · Examen final
#  Ejecutar:  streamlit run app.py
#
#  Idea clave de Streamlit: el script se ejecuta de ARRIBA A ABAJO
#  cada vez que el usuario mueve un filtro. Por eso los datos se
#  cargan con @st.cache_data (se leen una sola vez).
# ============================================================
import json
import pandas as pd
import plotly.express as px
import streamlit as st

# ── 1. Configuracion de la pagina ────────────────────────────
st.set_page_config(page_title="YouTube Trending · MX & US", page_icon="▶️", layout="wide")

# Colores estilo YouTube (se usan en todos los graficos)
ROJO = "#FF0000"
FONDO = "#0F0F0F"
GRIS = "#272727"
TEXTO = "#F1F1F1"
COLOR_PAIS = {"MX": "#FF0000", "US": "#3EA6FF"}
COLOR_SEGMENTO = {
    "Interaccion baja": "#AAAAAA",
    "Interaccion media": "#3EA6FF",
    "Interaccion muy alta": "#FF0000",
    "Alcance masivo": "#FFB000",
    "Fuera de segmentacion (> P99)": "#5A5A5A",
}
ORDEN_SEGMENTOS = list(COLOR_SEGMENTO.keys())

# Nombre de cada variable con su unidad (para ejes y tooltips)
ETIQUETAS = {
    "view_count": "Vistas (cantidad)",
    "likes": "Likes (cantidad)",
    "comment_count": "Comentarios (cantidad)",
    "likes_pct": "Likes sobre vistas (%)",
    "comentarios_pct": "Comentarios sobre vistas (%)",
    "dias_a_tendencia": "Dias hasta tendencia (dias)",
    "anio_mes": "Mes (año-mes)",
    "country": "Pais",
    "categoria": "Categoria",
    "segmento": "Segmento",
    "channelTitle": "Canal",
    "title": "Titulo",
    "registros": "Registros (cantidad)",
}

# CSS: tipografia Roboto, tarjetas y cabecera como YouTube
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stMetric {{ font-family: 'Roboto', sans-serif; }}
.block-container {{ padding-top: 3.8rem; }}  /* deja espacio bajo la barra superior de Streamlit */
.yt-header {{ display:flex; align-items:center; gap:14px; margin-bottom:4px; }}
.yt-logo {{ background:{ROJO}; width:54px; height:38px; border-radius:10px;
            display:flex; align-items:center; justify-content:center; }}
.yt-logo div {{ width:0; height:0; border-top:9px solid transparent;
                border-bottom:9px solid transparent; border-left:15px solid white; margin-left:4px; }}
.yt-title {{ font-size:30px; font-weight:700; color:{TEXTO}; letter-spacing:-0.5px; }}
.yt-title span {{ color:#AAAAAA; font-weight:400; font-size:20px; }}
.yt-pregunta {{ background:{GRIS}; border-left:4px solid {ROJO}; padding:10px 16px;
                border-radius:8px; color:{TEXTO}; margin:8px 0 16px 0; }}
div[data-testid="stMetric"] {{ background:{GRIS}; border-radius:12px; padding:14px 18px; }}
div[data-testid="stMetricLabel"] p {{ color:#AAAAAA; white-space:normal; }}
div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] div {{ overflow:visible; white-space:normal; }}
div[data-testid="stMetricValue"] div {{ font-size:1.35rem; overflow:visible; white-space:normal; }}
div[data-testid="stMetricDelta"] div {{ white-space:normal; overflow:visible; }}
.stTabs [data-baseweb="tab"] {{ font-weight:500; }}
.stTabs [aria-selected="true"] {{ color:{ROJO} !important; }}
</style>
""", unsafe_allow_html=True)


# ── 2. Carga de datos (cacheada) ─────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/youtube_limpio_muestra.csv", parse_dates=["publishedAt", "trending_date"])
    return df


@st.cache_data
def cargar_geojson():
    with open("data/paises.geojson", encoding="utf-8") as archivo:
        return json.load(archivo)


df = cargar_datos()
codo = pd.read_csv("data/codo.csv")
geo = cargar_geojson()


# Mismo estilo oscuro para todas las figuras
def estilo(fig):
    fig.update_layout(template="plotly_dark", paper_bgcolor=FONDO, plot_bgcolor=FONDO,
                      font=dict(family="Roboto", color=TEXTO), title_font_size=17,
                      margin=dict(l=10, r=10, t=55, b=10), legend_title_text="")
    return fig


# ── 3. Cabecera y pregunta del dashboard ─────────────────────
st.markdown("""
<div class="yt-header"><div class="yt-logo"><div></div></div>
<div class="yt-title">Trending <span>· Mexico y Estados Unidos 2020-2024</span></div></div>
""", unsafe_allow_html=True)
st.markdown("""<div class="yt-pregunta"><b>Pregunta:</b> ¿Que tipos de videos en tendencia logran mas
interaccion (likes y comentarios por vista) y como cambia eso segun el pais, la categoria y el tiempo?<br>
<small>Dirigido a creadores de contenido y equipos de marketing digital.</small></div>""", unsafe_allow_html=True)

# ── 4. Filtros globales (panel lateral) ──────────────────────
st.sidebar.markdown(f"<h2 style='color:{ROJO}'>Filtros</h2>", unsafe_allow_html=True)

paises = st.sidebar.multiselect("Pais", ["MX", "US"], default=["MX", "US"])

anio_min, anio_max = int(df["anio"].min()), int(df["anio"].max())
anios = st.sidebar.slider("Años en tendencia", anio_min, anio_max, (anio_min, anio_max))

todas_categorias = sorted(df["categoria"].unique())
categorias = st.sidebar.multiselect("Categoria", todas_categorias, default=todas_categorias)

segmentos = st.sidebar.multiselect("Segmento", ORDEN_SEGMENTOS, default=ORDEN_SEGMENTOS)

st.sidebar.caption("Muestra aleatoria de 100.000 registros (random_state = 42) "
                   "del dataset limpio del Certamen 2 (529.061 registros).")

# Mascara: se combinan todos los filtros
mascara = (
    df["country"].isin(paises)
    & df["anio"].between(anios[0], anios[1])
    & df["categoria"].isin(categorias)
    & df["segmento"].isin(segmentos)
)
dff = df[mascara]

# Si el filtro deja la tabla vacia, se avisa y se detiene la app
if dff.empty:
    st.warning("No hay videos con esa combinacion de filtros. Cambia la seleccion del panel lateral.")
    st.stop()

# ── 5. KPIs ──────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Registros", f"{len(dff):,}".replace(",", "."),
          delta=f"{len(dff) / len(df) * 100:.0f}% del total", delta_color="off")
k2.metric("Vistas (mediana)", f"{dff['view_count'].median():,.0f}".replace(",", "."),
          delta=f"{(dff['view_count'].median() / df['view_count'].median() - 1) * 100:+.1f}%")
k3.metric("% likes (mediana)", f"{dff['likes_pct'].median():.2f}%",
          delta=f"{dff['likes_pct'].median() - df['likes_pct'].median():+.2f} pp")
k4.metric("% coment. (mediana)", f"{dff['comentarios_pct'].median():.3f}%",
          delta=f"{dff['comentarios_pct'].median() - df['comentarios_pct'].median():+.3f} pp")
k5.metric("Canales", f"{dff['channelTitle'].nunique():,}".replace(",", "."))

# ── 6. Pestañas ──────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Distribucion", "Tiempo", "Relaciones", "Segmentos", "Jerarquia y perfiles", "Mapa"])

# ---------- 6.1 Univariado ----------
with tab1:
    c1, c2 = st.columns([1, 3])
    # Control local: solo afecta a este grafico
    variable = c1.selectbox("Variable a ver", ["likes_pct", "comentarios_pct", "view_count", "dias_a_tendencia"],
                            format_func=lambda x: ETIQUETAS[x])
    c1.caption("Se grafica hasta el percentil 99 para ver la forma de la distribucion.")
    p99 = dff[variable].quantile(0.99)
    # barmode="group": una barra por pais lado a lado. Con "overlay" el rojo y el azul se
    # superponian y la mezcla se veia como un segundo tono de rojo.
    fig = px.histogram(dff[dff[variable] <= p99], x=variable, color="country", nbins=40,
                       barmode="group", color_discrete_map=COLOR_PAIS,
                       category_orders={"country": ["MX", "US"]},
                       labels=ETIQUETAS, title=f"Distribucion de {ETIQUETAS[variable].lower()} por pais")
    fig.update_yaxes(title="Frecuencia (n° de registros)")
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Rango: %{x}<br>Registros: %{y:,}<extra></extra>")
    # Linea del color del fondo entre barras para separarlas
    fig.update_traces(marker_line_width=1, marker_line_color=FONDO)
    fig.update_layout(bargap=0.08)
    c2.plotly_chart(estilo(fig), width="stretch")

    conteo_cat = dff["categoria"].value_counts().reset_index()
    conteo_cat.columns = ["categoria", "registros"]
    fig = px.bar(conteo_cat.sort_values("registros"), x="registros", y="categoria", orientation="h",
                 color_discrete_sequence=[ROJO], labels=ETIQUETAS, title="Videos en tendencia por categoria",
                 hover_data={"registros": ":,"})
    st.plotly_chart(estilo(fig), width="stretch")

# ---------- 6.2 Temporal ----------
with tab2:
    metrica = st.radio("Metrica mensual", ["likes_pct", "view_count", "comentarios_pct"],
                       format_func=lambda x: "Mediana de " + ETIQUETAS[x].lower(), horizontal=True)
    mensual = dff.groupby(["anio_mes", "country"])[metrica].median().reset_index()
    fig = px.line(mensual, x="anio_mes", y=metrica, color="country", markers=True,
                  color_discrete_map=COLOR_PAIS, labels=ETIQUETAS,
                  title=f"Mediana mensual de {ETIQUETAS[metrica].lower()} por pais",
                  hover_data={metrica: ":.3f"})
    st.plotly_chart(estilo(fig), width="stretch")
    st.info("Hallazgo: la interaccion relativa cae con el tiempo; el % de likes baja de ~6,5 % en 2020 a ~4 % en 2024.")

# ---------- 6.3 Relaciones ----------
with tab3:
    c1, c2 = st.columns([1, 3])
    color_por = c1.selectbox("Colorear por", ["country", "segmento", "categoria"], format_func=lambda x: ETIQUETAS[x])
    c1.caption("Muestra de 5.000 puntos, hasta el percentil 99 de vistas.")
    muestra = dff[dff["view_count"] <= dff["view_count"].quantile(0.99)]
    muestra = muestra.sample(min(5000, len(muestra)), random_state=42)
    mapa_color = COLOR_PAIS if color_por == "country" else COLOR_SEGMENTO if color_por == "segmento" else None
    fig = px.scatter(muestra, x="view_count", y="likes_pct", color=color_por, opacity=0.6,
                     color_discrete_map=mapa_color, labels=ETIQUETAS,
                     hover_name="title",
                     hover_data={"channelTitle": True, "categoria": True, "view_count": ":,",
                                 "likes_pct": ":.2f", "country": True},
                     title="Vistas vs % de likes: mas vistas no significa mas interaccion")
    c2.plotly_chart(estilo(fig), width="stretch")
    c2.caption(f"Correlacion de Spearman vistas – % likes en la seleccion: "
               f"{dff['view_count'].rank().corr(dff['likes_pct'].rank()):.2f}")
    # Spearman = Pearson sobre los rankings (.rank()); asi no se necesita scipy

# ---------- 6.4 Segmentacion ----------
with tab4:
    seg = dff[dff["segmento"] != "Fuera de segmentacion (> P99)"]
    if seg.empty:
        st.warning("La seleccion no tiene videos segmentados.")
    else:
        c1, c2 = st.columns(2)
        fig = px.line(codo, x="k", y="inercia", markers=True, color_discrete_sequence=[ROJO],
                      labels={"k": "Numero de segmentos (k)", "inercia": "Inercia (suma de distancias²)"},
                      hover_data={"inercia": ":,.0f"}, title="Metodo del codo: se elige k = 4")
        c1.plotly_chart(estilo(fig), width="stretch")

        # Radar: promedios por segmento escalados de 0 a 1
        variables = ["view_count", "likes_pct", "comentarios_pct"]
        perfil = seg.groupby("segmento")[variables].mean()
        radar = (perfil - perfil.min()) / (perfil.max() - perfil.min())
        radar = radar.reset_index().melt(id_vars="segmento", var_name="variable", value_name="valor_escalado")
        radar["variable"] = radar["variable"].map(ETIQUETAS)
        fig = px.line_polar(radar, r="valor_escalado", theta="variable", color="segmento", line_close=True,
                            color_discrete_map=COLOR_SEGMENTO, hover_data={"valor_escalado": ":.2f"},
                            title="Radar de segmentos (escala 0-1)")
        fig.update_traces(fill="toself", opacity=0.6)
        # Leyenda abajo para que el radar use todo el ancho
        fig.update_layout(legend=dict(orientation="h", y=-0.15), height=450)
        c2.plotly_chart(estilo(fig), width="stretch")

        muestra_seg = seg.sample(min(5000, len(seg)), random_state=42)
        fig = px.scatter(muestra_seg, x="likes_pct", y="comentarios_pct", color="segmento", opacity=0.6,
                         color_discrete_map=COLOR_SEGMENTO, labels=ETIQUETAS, hover_name="title",
                         hover_data={"channelTitle": True, "view_count": ":,", "likes_pct": ":.2f",
                                     "comentarios_pct": ":.3f"},
                         title="Segmentos segun % de likes y % de comentarios")
        st.plotly_chart(estilo(fig), width="stretch")

        # Tabla de perfiles
        tabla = seg.groupby("segmento").agg(n=("video_id", "count"), vistas_promedio=("view_count", "mean"),
                                            likes_pct_promedio=("likes_pct", "mean"),
                                            comentarios_pct_promedio=("comentarios_pct", "mean"))
        tabla["porcentaje"] = tabla["n"] / tabla["n"].sum() * 100
        tabla["categoria_dominante"] = seg.groupby("segmento")["categoria"].agg(lambda x: x.value_counts().index[0])
        tabla["descripcion"] = tabla.index.map({
            "Interaccion baja": "Vistas normales, pocos likes y comentarios por vista",
            "Interaccion media": "Vistas normales, buen % de likes",
            "Interaccion muy alta": "Vistas normales, el publico da like y comenta mucho",
            "Alcance masivo": "Muchisimas vistas, interaccion moderada"})
        st.subheader("Tabla de perfiles")
        st.dataframe(tabla.sort_values("n", ascending=False).round(2), width="stretch",
                     column_config={"n": st.column_config.NumberColumn("Videos (n)", format="%d"),
                                    "porcentaje": st.column_config.NumberColumn("% del total", format="%.1f %%"),
                                    "vistas_promedio": st.column_config.NumberColumn("Vistas promedio", format="%.0f"),
                                    "likes_pct_promedio": st.column_config.NumberColumn("% likes promedio", format="%.2f"),
                                    "comentarios_pct_promedio": st.column_config.NumberColumn("% comentarios promedio", format="%.3f"),
                                    "categoria_dominante": "Categoria dominante", "descripcion": "Descripcion"})
        tabla = tabla[["n", "porcentaje", "vistas_promedio", "likes_pct_promedio", "comentarios_pct_promedio",
                       "categoria_dominante", "descripcion"]]
        mayor = tabla["n"].idxmax()
        st.info(f"Interpretacion: el segmento mas grande es «{mayor}» ({tabla.loc[mayor, 'porcentaje']:.0f} % de los "
                "videos segmentados). Estar en tendencia no garantiza interaccion: la mayoria recibe pocos likes y "
                "comentarios por vista. «Alcance masivo» suma vistas pero no interaccion, y «Interaccion muy alta» "
                "es el grupo mas valioso para un creador.")

        # Selector para ver el detalle de un segmento
        elegido = st.selectbox("Ver detalle del segmento", tabla.sort_values("n", ascending=False).index)
        detalle = seg[seg["segmento"] == elegido]
        d1, d2, d3 = st.columns(3)
        d1.metric("Videos del segmento", f"{len(detalle):,}".replace(",", "."))
        d2.metric("Mediana de vistas", f"{detalle['view_count'].median():,.0f}".replace(",", "."))
        d3.metric("Mediana % likes", f"{detalle['likes_pct'].median():.2f}%")
        top_cat = detalle["categoria"].value_counts().head(8).reset_index()
        top_cat.columns = ["categoria", "registros"]
        fig = px.bar(top_cat, x="categoria", y="registros", color_discrete_sequence=[COLOR_SEGMENTO[elegido]],
                     labels=ETIQUETAS, hover_data={"registros": ":,"},
                     title=f"Categorias principales en «{elegido}»")
        st.plotly_chart(estilo(fig), width="stretch")

# ---------- 6.5 Jerarquico y multidimensional ----------
with tab5:
    jerarquia = dff.groupby(["country", "categoria", "segmento"]).agg(
        registros=("video_id", "count"), likes_pct=("likes_pct", "median")).reset_index()
    fig = px.sunburst(jerarquia, path=["country", "categoria", "segmento"], values="registros",
                      # Misma escala que las coordenadas paralelas: azul = poca interaccion, rojo = mucha
                      color="likes_pct", color_continuous_scale=["#3EA6FF", "#FFFFFF", ROJO],
                      range_color=[jerarquia["likes_pct"].quantile(0.10), jerarquia["likes_pct"].quantile(0.90)],
                      maxdepth=2,
                      hover_data={"likes_pct": ":.2f"}, labels={"likes_pct": "Mediana % likes"},
                      title="Pais → categoria → segmento (tamaño = registros, color = mediana % likes)")
    fig.update_traces(marker_line_color=FONDO, marker_line_width=1.5, insidetextorientation="radial",
                      insidetextfont=dict(color="#000000"),  # texto negro sobre azul, blanco y rojo
                      hovertemplate="<b>%{label}</b><br>Ruta: %{id}<br>Registros: %{value:,}"
                                    "<br>Mediana % likes: %{color:.2f}<extra></extra>")
    fig.update_layout(height=620)
    st.plotly_chart(estilo(fig), width="stretch")
    st.caption("Rojo = mayor % de likes, azul = menor (misma escala que las coordenadas paralelas). Haz clic en una categoria para ver sus segmentos; "
               "clic en el centro para volver.")

    muestra_par = dff.sample(min(3000, len(dff)), random_state=42)
    muestra_par = muestra_par[muestra_par["view_count"] <= dff["view_count"].quantile(0.99)]
    fig = px.parallel_coordinates(muestra_par, dimensions=["view_count", "likes_pct", "comentarios_pct",
                                                           "dias_a_tendencia"],
                                  color="likes_pct", color_continuous_scale=["#3EA6FF", "#FFFFFF", "#FF0000"],
                                  labels=ETIQUETAS, title="Coordenadas paralelas (color = % de likes)")
    # Margen superior extra para que el titulo no tape los nombres de los ejes
    fig = estilo(fig).update_layout(margin=dict(l=70, r=30, t=120, b=30), height=520)
    st.plotly_chart(fig, width="stretch")

# ---------- 6.6 Mapa (coropleta por pais) ----------
with tab6:
    c1, c2 = st.columns([1, 3])
    metrica_mapa = c1.radio("Color del mapa", ["likes_pct", "comentarios_pct", "view_count"],
                            format_func=lambda x: "Mediana de " + ETIQUETAS[x].lower())
    por_pais = dff.groupby("country").agg(valor=(metrica_mapa, "median"), registros=("video_id", "count"),
                                          canales=("channelTitle", "nunique")).reset_index()
    por_pais["nombre"] = por_pais["country"].map({"MX": "Mexico", "US": "Estados Unidos"})
    fig = px.choropleth_map(por_pais, geojson=geo, locations="country", featureidkey="properties.iso2",
                            color="valor", color_continuous_scale=["#3EA6FF", "#FF0000"],
                            map_style="carto-darkmatter", zoom=2.1, center={"lat": 33, "lon": -100},
                            opacity=0.7, hover_name="nombre",
                            hover_data={"country": False, "valor": ":.3f", "registros": ":,", "canales": ":,"},
                            labels={"valor": "Mediana " + ETIQUETAS[metrica_mapa], "registros": "Registros",
                                    "canales": "Canales"},
                            title="Interaccion por pais")
    # Barra de color horizontal abajo, para que el mapa use todo el ancho
    fig.update_layout(height=520, coloraxis_colorbar=dict(orientation="h", y=-0.12, title_side="top"))
    c2.plotly_chart(estilo(fig), width="stretch")
    c1.caption("Mexico y Estados Unidos tienen casi el mismo numero de registros, pero distinta mezcla "
               "de categorias. El color muestra la mediana de la metrica elegida.")

# ── 7. Hallazgos principales ─────────────────────────────────
st.markdown("### Hallazgos principales")
h1, h2, h3 = st.columns(3)
h1.markdown("**1. Mas vistas ≠ mas interaccion.** La correlacion entre vistas y % de likes es casi 0.")
h2.markdown("**2. La interaccion cae con el tiempo.** El % de likes baja de ~6,5 % (2020) a ~4 % (2024).")
h3.markdown("**3. MX y US se parecen en tamaño, no en contenido.** Sports concentra su audiencia en "
            "interaccion baja.")

# ── 8. Tabla de datos filtrados ──────────────────────────────
with st.expander("Ver datos filtrados"):
    st.dataframe(dff, width="stretch")
