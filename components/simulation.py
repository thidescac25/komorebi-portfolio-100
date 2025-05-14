import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date
from utils.formatting import format_number_with_spaces

def plot_portfolio_simulation(hist_data, initial_investment=1000000, start_date_input=None, end_date_input=None):
    """Simule l'évolution d'un portefeuille d'investissement"""
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
        st.warning("Pas assez de données pour créer une simulation.")
        return None, 0, 0, 0, []
    
    # Assurer que nous avons trouvé des données valides après le 5 janvier 2023
    use_start_date = fixed_start_date
    use_end_date = end_date_input or datetime.now()
    
    # Créer une plage de dates sans fuseau horaire
    date_range = pd.date_range(start=use_start_date, end=use_end_date, freq='B')
    
    # Répartition équitable
    valid_tickers_with_data = []
    for ticker in valid_tickers:
        hist = hist_data[ticker]
        # On vérifie si on a des données pour ce ticker après la date fixe
        if not hist.empty and any(idx >= fixed_start_date for idx in hist.index):
            valid_tickers_with_data.append(ticker)
    
    num_stocks = len(valid_tickers_with_data)
    if num_stocks == 0:
        st.warning("Aucune action valide trouvée après le 5 janvier 2023.")
        return None, 0, 0, 0, []
    
    investment_per_stock = initial_investment / num_stocks
    
    # Créer le graphique
    fig = go.Figure()
    
    # Initialiser le DataFrame pour les valeurs
    portfolio_df = pd.DataFrame(index=date_range)
    # Assurer que la première valeur est exactement l'investissement initial
    portfolio_df['portfolio_value'] = initial_investment
    
    # Calculer l'évolution de la valeur de chaque action
    stock_info = []
    
    for ticker in valid_tickers_with_data:
        hist = hist_data[ticker]
        # Filtrer par dates communes
        filtered_hist = hist[(hist.index >= use_start_date) & (hist.index <= use_end_date)]
        if filtered_hist.empty:
            continue
            
        # S'assurer que nous avons des données au jour fixe
        if use_start_date not in filtered_hist.index:
            # Trouver la première date disponible après la date fixe
            available_dates = filtered_hist.index[filtered_hist.index >= use_start_date]
            if len(available_dates) == 0:
                continue
            first_available_date = available_dates[0]
            # Si trop loin de la date fixe, ignorer ce ticker
            if (first_available_date - use_start_date).days > 5:  # Maximum 5 jours de décalage
                continue
        
        # Réindexer pour correspondre à notre date_range
        reindexed = filtered_hist['Close'].reindex(date_range, method='ffill')
        
        if reindexed.empty or reindexed.isna().all() or reindexed.iloc[0] <= 0:
            continue
        
        # Calculer le nombre d'actions achetées au début
        initial_price = reindexed.iloc[0]
        num_shares = investment_per_stock / initial_price
        
        # Stocker les informations pour l'affichage
        stock_info.append({
            "ticker": ticker,
            "num_shares": int(num_shares) if not np.isnan(num_shares) else 0,
            "initial_investment": investment_per_stock
        })
        
        # Pour chaque date après la première, calculer la contribution à la performance
        for i in range(1, len(date_range)):
            current_date = date_range[i]
            current_value = reindexed.loc[current_date] * num_shares
            initial_value = investment_per_stock
            # Pour la 2ème date et suivantes, ajouter l'écart à la valeur initiale
            portfolio_df.loc[current_date, 'portfolio_value'] += (current_value - initial_value)
    
    # Extraire les valeurs du portefeuille
    portfolio_value = portfolio_df['portfolio_value']
    
    # Ajouter le portefeuille total
    fig.add_trace(go.Scatter(
        x=portfolio_value.index,
        y=portfolio_value.values,
        mode='lines',
        name='Portefeuille Total',
        line=dict(width=3, color='#3B1E0C')
    ))
    
    # Ajouter une ligne pour l'investissement initial
    fig.add_shape(
        type="line",
        x0=use_start_date,
        y0=initial_investment,
        x1=use_end_date,
        y1=initial_investment,
        line=dict(color="black", width=2, dash="dash")
    )
    
    # Mise en forme avec format des nombres européen
    fig.update_layout(
        title=f"Évolution d'un investissement de {format_number_with_spaces(initial_investment)} € réparti équitablement",
        xaxis_title="Date",
        yaxis_title="Valeur (€)",
        height=700,
        template="plotly_white",
        showlegend=False  # Supprimer la légende pour éviter l'encombrement
    )
    
    # Ajuster l'échelle Y pour mieux voir les courbes principales
    if not portfolio_value.empty:
        min_y = max(portfolio_value.min() * 0.9, 0)  # Ne pas descendre sous zéro
        max_y = portfolio_value.max() * 1.1
        
        # Mettre à jour les limites de l'axe Y
        fig.update_layout(yaxis=dict(range=[min_y, max_y]))
    
    # Calculer le gain/perte total
    if portfolio_value.empty:
        final_value = initial_investment
        gain_loss = 0
        percent_change = 0
    else:
        final_value = portfolio_value.iloc[-1]
        gain_loss = final_value - initial_investment
        percent_change = (gain_loss / initial_investment) * 100
    
    return fig, final_value, gain_loss, percent_change, stock_info