import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, date

def plot_performance(hist_data, reference_indices=None, start_date_input=None, end_date_input=None):
    """Affiche les graphiques de performance des actions et des indices"""
    # Convertir la date d'entrée en datetime
    if isinstance(start_date_input, date) and not isinstance(start_date_input, datetime):
        start_date = datetime.combine(start_date_input, datetime.min.time())
    else:
        start_date = start_date_input
    
    end_date = end_date_input or datetime.now()
    
    # Forcer la date de début au 5 janvier 2023
    fixed_start_date = datetime(2023, 1, 5)
    
    # Trouver les dates communes
    valid_tickers = []
    start_dates = []
    end_dates = []
    
    for ticker, hist in hist_data.items():
        if not hist.empty:
            # Vérifier si l'historique contient des données après la date fixe
            if hist.index[0] <= fixed_start_date or any(d >= fixed_start_date for d in hist.index):
                valid_tickers.append(ticker)
                start_dates.append(hist.index[0])
                end_dates.append(hist.index[-1])
    
    if not start_dates or not end_dates:
        st.warning("Pas assez de données pour créer un graphique.")
        return None
    
    # Assurer que nous avons trouvé des données valides après le 5 janvier 2023
    use_start_date = fixed_start_date
    use_end_date = end_date_input or datetime.now()
    
    # Créer le graphique
    fig = go.Figure()
    
    # Créer une plage de dates sans fuseau horaire
    date_range = pd.date_range(start=use_start_date, end=use_end_date, freq='B')
    
    # Initialiser le DataFrame pour les performances normalisées
    all_normalized = pd.DataFrame(index=date_range)
    
    # Ajouter chaque action
    valid_tickers_with_data = []
    for ticker in valid_tickers:
        hist = hist_data[ticker]
        # Filtrer par dates communes
        filtered_hist = hist[(hist.index >= use_start_date) & (hist.index <= use_end_date)]
        if filtered_hist.empty:
            continue
            
        # Réindexer pour s'assurer que les dates correspondent
        reindexed = filtered_hist['Close'].reindex(date_range, method='ffill')
        
        # Vérifier si nous avons des données valides pour la normalisation
        if reindexed.empty or reindexed.isna().all() or reindexed.iloc[0] <= 0:
            continue
        
        # Normaliser à 100
        normalized = reindexed / reindexed.iloc[0] * 100
        all_normalized[ticker] = normalized
        valid_tickers_with_data.append(ticker)
    
    # Assurer que nous avons au moins une action avec des données
    if all_normalized.empty or len(valid_tickers_with_data) == 0:
        st.warning("Pas assez de données valides pour calculer la performance du portefeuille.")
        return None
    
    # Calculer la performance du portefeuille
    portfolio_performance = all_normalized.mean(axis=1)
    
    # Créer la trace du portefeuille
    fig.add_trace(go.Scatter(
        x=portfolio_performance.index,
        y=portfolio_performance.values,
        mode='lines',
        name='Portefeuille 100 Valeurs',
        line=dict(width=4, color='#3B1E0C')
    ))
    
    # Ajouter les indices de référence
    if reference_indices:
        for name, ticker in reference_indices.items():
            try:
                reference = yf.Ticker(ticker)
                ref_hist = reference.history(start=use_start_date, end=use_end_date)
                if not ref_hist.empty:
                    # Rendre les dates naïves
                    ref_hist.index = ref_hist.index.tz_localize(None)
                    
                    # Réindexer pour correspondre à notre date_range
                    ref_close = ref_hist['Close'].reindex(date_range, method='ffill')
                    
                    # Vérifier si nous avons des données valides
                    if ref_close.empty or ref_close.isna().all() or ref_close.iloc[0] <= 0:
                        continue
                    
                    # Normaliser
                    ref_normalized = ref_close / ref_close.iloc[0] * 100
                    
                    # Ajouter la trace de l'indice
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
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Récupérer toutes les valeurs y de toutes les traces
    all_y_values = []
    for trace in fig.data:
        all_y_values.extend([y for y in trace.y if y is not None and not np.isnan(y)])
    
    if all_y_values:
        min_y = max(min(all_y_values) * 0.9, 0)
        max_y = max(all_y_values) * 1.1
        
        # Ajuster l'échelle Y
        fig.update_layout(yaxis=dict(range=[min_y, max_y]))
    
    return fig