import streamlit as st

def display_metrics_table(metrics_df):
    """Affiche le tableau détaillé des métriques"""
    st.markdown("<h3 style='color: #102040;'>Tableau détaillé des valeurs</h3>", unsafe_allow_html=True)
    
    st.dataframe(
        metrics_df.style.format({
            col: '{:.2f}' for col in metrics_df.select_dtypes(include=['float64']).columns
        }).set_properties(**{
            'color': '#000000', 
            'text-align': 'center',
            'font-weight': 'bold'
        }).set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center'), ('color', '#000000'), ('background-color', '#E5E9F0'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('text-align', 'center'), ('background-color', '#F0F0F0')]}
        ]),
        use_container_width=True,
        height=600,
        key="metrics_table"
    )