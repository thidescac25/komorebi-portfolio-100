import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import base64
import concurrent.futures

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
    .stock-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        border: 1px solid #e0e0e0;
    }
    .dataframe {
        font-size: 12px;
        color: #000000 !important;
    }
    .stDataFrame > div {
        font-size: 12px;
        color: #000000 !important;
    }
    .dataframe td {
        text-align: center !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    .dataframe th {
        text-align: center !important;
        color: #000000 !important;
        background-color: #E5E9F0 !important;
        font-weight: bold !important;
    }
    .css-1l269bu {
        color: #000000 !important;
    }
    .css-10trblm {
        color: #000000 !important;
    }
    .ticker-item {
        color: white !important;
    }
    
    /* Styles pour les graphiques Plotly */
    .plotly-graph-div .js-plotly-plot .plotly .modebar-container .modebar-group .modebar-btn {
        color: #000000 !important;
    }
    .plotly-graph-div .js-plotly-plot .plotly .layout .annotation text {
        fill: #000000 !important;
    }
    .plotly-graph-div .js-plotly-plot .plotly .legend text {
        fill: #000000 !important;
    }
    .plotly-graph-div .js-plotly-plot .plotly .xaxis .tick text,
    .plotly-graph-div .js-plotly-plot .plotly .yaxis .tick text {
        fill: #000000 !important;
    }
    .plotly-graph-div .js-plotly-plot .plotly .plot-container .svg-container .cartesianlayer .infolayer .hoverlayer .infoline text {
        fill: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour charger les données du CSV
@st.cache_data
def load_portfolio_data():
    try:
        df = pd.read_csv("data/tickers_final.csv")
        # Remplacer SEBP.PA par SK.PA si nécessaire
        df['ticker'] = df['ticker'].replace('SEBP.PA', 'SK.PA')
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier CSV: {e}")
        return pd.DataFrame()

# Chargement des données
portfolio_df = load_portfolio_data()

if portfolio_df.empty:
    st.stop()

# Mapping dynamique des devises basé sur les suffixes des tickers
def get_currency_from_ticker(ticker):
    if ticker.endswith('.PA'):
        return '€'
    elif ticker.endswith('.L'):
        return '£'
    elif ticker.endswith('.SW'):
        return 'CHF'
    elif ticker.endswith('.DE'):
        return '€'
    elif ticker.endswith('.T'):
        return '¥'
    elif ticker.endswith('.AX'):
        return 'A$'
    elif ticker.endswith('.NS'):
        return '₹'
    elif ticker.endswith('.KS'):
        return '₩'
    elif ticker.endswith('.BR'):
        return '€'
    elif ticker.endswith('.MC'):
        return '€'
    elif ticker.endswith('.CO'):
        return 'DKK'
    elif ticker.endswith('.OL'):
        return 'NOK'
    elif ticker.endswith('.LU'):
        return '€'
    elif ticker.endswith('.ST'):
        return 'SEK'
    else:
        return '$'

# Création du mapping des devises
currency_mapping = {row['ticker']: get_currency_from_ticker(row['ticker']) for _, row in portfolio_df.iterrows()}

# Titre principal
st.markdown("<h1 style='font-size:36px; margin-bottom:15px; color:#102040;'>Performance du Portefeuille<br>Date de début d'investissement au 03/01/2023</h1>", unsafe_allow_html=True)

# Fonction pour obtenir les données boursières actuelles avec threading
def get_stock_data_thread(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Données actuelles
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0))
        
        if current_price == 0 or previous_close == 0:
            # Alternative avec historical
            hist = stock.history(period="2d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                if len(hist) > 1:
                    previous_close = hist['Close'].iloc[-2]
                else:
                    previous_close = current_price
        
        change = current_price - previous_close
        percent_change = (change / previous_close) * 100 if previous_close else 0
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'previous_close': previous_close,
            'change': change,
            'percent_change': percent_change,
            'valid': True
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'current_price': 0,
            'previous_close': 0,
            'change': 0,
            'percent_change': 0,
            'valid': False
        }

# Fonction pour obtenir toutes les données boursières en parallèle
@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def get_all_stock_data():
    tickers = portfolio_df['ticker'].tolist()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_stock_data_thread, ticker) for ticker in tickers]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    return {result['ticker']: result for result in results}

