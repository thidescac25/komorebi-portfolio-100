import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, date

def calculate_portfolio_stats(hist_data, portfolio_df, start_date=None, end_date=None):
    """Calcule les statistiques de performance des actions du portefeuille"""
    if not hist_data:
        return None
    
    # Convertir les dates en datetime si nécessaire
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())
    
    # S'assurer que start_date est le 01/01/2023
    target_date = datetime(2023, 1, 1)
    
    # Vérifier si cette date est disponible dans les données historiques
    date_available = False
    for ticker, hist in hist_data.items():
        if not hist.empty and hist.index[0] <= target_date:
            date_available = True
            break
    
    use_start_date = target_date if date_available else max(target_date, min([hist.index[0] for ticker, hist in hist_data.items() if not hist.empty]))
    
    # Trouver la date de début commune
    start_dates = []
    
    for ticker, hist in hist_data.items():
        if not hist.empty:
            filtered = hist[(hist.index >= use_start_date) & (hist.index <= end_date)]
            if not filtered.empty:
                start_dates.append(filtered.index[0])
    
    if not start_dates:
        return None
    
    common_start_date = max(use_start_date, min(start_dates))
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

def display_top_contributors(df_perf):
    """Affiche les Top 15 contributeurs positifs et négatifs"""
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
        
        return True
    return False