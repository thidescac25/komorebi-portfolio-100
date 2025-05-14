import streamlit as st
import plotly.express as px
from utils.data_loader import load_sector_country_data

def display_portfolio_allocation(tickers):
    """Affiche les graphiques de répartition sectorielle et géographique"""
    # Charger les données secteur/pays
    df_sc = load_sector_country_data(tickers)
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