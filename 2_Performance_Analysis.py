# 2_Performance_Analysis.py

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
import plotly.graph_objects as go  # Import ajouté pour les tableaux

# Ajouter le dossier src au chemin d'importation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les modules personnalisés
from src.data_loader import load_portfolio_data, get_stock_data, get_historical_data, load_sector_country_data
from src.stock_utils import get_currency_mapping, determine_currency, get_company_name
from src.ui_components import apply_custom_css, create_scrolling_ticker, create_footer, create_metric_card, create_title
from src.visualization import plot_performance, plot_portfolio_simulation, calculate_portfolio_stats, display_top_contributors, create_bar_charts

# Configuration de la page
st.set_page_config(
    page_title="Komorebi 100 - Analyse de Performance",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Appliquer le CSS global perso
apply_custom_css()

# CSS SOLUTION CHATGPT : Réduire les espaces entre tableaux
st.markdown("""
<style>
/* enlève tout padding/marge autour du chart Plotly */
div[data-testid="stPlotlyChart"] {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* s'assure que vos <h4> restent serrés */
h4 {
    margin-top: 5px !important;
    margin-bottom: 5px !important;
}
</style>
""", unsafe_allow_html=True)

# CSS pour centrer cellules et en-têtes dans nos tables,
# fixer la largeur du tableau et le centrer
st.markdown(
    """
    <style>
      /* Centre le contenu des cellules */
      .komorebi-table th,
      .komorebi-table td {
        text-align: center !important;
        padding: 4px !important;  /* Réduire le padding */
      }
      /* Met le tableau à 80% de la largeur du conteneur, le centre, et fixe le layout */
      .komorebi-table {
        width: 80% !important;
        margin: 0 auto !important;
        table-layout: fixed !important;
        font-size: 0.85em !important;  /* Réduire la taille de la police */
      }
    </style>
    """,
    unsafe_allow_html=True
)

# Titre
st.markdown(create_title("Komorebi 100 valeurs"), unsafe_allow_html=True)

# Chargement des données
portfolio_df = load_portfolio_data()
currency_mapping = get_currency_mapping()

@st.cache_data(ttl=60)
def get_all_stock_data(tickers):
    return {t: get_stock_data(t) for t in tickers}

tickers = portfolio_df['ticker'].tolist()
stock_data_dict = get_all_stock_data(tickers)

# Ticker défilant
st.markdown(create_scrolling_ticker(portfolio_df, stock_data_dict, currency_mapping), unsafe_allow_html=True)

# Ajout d'espace après le bandeau défilant
st.markdown('<div style="height:35px;"></div>', unsafe_allow_html=True)  # Ajout de 35px d'espace

# Présentation performance
st.markdown('<div class="section-title">Présentation de la Performance</div>', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(
        "<div style='display: flex; align-items: center;'>"
        "<div>Date de début d'investissement</div>"
        "<div style='margin: 0 10px;'> - </div>"
        "<div style='color: #693112; font-style: italic;'>Fixée au 05/01/2023</div>"
        "</div>",
        unsafe_allow_html=True
    )
    start_date = datetime(2023, 1, 5)
with col2:
    indices_options = {
        "CAC 40": "^FCHI",
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "EURO STOXX 50": "^STOXX50E"
    }
    selected = st.multiselect("Indices de référence", options=list(indices_options.keys()), default=["CAC 40", "S&P 500"])
    reference_indices = {k: indices_options[k] for k in selected}

end_date = datetime.now()

# Données historiques & graphique
with st.spinner("Chargement des données historiques..."):
    hist_data = get_historical_data(tickers, start_date, end_date)

perf_fig = plot_performance(
    hist_data,
    reference_indices=reference_indices,
    end_date_ui=end_date,
    force_start_date=start_date
)

if perf_fig:
    st.plotly_chart(perf_fig, use_container_width=True, key="perf")
else:
    st.warning("Pas assez de données pour afficher le graphique de performance.")

# Simulation
st.markdown('<div class="section-title">Simulation d\'investissement</div>', unsafe_allow_html=True)
with st.spinner("Calcul de la simulation..."):
    sim_fig, final_val, gain_loss, pct, _ = plot_portfolio_simulation(
        hist_data, 1_000_000, end_date_ui=end_date, max_traces=20, force_start_date=start_date
    )
if sim_fig:
    st.plotly_chart(sim_fig, use_container_width=True, key="sim")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(create_metric_card("Valeur finale", int(final_val), "Valeur totale du portefeuille", is_currency=True, currency="€"), unsafe_allow_html=True)
    with c2:
        st.markdown(create_metric_card("Gain/Perte", int(gain_loss), "Depuis l'investissement initial", is_currency=True, currency="€", positive_color=True), unsafe_allow_html=True)
    with c3:
        st.markdown(create_metric_card("Performance", pct, "Rendement total", is_percentage=True, positive_color=True), unsafe_allow_html=True)
else:
    st.warning("Pas assez de données pour afficher la simulation.")

# Contributeurs
if hist_data and 'name' in portfolio_df.columns:
    df_perf = calculate_portfolio_stats(hist_data, portfolio_df, start_date, end_date)
    display_top_contributors(df_perf)
else:
    st.warning("Impossible de calculer les contributeurs à la performance.")

# Analyse par secteur et pays
st.markdown('<div class="section-title">Analyse par Secteur et Pays</div>', unsafe_allow_html=True)
df_sc = load_sector_country_data(tickers)

# Calcul des variations
perf_list = []
for t in tickers:
    if t in hist_data and not hist_data[t].empty:
        dfh = hist_data[t]
        i0 = dfh.index.get_indexer([start_date], method='nearest')[0]
        if 0 <= i0 < len(dfh):
            p0, p1 = dfh['Close'].iloc[i0], dfh['Close'].iloc[-1]
            if p0 > 0:
                pctc = (p1 - p0) / p0 * 100
                comp = portfolio_df[portfolio_df['ticker'] == t]
                name = comp.iloc[0]['name'] if not comp.empty else t
                perf_list.append({'Ticker': t, 'Société': name, 'Variation(%)': pctc})
perf_df = pd.DataFrame(perf_list)
analysis_df = pd.merge(df_sc, perf_df, on='Ticker')

# --- Performances par secteur ---
st.markdown("<h5 style='font-size:16px;'>Performance par secteur</h5>", unsafe_allow_html=True)
sector_stats = (
    analysis_df.groupby('Sector')
    .agg({'Ticker':'count','Variation(%)':['mean','min','max']})
    .reset_index()
)
sector_stats.columns = ['Secteur','Nombre','Performance Moyenne (%)','Performance Min (%)','Performance Max (%)']
sector_stats.index += 1

sector_html = (
    sector_stats.style
      .format({
          'Performance Moyenne (%)':'{:+.2f}%',
          'Performance Min (%)':'{:+.2f}%',
          'Performance Max (%)':'{:+.2f}%'
      })
      .background_gradient(cmap='RdYlGn', subset=['Performance Moyenne (%)'], vmin=-50, vmax=150)
      .set_table_attributes('class="komorebi-table"')
      .to_html()
)
st.markdown(sector_html, unsafe_allow_html=True)

# --- Performances par pays ---
st.markdown("<h5 style='font-size:16px;'>Performance par pays</h5>", unsafe_allow_html=True)
country_stats = (
    analysis_df.groupby('Country')
    .agg({'Ticker':'count','Variation(%)':['mean','min','max']})
    .reset_index()
)
country_stats.columns = ['Pays','Nombre','Performance Moyenne (%)','Performance Min (%)','Performance Max (%)']
country_stats.index += 1

country_html = (
    country_stats.style
      .format({
          'Performance Moyenne (%)':'{:+.2f}%',
          'Performance Min (%)':'{:+.2f}%',
          'Performance Max (%)':'{:+.2f}%'
      })
      .background_gradient(cmap='RdYlGn', subset=['Performance Moyenne (%)'], vmin=-50, vmax=150)
      .set_table_attributes('class="komorebi-table"')
      .to_html()
)
st.markdown(country_html, unsafe_allow_html=True)

# Ajouter plus d'espace avant la section "Répartition Sectorielle et Géographique"
st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)

# Ajout de la section "Répartition Sectorielle et Géographique" à la fin de la page
st.markdown('<div class="section-title">Répartition Sectorielle et Géographique</div>', unsafe_allow_html=True)

# Allocation égale pour chaque action (répartition équitable pour 100 valeurs)
df_sc["Weight"] = 1.0 / len(df_sc)

# Créer les graphiques à barres horizontales
fig_sector, fig_geo = create_bar_charts(df_sc)

# Agrandir la hauteur des graphiques
fig_sector.update_layout(height=600)
fig_geo.update_layout(height=600)

# Afficher les graphiques côte à côte
col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    st.plotly_chart(fig_sector, use_container_width=True)
with col_chart2:
    st.plotly_chart(fig_geo, use_container_width=True)

# Ajouter plus d'espace avant la nouvelle section
st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)

