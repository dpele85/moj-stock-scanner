import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from textblob import TextBlob

# 1. Postavke stranice
st.set_page_config(page_title="AI Financijski Radar V7", layout="wide", initial_sidebar_state="collapsed")

# 2. Naslov i gumb za osvježavanje
st.title("🤖 Moj AI Financijski Radar V7")
st.caption("Sustav automatski analizira tehničke podatke i koristi NLP umjetnu inteligenciju za ocjenu sentimenta vijesti.")

if st.button("🔄 OSVJEŽI SVE PODATKE I AI SENTIMENT", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 3. Popis imovine po grupama
kat_makro = ["GC=F", "CL=F"]
kat_penny = ["TMC", "TRVN", "ATOS", "GFAI", "OTLK"]
kat_catalyst = ["ASTS", "LAC", "CHPT", "NIO", "MARA"]
kat_divovi = ["PLTR", "SOFI", "HOOD", "BABA", "TSM"]

imena_makro = {"GC=F": "Zlato (Gold Futures)", "CL=F": "Sirova Nafta (Crude Oil)"}

# Pomoćna AI funkcija za analizu teksta
def analiziraj_sentiment(tekst):
    if not tekst or tekst == "Nema naslova":
        return 0, "🟡 Neutralno"
    analysis = TextBlob(tekst)
    score = analysis.sentiment.polarity # Vraća broj od -1 (skroz negativno) do +1 (skroz pozitivno)
    
    if score > 0.05:
        return score, "🟢 Bullish (Pozitivno)"
    elif score < -0.05:
        return score, "🔴 Bearish (Negativno)"
    else:
        return score, "🟡 Neutralno"

@st.cache_data(ttl=600)
def dohvati_podatke(ticker):
    try:
        dionica = yf.Ticker(ticker)
        povijest = dionica.history(period="5d")
        
        if len(povijest) < 2:
            return None
            
        trenutna_cijena = povijest['Close'].iloc[-1]
        prethodno_zatvaranje = povijest['Close'].iloc[-2]
        postotak = ((trenutna_cijena - prethodno_zatvaranje) / prethodno_zatvaranje) * 100
        
        trenutni_volumen = povijest['Volume'].iloc[-1]
        info = dionica.info
        prosjecni_volumen = info.get('averageVolume', 1)
        if prosjecni_volumen == 1:
            prosjecni_volumen = info.get('averageDailyVolume10Day', 1)
            
        volume_score = trenutni_volumen / prosjecni_volumen if prosjecni_volumen > 1 else 0
        
        if ticker in imena_makro:
            ime = imena_makro[ticker]
        else:
            ime = info.get('longName', ticker)
        
        # Izvlačenje vijesti i AI analiza
        pokupljene_vijesti = []
        ukupni_sentiment_score = 0
        broj_vijesti = 0
        
        try:
            vijesti_izvor = dionica.news
            if vijesti_izvor:
                for v in vijesti_izvor[:3]:
                    naslov = v.get('title', 'Nema naslova')
                    izvor = v.get('publisher', 'Nepoznato')
                    link = v.get('link', '#')
                    
                    # Pokreni AI analizu na naslovu vijesti
                    score, oznaka = analiziraj_sentiment(naslov)
                    ukupni_sentiment_score += score
                    broj_vijesti += 1
                    
                    pokupljene_vijesti.append({
                        "naslov": naslov, 
                        "izvor": izvor, 
                        "link": link,
                        "ai_oznaka": oznaka
                    })
        except:
            pass
        
        # Konačna AI ocjena za cijelu dionicu
        if broj_vijesti > 0:
            prosjek = ukupni_sentiment_score / broj_vijesti
            if prosjek > 0.05:
                konacni_sentiment = "🟢 POZITIVAN"
            elif prosjek < -0.05:
                konacni_sentiment = "🔴 NEGATIVAN"
            else:
                konacni_sentiment = "🟡 NEUTRALAN"
        else:
            konacni_sentiment = "🟡 Nema vijesti (Vikend)"
            
        return {
            "Ticker": ticker,
            "Ime Kompanije": ime,
            "Cijena ($)": round(trenutna_cijena, 3),
            "Promjena (%)": round(postotak, 2),
            "Volume Score": round(volume_score, 2),
            "AI Sentiment": konacni_sentiment,
            "Vijesti": pokupljene_vijesti
        }
    except:
        return None

def prikazi_tablicu_i_graf(lista_tickera, kljuc_grafikona):
    podaci_lista = []
    for t in lista_tickera:
        rezultat = dohvati_podatke(t)
        if rezultat:
            podaci_lista.append(rezultat)
            
    if podaci_lista:
        df = pd.DataFrame(podaci_lista)
        
        # Prikaz tablice u kojoj je sada ugrađen i AI stupac!
        prikaz_df = df.drop(columns=["Vijesti"])
        st.dataframe(
            prikaz_df.style.format({
                "Cijena ($)": "{:.3f}",
                "Promjena (%)": "{:+.2f}%",
                "Volume Score": "{:.2f}x"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Grafikon volumena
        fig = px.bar(
            df, 
            x="Ticker", 
            y="Volume Score", 
            text="Volume Score",
            title="Snaga Volumena (Sve preko 1.00x je pojačani interes)",
            labels={"Volume Score": "Koliko puta veći volumen od prosjeka"},
            color="Volume Score",
            color_continuous_scale="Viridis"
        )
        fig.update_traces(texttemplate='%{text}x', textposition='outside')
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Prosjek (1x)")
        st.plotly_chart(fig, use_container_width=True, key=kljuc_grafikona)
        
        # AI Sekcija za detaljne vijesti
        st.subheader("📰 AI Analiza pojedinačnih vijesti:")
        ima_vijesti = False
        for stavka in podaci_lista:
            if stavka["Vijesti"]:
                ima_vijesti = True
                with st.expander(f"AI Analiza za {stavka['Ticker']} ({stavka['Ime Kompanije']})"):
                    for v in stavka["Vijesti"]:
                        st.markdown(f"**[{v['naslov']}]({v['link']})**")
                        st.write(f"🕵️‍♂️ **AI Ocjena ove vijesti:** {v['ai_oznaka']}")
                        st.caption(f"Izvor: {v['izvor']}")
                        st.write("---")
        if not ima_vijesti:
            st.info("Trenutno nema novih vijesti za analizu (vikend ili nema objava).")
    else:
        st.warning("Nije moguće učitati podatke.")

# TABS sučelje
tab0, tab1, tab2, tab3 = st.tabs(["🌍 Geopolitika & Makro (Zlato/Nafta)", "💰 Penny / Mali Radari", "⚡ Catalyst Dionice", "🏛️ Globalni Divovi"])

with tab0:
    st.header("Zlato i Nafta (Glavni obrambeni instrumenti)")
    prikazi_tablicu_i_graf(kat_makro, "graf_makro")

with tab1:
    st.header("Popis malih potencijala i TMC")
    prikazi_tablicu_i_graf(kat_penny, "graf_penny")

with tab2:
    st.header("Dionice s jakim katalizatorima vijesti")
    prikazi_tablicu_i_graf(kat_catalyst, "graf_cat")

with tab3:
    st.header("Velike stabilne kompanije i HOOD")
    prikazi_tablicu_i_graf(kat_divovi, "graf_div")
