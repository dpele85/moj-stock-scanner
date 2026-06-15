import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from textblob import TextBlob
from streamlit_gsheets import GSheetsConnection

# 1. Postavke stranice
st.set_page_config(page_title="AI Financijski Terminal V15", layout="wide", initial_sidebar_state="collapsed")

# --- SPAJANJE NA GOOGLE SHEETS BAZU ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Greška s povezivanjem na Google Sheets. Provjeri Secrets! Detalji: {e}")

# Pomoćne funkcije za čitanje i pisanje u Google Sheets
def ucitaj_list(ime_lista):
    try:
        df = conn.read(worksheet=ime_lista, ttl=0)
        if df.empty or df.dropna(how='all').empty:
            return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

def spremi_u_list(df, ime_lista):
    try:
        conn.update(worksheet=ime_lista, data=df)
    except Exception as e:
        st.error(f"Nije uspjelo spremanje u Google Sheets: {e}")

# Inicijalizacija privremene radne memorije iz Google tablice
if "kupljene_dionice" not in st.session_state:
    st.session_state.kupljene_dionice = {}
    df_port = ucitaj_list("Portfolio")
    if not df_port.empty and "Ticker" in df_port.columns:
        for _, red in df_port.iterrows():
            st.session_state.kupljene_dionice[red["Ticker"]] = {
                "ulazna_cijena": float(red["Ulazna Cijena"]),
                "ulozeno_novca": float(red["Ulozeno Novca"])
            }

if "povijest_trejdova" not in st.session_state:
    df_hist = ucitaj_list("Povijest")
    if not df_hist.empty:
        st.session_state.povijest_trejdova = df_hist.to_dict(orient="records")
    else:
        st.session_state.povijest_trejdova = []
# -----------------------------------------------------

# 2. Naslov i gumb za osvježavanje
st.title("🤖 Moj AI Financijski Terminal V15")
st.caption("Profesionalni radar s trajnom Google Sheets memorijom i kalkulatorom profita uživo.")

