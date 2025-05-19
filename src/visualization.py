import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from .stock_utils import get_company_name, determine_currency

def plot_performance(hist_data, weights=None, reference_indices=None, end_date_ui=None, force_start_date=None):
    """
    Crée un graphique de performance comparée.
    
    Args:
        hist_data (dict): Dictionnaire de DataFrames avec historique des prix
        weights (list, optional): Liste des poids de chaque action
        reference_indices (dict, optional): Dictionnaire des indices de référence
        end_date_ui (datetime, optional): Date de fin spécifiée par l'UI
        force_start_date (datetime, optional): Date de début forcée (05/01/2023)
        
    Returns:
        go.Figure: Figure Plotly avec graphique de performance
    """
    if weights is None:
        weights = [1/len(hist_data)] * len(hist_data)
    
    # Trouver les dates communes
    start_dates = []
    end_dates = []
    
    for ticker, hist in hist_data.items():
        if not hist.empty:
            start_dates.append(hist.index[0])
            end_dates.append(hist.index[-1])
    
    if not start_dates or not end_dates:
        st.warning("Pas assez de données pour créer un graphique.")
        return None
    
    # Utiliser la date forcée si fournie, sinon utiliser la date max des données
    start_date = force_start_date if force_start_date else max(start_dates)
    # Utiliser la date de fin fournie par l'UI ou la date maximale disponible
    end_date = end_date_ui or max(end_dates)
    
    # Créer le graphique
    fig = go.Figure()
    
    # Créer une plage de dates sans fuseau horaire
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # Initialiser le DataFrame pour les performances normalisées
    all_normalized = pd.DataFrame(index=date_range)
    
    # Variables pour stocker les traces
    portfolio_trace = None
    indices_traces = []
    
    # Ajouter chaque action
    valid_tickers = []
    for i, (ticker, hist) in enumerate(hist_data.items()):
        if hist.empty:
            continue
            
        # Filtrer par dates communes
        filtered_hist = hist[(hist.index >= start_date) & (hist.index <= end_date)]
        if filtered_hist.empty:
            continue
        
        valid_tickers.append(ticker)
            
        # Réindexer pour s'assurer que les dates correspondent
        reindexed = filtered_hist['Close'].reindex(date_range, method='ffill')
        
        # Normaliser à 100
        if reindexed.iloc[0] > 0:  # Vérifier que la première valeur n'est pas zéro
            normalized = reindexed / reindexed.iloc[0] * 100
            all_normalized[ticker] = normalized
    
    # Vérifier que nous avons des données valides
    if all_normalized.empty or len(valid_tickers) == 0:
        st.warning("Pas assez de données pour calculer la performance du portefeuille.")
        return None
    
    # Recalculer les poids si nécessaire pour n'inclure que les tickers valides
    if len(valid_tickers) < len(hist_data):
        weights = [1/len(valid_tickers)] * len(valid_tickers)
        
    # Calculer la performance du portefeuille (répartition équitable)
    portfolio_performance = all_normalized.mean(axis=1)
    
    # Vérifier que la performance du portefeuille a été calculée
    if portfolio_performance.empty or portfolio_performance.isna().all():
        st.warning("Impossible de calculer la performance du portefeuille. Données insuffisantes.")
        return None
    
    # Créer la trace du portefeuille
    portfolio_trace = go.Scatter(
        x=portfolio_performance.index,
        y=portfolio_performance.values,
        mode='lines',
        name='Portefeuille 100 Valeurs',
        line=dict(width=3, color='#693112')
    )
    
    # Ajouter les indices de référence
    if reference_indices:
        for name, ticker in reference_indices.items():
            try:
                reference = yf.Ticker(ticker)
                ref_hist = reference.history(start=start_date, end=end_date)
                if not ref_hist.empty:
                    # Rendre les dates naïves
                    ref_hist.index = ref_hist.index.tz_localize(None)
                    
                    # Réindexer pour correspondre à notre date_range
                    ref_close = ref_hist['Close'].reindex(date_range, method='ffill')
                    
                    # Normaliser
                    if ref_close.iloc[0] > 0:  # Vérifier que la première valeur n'est pas zéro
                        ref_normalized = ref_close / ref_close.iloc[0] * 100
                        
                        # Sauvegarder la trace de l'indice
                        indices_traces.append(go.Scatter(
                            x=ref_normalized.index,
                            y=ref_normalized.values,
                            mode='lines',
                            name=name,
                            line=dict(width=2.5, dash='dash')  # Ligne plus épaisse pour les indices
                        ))
            except Exception as e:
                st.warning(f"Erreur lors de la récupération des données pour {name}: {e}")
    
    # Ajouter les traces dans l'ordre : d'abord le portefeuille, puis les indices
    if portfolio_trace:
        fig.add_trace(portfolio_trace)
    
    for trace in indices_traces:
        fig.add_trace(trace)
    
    # Mise en forme
    fig.update_layout(
        title="Performance Comparée (Base 100)",
        xaxis_title="Date",
        yaxis_title="Performance (%)",
        height=500,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Debug: afficher un avertissement si la trace du portefeuille est manquante
    if portfolio_trace is None:
        st.warning("Attention: La trace du portefeuille n'a pas pu être créée.")
    
    # Ajuster l'échelle Y pour mieux voir les courbes principales
    y_values = []
    
    # Récupérer les valeurs du portefeuille
    if portfolio_trace:
        y_values.extend(portfolio_trace.y)
    
    # Récupérer les valeurs des indices
    for trace in indices_traces:
        y_values.extend(trace.y)
    
    if y_values:
        # Calculer les percentiles pour déterminer une échelle appropriée
        y_values = [y for y in y_values if y is not None]
        if y_values:
            min_y = max(min(y_values) * 0.9, 0)  # Ne pas descendre en dessous de 0
            max_y = min(max(y_values) * 1.1, max(y_values) * 1.5)  # Limiter l'étendue supérieure
            
            # Calculer une valeur max raisonnable (ne pas aller trop haut)
            reasonable_max = max(150, min(max_y, 300))  # Entre 150% et 300% max
            
            # Mettre à jour les limites de l'axe Y
            fig.update_layout(yaxis=dict(range=[min_y, reasonable_max]))
    
    return fig

def plot_portfolio_simulation(hist_data, initial_investment=1000000, end_date_ui=None, max_traces=20, force_start_date=None):
    """
    Crée un graphique de simulation d'investissement.
    Avec 100 valeurs, on limite le nombre de traces à afficher.
    
    Args:
        hist_data (dict): Dictionnaire de DataFrames avec historique des prix
        initial_investment (float): Montant initial d'investissement
        end_date_ui (datetime, optional): Date de fin spécifiée par l'UI
        max_traces (int): Nombre maximum de traces individuelles à afficher
        force_start_date (datetime, optional): Date de début forcée (05/01/2023)
        
    Returns:
        tuple: (Figure Plotly, valeur finale, gain/perte, % changement, info actions)
    """
    # Trouver les dates communes
    start_dates = []
    end_dates = []
    
    for ticker, hist in hist_data.items():
        if not hist.empty:
            start_dates.append(hist.index[0])
            end_dates.append(hist.index[-1])
    
    if not start_dates or not end_dates:
        st.warning("Pas assez de données pour créer une simulation.")
        return None, 0, 0, 0, []
    
    # Utiliser la date forcée si fournie, sinon utiliser la date max des données
    start_date = force_start_date if force_start_date else max(start_dates)
    # Utiliser la date de fin fournie par l'UI ou la date maximale disponible
    end_date = end_date_ui or max(end_dates)
    
    # Créer une plage de dates sans fuseau horaire
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # Répartition équitable
    num_stocks = len(hist_data)
    investment_per_stock = initial_investment / num_stocks
    
    # Créer le graphique
    fig = go.Figure()
    
    # Initialiser le DataFrame pour les valeurs
    all_values = pd.DataFrame(index=date_range)
    
    # Calculer l'évolution de la valeur de chaque action
    stock_info = []
    
    # Pour limiter le nombre de traces individuelles (car 100 serait trop)
    sorted_tickers = sorted(hist_data.keys(), key=lambda x: len(hist_data[x]) if not hist_data[x].empty else 0, reverse=True)
    display_tickers = sorted_tickers[:max_traces]
    
    for ticker, hist in hist_data.items():
        if hist.empty:
            continue
            
        # Réindexer pour correspondre à notre date_range
        reindexed = hist['Close'].reindex(date_range, method='ffill')
        
        if reindexed.empty or reindexed.isna().all() or reindexed.iloc[0] == 0:
            continue
        
        # Calculer le nombre d'actions achetées au début
        initial_price = reindexed.iloc[0]
        num_shares = investment_per_stock / initial_price
        
        # Stocker les informations pour l'affichage
        # Vérifier si num_shares est NaN avant de le convertir en entier
        if pd.notna(num_shares):
            stock_info.append({
                "ticker": ticker,
                "num_shares": int(num_shares),
                "initial_investment": investment_per_stock
            })
        else:
            # Si num_shares est NaN, utiliser 0 comme valeur par défaut
            stock_info.append({
                "ticker": ticker,
                "num_shares": 0,
                "initial_investment": investment_per_stock
            })
        
        # Calculer la valeur au fil du temps
        stock_value = reindexed * num_shares
        all_values[ticker] = stock_value
        
        # N'ajouter la trace que si elle fait partie des top tickers à afficher
        if ticker in display_tickers:
            fig.add_trace(go.Scatter(
                x=stock_value.index,
                y=stock_value.values,
                mode='lines',
                name=ticker,
                line=dict(width=1, dash='dot'),
                opacity=0.3
            ))
    
    # Calculer la valeur totale du portefeuille
    portfolio_value = all_values.sum(axis=1)
    
    # Ajouter le portefeuille total
    fig.add_trace(go.Scatter(
        x=portfolio_value.index,
        y=portfolio_value.values,
        mode='lines',
        name='Portefeuille Total',
        line=dict(width=3, color='#693112')
    ))
    
    # Ajouter une ligne pour l'investissement initial
    fig.add_shape(
        type="line",
        x0=start_date,
        y0=initial_investment,
        x1=end_date,
        y1=initial_investment,
        line=dict(color="black", width=2, dash="dash")
    )
    
    # Mise en forme
    fig.update_layout(
        title=f"Évolution d'un investissement de {f'{initial_investment:_}'.replace('_', ' ')} € réparti équitablement",
        xaxis_title="Date",
        yaxis_title="Valeur (€)",
        height=500,
        template="plotly_white",
        showlegend=False  # Supprimer la légende complètement
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

def create_bar_charts(df, weight_column="Weight"):
    """
    Crée des graphiques à barres horizontales pour la répartition sectorielle et géographique.
    
    Args:
        df (DataFrame): DataFrame avec les colonnes Sector, Country et Weight
        weight_column (str): Nom de la colonne contenant les poids
        
    Returns:
        tuple: (Figure secteur, Figure pays)
    """
    # Calcul des répartitions
    sector_alloc = df.groupby("Sector")[weight_column].sum().reset_index()
    country_alloc = df.groupby("Country")[weight_column].sum().reset_index()
    
    # Trier par valeur décroissante
    sector_alloc = sector_alloc.sort_values(by=weight_column, ascending=False)
    country_alloc = country_alloc.sort_values(by=weight_column, ascending=False)
    
    # Convertir en pourcentage pour l'affichage
    sector_alloc[f"{weight_column} (%)"] = sector_alloc[weight_column] * 100
    country_alloc[f"{weight_column} (%)"] = country_alloc[weight_column] * 100
    
    # Palettes de couleurs
    sector_colors = ['#693112', '#8B4513', '#A0522D', '#CD853F', '#D2691E', '#B8860B', '#DAA520', 
                    '#DEB887', '#F4A460', '#D2B48C', '#BC8F8F', '#F5DEB3', '#FFE4B5', '#FFDEAD',
                    '#EEE8AA', '#F0E68C', '#BDB76B', '#E6E6FA', '#D8BFD8', '#DDA0DD']
    
    country_colors = ['#102040', '#1A365D', '#27496D', '#142F43', '#0F3460', '#2C3E50', '#34495E', '#283747',
                     '#21618C', '#2874A6', '#5499C7', '#7FB3D5', '#A9CCE3', '#D4E6F1', '#EBF5FB', '#AED6F1',
                     '#3498DB', '#2E86C1', '#2874A6', '#5DADE2']
    
    # Graphique secteur - barres horizontales
    fig_sector = px.bar(
        sector_alloc,
        y="Sector",  # Axe Y pour les barres horizontales
        x=f"{weight_column} (%)",
        title="Répartition Sectorielle",
        color="Sector",
        color_discrete_sequence=sector_colors,
        orientation='h',  # Barres horizontales
        text=f"{weight_column} (%)"  # Afficher les pourcentages sur les barres
    )
    
    fig_sector.update_traces(
        texttemplate='%{text:.1f}%',  # Format du texte affiché
        textposition='outside',  # Position du texte
    )
    
    fig_sector.update_layout(
        showlegend=False,
        font=dict(color="#102040"),
        title_font=dict(color="#693112", size=18),
        xaxis_title="Pourcentage (%)",
        yaxis_title="",
        xaxis=dict(range=[0, max(sector_alloc[f"{weight_column} (%)"]) * 1.1])  # Ajuster l'échelle X
    )
    
    # Graphique géographique - barres horizontales
    fig_geo = px.bar(
        country_alloc,
        y="Country",  # Axe Y pour les barres horizontales
        x=f"{weight_column} (%)",
        title="Répartition Géographique",
        color="Country",
        color_discrete_sequence=country_colors,
        orientation='h',  # Barres horizontales
        text=f"{weight_column} (%)"  # Afficher les pourcentages sur les barres
    )
    
    fig_geo.update_traces(
        texttemplate='%{text:.1f}%',  # Format du texte affiché
        textposition='outside',  # Position du texte
    )
    
    fig_geo.update_layout(
        showlegend=False,
        font=dict(color="#102040"),
        title_font=dict(color="#693112", size=18),
        xaxis_title="Pourcentage (%)",
        yaxis_title="",
        xaxis=dict(range=[0, max(country_alloc[f"{weight_column} (%)"]) * 1.1])  # Ajuster l'échelle X
    )
    
    return fig_sector, fig_geo

def calculate_portfolio_stats(hist_data, portfolio_df, start_date, end_date):
    """
    Calcule les statistiques de performance pour chaque action du portefeuille.
    
    Args:
        hist_data (dict): Données historiques des actions
        portfolio_df (DataFrame): DataFrame contenant les informations du portefeuille
        start_date (datetime): Date de début
        end_date (datetime): Date de fin
        
    Returns:
        DataFrame: DataFrame avec les statistiques calculées
    """
    results = []
    
    # S'assurer que start_date et end_date sont définis
    if not start_date:
        start_date = min([hist.index[0] for ticker, hist in hist_data.items() if not hist.empty], default=None)
    if not end_date:
        end_date = max([hist.index[-1] for ticker, hist in hist_data.items() if not hist.empty], default=None)
    
    if not start_date or not end_date:
        return pd.DataFrame()
    
    for ticker, hist in hist_data.items():
        if hist.empty:
            continue
            
        # Filtrer pour la période demandée
        filtered_hist = hist[(hist.index >= start_date) & (hist.index <= end_date)]
        if filtered_hist.empty or len(filtered_hist) < 2:
            continue
            
        # Calculer la performance
        initial_price = filtered_hist['Close'].iloc[0]
        final_price = filtered_hist['Close'].iloc[-1]
        
        if initial_price <= 0:
            continue
            
        percent_change = ((final_price - initial_price) / initial_price) * 100
        
        # Récupérer le nom de la société
        name = get_company_name(ticker, portfolio_df)
        
        # Récupérer les autres informations du secteur/pays si disponibles
        # Pour le moment, on les laisse vides car on se concentre sur la performance
        results.append({
            'Ticker': ticker,
            'Name': name,
            'Initial Price': initial_price,
            'Final Price': final_price,
            'Performance (%)': percent_change,
            'Weight (%)': 100.0/len(hist_data),  # Répartition équitable
            'Contribution': percent_change/len(hist_data)  # Contribution équitable
        })
    
    # Convertir en DataFrame et trier par performance
    if results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values(by='Performance (%)', ascending=False)
        return df_results
    else:
        return pd.DataFrame()

def display_top_contributors(df_perf, top_n=15):
    """
    Affiche les contributeurs positifs et négatifs.
    
    Args:
        df_perf (DataFrame): DataFrame avec les performances calculées
        top_n (int): Nombre de contributeurs à afficher
    """
    if df_perf.empty:
        st.warning("Pas assez de données pour calculer les contributeurs.")
        return
    
    # Ajouter de l'espace avant le titre
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    # Un seul titre principal
    st.markdown('<div class="section-title">Contributeurs à la performance</div>', unsafe_allow_html=True)
    
    # Ajouter un peu d'espace après le titre principal
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Séparer les contributeurs positifs et négatifs
    positive_contributors = df_perf[df_perf['Performance (%)'] > 0].head(top_n)
    negative_contributors = df_perf[df_perf['Performance (%)'] < 0].sort_values(by='Performance (%)').head(top_n)
    
    # Création des colonnes pour l'affichage
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="subsection-title">📈 TOP 15 Contributeurs Positifs</div>', unsafe_allow_html=True)
        
        if not positive_contributors.empty:
            # Créer un tableau pour les contributeurs positifs
            fig_pos = go.Figure(data=[go.Table(
                header=dict(
                    values=['<b>Ticker</b>', '<b>Nom</b>', '<b>Perf (%)</b>', '<b>Contribution</b>'],
                    font=dict(size=14, color='white'),
                    fill_color='#693112',
                    align='center',
                    height=40
                ),
                cells=dict(
                    values=[
                        positive_contributors['Ticker'],
                        positive_contributors['Name'],
                        positive_contributors['Performance (%)'].round(2),
                        positive_contributors['Contribution'].round(2)
                    ],
                    font=dict(size=13, color='#000000', weight='bold'),  # MODIFIÉ: couleur noire et gras
                    align='center',  # MODIFIÉ: toutes les colonnes centrées
                    format=[None, None, '.2f', '.2f'],
                    fill_color=['#F5F5F5'],
                    height=30
                )
            )])
            
            fig_pos.update_layout(
                margin=dict(l=5, r=5, t=5, b=5),
                height=min(40 * len(positive_contributors) + 50, 600)
            )
            
            st.plotly_chart(fig_pos, use_container_width=True)
        else:
            st.info("Aucun contributeur positif trouvé.")
    
    with col2:
        st.markdown('<div class="subsection-title">📉 TOP 15 Contributeurs Négatifs</div>', unsafe_allow_html=True)
        
        if not negative_contributors.empty:
            # Créer un tableau pour les contributeurs négatifs
            fig_neg = go.Figure(data=[go.Table(
                header=dict(
                    values=['<b>Ticker</b>', '<b>Nom</b>', '<b>Perf (%)</b>', '<b>Contribution</b>'],
                    font=dict(size=14, color='white'),
                    fill_color='#693112',
                    align='center',
                    height=40
                ),
                cells=dict(
                    values=[
                        negative_contributors['Ticker'],
                        negative_contributors['Name'],
                        negative_contributors['Performance (%)'].round(2),
                        negative_contributors['Contribution'].round(2)
                    ],
                    font=dict(size=13, color='#000000', weight='bold'),  # MODIFIÉ: couleur noire et gras
                    align='center',  # MODIFIÉ: toutes les colonnes centrées
                    format=[None, None, '.2f', '.2f'],
                    fill_color=['#F5F5F5'],
                    height=30
                )
            )])
            
            fig_neg.update_layout(
                margin=dict(l=5, r=5, t=5, b=5),
                height=min(40 * len(negative_contributors) + 50, 600)
            )
            
            st.plotly_chart(fig_neg, use_container_width=True)
        else:
            st.info("Aucun contributeur négatif trouvé.")

def create_stock_chart(hist, ticker, currency="€", period="1 an"):
    """
    Crée un graphique d'évolution du cours d'une action.
    
    Args:
        hist (DataFrame): DataFrame avec l'historique des prix
        ticker (str): Symbole de l'action
        currency (str): Symbole de la devise
        period (str): Période à afficher ("1 mois", "6 mois", "1 an")
        
    Returns:
        go.Figure: Figure Plotly avec graphique de cours
    """
    if hist.empty:
        return None
    
    # Filtrer les données selon la période sélectionnée
    if period == "1 mois":
        filtered_hist = hist.iloc[-30:]
    elif period == "6 mois":
        filtered_hist = hist.iloc[-180:]
    else:  # 1 an
        filtered_hist = hist
        
    # Calculer les statistiques
    avg_price = filtered_hist['Close'].mean()
    max_price = filtered_hist['Close'].max()
    min_price = filtered_hist['Close'].min()
        
    # Créer le graphique
    fig = go.Figure()
    
    # Ajouter la ligne de prix
    fig.add_trace(go.Scatter(
        x=filtered_hist.index,
        y=filtered_hist['Close'],
        mode='lines',
        name='Prix',
        line=dict(color='#693112', width=2)
    ))
    
    # Ajouter le volume en bas
    fig.add_trace(go.Bar(
        x=filtered_hist.index,
        y=filtered_hist['Volume'] / filtered_hist['Volume'].max() * filtered_hist['Close'].min() * 0.2,
        marker_color='rgba(105, 49, 18, 0.2)',
        name='Volume',
        yaxis='y2'
    ))
    
    # Mise en page
    fig.update_layout(
        height=450,
        margin=dict(l=0, r=0, t=10, b=10),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        yaxis=dict(
            title=f'Prix ({currency})',
            side='left',
            showgrid=True,
            gridcolor='rgba(105, 49, 18, 0.1)'
        ),
        yaxis2=dict(
            showgrid=False,
            showticklabels=False,
            overlaying='y',
            range=[0, filtered_hist['Close'].min() * 0.3]
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(105, 49, 18, 0.1)'
        ),
        plot_bgcolor='white'
    )
    
    return fig, avg_price, max_price, min_price