# NOUVELLE SECTION: Liste des 100 valeurs présentes dans le Portefeuille
st.markdown('<div class="section-title">Liste des 100 valeurs présentes dans le Portefeuille</div>', unsafe_allow_html=True)

# Fusionner les données du portefeuille avec les données de secteur/pays et performances
portfolio_complete = portfolio_df.copy()

# Ajouter les données de secteur/pays
portfolio_complete = portfolio_complete.merge(df_sc, left_on='ticker', right_on='Ticker', how='left')

# Ajouter les performances du jour
daily_performance = []
for _, row in portfolio_complete.iterrows():
    ticker = row['ticker']
    stock_data = stock_data_dict.get(ticker, {})
    
    # Récupérer la performance du jour
    current_price = stock_data.get('current_price', 0)
    percent_change = stock_data.get('percent_change', 0)
    
    # Formater la performance du jour
    if percent_change >= 0:
        performance_text = f"{current_price:.2f} (+{percent_change:.2f}%)"
    else:
        performance_text = f"{current_price:.2f} ({percent_change:.2f}%)"
    
    # Déterminer la devise
    currency = determine_currency(ticker)
    
    daily_performance.append({
        'ticker': ticker,
        'performance_day': performance_text,
        'currency': currency
    })

# Convertir en DataFrame et fusionner
daily_perf_df = pd.DataFrame(daily_performance)
portfolio_complete = portfolio_complete.merge(daily_perf_df, on='ticker', how='left')

