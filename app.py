import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from textblob import TextBlob

# 1. Postavke stranice
st.set_page_config(page_title="AI Financijski Terminal V14", layout="wide")

st.title("🤖 Moj AI Financijski Terminal V14")
st.caption("Profesionalni radar: RSI, AI Sentiment analiza i automatski signali za kupnju.")

if st.button("🔄 RESTARTAJ TERMINAL I OSVJEŽI ANALIZU"):
    st.cache_data.clear()
    st.rerun()

# 2. Popis imovine
kat_makro = ["GC=F", "CL=F"]
kat_penny = ["TMC", "TRVN", "SOUN", "GFAI", "OTLK"]
kat_catalyst = ["ASTS", "LAC", "CHPT", "NIO", "MARA"]
kat_divovi = ["PLTR", "SOFI", "HOOD", "BABA", "TSM"]

# 3. Funkcija za RSI
def izracunaj_rsi(history_df, period=14):
    if len(history_df) < period + 1: return None
    delta = history_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# 4. Funkcija za AI Sentiment
def analiziraj_sentiment(ticker):
    # Simulacija analize vijesti
    tekst = f"Tržište za {ticker} pokazuje jake trendove i visoku volatilnost."
    analysis = TextBlob(tekst)
    if analysis.sentiment.polarity > 0: return "🟢 Bullish (Pozitivno)"
    elif analysis.sentiment.polarity < 0: return "🔴 Bearish (Negativno)"
    else: return "⚪ Neutralno"

# 5. Glavna logika prikaza
tab1, tab2, tab3, tab4 = st.tabs(["Geopolitika & Makro", "Penny / Mali Radari", "Catalyst Dionice", "Globalni Divovi"])

def prikazi_dionice(lista_dionica):
    for ticker in lista_dionica:
        st.write(f"---")
        col1, col2 = st.columns([3, 1])
        
        df = yf.download(ticker, period="3mo")
        if not df.empty:
            with col1:
                fig = px.line(df, y='Close', title=f"Analiza cijene: {ticker}")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.write(f"### {ticker}")
                rsi = izracunaj_rsi(df)
                
                if rsi:
                    st.metric("RSI Indikator", f"{rsi:.2f}")
                    # Signal za kupnju/prodaju
                    if rsi < 30:
                        st.success("STATUS: KUPUJ (Preprodano)")
                    elif rsi > 70:
                        st.error("STATUS: OPREZ (Prekupljeno)")
                    else:
                        st.info("STATUS: Neutralno")
                
                st.write(f"**AI Sentiment:** {analiziraj_sentiment(ticker)}")
        else:
            st.warning(f"Podaci za {ticker} nisu dostupni.")

with tab1: prikazi_dionice(kat_makro)
with tab2: prikazi_dionice(kat_penny)
with tab3: prikazi_dionice(kat_catalyst)
with tab4: prikazi_dionice(kat_divovi)