# Création du bandeau défilant pour les 100 valeurs (plus grand)
def create_scrolling_ticker():
    all_stock_data = get_all_stock_data()
    ticker_items = ""
    
    for _, row in portfolio_df.iterrows():
        stock_data = all_stock_data.get(row['ticker'])
        if not stock_data or not stock_data['valid']:
            continue
            
        ticker = row['ticker']
        currency = currency_mapping.get(ticker, "$")
        
        if stock_data['change'] >= 0:
            change_class = "positive"
            arrow = '<span style="font-size: 28px;">&#x25B2;</span>'
        else:
            change_class = "negative"
            arrow = '<span style="font-size: 28px;">&#x25BC;</span>'
        
        ticker_items += f"""
        <div class="ticker-item">
            <span class="ticker-name">{row['name']}</span>
            <span class="ticker-price">{currency}{stock_data['current_price']:.2f}</span>
            <span class="ticker-change {change_class}">{arrow} {stock_data['percent_change']:.2f}%</span>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background-color: #102040;
                font-family: Arial, sans-serif;
            }}
            .ticker-container {{
                width: 100%;
                overflow: hidden;
                white-space: nowrap;
                padding: 25px 0; /* Augmenter le padding vertical */
            }}
            .ticker-tape {{
                display: inline-block;
                animation: ticker-scroll 600s linear infinite;
                padding-left: 100%;
            }}
            .ticker-item {{
                display: inline-block;
                padding: 0 50px; /* Augmenter le padding horizontal */
                color: white;
                font-size: 22px; /* Agrandir la taille de la police */
            }}
            .ticker-name {{
                font-weight: bold;
                margin-right: 20px; /* Augmenter la marge */
            }}
            .ticker-price {{
                margin-right: 20px; /* Augmenter la marge */
            }}
            .positive {{
                color: #00ff00;
                font-weight: bold;
                font-size: 24px; /* Agrandir la taille de la police */
            }}
            .negative {{
                color: #ff4d4d;
                font-weight: bold;
                font-size: 24px; /* Agrandir la taille de la police */
            }}
            @keyframes ticker-scroll {{
                0% {{ transform: translate3d(0, 0, 0); }}
                100% {{ transform: translate3d(-100%, 0, 0); }}
            }}
        </style>
    </head>
    <body>
        <div class="ticker-container">
            <div class="ticker-tape">
                {ticker_items}
                {ticker_items}
            </div>
        </div>
    </body>
    </html>
    """
    
    b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    iframe_html = f'<iframe src="data:text/html;base64,{b64}" width="100%" height="100px" frameborder="0" scrolling="no"></iframe>'
    return iframe_html

# Bandeau défilant après le titre principal
st.markdown(create_scrolling_ticker(), unsafe_allow_html=True)

# Zone d'options
col1, col2 = st.columns([3, 2])

with col1:
    # Widget date_input actif
    start_date = st.date_input(
        "Choisissez votre date de début d'investissement",
        value=datetime(2023, 1, 3),
        min_value=datetime(2020, 1, 1),
        max_value=datetime.now() - timedelta(days=1),
        label_visibility="visible"
    )
    end_date = datetime.now()

with col2:
    # Sélection des indices de référence
    indices_options = {
        "CAC 40": "^FCHI",
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "EURO STOXX 50": "^STOXX50E",
        "DAX": "^GDAXI",
        "Nikkei 225": "^N225",
        "FTSE 100": "^FTSE"
    }
    selected_indices = st.multiselect(
        "Indices de référence",
        options=list(indices_options.keys()),
        default=["CAC 40", "S&P 500"]
    )
    reference_indices = {name: indices_options[name] for name in selected_indices}