if st.button("🔄 RESTARTAJ TERMINAL I OSVJEŽI ANALIZU", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 3. Popis imovine po grupama
kat_makro = ["GC=F", "CL=F"]
kat_penny = ["TMC", "TRVN", "SOUN", "GFAI", "OTLK"]
kat_catalyst = ["ASTS", "LAC", "CHPT", "NIO", "MARA"]
kat_divovi = ["PLTR", "SOFI", "HOOD", "BABA", "TSM"]

imena_makro = {"GC=F": "Zlato (Gold Futures)", "CL=F": "Sirova Nafta (Crude Oil)"}

def izracunaj_rsi(history_df, period=14):
    if len(history_df) < period + 1:
        return None
    delta = history_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rs = rs.fillna(0)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

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

@st.cache_data(ttl=300)
def dohvati_podatke(ticker):
    try:
        dionica = yf.Ticker(ticker)
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
        rsi_vrijednost = izracunaj_rsi(povijest)
        
        low_52 = info.get('fiftyTwoWeekLow', trenutna_cijena)
        high_52 = info.get('fiftyTwoWeekHigh', trenutna_cijena)
        raspon_52 = f"${round(low_52, 2)} - ${round(high_52, 2)}"
        
        if ticker in imena_makro:
            ime = imena_makro[ticker]
        else:
            ime = info.get('longName', ticker)
        
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
                        pokupljene_vijesti.append({"naslov": naslov, "izvor": izvor, "link": link, "ai_oznaka": oznaka})
        except:
            pass
        
        if len(pokupljene_vijesti) == 0:
            pokupljene_vijesti.append({
                "naslov": "Tržište trenutno miruje. Nove AI vijesti stižu s otvaranjem burze.",
                "izvor": "Sustav Radara", "link": "#", "ai_oznaka": "🟡 Neutralno (Čekanje)"
            })
        
        if broj_pravih_vijesti > 0:
            prosjek = ukupni_sentiment_score / broj_pravih_vijesti
            konacni_sentiment = "🟢 POZITIVAN" if prosjek > 0.05 else ("🔴 NEGATIVAN" if prosjek < -0.05 else "🟡 NEUTRALAN")
        else:
            konacni_sentiment = "⏳ ČEKAM"
            
        if rsi_vrijednost is not None:
            if rsi_vrijednost > 70:
                status = "⚠️ RISK (PREKUPLJENO)"
            elif rsi_vrijednost < 32 and (konacni_sentiment == "🟢 POZITIVAN" or volume_score > 1.2):
                status = "🔥 SIGNAL KUPNJE"
            elif volume_score > 2.0 and postotak > 2:
                if rsi_vrijednost < 60:
                    status = "🚀 PROBOJ (MOŽE SE KUPITI)"
                else:
                    status = "⚠️ PROBOJ (RIZIK VRHA)"
            elif rsi_vrijednost < 35:
                status = "🛒 JEFTINO (PRATI)"
            else:
                status = "⏳ PROMATRAJ"
        else:
            status = "⏳ ČEKAM PODATKE"
            
        rsi_prikaz = round(rsi_vrijednost, 1) if rsi_vrijednost is not None else "N/A"
        
        return {
            "Ticker": ticker, "Ime Kompanije": ime, "Cijena ($)": round(trenutna_cijena, 3),
            "Promjena (%)": round(postotak, 2), "Volume Score": round(volume_score, 2),
            "RSI (14)": rsi_prikaz, "AI Sentiment": konacni_sentiment, "AI Status": status,
            "52-Tjedni Raspon": raspon_52, "Vijesti": pokupljene_vijesti
        }
    except:
        return None

def prikazi_tablicu_i_graf(lista_tickera, kljuc_grafikona):
    podaci_lista = []
    with st.spinner("🤖 AI povlači podatke s burze..."):
        for t in lista_tickera:
            rezultat = dohvati_podatke(t)
            if resultado := rezultat: # Popravljeno za stabilan prikaz
                podaci_lista.append(resultado)
            
    if podaci_lista:
        df = pd.DataFrame(podaci_lista)
        stupci_za_prikaz = ["Ticker", "Cijena ($)", "Promjena (%)", "Volume Score", "RSI (14)", "AI Status", "52-Tjedni Raspon"]
        st.dataframe(
            df[stupci_za_prikaz].style.format({"Cijena ($)": "{:.3f}", "Promjena (%)": "{:+.2f}%", "Volume Score": "{:.2f}x"}),
            use_container_width=True, hide_index=True
        )
        
        st.markdown("### 🛒 Unesi uloženi iznos i potvrdi kupnju:")
        for stavka in podaci_lista:
            t = stavka["Ticker"]
            if t in st.session_state.kupljene_dionice:
                if st.button(f"🔴 Odznači / Makni {t}", key=f"del_{kljuc_grafikona}_{t}"):
                    del st.session_state.kupljene_dionice[t]
                    # Osvježi Google Sheets
                    if st.session_state.kupljene_dionice:
                        novi_df = pd.DataFrame([{"Ticker": k, "Ulazna Cijena": v["ulazna_cijena"], "Ulozeno Novca": v["ulozeno_novca"]} for k, v in st.session_state.kupljene_dionice.items()])
                    else:
                        novi_df = pd.DataFrame(columns=["Ticker", "Ulazna Cijena", "Ulozeno Novca"])
                    spremi_u_list(novi_df, "Portfolio")
                    st.rerun()
            else:
                col_novac, col_gumb = st.columns([2, 1])
                with col_novac:
                    iznos = st.number_input(f"Koliko novca ulažeš u {t}?", min_value=1.0, value=50.0, step=10.0, key=f"input_{kljuc_grafikona}_{t}")
                with col_gumb:
                    st.write("")
                    st.write("")
                    if st.button(f"🟢 Kupio {t}", key=f"add_{kljuc_grafikona}_{t}"):
                        st.session_state.kupljene_dionice[t] = {"ulazna_cijena": stavka["Cijena ($)"], "ulozeno_novca": iznos}
                        # Osvježi Google Sheets
                        novi_df = pd.DataFrame([{"Ticker": k, "Ulazna Cijena": v["ulazna_cijena"], "Ulozeno Novca": v["ulozeno_novca"]} for k, v in st.session_state.kupljene_dionice.items()])
                        spremi_u_list(novi_df, "Portfolio")
                        st.rerun()

        fig = px.bar(df, x="Ticker", y="Volume Score", text="Volume Score", title="Snaga Volumena", color="Volume Score", color_continuous_scale="Viridis")
        fig.update_traces(texttemplate='%{text}x', textposition='outside')
        fig.add_hline(y=1.0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True, key=kljuc_grafikona)
        
        st.subheader("📰 AI Analiza pojedinačnih vijesti:")
        for stavka in podaci_lista:
            if stavka["Vijesti"]:
                with st.expander(f"AI Analiza za {stavka['Ticker']}"):
                    for v in stavka["Vijesti"]:
                        st.markdown(f"**[{v['naslov']}]({v['link']})**" if v['link'] != "#" else f"**{v['naslov']}**")
                        st.write(f"🕵️‍♂️ **AI Ocjena:** {v['ai_oznaka']} | Izvor: {v['izvor']}")
                        st.write("---")
    else:
        st.warning("Trenutno nema dostupnih podataka za odabranu grupu.")

tab_portfolio, tab_history, tab0, tab1, tab2, tab3 = st.tabs([
    "💼 MOJE OTVORENE POZICIJE", "📜 POVIJEST TREJDOVA", "🌍 Geopolitika & Makro", "💰 Penny / Mali Radari", "⚡ Catalyst Dionice", "🏛️ Globalni Divovi"
])

with tab_portfolio:
    st.header("Active Trades (Tvoje trenutne investicije)")
    st.caption("☁️ SINKRONIZIRANO S GOOGLE SHEETS BAZOM PODATAKA")
    
    if not st.session_state.kupljene_dionice:
        st.info("Trenutno nemaš kupljenih dionica. Unesi iznos i klikni 'Kupio' na radarima.")
    else:
        portfolio_podaci = []
        with st.spinner("🤖 AI osvježava tvoj portfelj..."):
            for t, podaci in list(st.session_state.kupljene_dionice.items()):
                cijena_kupnje = podaci["ulazna_cijena"]
                ulozeno = podaci["ulozeno_novca"]
                trenutni_rezultat = dohvati_podatke(t)
                if trenutni_rezultat:
                    trenutna_c = trenutni_rezultat["Cijena ($)"]
                    moj_porast = ((trenutna_c - cijena_kupnje) / cijena_kupnje) * 100
                    novcana_zarada = ulozeno * (moj_porast / 100.0)
                    
                    sugestija = "🟢 DRŽI"
                    if moj_porast <= -10.0: sugestija = "🚨 REŽI GUBITAK"
                    elif moj_porast >= 15.0: sugestija = "💰 UZMI PROFIT"
                    
                    portfolio_podaci.append({
                        "Ticker": t, "Uloženo Novca": ulozeno, "Zarada/Gubitak (Novac)": novcana_zarada,
                        "Tvoj Profit/Gubitak (%)": moj_porast, "Moja Ulazna Cijena ($)": cijena_kupnje,
                        "Trenutna Cijena ($)": trenutna_c, "RSI (14)": trenutni_rezultat["RSI (14)"], "AI Sugestija": sugestija
                    })
        
        if portfolio_podaci:
            df_port_prikaz = pd.DataFrame(portfolio_podaci)
            prikaz_stupaca = ["Ticker", "Uloženo Novca", "Zarada/Gubitak (Novac)", "Tvoj Profit/Gubitak (%)", "Moja Ulazna Cijena ($)", "Trenutna Cijena ($)", "RSI (14)", "AI Sugestija"]
            st.dataframe(
                df_port_prikaz[prikaz_stupaca].style.format({
                    "Uloženo Novca": "{:.2f} $", "Zarada/Gubitak (Novac)": "{:+.2f} $",
                    "Tvoj Profit/Gubitak (%)": "{:+.2f}%", "Moja Ulazna Cijena ($)": "{:.3f}", "Trenutna Cijena ($)": "{:.3f}"
                }), use_container_width=True, hide_index=True
            )
            
            st.markdown("### 🏃‍♂️ Zatvori poziciju:")
            port_kolone = st.columns(len(portfolio_podaci))
            for idx, p in enumerate(portfolio_podaci):
                with port_kolone[idx]:
                    if st.button(f"❌ Prodano {p['Ticker']}", key=f"port_del_{p['Ticker']}"):
                        st.session_state.povijest_trejdova.append({
                            "Ticker": p["Ticker"], "Ulozeno": p["Uloženo Novca"],
                            "Zarada_Gubitak": p["Zarada/Gubitak (Novac)"], "Konacni_Rezultat_Postotak": p["Tvoj Profit/Gubitak (%)"]
                        })
                        del st.session_state.kupljene_dionice[p['Ticker']]
                        
                        if st.session_state.kupljene_dionice:
                            df_g_port = pd.DataFrame([{"Ticker": k, "Ulazna Cijena": v["ulazna_cijena"], "Ulozeno Novca": v["ulozeno_novca"]} for k, v in st.session_state.kupljene_dionice.items()])
                        else:
                            df_g_port = pd.DataFrame(columns=["Ticker", "Ulazna Cijena", "Ulozeno Novca"])
                            
                        spremi_u_list(df_g_port, "Portfolio")
                        spremi_u_list(pd.DataFrame(st.session_state.povijest_trejdova), "Povijest")
                        st.rerun()

with tab_history:
    st.header("Zatvorene Pozicije & Statistika")
    if not st.session_state.povijest_trejdova:
        st.info("Ovdje će se pojaviti tvoji završeni trejdovi.")
    else:
        df_hist = pd.DataFrame(st.session_state.povijest_trejdova)
        ukupni_novac = df_hist["Zarada_Gubitak"].sum() if "Zarada_Gubitak" in df_hist.columns else 0.0
        st.metric(label="Ukupni profit/gubitak u novcu", value=f"{round(ukupni_novac, 2)} $", delta=f"{round(ukupni_novac, 2)} $")
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ OČISTI CIJELU POVIJEST STATISTIKE", use_container_width=True):
            st.session_state.povijest_trejdova = []
            spremi_u_list(pd.DataFrame(), "Povijest")
            st.rerun()

with tab0: prikazi_tablicu_i_graf(kat_makro, "graf_makro")
with tab1: prikazi_tablicu_i_graf(kat_penny, "graf_penny")
with tab2: prikazi_tablicu_i_graf(kat_catalyst, "graf_cat")
with tab3: prikazi_tablicu_i_graf(kat_divovi, "graf_div")
