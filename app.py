import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from textblob import TextBlob

# 1. Postavke stranice
st.set_page_config(page_title="AI Financijski Terminal V15", layout="wide", initial_sidebar_state="collapsed")

# Naslov aplikacije
st.title("📊 AI Financijski Terminal V15")
st.write("Dobrodošli natrag! Vaša stabilna verzija za analizu dionica je spremna.")

# --- POMOĆNE FUNKCIJE ---
def dohvati_podatke(ticker, period="1y"):
    try:
        dionica = yf.Ticker(ticker)
        povijest = dionica.history(period=period)
        info = dionica.info
        return povijest, info
    except Exception as e:
        st.error(f"Greška pri dohvaćanju podataka za {ticker}: {e}")
        return pd.DataFrame(), {}

def analiziraj_sentiment(tekst):
    if not tekst:
        return 0.0
    analiza = TextBlob(tekst)
    return analiza.sentiment.polarity

# --- GLAVNI DEO APLIKACIJE ---
# Sidebar za unos dionice
st.sidebar.header("Postavke pretraživanja")
odabrani_ticker = st.sidebar.text_input("Unesite oznaku dionice (npr. AAPL, TSLA, GOOG):", value="AAPL").upper()
vremenski_period = st.sidebar.selectbox("Period grafokona:", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)

if odabrani_ticker:
    with st.spinner(f"Učitavam podatke za {odabrani_ticker}..."):
        df, info_podaci = dohvati_podatke(odabrani_ticker, vremenski_period)
        
    if not df.empty:
        # Metrike na vrhu ekrana
        trenutna_cijena = info_podaci.get('currentPrice', df['Close'].iloc[-1])
        valuta = info_podaci.get('currency', 'USD')
        ime_tvrtke = info_podaci.get('longName', odabrani_ticker)
        
        st.subheader(f"Pregled za tvrtku: {ime_tvrtke} ({odabrani_ticker})")
        
        kol1, kol2, kol3 = st.columns(3)
        with kol1:
            st.metric("Trenutna cijena", f"{trenutna_cijena:.2f} {valuta}")
        with kol2:
            promjena = df['Close'].iloc[-1] - df['Close'].iloc[-2]
            postotak = (promjena / df['Close'].iloc[-2]) * 100
            st.metric("Dnevna promjena", f"{promjena:.2f} {valuta}", f"{postotak:.2f}%")
        with kol3:
            st.metric("Volumen trgovanja", f"{df['Volumen'].iloc[-1]:,}" if 'Volumen' in df.columns else f"{df['Volume'].iloc[-1]:,}")

        # Grafikon kretanja cijene
        st.write("### Kretanje cijene zatvaranja (Close)")
        fig = px.line(df, x=df.index, y='Close', title=f"Grafikon cijene za {odabrani_ticker} ({vremenski_period})")
        fig.update_xaxes(title_text="Datum")
        fig.update_yaxes(title_text=f"Cijena ({valuta})")
        st.plotly_chart(fig, use_container_width=True)

        # Tablica s povijesnim podacima
        st.write("### Povijesni podaci (Zadnjih nekoliko dana)")
        st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True)
        
        # AI Kratka analiza (Sentiment)
        st.write("### 🤖 AI Analiza Sentimenta")
        opis_tvrtke = info_podaci.get('longBusinessSummary', '')
        if opis_tvrtke:
            st.write("**Opis poslovanja tvrtke:**")
            st.info(opis_tvrtke[:500] + "...") # Prikazujemo samo dio opisa radi preglednosti
            
            # Izračun bazičnog sentimenta opisa tvrtke kao primjer
            ocjena_sentimenta = analiziraj_sentiment(opis_tvrtke)
            if ocjena_sentimenta > 0:
                st.success(f"Sentiment opisa tvrtke je pozitivan ({ocjena_sentimenta:.2f}).")
            elif ocjena_sentimenta < 0:
                st.warning(f"Sentiment opisa tvrtke je oprezan/negativan ({ocjena_sentimenta:.2f}).")
            else:
                st.view("Sentiment je neutralan.")
        else:
            st.write("Opis tvrtke trenutno nije dostupan za AI analizu.")
    else:
        st.warning(f"Nije moguće pronaći podatke za ticker '{odabrani_ticker}'. Provjerite jeste li upisali ispravnu oznaku.")
