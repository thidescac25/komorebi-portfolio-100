import base64
import streamlit as st
from utils.data_loader import get_all_stock_data

def create_scrolling_ticker(portfolio_df, currency_mapping):
    """Crée un bandeau défilant avec les données des actions en temps réel"""
    all_stock_data = get_all_stock_data(portfolio_df['ticker'].tolist())
    ticker_items = ""
    
    for _, row in portfolio_df.iterrows():
        stock_data = all_stock_data.get(row['ticker'])
        if not stock_data or not stock_data['valid']:
            continue
            
        ticker = row['ticker']
        currency = currency_mapping.get(ticker, "$")
        
        if stock_data['change'] >= 0:
            change_class = "positive"
            arrow = '<span style="font-size: 22px;">&#x25B2;</span>'
        else:
            change_class = "negative"
            arrow = '<span style="font-size: 22px;">&#x25BC;</span>'
        
        ticker_items += f"""
        <div class="ticker-item">
            <span class="ticker-name">{row['name']}</span>
            <span class="ticker-price">{currency}{stock_data['current_price']:.2f}</span>
            <span class="ticker-change {change_class}">{arrow} {stock_data['percent_change']:.2f}%</span>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background-color: #102040;
                font-family: Arial, sans-serif;
            }}
            .ticker-container {{
                width: 100%;
                overflow: hidden;
                white-space: nowrap;
                padding: 10px 0;
            }}
            .ticker-tape {{
                display: inline-block;
                animation: ticker-scroll 1300s linear infinite;
                padding-left: 100%;
            }}
            .ticker-item {{
                display: inline-block;
                padding: 0 50px;
                color: white;
                font-size: 20px;
            }}
            .ticker-name {{
                font-weight: bold;
                margin-right: 15px;
            }}
            .ticker-price {{
                margin-right: 15px;
            }}
            .positive {{
                color: #00ff00;
                font-weight: bold;
                font-size: 20px;
            }}
            .negative {{
                color: #ff4d4d;
                font-weight: bold;
                font-size: 20px;
            }}
            @keyframes ticker-scroll {{
                0% {{ transform: translate3d(0, 0, 0); }}
                100% {{ transform: translate3d(-100%, 0, 0); }}
            }}
        </style>
    </head>
    <body>
        <div class="ticker-container">
            <div class="ticker-tape">
                {ticker_items}
                {ticker_items}
            </div>
        </div>
    </body>
    </html>
    """
    
    b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    iframe_html = f'<iframe src="data:text/html;base64,{b64}" width="100%" height="50px" frameborder="0" scrolling="no"></iframe>'
    return iframe_html