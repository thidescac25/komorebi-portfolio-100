# stock_utils.py

# Utilitaires pour la gestion des devises et autres fonctions boursières

# Mapping des devises pour chaque ticker
def get_currency_mapping():
    """
    Retourne un dictionnaire de mapping entre tickers et devises.
    Se base sur les suffixes des tickers pour déterminer la devise.
    """
    # Cette fonction sera utilisée avec determine_currency pour un mapping dynamique
    # Pas besoin d'un mapping statique, on utilise la logique des suffixes
    return {}

def determine_currency(ticker):
    """
    Détermine la devise d'un titre en fonction de son suffixe ou du ticker spécifique.
    
    Args:
        ticker (str): Symbole du titre
        
    Returns:
        str: Symbole de devise
    """
    # Cas spécifiques pour certaines actions
    specific_tickers = {
        '005830.KS': '₩',  # Actions coréennes spécifiques
        '005380.KS': '₩',  
        'MQG.AX': 'A$',    # Macquarie Group
    }
    
    if ticker in specific_tickers:
        return specific_tickers[ticker]
    
    # Pour les tickers avec extensions spécifiques (logique du projet actuel)
    if ticker.endswith('.PA'):      # Actions françaises
        return "€"
    elif ticker.endswith('.L'):     # Actions britanniques  
        return "£"
    elif ticker.endswith('.SW'):    # Actions suisses
        return "CHF"
    elif ticker.endswith('.DE'):    # Actions allemandes
        return "€"
    elif ticker.endswith('.T'):     # Actions japonaises
        return "¥"
    elif ticker.endswith('.AX'):    # Actions australiennes
        return "A$"
    elif ticker.endswith('.NS'):    # Actions indiennes
        return "₹"
    elif ticker.endswith('.KS'):    # Actions coréennes
        return "₩"
    elif ticker.endswith('.BR'):    # Actions belges
        return "€"
    elif ticker.endswith('.MC'):    # Actions espagnoles
        return "€"
    elif ticker.endswith('.CO'):    # Actions danoises
        return "DKK"
    elif ticker.endswith('.OL'):    # Actions norvégiennes
        return "NOK"
    elif ticker.endswith('.LU'):    # Actions luxembourgeoises
        return "€"
    elif ticker.endswith('.ST'):    # Actions suédoises
        return "SEK"
    elif ticker.endswith('.HK'):    # Actions de Hong Kong
        return "HK$"
    elif ticker.endswith('.SS') or ticker.endswith('.SZ'):  # Actions chinoises
        return "¥"
    elif ticker.endswith('.AS'):    # Actions néerlandaises
        return "€"
    elif ticker.endswith('.MI'):    # Actions italiennes
        return "€"
    # Actions américaines (sans suffixe ou avec .N, .O, etc.)
    elif '.' not in ticker or ticker.endswith('.N') or ticker.endswith('.O'):
        return "$"
    # Cas par défaut
    else:
        return "$"

# Rendements des dividendes par société (optionnel - peut être étendu si nécessaire)
def get_dividend_yields():
    """
    Retourne un dictionnaire des rendements de dividendes manuels.
    Pour le moment, retourne un dictionnaire vide - les dividendes
    sont récupérés via yfinance dans data_loader.py
    """
    return {}

# Fonction pour formatter les valeurs monétaires
def format_currency(value, currency="€"):
    """
    Formate une valeur monétaire avec le symbole de devise approprié.
    
    Args:
        value (float): Valeur à formater
        currency (str): Symbole de la devise ($, €, £, CHF, etc.)
        
    Returns:
        str: Valeur formatée avec devise
    """
    if currency in ["$", "€", "£"]:
        return f"{currency}{value:,.2f}".replace(',', ' ')  # Espaces comme séparateurs
    else:
        return f"{value:,.2f} {currency}".replace(',', ' ')

# Fonction pour formatter les pourcentages
def format_percentage(value, include_sign=True):
    """
    Formate une valeur en pourcentage.
    
    Args:
        value (float): Valeur à formater
        include_sign (bool): Inclure le signe + pour les valeurs positives
        
    Returns:
        str: Valeur formatée en pourcentage
    """
    sign = "+" if value > 0 and include_sign else ""
    return f"{sign}{value:.2f}%"

