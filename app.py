import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# 1. Postavke stranice
st.set_page_config(page_title="Financijski Radar V5", layout="wide", initial_sidebar_state="collapsed")

# 2. Naslov i gumb za mobitele (svaki u svom redu, bez stupaca)
st.title("🚀 Moj Financijski Radar V5")

if st.button("🔄 OSVJEŽI PODATKE", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 3. Popis dionica po grupama
kat_penny = ["TMC", "TRVN", "ATOS", "GFAI", "OTLK"]
kat_catalyst = ["ASTS", "LAC", "CHPT", "NIO", "MARA"]
kat_divovi = ["PLTR", "SOFI", "HOOD", "BABA", "TSM"]

@st.cache_data(ttl=600)  # Podaci se automatski osvježavaju svakih 10 minuta ako se ne klikne gumb
def dohvati_podatke(ticker):
    try:
        dionica = yf.Ticker(ticker)
        povijest = dionica.history(period="2d")
        info = dionica.info
        
        if len(povijest) < 2:
            return None
            
        trenutna_cijena = povijest['Close'].iloc[-1]
        prethodno_zatvaranje = povijest['Close'].iloc[-2]
        postotak = ((trenutna_cijena - prethodno_zatvaranje) / prethodno_zatvaranje) * 100
        
        trenutni_volumen = povijest['Volume'].iloc[-1]
        prosjecni_volumen = info.get('averageVolume', 1)
        if prosjecni_volumen == 1:
            prosjecni_volumen = info.get('averageDailyVolume10Day', 1)
            
        volume_score = trenutni_volumen / prosjecni_volumen if prosjecni_volumen > 1 else 0
        ime = info.get('longName', ticker)
        
        return {
            "Ticker": ticker,
            "Ime Kompanije": ime,
            "Cijena ($)": round(trenutna_cijena, 3),
            "Promjena (%)": round(postotak, 2),
            "Volumen Danas": trenutni_volumen,
            "Volume Score": round(volume_score, 2)
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
        
        # Formatiranje prikaza tablice
        st.dataframe(
            df.style.format({
                "Cijena ($)": "{:.3f}",
                "Promjena (%)": "{:+.2f}%",
                "Volumen Danas": "{:,}",
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
    else:
        st.warning("Nije moguće učitati podatketrace za ove dionice u ovom trenutku.")

# TABS (Kartice) sučelje
tab1, tab2, tab3 = st.tabs(["💰 Penny / Mali Radari", "⚡ Catalyst Dionice", "🏛️ Globalni Divovi"])

with tab1:
    st.header("Popis malih potencijala i TMC")
    prikazi_tablicu_i_graf(kat_penny, "graf_penny")

with tab2:
    st.header("Dionice s jakim katalizatorima vijesti")
    prikazi_tablicu_i_graf(kat_catalyst, "graf_cat")

with tab3:
    st.header("Velike stabilne kompanije i HOOD")
    prikazi_tablicu_i_graf(kat_divovi, "graf_div")
