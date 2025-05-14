import streamlit as st
from datetime import datetime, timedelta

# Import des modules personnalisés
from utils.data_loader import load_portfolio_data, get_historical_data, load_metrics
from utils.formatting import get_currency_from_ticker, format_number_with_spaces
from components.ticker_banner import create_scrolling_ticker
from components.performance import plot_performance
from components.simulation import plot_portfolio_simulation
from components.metrics import display_metrics_table
from analysis.portfolio import calculate_portfolio_stats, display_top_contributors
from analysis.statistics import display_portfolio_allocation

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Komorebi 100 - Performance Portefeuille",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour la page
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
    }
    .section-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        color: #3B1E0C;
        border-bottom: 3px solid #3B1E0C;
        padding-bottom: 10px;
    }
    .metric-container {
        background-color: #F5F0EA;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-title {
        font-size: 16px;
        color: #3B1E0C;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
    }
    .metric-subtitle {
        font-size: 12px;
        color: #888;
    }
    .positive {
        color: #0E5F0E;
    }
    .negative {
        color: #8B0000;
    }
    .neutral {
        color: #102040;
    }
    .ticker-item {
        color: white !important;
    }
    .reference-indices {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
        text-align: right;
    }
    .indices-selection {
        font-size: 12px;
        padding: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Chargement des données
portfolio_df = load_portfolio_data()

if portfolio_df.empty:
    st.stop()

# Création du mapping des devises
currency_mapping = {row['ticker']: get_currency_from_ticker(row['ticker']) for _, row in portfolio_df.iterrows()}

# Titre principal
st.markdown("<h1 style='font-size:36px; margin-bottom:15px; color:#102040;'>Performance du Portefeuille international de 100 valeurs</h1>", unsafe_allow_html=True)

# Ajouter la date fixe sous le titre
st.markdown("<h3 style='font-size:22px; margin-bottom:25px; color:#3B1E0C;'>Date de début d'investissement au 05/01/2023</h3>", unsafe_allow_html=True)

# Bandeau défilant après le titre principal
st.markdown(create_scrolling_ticker(portfolio_df, currency_mapping), unsafe_allow_html=True)

# Définir les dates sans widget visible
start_date = datetime(2023, 1, 5)
end_date = datetime.now()

# Charger les données historiques
with st.spinner("Chargement des données historiques pour les 100 valeurs..."):
    hist_data = get_historical_data(portfolio_df['ticker'].tolist(), start_date, end_date)

# Configuration des indices de référence - options disponibles
indices_options = {
    "CAC 40": "^FCHI",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EURO STOXX 50": "^STOXX50E",
    "DAX": "^GDAXI",
    "Nikkei 225": "^N225",
    "FTSE 100": "^FTSE"
}

# Définir des valeurs par défaut
selected_indices = ["CAC 40", "S&P 500"]
reference_indices = {name: indices_options[name] for name in selected_indices}

# Afficher le graphique de performance
if hist_data:
    # Ajout d'un conteneur pour le graphique de performance
    st.markdown('<div id="performance-graph-container">', unsafe_allow_html=True)
    
    # Afficher les indices de référence de manière discrète au-dessus des légendes
    st.markdown('<div class="reference-indices">Indices de référence: CAC 40, S&P 500</div>', unsafe_allow_html=True)
    
    performance_fig = plot_performance(hist_data, reference_indices, start_date, end_date)
    if performance_fig:
        st.plotly_chart(performance_fig, use_container_width=True, key="performance_chart")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Simulation d'investissement
st.markdown('<div class="section-title">Simulation d\'investissement</div>', unsafe_allow_html=True)

# Montant d'investissement
investment_amount = 1000000  # 1 million d'euros fixe

# Simulation
simulation_fig, final_value, gain_loss, percent_change, stock_info = plot_portfolio_simulation(
    hist_data, 
    investment_amount,
    start_date,
    end_date
)

if simulation_fig:
    st.plotly_chart(simulation_fig, use_container_width=True, key="simulation_chart")
    
    # Afficher les résultats de la simulation avec format des nombres européen
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">Valeur finale</div>
                <div class="metric-value">{format_number_with_spaces(final_value)} €</div>
            </div>
            """,
            unsafe_allow_html=True
        )
   
    with col2:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">Gain/Perte</div>
                <div class="metric-value {'positive' if gain_loss >= 0 else 'negative'}">{'+' if gain_loss >= 0 else ''}{format_number_with_spaces(gain_loss)} €</div>
            </div>
            """,
            unsafe_allow_html=True
        )
   
    with col3:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">Performance</div>
                <div class="metric-value {'positive' if percent_change >= 0 else 'negative'}">{percent_change:+.2f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Ajouter un séparateur marron entre les sections
st.markdown("""
<div style="height: 3px; background-color: #3B1E0C; margin: 40px 0px 30px 0px;"></div>
""", unsafe_allow_html=True)

# TOP 15 Contributeurs Positifs et Négatifs
st.markdown('<div class="section-title">TOP 15 Contributeurs</div>', unsafe_allow_html=True)

# Calculer les performances des actions pour les top contributeurs
if hist_data:
    df_perf = calculate_portfolio_stats(hist_data, portfolio_df, start_date=start_date, end_date=end_date)
    # Affichage des top contributeurs
    display_top_contributors(df_perf)

# Ajouter un séparateur marron entre les sections
st.markdown("""
<div style="height: 3px; background-color: #3B1E0C; margin: 40px 0px 30px 0px;"></div>
""", unsafe_allow_html=True)

# Répartition géographique et sectorielle pour les 100 valeurs
st.markdown('<div class="section-title">Répartition du Portefeuille 100 Valeurs</div>', unsafe_allow_html=True)

# Afficher les graphiques de répartition
display_portfolio_allocation(portfolio_df['ticker'].tolist())

# Ajouter un séparateur marron pour le tableau détaillé des métriques
st.markdown("""
<div style="height: 3px; background-color: #3B1E0C; margin: 40px 0px 30px 0px;"></div>
""", unsafe_allow_html=True)

# Charger et afficher les métriques
metrics_df = load_metrics(portfolio_df['ticker'].tolist())
display_metrics_table(metrics_df)

# Pied de page
st.markdown("""
<div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #102040;">
   <p>Komorebi Investments © 2025 - Analyse de Portefeuille 100 Valeurs</p>
   <p style="font-size: 12px; margin-top: 10px;">Les informations présentées ne constituent en aucun cas un conseil d'investissement, ni une sollicitation à acheter ou vendre des instruments financiers. L'investisseur est seul responsable de ses décisions d'investissement.</p>
</div>
""", unsafe_allow_html=True)