# SOLUTION CHATGPT : Pays disponibles (hors "Non disponible")
countries = sorted([
    c for c in portfolio_complete['Country'].unique() 
    if pd.notna(c) and c != "Non disponible"
])

# On veut que "France" soit affichée en dernier
if "France" in countries:
    countries.remove("France")
    countries.append("France")

for country in countries:
    if country == "Non disponible":
        continue
        
    # Filtrer les données pour ce pays
    country_data = portfolio_complete[portfolio_complete['Country'] == country]
    
    if country_data.empty:
        continue
    
    # Préparer les données pour le tableau
    table_data = []
    for _, row in country_data.iterrows():
        # Secteur (avec valeur par défaut si manquante)
        sector = row.get('Sector', 'Non disponible')
        if pd.isna(sector):
            sector = 'Non disponible'
            
        table_data.append({
            'name': row['name'],
            'performance': row['performance_day'],
            'sector': sector,
            'currency': row['currency']
        })
    
    if not table_data:
        continue
    
    # Convertir en DataFrame
    country_df = pd.DataFrame(table_data)
    
    # Créer le titre du pays avec marges réduites
    st.markdown(f"<h4 style='color: #693112; margin-top: 5px; margin-bottom: 5px;'>🌍 {country} ({len(country_df)} valeurs)</h4>", unsafe_allow_html=True)
    
    # Créer le tableau avec Plotly - ORDRE MODIFIÉ DES COLONNES
    fig_country = go.Figure(data=[go.Table(
        header=dict(
            # NOUVEL ORDRE: Nom - Secteur - Performance - Devise
            values=['<b>Nom complet de la société</b>', '<b>Secteur</b>', '<b>Performance du jour (%)</b>', '<b>Devise</b>'],
            font=dict(size=14, color='white'),
            fill_color='#693112',  # Fond marron
            align='center',
            height=40
        ),
        cells=dict(
            # NOUVEL ORDRE des valeurs: name - sector - performance - currency
            values=[
                country_df['name'],
                country_df['sector'],
                country_df['performance'],
                country_df['currency']
            ],
            font=dict(size=14, color='#000000', weight='bold'),
            align='center',
            format=[None, None, None, None],
            fill_color=['#F9F9F9'],
            height=30
        )
    )])
    
    # SOLUTION CHATGPT : Calcul de la hauteur
    n_rows = len(country_df)
    base_height = 40 * n_rows + 50  # 40px par ligne + 50px pour l'en-tête
    
    if country == "France":
        height = base_height  # on l'affiche en entier
    else:
        height = min(base_height, 800)  # pour les autres, on garde un max
    
    # Mise en page du tableau avec hauteur adaptée
    fig_country.update_layout(
        margin=dict(l=5, r=5, t=0, b=0),
        height=height
    )
    
    # Afficher le tableau
    st.plotly_chart(fig_country, use_container_width=True, key=f"country_{country}")

