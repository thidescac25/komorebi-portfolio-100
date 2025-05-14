def format_number_with_spaces(number):
    """Formate un nombre avec des espaces comme séparateurs de milliers (format européen)"""
    return f"{number:_.0f}".replace("_", " ")
    
def get_currency_from_ticker(ticker):
    """Détermine la devise en fonction du suffixe du ticker"""
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