# Fonction pour formatter les nombres avec espaces (style européen)
def format_number_with_spaces(number):
    """
    Formate un nombre avec des espaces comme séparateurs de milliers (format européen).
    
    Args:
        number (int/float): Nombre à formater
        
    Returns:
        str: Nombre formaté avec espaces
    """
    return f"{number:_.0f}".replace("_", " ")

# Fonction utilitaire pour obtenir le nom de la société depuis le portfolio
def get_company_name(ticker, portfolio_df):
    """
    Récupère le nom de la société à partir du ticker.
    
    Args:
        ticker (str): Symbole de l'action
        portfolio_df (DataFrame): DataFrame du portefeuille
        
    Returns:
        str: Nom de la société ou ticker si non trouvé
    """
    company_row = portfolio_df[portfolio_df['ticker'] == ticker]
    if not company_row.empty and 'name' in company_row.columns:
        return company_row.iloc[0]['name']
    return ticker

# Fonction utilitaire pour calculer les métriques de base
def calculate_change_metrics(current_price, previous_close):
    """
    Calcule le changement absolu et en pourcentage.
    
    Args:
        current_price (float): Prix actuel
        previous_close (float): Prix de clôture précédent
        
    Returns:
        tuple: (changement absolu, changement en pourcentage)
    """
    change = current_price - previous_close
    percent_change = (change / previous_close) * 100 if previous_close else 0
    return change, percent_change

# Constantes utiles
BOURSES_MAPPING = {
    '.PA': 'Euronext Paris',
    '.L': 'London Stock Exchange',
    '.SW': 'SIX Swiss Exchange',
    '.DE': 'XETRA',
    '.T': 'Tokyo Stock Exchange',
    '.AX': 'Australian Securities Exchange',
    '.NS': 'National Stock Exchange of India',
    '.KS': 'Korea Exchange',
    '.BR': 'Euronext Brussels',
    '.MC': 'Bolsa de Madrid',
    '.CO': 'Nasdaq Copenhagen',
    '.OL': 'Oslo Børs',
    '.LU': 'Bourse de Luxembourg',
    '.ST': 'Nasdaq Stockholm',
    '.HK': 'Hong Kong Stock Exchange',
    '.SS': 'Shanghai Stock Exchange',
    '.SZ': 'Shenzhen Stock Exchange',
    '.AS': 'Euronext Amsterdam',
    '.MI': 'Borsa Italiana'
}

def get_exchange_name(ticker):
    """
    Retourne le nom de la bourse à partir du ticker.
    
    Args:
        ticker (str): Symbole de l'action
        
    Returns:
        str: Nom de la bourse
    """
    for suffix, exchange in BOURSES_MAPPING.items():
        if ticker.endswith(suffix):
            return exchange
    return 'NASDAQ/NYSE'  # Par défaut pour les actions américaines

# Mapping des suffixes de ticker vers les pays
TICKER_COUNTRY_MAPPING = {
    '.PA': 'France',
    '.L': 'Royaume-Uni', 
    '.SW': 'Suisse',
    '.DE': 'Allemagne',
    '.T': 'Japon',
    '.AX': 'Australie',
    '.NS': 'Inde',
    '.KS': 'Corée du Sud',
    '.BR': 'Belgique',
    '.MC': 'Espagne',
    '.CO': 'Danemark',
    '.OL': 'Norvège',
    '.LU': 'Luxembourg',
    '.ST': 'Suède',
    '.HK': 'Hong Kong',
    '.SS': 'Chine',
    '.SZ': 'Chine',
    '.AS': 'Pays-Bas',
    '.MI': 'Italie'
}

def get_country_from_ticker(ticker):
    """
    Retourne le pays à partir du suffixe du ticker.
    
    Args:
        ticker (str): Symbole de l'action
        
    Returns:
        str: Nom du pays
    """
    for suffix, country in TICKER_COUNTRY_MAPPING.items():
        if ticker.endswith(suffix):
            return country
    return 'États-Unis'  # Par défaut pour les actions américaines