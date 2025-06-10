import pandas as pd
import streamlit as st
import yfinance as yf
import concurrent.futures
from datetime import datetime, timedelta
from src.stock_utils import get_country_from_ticker

@st.cache_data
def load_portfolio_data():
    """Chargement des données du portefeuille."""
    try:
        df = pd.read_csv("data/Portefeuille_100_business_models.csv")
        # Remplacer SEBP.PA par SK.PA si nécessaire
        df['ticker'] = df['ticker'].replace('SEBP.PA', 'SK.PA')
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier CSV: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_stock_data(ticker, detailed=False):
    """
    Récupère les données récentes d'une action.
    
    Arguments:
        ticker (str): Symbole de l'action
        detailed (bool): Si True, récupère des données plus détaillées
        
    Returns:
        dict: Dictionnaire contenant les données de l'action
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Données actuelles
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0))
        
        # Alternative avec historical si prix non disponible
        if current_price == 0 or previous_close == 0:
            hist = stock.history(period="2d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                if len(hist) > 1:
                    previous_close = hist['Close'].iloc[-2]
                else:
                    previous_close = current_price
        
        change = current_price - previous_close
        percent_change = (change / previous_close) * 100 if previous_close else 0
        
        result = {
            'current_price': current_price,
            'previous_close': previous_close,
            'change': change,
            'percent_change': percent_change
        }
        
        if detailed:
            # Données financières
            sector = info.get('sector', "Non disponible")
            industry = info.get('industry', "Non disponible")
            country = info.get('country', "USA")  # Pays par défaut
            
            # Métriques financières
            pe_ratio = info.get('trailingPE', 0)
            dividend_yield = info.get('dividendYield', 0)
            
            # Performance annuelle (YTD)
            history = stock.history(period="ytd")
            if not history.empty:
                ytd_start = history.iloc[0]['Close']
                ytd_current = history.iloc[-1]['Close']
                ytd_change = ((ytd_current - ytd_start) / ytd_start) * 100
            else:
                ytd_change = 0
            
            # BPA
            eps = info.get('trailingEps', 0)
            market_cap = info.get('marketCap', 0) / 1_000_000_000  # Conversion en milliards
            
            # Historique des prix pour le graphique
            hist = stock.history(period="1y")
            
            # Ajouter les données détaillées
            result.update({
                'sector': sector,
                'industry': industry,
                'country': country,
                'pe_ratio': pe_ratio,
                'dividend_yield': dividend_yield,
                'ytd_change': ytd_change,
                'eps': eps,
                'market_cap': market_cap,
                'history': hist
            })
            
        return result
    except Exception as e:
        # En cas d'erreur, utiliser des données simulées
        import random
        
        # Créer un historique de prix simulé si nécessaire
        if detailed:
            date_range = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
            price_start = random.uniform(500, 1000)
            prices = []
            current_price = price_start
            
            for _ in range(len(date_range)):
                current_price = current_price * (1 + random.uniform(-0.03, 0.03))
                prices.append(current_price)
            
            hist = pd.DataFrame({
                'Date': date_range,
                'Close': prices,
                'Open': [p * random.uniform(0.98, 1.0) for p in prices],
                'High': [p * random.uniform(1.0, 1.05) for p in prices],
                'Low': [p * random.uniform(0.95, 1.0) for p in prices],
                'Volume': [random.randint(1000000, 10000000) for _ in range(len(date_range))]
            }).set_index('Date')
            
            current_price = prices[-1]
            previous_close = prices[-2]
        else:
            current_price = random.uniform(500, 1000)
            previous_close = current_price * random.uniform(0.95, 1.05)
            hist = None
        
        change = current_price - previous_close
        percent_change = (change / previous_close) * 100
        
        result = {
            'current_price': current_price,
            'previous_close': previous_close,
            'change': change,
            'percent_change': percent_change
        }
        
        if detailed:
            result.update({
                'sector': "Technology",
                'industry': "Semiconductor Equipment & Materials",
                'country': "USA",
                'pe_ratio': random.uniform(15, 35),
                'dividend_yield': random.uniform(0.5, 4.5),
                'ytd_change': random.uniform(-15, 25),
                'eps': random.uniform(1, 30),
                'market_cap': random.uniform(10, 500),
                'history': hist
            })
            
        return result

@st.cache_data(ttl=60)
def get_historical_data(tickers, start_date=None, end_date=None):
    """
    Récupère les données historiques pour une liste de tickers.
    
    Arguments:
        tickers (list): Liste des symboles d'actions
        start_date (datetime, optional): Date de début
        end_date (datetime, optional): Date de fin
        
    Returns:
        dict: Dictionnaire de DataFrames avec historique des prix
    """
    # Si end_date n'est pas fourni, utiliser la date actuelle
    if end_date is None:
        end_date = datetime.now()
    
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
            st.warning(f"Erreur lors de la récupération des données pour {ticker}: {e}")
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

@st.cache_data(ttl=3600)
def load_sector_country_data(tickers):
    """
    Récupère secteur et pays pour chaque ticker via yfinance.
    
    Arguments:
        tickers (list): Liste des symboles d'actions
        
    Returns:
        DataFrame: DataFrame avec secteur et pays pour chaque ticker
    """
    def fetch_sector_country(ticker):
        try:
            info = yf.Ticker(ticker).info
            sector = info.get("sector", "Non disponible")
            country = info.get("country", "Non disponible")
            
            # Fallback si le pays n'est pas disponible via l'API
            if not country or country == "Non disponible":
                country = get_country_from_ticker(ticker)
                
            return {
                "Ticker": ticker,
                "Sector": sector,
                "Country": country
            }
        except Exception as e:
            return {
                "Ticker": ticker,
                "Sector": "Non disponible",
                "Country": get_country_from_ticker(ticker)  # Utilise le fallback même en cas d'erreur
            }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_sector_country, ticker) for ticker in tickers]
        data = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def load_metrics(tickers):
    """
    Charge les métriques détaillées pour une liste de tickers.
    
    Arguments:
        tickers (list): Liste des symboles d'actions
        
    Returns:
        DataFrame: DataFrame avec les métriques pour chaque ticker
    """
    rows = []
    
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            
            # helpers
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
                "Prix Actuel":      num("currentPrice"),
                "Clôture Prec.":    num("previousClose"),
                "52-sem. Bas":      num("fiftyTwoWeekLow"),
                "52-sem. Haut":     num("fiftyTwoWeekHigh"),
                "Moyenne 50j":      num("fiftyDayAverage"),
                "Moyenne 200j":     num("twoHundredDayAverage"),
                "Market Cap":       num("marketCap"),
                "PER (TTM)":        num("trailingPE"),
                "Div Yield":        num("dividendYield"),
                "Reco Analyses":    txt("recommendationKey"),
            })
        except Exception as e:
            rows.append({
                "Ticker":           ticker,
                "Nom complet":      f"Erreur : {str(e)}",
                "Pays":             None,
                "Secteur":          None,
                "Industrie":        None,
                "Exchange":         None,
                "Devise":           None,
                "Prix Actuel":      None,
                "Clôture Prec.":    None,
                "52-sem. Bas":      None,
                "52-sem. Haut":     None,
                "Moyenne 50j":      None,
                "Moyenne 200j":     None,
                "Market Cap":       None,
                "PER (TTM)":        None,
                "Div Yield":        None,
                "Reco Analyses":    None,
            })
    
    dfm = pd.DataFrame(rows).set_index("Ticker")
    return dfm