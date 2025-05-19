# Komorebi Portfolio 100

## Description
Application de suivi de performance pour un portefeuille de 100 actions diversifiées à travers le monde. Développée avec Streamlit et Python, avec une architecture modulaire optimisée.

## Fonctionnalités
- Bandeau défilant interactif avec les 100 valeurs en temps réel
- Performance comparative avec différents indices boursiers (CAC 40, S&P 500, NASDAQ, EURO STOXX 50)
- Simulation d'investissement de 1 000 000 € réparti équitablement
- Identification des meilleurs et pires contributeurs à la performance
- Visualisation de la répartition sectorielle et géographique du portefeuille
- Liste complète des 100 valeurs organisée par pays
- Tableau France complet en dernière position sans scroll interne

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py

Architecture
KOMOREBI INVEST 100/
├── app.py      # Fichier principal de l'application
├── src/                          # Modules modulaires
│   ├── data_loader.py           # Chargement des données boursières
│   ├── stock_utils.py           # Utilitaires devises et formatage
│   ├── ui_components.py         # Composants interface (bandeau, CSS)
│   └── visualization.py         # Graphiques et analyses
├── data/
│   └── Portefeuille_100_business_models.csv  # Données du portefeuille
└── requirements.txt

Données
L'application utilise l'API yfinance pour récupérer les données boursières en temps réel avec une mise à jour automatique toutes les 60 secondes.
Fonctionnalités techniques

Cache intelligent pour optimiser les performances
Style identique au portefeuille 55 valeurs Komorebi
Interface responsive adaptée aux grands écrans
Chargement parallèle des données pour 100 valeurs
Support multi-devises automatique par suffixe ticker

Version en ligne
Une version déployée est disponible sur Streamlit Cloud.

Auteur 
Thierry