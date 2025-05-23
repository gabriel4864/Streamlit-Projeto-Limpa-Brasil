# pip install streamlit streamlit-option-menu plotly pandas openpyxl folium streamlit-folium

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from streamlit_folium import folium_static
import folium
from folium.plugins import MarkerCluster

# Configuração da página
st.set_page_config(page_title="Dashboard de Coleta de Lixo", page_icon="🌎", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("dados_tratados8.0.xlsx")
    df.columns = df.columns.str.strip().str.replace(":", "", regex=False)
    return df

df = carregar_dados()

filtros = {
    "Organizacao": "Representa alguma Organização/ONG/Escola/Empresa etc? Se sim, descreva o nome",
    "Tipo_participante": "Participante como",
    "Campanha": "Nome",
    "Participantes": "Número aproximado de participantes",
    "Crianca": "Número aproximado de crianças",
    "Jovem": "Número aproximado de jovens",
    "Adulto": "Número aproximado de adultos",
    "Idoso": "Número aproximado de idosos",
    "Coletados": "Quantidade total de itens coletados",
    "Zoneamento": "Zoneamento",
    "Regiao": "Cidade"
}

def aplicar_filtros_avancados(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    with st.sidebar.expander("🔍 Filtros Avançados", expanded=True):
        df_filtrado = df.copy()

        if st.button("🔄 Resetar Filtros"):
            st.experimental_rerun()

        coluna_org = filtros.get("Organizacao")
        if coluna_org and coluna_org in df.columns:
            st.markdown("<p style='font-size:18px; font-weight:bold;'>Buscar por Organização</p>", unsafe_allow_html=True)
            sugestoes = sorted(df[coluna_org].dropna().unique())
            selecionado = st.selectbox("🔎 Digite para buscar:", options=sugestoes, index=None, placeholder="Digite parte do nome da organização...", key="org_autocomplete")
            if selecionado:
                df_filtrado = df_filtrado[df_filtrado[coluna_org] == selecionado]

        st.markdown("---")
        st.subheader("Outros filtros:")

        for chave, coluna in filtros.items():
            if coluna not in df.columns or coluna == coluna_org:
                continue

            usar_filtro = st.checkbox(f"Filtrar por: {coluna}", key=f"{chave}_check")
            if usar_filtro:
                if pd.api.types.is_numeric_dtype(df[coluna]):
                    minimo = int(df[coluna].min(skipna=True))
                    maximo = int(df[coluna].max(skipna=True))
                    col_min, col_max = st.columns(2)
                    with col_min:
                        min_val = st.number_input(f"Mínimo de {coluna}", value=minimo, key=f"{coluna}_min")
                    with col_max:
                        max_val = st.number_input(f"Máximo de {coluna}", value=maximo, key=f"{coluna}_max")
                    df_filtrado = df_filtrado[df_filtrado[coluna].between(min_val, max_val)]
                else:
                    opcoes = sorted(df[coluna].dropna().unique())
                    selecao = st.multiselect(coluna, opcoes, default=opcoes, key=chave)
                    if selecao:
                        df_filtrado = df_filtrado[df_filtrado[coluna].isin(selecao)]

    return df_filtrado

df_filtrado = aplicar_filtros_avancados(df, filtros)

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# Página Home
def pagina_home():
    st.title("📊 Visão Geral da Coleta de Lixo")

    total = df_filtrado["Quantidade total de itens coletados"].sum()
    media = df_filtrado["Quantidade total de itens coletados"].mean()
    campanhas = df_filtrado["Nome"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Itens Coletados", int(total))
    col2.metric("Média por Entrada", f"{media:.1f}")
    col3.metric("Campanhas Diferentes", campanhas)

    st.markdown("---")
    st.title("📊 Visão Geral dos Participantes")

    col6, col7, col8, col9, col10 = st.columns(5)
    col6.metric("Participantes", int(df_filtrado["Número aproximado de participantes"].sum()))
    col7.metric("Crianças", int(df_filtrado["Número aproximado de crianças"].sum()))
    col8.metric("Jovens", int(df_filtrado["Número aproximado de jovens"].sum()))
    col9.metric("Adultos", int(df_filtrado["Número aproximado de adultos"].sum()))
    col10.metric("Idosos", int(df_filtrado["Número aproximado de idosos"].sum()))

# Página Gráficos
def pagina_graficos():
    st.title("📈 Gráficos Interativos")

    aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
        "Coleta por Cidade e Zoneamento",
        "Top 15 Campanhas",
        "Distribuição por Faixa Etária",
        "Proporção por Faixa Etária",
        "Proporção por Cidade e Zoneamento",
        "Distribuição Etária por Cidade"
    ])

    with aba1:
        st.subheader("Itens Coletados por Cidade")
        graf_cidade = px.bar(
            df_filtrado.groupby("Cidade")["Quantidade total de itens coletados"].sum().reset_index(),
            x="Cidade", y="Quantidade total de itens coletados", color="Cidade"
        )
        st.plotly_chart(graf_cidade, use_container_width=True)

        st.subheader("Itens Coletados por Zoneamento")
        graf_zoneamento = px.bar(
            df_filtrado.groupby("Zoneamento")["Quantidade total de itens coletados"].sum().reset_index(),
            x="Zoneamento", y="Quantidade total de itens coletados", color="Zoneamento"
        )
        st.plotly_chart(graf_zoneamento, use_container_width=True)

    with aba2:
        st.subheader("Top 15 Campanhas")
        campanhas = df_filtrado["Nome"].value_counts().nlargest(15).reset_index()
        campanhas.columns = ["Campanha", "Quantidade"]
        graf_campanhas = px.bar(campanhas, x="Campanha", y="Quantidade", color="Campanha")
        st.plotly_chart(graf_campanhas, use_container_width=True)

    with aba3:
        st.subheader("Distribuição por Faixa Etária")
        faixa_df = pd.DataFrame({
            "Faixa Etária": ["Crianças", "Jovens", "Adultos", "Idosos"],
            "Quantidade": [
                df_filtrado["Número aproximado de crianças"].sum(),
                df_filtrado["Número aproximado de jovens"].sum(),
                df_filtrado["Número aproximado de adultos"].sum(),
                df_filtrado["Número aproximado de idosos"].sum()
            ]
        })

        graf_faixa_etaria = px.bar(faixa_df, x="Faixa Etária", y="Quantidade", color="Faixa Etária")
        st.plotly_chart(graf_faixa_etaria, use_container_width=True)

    with aba4:
        st.subheader("Proporção por Faixa Etária")
        graf_pizza_faixa = px.pie(faixa_df, names="Faixa Etária", values="Quantidade", hole=0.4)
        st.plotly_chart(graf_pizza_faixa, use_container_width=True)

    with aba5:
        st.subheader("Proporção por Zoneamento")
        zona_pizza = df_filtrado.groupby("Zoneamento")["Quantidade total de itens coletados"].sum().reset_index()
        graf_pizza_zona = px.pie(zona_pizza, names="Zoneamento", values="Quantidade total de itens coletados", hole=0.4)
        st.plotly_chart(graf_pizza_zona, use_container_width=True)

        st.subheader("Proporção por Cidade")
        regiao_pizza = df_filtrado.groupby("Cidade")["Quantidade total de itens coletados"].sum().reset_index()
        graf_pizza_regiao = px.pie(regiao_pizza, names="Cidade", values="Quantidade total de itens coletados", hole=0.4)
        st.plotly_chart(graf_pizza_regiao, use_container_width=True)

    with aba6:
        st.subheader("Distribuição Etária por Cidade")
        df_faixas_cidade = df_filtrado.groupby("Cidade")[[
            "Número aproximado de crianças",
            "Número aproximado de jovens",
            "Número aproximado de adultos",
            "Número aproximado de idosos"
        ]].sum().reset_index()

        df_faixas_cidade_melt = df_faixas_cidade.melt(id_vars="Cidade", var_name="Faixa Etária", value_name="Quantidade")

        graf_faixa_cidade = px.bar(df_faixas_cidade_melt, x="Cidade", y="Quantidade", color="Faixa Etária")
        st.plotly_chart(graf_faixa_cidade, use_container_width=True)

# Página Mapa
def pagina_mapa():
    st.title("🗺 Mapa da Coleta por Cidade")

    dados_cidade = df_filtrado.groupby("Cidade")["Quantidade total de itens coletados"].sum().reset_index()

    coordenadas = {
        "São Paulo": [-23.5505, -46.6333],
        "Campinas": [-22.9056, -47.0608],
        "Santos": [-23.9608, -46.3336],
        "Sorocaba": [-23.5015, -47.4526],
        "Ribeirão Preto": [-21.1783, -47.8060],
        "Americana": [-22.729958, -47.334938],
        "Belo Horizonte": [-19.917, -43.933],
        "Bequimão": [-2.4333, -44.7833],
        "Brasília": [-15.79389, -47.88278],
        "Cabedelo": [-6.98083, -34.83389],
        "Campo Grande": [-20.48389, -54.615],
        "Curitiba": [-25.42972, -49.27111],
        "Delmiro Gouveia": [-9.38583, -37.99583],
        "Feira de Santana": [-12.2667, -38.9667],
        "Florianópolis": [-27.5935, -48.55854],
        "Fortaleza": [-3.7275, -38.5275],
        "Goiânia": [-16.6864, -49.2643],
        "Gravataí": [-29.94389, -50.99194],
        "Guarapari": [-20.6537, -40.4975],
        "Guarulhos": [-23.46278, -46.53278],
        "Imbé": [-29.975, -50.128],
        "Ipatinga": [-19.4706, -42.5476],
        "Itanhaém": [-24.1736, -46.7889],
        "Itatiba": [-23.0039, -46.8461],
        "João Pessoa": [-7.115, -34.8631],
        "Jundiaí": [-23.1857, -46.8978],
        "Lençóis Paulista": [-22.5986, -48.8031],
        "Londrina": [-23.3045, -51.1696],
        "Marabá": [-5.3686, -49.1178],
        "Mauá": [-23.6678, -46.4614],
        "Natal": [-5.7945, -35.211],
        "Nova Friburgo": [-22.2819, -42.5311],
        "Nova Santa Rita": [-29.8511, -51.2831],
        "Olinda": [-7.9998, -34.845],
        "Pinheiro": [-2.5225, -45.0825],
        "Pirassununga": [-21.9961, -47.4258],
        "Recife": [-8.0476, -34.877],
        "Rio Formoso": [-8.6592, -35.1581],
        "Rio de Janeiro": [-22.9068, -43.1729]
    }

    mapa = folium.Map(location=[-15.793889, -47.882778], zoom_start=4)

    marker_cluster = MarkerCluster().add_to(mapa)

    for idx, row in dados_cidade.iterrows():
        cidade = row["Cidade"]
        total_itens = row["Quantidade total de itens coletados"]
        coord = coordenadas.get(cidade)
        if coord:
            folium.Marker(
                location=coord,
                popup=f"<b>{cidade}</b><br>Total de itens: {int(total_itens)}",
                tooltip=cidade,
                icon=folium.Icon(color='green', icon='trash', prefix='fa')
            ).add_to(marker_cluster)

    folium_static(mapa)

# Menu lateral
with st.sidebar:
    escolha = option_menu("Menu Principal", ["Home", "Gráficos", "Mapa"], 
                          icons=["house", "bar-chart-line", "map"], menu_icon="cast", default_index=0)

if escolha == "Home":
    pagina_home()
elif escolha == "Gráficos":
    pagina_graficos()
elif escolha == "Mapa":
    pagina_mapa()