import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from textblob import TextBlob

# 1. Postavke stranice
st.set_page_config(page_title="AI Financijski Terminal V8", layout="wide", initial_sidebar_state="collapsed")

# 2. Naslov i gumb za osvježavanje
st.title("🤖 Moj AI Financijski Terminal V8")
st.caption("Profesionalni radar s ugrađenim RSI indikatorom, 52-tjednim rasponom i AI generiranim signalima za trgovanje.")

if st.button("🔄 RESTARTAJ TERMINAL I OSVJEŽI ANALIZU", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 3. Popis imovine po grupama
kat_makro = ["GC=F", "CL=F"]
kat_penny = ["TMC", "TRVN", "ATOS", "GFAI", "OTLK"]
kat_catalyst = ["ASTS", "LAC", "CHPT", "NIO", "MARA"]
kat_divovi = ["PLTR", "SOFI", "HOOD", "BABA", "TSM"]

imena_makro = {"GC=F": "Zlato (Gold Futures)", "CL=F": "Sirova Nafta (Crude Oil)"}

# Funkcija za izračun RSI indikatora
def izracunaj_rsi(history_df, period=14):
    if len(history_df) < period + 1:
        return None
    delta = history_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Izbjegavanje dijeljenja s nulom
    rs = gain / loss
    rs = rs.fillna(0)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# Pomoćna AI funkcija za analizu teksta
def analiziraj_sentiment(tekst):
    if not tekst or tekst == "Nema naslova" or "Tržište miruje" in tekst:
        return 0, "🟡 Neutralno"
    analysis = TextBlob(tekst)
    score = analysis.sentiment.polarity
    
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
        # Uzimamo zadnjih 30 dana kako bismo imali dovoljno podataka za stabilan RSI (14)
        povijest = dionica.history(period="30d")
        
        if len(povijest) < 15:
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
        
        # Izračun RSI-ja
        rsi_vrijednost = izracunaj_rsi(povijest)
        
        # Izvlačenje 52-tjednog raspona
        low_52 = info.get('fiftyTwoWeekLow', trenutna_cijena)
        high_52 = info.get('fiftyTwoWeekHigh', trenutna_cijena)
        raspon_52 = f"${round(low_52, 2)} - ${round(high_52, 2)}"
        
        if ticker in imena_makro:
            ime = imena_makro[ticker]
        else:
            ime = info.get('longName', ticker)
        
        # Izvlačenje vijesti i AI analiza
        pokupljene_vijesti = []
        ukupni_sentiment_score = 0
        broj_pravih_vijesti = 0
        
        try:
            vijesti_izvor = dionica.news
            if vijesti_izvor and len(vijesti_izvor) > 0:
                for v in vijesti_izvor[:3]:
                    naslov = v.get('title', '').strip()
                    izvor = v.get('publisher', 'Nepoznato')
                    link = v.get('link', '#')
                    
                    if naslov and naslov != "Nema naslova" and izvor != "Nepoznato":
                        score, oznaka = analiziraj_sentiment(naslov)
                        ukupni_sentiment_score += score
                        broj_pravih_vijesti += 1
                        pokupljene_vijesti.append({
                            "naslov": naslov, 
                            "izvor": izvor, 
                            "link": link,
                            "ai_oznaka": oznaka
                        })
        except:
            pass
        
        if len(pokupljene_vijesti) == 0:
            pokupljene_vijesti.append({
                "naslov": "Tržište trenutno miruje. Nove AI vijesti stižu s otvaranjem burze.",
                "izvor": "Sustav Radara",
                "link": "#",
                "ai_oznaka": "🟡 Neutralno (Čekanje)"
            })
        
        # Određivanje konačnog AI sentimenta tekstualno
        if broj_pravih_vijesti > 0:
            prosjek = ukupni_sentiment_score / broj_pravih_vijesti
            konacni_sentiment = "🟢 POZITIVAN" if prosjek > 0.05 else ("🔴 NEGATIVAN" if prosjek < -0.05 else "🟡 NEUTRALAN")
        else:
            konacni_sentiment = "⏳ ČEKAM"
            
        # LOGIKA ZA AUTOMATSKI AI STATUS (GENERIRANJE SIGNALA)
        if rsi_vrijednost is not None:
            if rsi_vrijednost < 32 and (konacni_sentiment == "🟢 POZITIVAN" or volume_score > 1.2):
                status = "🔥 SIGNAL KUPNJE"
            elif rsi_vrijednost > 70:
                status = "⚠️ RISK (PREKUPLJENO)"
            elif rsi_vrijednost < 35:
                status = "🛒 JEFTINO (PRATI)"
            elif volume_score > 2.0 and postotak > 2:
                status = "🚀 PROBOJ (BREAKOUT)"
            else:
                status = "⏳ PROMATRAJ"
        else:
            status = "⏳ ČEKAM PODATKE"
            
        rsi_prikaz = round(rsi_vrijednost, 1) if rsi_vrijednost is not None else "N/A"
        
        return {
            "Ticker": ticker,
            "Ime Kompanije": ime,
            "Cijena ($)": round(trenutna_cijena, 3),
            "Promjena (%)": round(postotak, 2),
            "Volume Score": round(volume_score, 2),
            "RSI (14)": rsi_prikaz,
            "AI Sentiment": konacni_sentiment,
            "AI Status": status,
            "52-Tjedni Raspon": raspon_52,
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
        
        # Reorganizacija stupaca za maksimalnu preglednost na mobitelu
        stupci_za_prikaz = ["Ticker", "Cijena ($)", "Promjena (%)", "Volume Score", "RSI (14)", "AI Status", "52-Tjedni Raspon"]
        prikaz_df = df[stupci_za_prikaz]
        
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
        for stavka in podaci_lista:
            if stavka["Vijesti"]:
                with st.expander(f"AI Analiza za {stavka['Ticker']} ({stavka['Ime Kompanije']})"):
                    for v in stavka["Vijesti"]:
                        if v['link'] != "#":
                            st.markdown(f"**[{v['naslov']}]({v['link']})**")
                        else:
                            st.markdown(f"**{v['naslov']}**")
                        st.write(f"🕵️‍♂️ **AI Ocjena:** {v['ai_oznaka']}")
                        st.caption(f"Izvor: {v['izvor']}")
                        st.write("---")
    else:
        st.warning("Nije moguće učitati podatke.")

# TABS sučelje
tab0, tab1, tab2, tab3 = st.tabs(["🌍 Geopolitika & Makro", "💰 Penny / Mali Radari", "⚡ Catalyst Dionice", "🏛️ Globalni Divovi"])

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