# Récupérer les données historiques avec threading
@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def get_historical_data(tickers, start_date=None, end_date=None):
    data = {}
    
    def fetch_ticker_data(ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            if not hist.empty:
                hist.index = hist.index.tz_localize(None)
                return ticker, hist
            return ticker, None
        except Exception as e:
            print(f"Erreur pour {ticker}: {e}")
            return ticker, None
    
    # Utiliser ThreadPoolExecutor pour télécharger en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_ticker_data, ticker) for ticker in tickers]
        
        # Afficher une barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            ticker, hist = future.result()
            if hist is not None:
                data[ticker] = hist
            progress_bar.progress((i + 1) / len(futures))
            status_text.text(f"Chargé: {i+1}/{len(futures)} valeurs")
        
        progress_bar.empty()
        status_text.empty()
    
    return data

# Fonction pour afficher les performances
def plot_performance(hist_data, reference_indices=None, start_date_input=None, end_date_input=None):
    # Convertir la date d'entrée en datetime
    if isinstance(start_date_input, date) and not isinstance(start_date_input, datetime):
        start_date = datetime.combine(start_date_input, datetime.min.time())
    else:
        start_date = start_date_input
    
    end_date = end_date_input or datetime.now()
    
    # Trouver la date de début commune
    start_dates = []
    
    for ticker, hist in hist_data.items():
        if not hist.empty:
            filtered = hist[(hist.index >= start_date) & (hist.index <= end_date)]
            if not filtered.empty:
                start_dates.append(filtered.index[0])
    
    if not start_dates:
        st.warning("Pas assez de données pour créer un graphique.")
        return None
    
    common_start_date = max(start_dates)
    # Ne pas utiliser min(end_dates) pour garantir que le graphique s'étend jusqu'à end_date
    
    # Créer le graphique
    fig = go.Figure()
    
    # Créer une plage de dates sans fuseau horaire
    date_range = pd.date_range(start=common_start_date, end=end_date, freq='B')
    
    # Initialiser le DataFrame pour les performances normalisées
    all_normalized = pd.DataFrame(index=date_range)
    
    # Ajouter chaque action (invisibles dans le graphique final)
    for ticker, hist in hist_data.items():
        if hist.empty:
            continue
            
        # Filtrer par dates communes
        filtered_hist = hist[(hist.index >= common_start_date) & (hist.index <= end_date)]
        if filtered_hist.empty:
            continue
            
        # Réindexer pour s'assurer que les dates correspondent
        reindexed = filtered_hist['Close'].reindex(date_range, method='ffill')
        
        # Normaliser à 100
        normalized = (reindexed / reindexed.iloc[0]) * 100
        all_normalized[ticker] = normalized
    
    # Calculer la performance du portefeuille (équipondéré)
    if all_normalized.empty:
        st.warning("Pas assez de données pour calculer la performance du portefeuille.")
        return None
        
    portfolio_performance = all_normalized.mean(axis=1)
    
    # Créer la trace du portefeuille
    fig.add_trace(go.Scatter(
        x=portfolio_performance.index,
        y=portfolio_performance.values,
        mode='lines',
        name='Portefeuille 100 Valeurs',
        line=dict(width=4, color='#3B1E0C'),
        hovertemplate="<b>Portefeuille 100 Valeurs</b><br>%{x}<br>%{y:.2f}%<extra></extra>"
    ))
    
    # Ajouter les indices de référence
    if reference_indices:
        for name, ticker in reference_indices.items():
            try:
                reference = yf.Ticker(ticker)
                ref_hist = reference.history(start=common_start_date, end=end_date)
                if not ref_hist.empty:
                    # Rendre les dates naïves
                    ref_hist.index = ref_hist.index.tz_localize(None)
                    
                    # Réindexer pour correspondre à notre date_range
                    ref_close = ref_hist['Close'].reindex(date_range, method='ffill')
                    
                    # Normaliser
                    ref_normalized = (ref_close / ref_close.iloc[0]) * 100
                    
                    # Tracer l'indice de référence
                    fig.add_trace(go.Scatter(
                        x=ref_normalized.index,
                        y=ref_normalized.values,
                        mode='lines',
                        name=name,
                        line=dict(width=2.5, dash='dash')
                    ))
            except Exception as e:
                st.warning(f"Erreur lors de la récupération des données pour {name}: {e}")
    
    # Mise en forme
    fig.update_layout(
        title="Performance Comparée - Portefeuille et Indices (Base 100)",
        xaxis_title="Date",
        yaxis_title="Performance (%)",
        height=700,
        template="plotly_white",
        showlegend=True,
        hovermode='x unified',
        font=dict(color="#00008B", size=14),  # Bleu foncé pour le texte
        legend=dict(
            font=dict(color="#00008B"),  # Bleu foncé pour la légende
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Fonction pour simuler l'évolution du portefeuille - corrigée
def plot_portfolio_simulation(hist_data, initial_investment=1000000, start_date_input=None, end_date_input=None):
    # Convertir la date d'entrée en datetime
    if isinstance(start_date_input, date) and not isinstance(start_date_input, datetime):
        start_date = datetime.combine(start_date_input, datetime.min.time())
    else:
        start_date = start_date_input
    
    end_date = end_date_input or datetime.now()
    
    # Trouver la date de début commune
    start_dates = []
    
    for ticker, hist in hist_data.items():
        if not hist.empty:
            filtered = hist[(hist.index >= start_date) & (hist.index <= end_date)]
            if not filtered.empty:
                start_dates.append(filtered.index[0])
    
    if not start_dates:
        st.warning("Pas assez de données pour créer une simulation.")
        return None, 0, 0, 0
    
    common_start_date = max(start_dates)
    
    # Créer une plage de dates sans fuseau horaire
    date_range = pd.date_range(start=common_start_date, end=end_date, freq='B')
    
    # Définir les taux de change par défaut pour les devises (à ajuster avec des données réelles si possible)
    exchange_rates = {
        '$': 0.85,       # USD en EUR
        '£': 1.15,       # GBP en EUR
        'CHF': 0.92,     # CHF en EUR
        '¥': 0.0068,     # JPY en EUR
        'A$': 0.60,      # AUD en EUR
        '₹': 0.011,      # INR en EUR
        '₩': 0.00068,    # KRW en EUR
        'DKK': 0.13,     # DKK en EUR
        'NOK': 0.095,    # NOK en EUR
        'SEK': 0.093,    # SEK en EUR
        '€': 1.0         # EUR en EUR (pas de conversion)
    }
    
    # Répartition équitable du capital initial
    num_stocks = len(hist_data)
    if num_stocks == 0:
        st.warning("Pas assez de données valides pour créer une simulation.")
        return None, 0, 0, 0
        
    investment_per_stock = initial_investment / num_stocks
    
    # Créer le graphique
    fig = go.Figure()
    
    # Initialiser le DataFrame pour les valeurs avec une colonne portefeuille
    portfolio_df = pd.DataFrame(index=date_range)
    portfolio_df['portfolio_value'] = initial_investment  # Commencer exactement à 1M€
    
    # Calculer l'évolution de la valeur du portefeuille avec prise en compte des taux de change
    for ticker, hist in hist_data.items():
        if hist.empty:
            continue
        
        # Déterminer la devise du ticker
        currency = currency_mapping.get(ticker, '$')
        exchange_rate = exchange_rates.get(currency, 1.0)  # Taux de change vers EUR
        
        # Filtrer les données pour la période demandée
        filtered_hist = hist[(hist.index >= common_start_date) & (hist.index <= end_date)]
        if filtered_hist.empty:
            continue
            
        # S'assurer que l'action a des données pour le premier jour
        if filtered_hist.index[0] != common_start_date:
            continue
            
        # Réindexer pour correspondre à notre date_range
        reindexed = filtered_hist['Close'].reindex(date_range, method='ffill')
        
        if reindexed.empty or reindexed.isna().all() or reindexed.iloc[0] == 0:
            continue
        
        # Calculer le nombre d'actions achetées au début (avec conversion EUR)
        initial_price = reindexed.iloc[0]
        initial_price_eur = initial_price * exchange_rate
        num_shares = investment_per_stock / initial_price_eur
        
        # Suivre la valeur au fil du temps (avec conversion EUR)
        for idx, current_date in enumerate(date_range):  # Remplacé 'date' par 'current_date'
            if idx > 0:  # Commencer après le premier jour pour préserver la valeur initiale exacte
                if current_date in reindexed.index:  # Utilisez 'current_date' ici
                    price = reindexed.loc[current_date]  # Et ici
                    price_eur = price * exchange_rate
                    stock_value = price_eur * num_shares
                    
                    # Contribution à la performance du portefeuille
                    portfolio_contribution = stock_value - (investment_per_stock)
                    portfolio_df.loc[current_date, 'portfolio_value'] += portfolio_contribution  # Et ici
    
    # Assurer que la première valeur est exactement initial_investment
    portfolio_df.iloc[0, 0] = initial_investment
    
    # Ajouter le portefeuille total
    fig.add_trace(go.Scatter(
        x=portfolio_df.index,
        y=portfolio_df['portfolio_value'],
        mode='lines',
        name='Portefeuille Total',
        line=dict(width=3, color='#3B1E0C')
    ))
    
    # Ajouter une ligne pour l'investissement initial
    fig.add_shape(
        type="line",
        x0=common_start_date,
        y0=initial_investment,
        x1=end_date,
        y1=initial_investment,
        line=dict(color="black", width=2, dash="dash")
    )
    
    # Mise en forme
    fig.update_layout(
        title=f"Évolution d'un investissement de {initial_investment:,.0f} € réparti équitablement",
        xaxis_title="Date",
        yaxis_title="Valeur (€)",
        height=700,
        template="plotly_white",
        font=dict(color="#00008B", size=14),  # Bleu foncé pour le texte
        legend=dict(
            font=dict(color="#00008B"),  # Bleu foncé pour la légende
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Ajuster l'échelle Y pour mieux voir les courbes principales
    if not portfolio_df.empty:
        min_y = max(portfolio_df['portfolio_value'].min() * 0.9, 0)  # Ne pas descendre sous zéro
        max_y = portfolio_df['portfolio_value'].max() * 1.1
        
        # Mettre à jour les limites de l'axe Y
        fig.update_layout(yaxis=dict(range=[min_y, max_y]))
    
    # Calculer le gain/perte total
    if portfolio_df.empty:
        final_value = initial_investment
        gain_loss = 0
        percent_change = 0
    else:
        final_value = portfolio_df['portfolio_value'].iloc[-1]
        gain_loss = final_value - initial_investment
        percent_change = (gain_loss / initial_investment) * 100
    
    return fig, final_value, gain_loss, percent_change

# Fonction pour calculer les statistiques du portefeuille (pour les top contributeurs)
def calculate_portfolio_stats(hist_data, start_date=None, end_date=None):
    if not hist_data:
        return None
    
    # Convertir les dates en datetime si nécessaire
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())
    
    # Trouver la date de début commune
    start_dates = []
    
    for ticker, hist in hist_data.items():
        if not hist.empty:
            filtered = hist[(hist.index >= start_date) & (hist.index <= end_date)]
            if not filtered.empty:
                start_dates.append(filtered.index[0])
    
    if not start_dates:
        return None
    
    common_start_date = max(start_dates)
    # Utiliser end_date directement
    
    # Liste pour stocker les performances individuelles
    stock_performance = []
    
    # Calculer la performance pour chaque action
    for ticker, hist in hist_data.items():
        try:
            # Filtrer les données sur la période commune
            hist_filtered = hist[(hist.index >= common_start_date) & (hist.index <= end_date)]
            
            if hist_filtered.empty or len(hist_filtered) < 2:
                continue
            
            # Calculer correctement les prix de début et fin
            start_price = hist_filtered['Close'].iloc[0]
            end_price = hist_filtered['Close'].iloc[-1]
            
            # Vérifier que les prix sont valides
            if start_price <= 0 or np.isnan(start_price) or end_price <= 0 or np.isnan(end_price):
                continue
            
            # Calcul correct de la performance en pourcentage
            stock_return_pct = ((end_price - start_price) / start_price) * 100
            
            # Récupérer les informations de l'entreprise
            company_info = portfolio_df[portfolio_df['ticker'] == ticker]
            if not company_info.empty:
                company_name = company_info['name'].iloc[0]
            else:
                company_name = ticker
            
            stock_performance.append({
                'Ticker': ticker,
                'Société': company_name,
                'Performance (%)': stock_return_pct
            })
            
        except Exception as e:
            print(f"Erreur pour {ticker}: {e}")
            continue
    
    return pd.DataFrame(stock_performance)

# Charger les données historiques
with st.spinner("Chargement des données historiques pour les 100 valeurs..."):
    hist_data = get_historical_data(portfolio_df['ticker'].tolist(), start_date, end_date)

# Afficher le graphique de performance
if hist_data:
    performance_fig = plot_performance(hist_data, reference_indices, start_date, end_date)
    if performance_fig:
        st.plotly_chart(performance_fig, use_container_width=True, key="performance_chart")

# Simulation d'investissement
st.markdown('<div class="section-title">Simulation d\'investissement</div>', unsafe_allow_html=True)

# Montant d'investissement
investment_amount = 1000000  # 1 million d'euros fixe

# Simulation
simulation_fig, final_value, gain_loss, percent_change = plot_portfolio_simulation(
    hist_data, 
    investment_amount,
    start_date,
    end_date
)

if simulation_fig:
    st.plotly_chart(simulation_fig, use_container_width=True, key="simulation_chart")
    
    # Afficher les résultats de la simulation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-title">
                <div class="metric-title">Valeur finale</div>
               <div class="metric-value">{final_value:,.0f} €</div>
           </div>
           """,
           unsafe_allow_html=True
       )
   
    with col2:
       st.markdown(
           f"""
           <div class="metric-container">
               <div class="metric-title">Gain/Perte</div>
               <div class="metric-value {'positive' if gain_loss >= 0 else 'negative'}">{gain_loss:+,.0f} €</div>
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
   df_perf = calculate_portfolio_stats(hist_data, start_date=start_date, end_date=end_date)
   
   if df_perf is not None and not df_perf.empty:
       # Trier par performance
       df_perf = df_perf.sort_values('Performance (%)', ascending=False)
       
       # Créer deux colonnes pour les contributeurs
       col_pos, col_neg = st.columns(2)
       
       with col_pos:
           st.markdown("<h4 style='color: #102040;'>🟢 TOP 15 Contributeurs Positifs</h4>", unsafe_allow_html=True)
           top_positive = df_perf.head(15)[['Société', 'Performance (%)']]
           st.dataframe(
               top_positive.style.format({
                   'Performance (%)': '{:+.2f}%'
               }).set_properties(**{
                   'color': '#000000',
                   'font-weight': 'bold',
                   'background-color': '#f5f5f5'
               }),
               use_container_width=True,
               height=300
           )
       
       with col_neg:
           st.markdown("<h4 style='color: #102040;'>🔴 TOP 15 Contributeurs Négatifs</h4>", unsafe_allow_html=True)
           # Utiliser nsmallest pour obtenir les 15 pires performances
           top_negative = df_perf.nsmallest(15, 'Performance (%)')[['Société', 'Performance (%)']]
           st.dataframe(
               top_negative.style.format({
                   'Performance (%)': '{:+.2f}%'
               }).set_properties(**{
                   'color': '#000000',
                   'font-weight': 'bold',
                   'background-color': '#f5f5f5'
               }),
               use_container_width=True,
               height=300
           )

# Ajouter un séparateur marron entre les sections
st.markdown("""
<div style="height: 3px; background-color: #3B1E0C; margin: 40px 0px 30px 0px;"></div>
""", unsafe_allow_html=True)

# Répartition géographique et sectorielle pour les 100 valeurs
st.markdown('<div class="section-title">Répartition du Portefeuille 100 Valeurs</div>', unsafe_allow_html=True)

# Charger les données secteur/pays
@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def load_sector_country_100(tickers):
   data = []
   
   def fetch_sector_country(ticker):
       try:
           info = yf.Ticker(ticker).info
           return {
               "Ticker": ticker,
               "Sector": info.get("sector", "Non disponible"),
               "Country": info.get("country", "Non disponible")
           }
       except Exception as e:
           return {
               "Ticker": ticker,
               "Sector": "Non disponible",
               "Country": "Non disponible"
           }
   
   with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
       futures = [executor.submit(fetch_sector_country, ticker) for ticker in tickers]
       data = [future.result() for future in concurrent.futures.as_completed(futures)]
   
   return pd.DataFrame(data)

df_sc = load_sector_country_100(portfolio_df['ticker'].tolist())
df_sc["Weight"] = 1.0 / len(df_sc)

# Calcul des répartitions
sector_alloc = df_sc.groupby("Sector")["Weight"].sum().reset_index()
country_alloc = df_sc.groupby("Country")["Weight"].sum().reset_index()

# Convertir les poids en pourcentages pour l'affichage
sector_alloc["Weight_pct"] = (sector_alloc["Weight"] * 100).round(1)
country_alloc["Weight_pct"] = (country_alloc["Weight"] * 100).round(1)

# Afficher les diagrammes en colonnes côte à côte avec couleurs plus foncées
col_bar1, col_bar2 = st.columns(2)

with col_bar1:
   # Palette de couleurs foncées multi-couleurs pour les secteurs
   sector_colors = ['#3B1E0C', '#00008B', '#006400', '#8B0000', '#4B0082', '#800000', '#000080', 
                   '#556B2F', '#8B4513', '#2F4F4F', '#191970', '#8B008B', '#006400', '#483D8B']
   
   fig_sector = px.bar(
       sector_alloc.sort_values('Weight', ascending=False),
       x='Sector',
       y='Weight_pct',
       title='Répartition Sectorielle des 100 Valeurs',
       color='Sector',
       color_discrete_sequence=sector_colors,  # Couleurs foncées variées
       text='Weight_pct'
   )
   
   fig_sector.update_traces(
       texttemplate='%{text}%',
       textposition='outside',
       textfont=dict(color="#000000", size=12, family="Arial")  # Texte noir pour meilleure visibilité
   )
   
   fig_sector.update_layout(
       showlegend=True,
       xaxis_title='Secteur',
       yaxis_title='Pourcentage (%)',
       xaxis_tickangle=-45,
       font=dict(color="#000000", size=12),  # Noir pour meilleure visibilité
       title_font=dict(color="#000000", size=16, family="Arial Bold"),
       yaxis=dict(range=[0, max(sector_alloc['Weight_pct']) * 1.2]),
       # Style pour les légendes
       legend=dict(
           font=dict(color="#000000", size=12, family="Arial Bold"),
           bgcolor="rgba(255, 255, 255, 0.9)",
           bordercolor="Black",
           borderwidth=1
       )
   )
   
   # Améliorer la visibilité des noms de secteurs sur l'axe X
   fig_sector.update_xaxes(
       tickfont=dict(color="#000000", size=12, family="Arial Bold")
   )
   
   st.plotly_chart(fig_sector, use_container_width=True, key="sector_bar")

with col_bar2:
   # Palette de couleurs foncées multi-couleurs pour les pays
   country_colors = ['#4B0082', '#8B0000', '#006400', '#000080', '#3B1E0C', '#800000', '#483D8B', 
                    '#556B2F', '#8B4513', '#2F4F4F', '#191970', '#8B008B', '#006400', '#000080']
   
   fig_geo = px.bar(
       country_alloc.sort_values('Weight', ascending=False),
       x='Country',
       y='Weight_pct',
       title='Répartition Géographique des 100 Valeurs',
       color='Country',
       color_discrete_sequence=country_colors,  # Couleurs foncées variées
       text='Weight_pct'
   )
   
   fig_geo.update_traces(
       texttemplate='%{text}%',
       textposition='outside',
       textfont=dict(color="#000000", size=12, family="Arial")  # Texte noir pour meilleure visibilité
   )
   
   fig_geo.update_layout(
       showlegend=True,
       xaxis_title='Pays',
       yaxis_title='Pourcentage (%)',
       xaxis_tickangle=-45,
       font=dict(color="#000000", size=12),  # Noir pour meilleure visibilité
       title_font=dict(color="#000000", size=16, family="Arial Bold"),
       yaxis=dict(range=[0, max(country_alloc['Weight_pct']) * 1.2]),
       # Style pour les légendes
       legend=dict(
           font=dict(color="#000000", size=12, family="Arial Bold"),
           bgcolor="rgba(255, 255, 255, 0.9)",
           bordercolor="Black",
           borderwidth=1
       )
   )
   
   # Améliorer la visibilité des noms de pays sur l'axe X
   fig_geo.update_xaxes(
       tickfont=dict(color="#000000", size=12, family="Arial Bold")
   )
   
   st.plotly_chart(fig_geo, use_container_width=True, key="geo_bar")

# Ajouter un séparateur marron pour le tableau détaillé des métriques
st.markdown("""
<div style="height: 3px; background-color: #3B1E0C; margin: 40px 0px 30px 0px;"></div>
""", unsafe_allow_html=True)

# Charger les métriques
@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def load_metrics(tickers):
   rows = []
   for ticker in tickers:
       try:
           info = yf.Ticker(ticker).info
           def txt(k): return info.get(k, None)
           def num(k):
               v = info.get(k, None)
               return float(v) if v is not None else None
           rows.append({
               "Ticker":           ticker,
               "Nom complet":      txt("longName"),
               "Pays":             txt("country"),
               "Secteur":          txt("sector"),
               "Industrie":        txt("industry"),
               "Exchange":         txt("exchange"),
               "Devise":           txt("currency"),
               "Prix Ouv.":        num("open"),
               "Prix Actuel":      num("currentPrice"),
               "Clôture Prec.":    num("previousClose"),
               "52-sem. Bas":      num("fiftyTwoWeekLow"),
               "52-sem. Haut":     num("fiftyTwoWeekHigh"),
               "Moyenne 50j":      num("fiftyDayAverage"),
               "Moyenne 200j":     num("twoHundredDayAverage"),
               "Volume":           num("volume"),
               "Vol Moy. (10j)":   num("averageDailyVolume10Day"),
               "Market Cap":       num("marketCap"),
               "Beta":             num("beta"),
               "PER (TTM)":        num("trailingPE"),
               "PER Forward":      num("forwardPE"),
               "Div Yield":        num("dividendYield"),
               "Reco Analyses":    txt("recommendationKey"),
               "Objectif Prix":    num("targetMeanPrice"),
               "Nb Avis Anal.":    num("numberOfAnalystOpinions"),
           })
       except Exception as e:
           st.warning(f"Erreur lors de la récupération des métriques pour {ticker}: {e}")
           rows.append({
               "Ticker":           ticker,
               "Nom complet":      f"Erreur : {str(e)}",
               "Pays":             None,
               "Secteur":          None,
               "Industrie":        None,
               "Exchange":         None,
               "Devise":           None,
               "Prix Ouv.":        None,
               "Prix Actuel":      None,
               "Clôture Prec.":    None,
               "52-sem. Bas":      None,
               "52-sem. Haut":     None,
               "Moyenne 50j":      None,
               "Moyenne 200j":     None,
               "Volume":           None,
               "Vol Moy. (10j)":   None,
               "Market Cap":       None,
               "Beta":             None,
               "PER (TTM)":        None,
               "PER Forward":      None,
               "Div Yield":        None,
               "Reco Analyses":    None,
               "Objectif Prix":    None,
               "Nb Avis Anal.":    None,
           })
   dfm = pd.DataFrame(rows).set_index("Ticker")
   return dfm

# Utilisation des métriques pour le tableau
metrics_df = load_metrics(portfolio_df['ticker'].tolist())

# Affichage du tableau des métriques
st.markdown("<h3 style='color: #102040;'>Tableau détaillé des valeurs</h3>", unsafe_allow_html=True)
st.dataframe(
   metrics_df.style.format({
       col: '{:.2f}' for col in metrics_df.select_dtypes(include=['float64']).columns
   }).set_properties(**{
       'color': '#000000', 
       'text-align': 'center',
       'font-weight': 'bold'
   }).set_table_styles([
       {'selector': 'th', 'props': [('text-align', 'center'), ('color', '#000000'), ('background-color', '#E5E9F0'), ('font-weight', 'bold')]},
       {'selector': 'td', 'props': [('text-align', 'center'), ('background-color', '#F0F0F0')]}
   ]),
   use_container_width=True,
   height=600,
   key="metrics_table"
)

# Pied de page
st.markdown("""
<div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #102040;">
   <p>Komorebi Investments © 2025 - Analyse de Portefeuille 100 Valeurs</p>
   <p style="font-size: 12px; margin-top: 10px;">Les informations présentées ne constituent en aucun cas un conseil d'investissement, ni une sollicitation à acheter ou vendre des instruments financiers. L'investisseur est seul responsable de ses décisions d'investissement.</p>
</div>
""", unsafe_allow_html=True)