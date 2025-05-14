import pandas as pd
import yfinance as yf
import streamlit as st
import concurrent.futures
from datetime import datetime

@st.cache_data
def load_portfolio_data():
    """Charge les données du portefeuille à partir du CSV"""
    try:
        df = pd.read_csv("data/tickers_final.csv")
        # Remplacer SEBP.PA par SK.PA si nécessaire
        df['ticker'] = df['ticker'].replace('SEBP.PA', 'SK.PA')
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier CSV: {e}")
        return pd.DataFrame()

def get_stock_data_thread(ticker):
    """Récupère les données d'une action en temps réel"""
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

@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def get_all_stock_data(tickers):
    """Récupère les données de toutes les actions en parallèle"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_stock_data_thread, ticker) for ticker in tickers]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    return {result['ticker']: result for result in results}

@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def get_historical_data(tickers, start_date=None, end_date=None):
    """Récupère les données historiques pour une liste de tickers"""
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

@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def load_metrics(tickers):
    """Charge les métriques pour chaque ticker"""
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

@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def load_sector_country_data(tickers):
    """Récupère secteur et pays pour chaque ticker"""
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