# Afficher les valeurs sans pays défini (si il y en a)
no_country_data = portfolio_complete[
    (portfolio_complete['Country'].isna()) | 
    (portfolio_complete['Country'] == "Non disponible")
]

if not no_country_data.empty:
    # Titre avec marges réduites
    st.markdown(f"<h4 style='color: #693112; margin-top: 5px; margin-bottom: 5px;'>❓ Pays non défini ({len(no_country_data)} valeurs)</h4>", unsafe_allow_html=True)
    
    # Préparer les données
    table_data = []
    for _, row in no_country_data.iterrows():
        sector = row.get('Sector', 'Non disponible')
        if pd.isna(sector):
            sector = 'Non disponible'
            
        table_data.append({
            'name': row['name'],
            'performance': row['performance_day'],
            'sector': sector,
            'currency': row['currency']
        })
    
    no_country_df = pd.DataFrame(table_data)
    
    # Créer le tableau - ORDRE MODIFIÉ DES COLONNES
    fig_no_country = go.Figure(data=[go.Table(
        header=dict(
            # NOUVEL ORDRE: Nom - Secteur - Performance - Devise
            values=['<b>Nom complet de la société</b>', '<b>Secteur</b>', '<b>Performance du jour (%)</b>', '<b>Devise</b>'],
            font=dict(size=14, color='white'),
            fill_color='#693112',
            align='center',
            height=40
        ),
        cells=dict(
            # NOUVEL ORDRE des valeurs: name - sector - performance - currency
            values=[
                no_country_df['name'],
                no_country_df['sector'],
                no_country_df['performance'],
                no_country_df['currency']
            ],
            font=dict(size=14, color='#000000', weight='bold'),
            align='center',
            format=[None, None, None, None],
            fill_color=['#F9F9F9'],
            height=30
        )
    )])
    
    # Hauteur adaptée pour "Pays non défini"
    n_rows = len(no_country_df)
    base_height = 40 * n_rows + 50
    height = min(base_height, 800)  # Limite pour éviter des pages trop longues
    
    fig_no_country.update_layout(
        margin=dict(l=5, r=5, t=0, b=0),
        height=height
    )
    
    st.plotly_chart(fig_no_country, use_container_width=True, key="country_undefined")

# Footer
st.markdown(create_footer(), unsafe_allow_html=True)