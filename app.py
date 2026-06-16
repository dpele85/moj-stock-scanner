import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from textblob import TextBlob
import json
import requests
import base64

# 1. Postavke stranice
st.set_page_config(page_title="AI Financijski Terminal V17", layout="wide", initial_sidebar_state="collapsed")

# --- PA_METNA GITHUB POHRANA ---
REPO = "dpele85/moj-stock-scanner"
FILE_PATH = "portfolio.json"
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")

def ucitaj_trajne_podatke():
    """Povlači portfolio.json direktno s tvog GitHub repozitorija."""
    if not GITHUB_TOKEN:
        return {}, []
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        try:
            sadrzaj = base64.b64decode(res.json()["content"]).decode("utf-8")
            podaci = json.loads(sadrzaj)
            return podaci.get("kupljene_dionice", {}), list(podaci.get("povijest_trejdova", []))
        except:
            pass
    return {}, []

def spremi_trajne_podatke(kupljene, povijest):
    """Sprema i radi automatski Commit tvojih podataka na tvoj GitHub račun."""
    if not GITHUB_TOKEN:
        return
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    novi_podaci = {"kupljene_dionice": kupljene, "povijest_trejdova": povijest}
    sadrzaj_bytes = json.dumps(novi_podaci, indent=4, ensure_ascii=False).encode("utf-8")
    sadrzaj_b64 = base64.b64encode(sadrzaj_bytes).decode("utf-8")
    
    payload = {
        "message": "Automatsko ažuriranje portfolija iz AI Terminala",
        "content": sadrzaj_b64
    }
    if sha:
        payload["sha"] = sha
        
    requests.put(url, headers=headers, json=payload)

# Inicijalizacija podataka iz sigurnog GitHub oblaka
trajne_dionice, trajna_povijest = ucitaj_trajne_podatke()

if "kupljene_dionice" not in st.session_state:
    st.session_state.kupljene_dionice = trajne_dionice
if "povijest_trejdova" not in st.session_state:
    st.session_state.povijest_trejdova = trajna_povijest

# --- NASLOV TERMINALA ---
st.title("🤖 Moj AI Financijski Terminal V17")
st.caption("Profesionalni radar s RSI-om, AI analizom i neuništivom GitHub memorijom.")

if st.button("🔄 RESTARTAJ TERMINAL I OSVJEŽI ANALIZU", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Grupe dionica
kat_makro = ["GC=F", "CL=F"]
kat_penny = ["TMC", "TRVN", "SOUN", "GFAI", "OTLK"]
kat_catalyst = ["ASTS", "LAC", "CHPT", "NIO", "MARA"]
kat_divovi = ["PLTR", "SOFI", "HOOD", "BABA", "TSM"]
imena_makro = {"GC=F": "Zlato (Gold Futures)", "CL=F": "Sirova Nafta (Crude Oil)"}

def izracunaj_rsi(history_df, period=14):
    if len(history_df) < period + 1: return None
    delta = history_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.fillna(0)))
    return rsi.iloc[-1]

def analiziraj_sentiment(tekst):
    if not tekst or tekst == "Nema naslova" or "Tržište miruje" in tekst: return 0, "🟡 Neutralno"
    analysis = TextBlob(tekst)
    score = analysis.sentiment.polarity
    if score > 0.05: return score, "🟢 Bullish (Pozitivno)"
    elif score < -0.05: return score, "🔴 Bearish (Negativno)"
    return score, "🟡 Neutralno"

@st.cache_data(ttl=300)
def dohvati_podatke(ticker):
    try:
        dionica = yf.Ticker(ticker)
        povijest = dionica.history(period="30d")
        if len(povijest) < 15: return None
        
        # 🔥 POPRAVAK ZA YFINANCE MULTI-INDEX BUG (Sprječava crveni ekran)
        if isinstance(povijest.columns, pd.MultiIndex):
            povijest.columns = [col[0] for col in povijest.columns]
            
        trenutna_cijena = povijest['Close'].iloc[-1]
        prethodno_zatvaranje = povijest['Close'].iloc[-2]
        postotak = ((trenutna_cijena - prethodno_zatvaranje) / prethodno_zatvaranje) * 100
        trenutni_volumen = povijest['Volume'].iloc[-1]
        
        info = dionica.info
        prosjecni_volumen = info.get('averageVolume', 1)
        if prosjecni_volumen == 1: prosjecni_volumen = info.get('averageDailyVolume10Day', 1)
        volume_score = trenutni_volumen / prosjecni_volumen if prosjecni_volumen > 1 else 0
        rsi_vrijednost = izracunaj_rsi(povijest)
        raspon_52 = f"${round(info.get('fiftyTwoWeekLow', trenutna_cijena), 2)} - ${round(info.get('fiftyTwoWeekHigh', trenutna_cijena), 2)}"
        ime = imena_makro[ticker] if ticker in imena_makro else info.get('longName', ticker)
        
        pokupljene_vijesti, ukupni_sentiment_score, broj_pravih_vijesti = [], 0, 0
        try:
            vijesti_izvor = dionica.news
            if vijesti_izvor and isinstance(vijesti_izvor, list):
                for v in vijesti_izvor[:5]:
                    naslov = v.get('title', '').strip()
                    if naslov:
                        score, oznaka = analiziraj_sentiment(naslov)
                        ukupni_sentiment_score += score
                        broj_pravih_vijesti += 1
                        pokupljene_vijesti.append({"naslov": naslov, "izvor": v.get('publisher', 'Yahoo Finance'), "link": v.get('link', '#'), "ai_oznaka": oznaka})
        except: pass
        if not pokupljene_vijesti: pokupljene_vijesti.append({"naslov": "Nema novih objava.", "izvor": "Sustav", "link": "#", "ai_oznaka": "🟡 Neutralno"})
        konacni_sentiment = "🟢 POZITIVAN" if (ukupni_sentiment_score / broj_pravih_vijesti if broj_pravih_vijesti > 0 else 0) > 0.05 else ("🔴 NEGATIVAN" if (ukupni_sentiment_score / broj_pravih_vijesti if broj_pravih_vijesti > 0 else 0) < -0.05 else "🟡 NEUTRALAN")
        
        if rsi_vrijednost is not None:
            if rsi_vrijednost > 70: status = "⚠️ RISK (PREKUPLJENO)"
            elif rsi_vrijednost < 33: status = "🔥 SIGNAL KUPNJE"
            elif volume_score > 2.0 and postotak > 2: status = "🚀 PROBOJ (MOŽE SE KUPITI)" if rsi_vrijednost < 60 else "⚠️ PROBOJ (RIZIK VRHA)"
            elif rsi_vrijednost < 38: status = "🛒 JEFTINO (PRATI)"
            else: status = "⏳ PROMATRAJ"
        else: status = "⏳ ČEKAM PODATKE"
        
        return {"Ticker": ticker, "Ime Kompanije": ime, "Cijena ($)": round(trenutna_cijena, 3), "Promjena (%)": round(postotak, 2), "Volume Score": round(volume_score, 2), "RSI (14)": round(rsi_vrijednost, 1) if rsi_vrijednost is not None else "N/A", "AI Sentiment": konacni_sentiment, "AI Status": status, "52-Tjedni Raspon": raspon_52, "Vijesti": pokupljene_vijesti}
    except: return None

# --- PRIKAZ RADARA I GRAFIKONA UNUTAR TABOVA ---
def prikazi_tablicu_i_graf(lista_tickera, kljuc_grafikona):
    podaci_lista = []
    with st.spinner("🤖 AI povlači podatke s burze..."):
        for t in lista_tickera:
            rezultat = dohvati_podatke(t)
            if rezultat: podaci_lista.append(rezultat)
            
    if podaci_lista:
        df = pd.DataFrame(podaci_lista)
        st.dataframe(df[["Ticker", "Cijena ($)", "Promjena (%)", "Volume Score", "RSI (14)", "AI Status", "52-Tjedni Raspon"]].style.format({"Cijena ($)": "{:.3f}", "Promjena (%)": "{:+.2f}%", "Volume Score": "{:.2f}x"}), use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(df, x="Ticker", y="Promjena (%)", color="Promjena (%)", color_continuous_scale=["red", "gray", "green"], title="Dnevni postotni pomak dionica"), use_container_width=True)
        
        st.markdown("### 🛒 Unesi kupljene pozicije:")
        mini_kolone = st.columns(len(df))
        for i, redak in df.iterrows():
            ticker = redak['Ticker']
            with mini_kolone[i]:
                with st.popover(f"Kupi {ticker}", use_container_width=True):
                    kolicina_unos = st.number_input("Količina:", min_value=0.001, value=1.0, step=1.0, key=f"qty_{kljuc_grafikona}_{ticker}")
                    cijena_unos = st.number_input("Cijena ($):", min_value=0.0, value=float(redak['Cijena ($)']), format="%.3f", key=f"prc_{kljuc_grafikona}_{ticker}")
                    if st.button("Potvrdi i spremi", key=f"btn_{kljuc_grafikona}_{ticker}", use_container_width=True):
                        if ticker in st.session_state.kupljene_dionice:
                            stara_kol = st.session_state.kupljene_dionice[ticker]['kolicina']
                            stara_cij = st.session_state.kupljene_dionice[ticker]['cijena']
                            nova_kol = stara_kol + kolicina_unos
                            st.session_state.kupljene_dionice[ticker] = {'cijena': round(((stara_kol * stara_cij) + (kolicina_unos * cijena_unos)) / nova_kol, 3), 'kolicina': round(nova_kol, 3)}
                        else:
                            st.session_state.kupljene_dionice[ticker] = {'cijena': round(cijena_unos, 3), 'kolicina': round(kolicina_unos, 3)}
                        st.session_state.povijest_trejdova.append(f"Kupljeno {kolicina_unos} komada {ticker} po ${cijena_unos}")
                        
                        # OKIDAČ KOJI ŠALJE PODATKE DIREKTNO NA GITHUB OBLAK
                        spremi_trajne_podatke(st.session_state.kupljene_dionice, st.session_state.povijest_trejdova)
                        st.success(f"Uspješno i trajno spremljeno na GitHub!")
                        st.rerun()
                        
        with st.expander("📰 Pogledaj AI vijesti"):
            for d in podaci_lista:
                st.write(f"**{d['Ticker']}** | Sentiment: **{d['AI Sentiment']}**")
                for v in d['Vijesti']: st.write(f"- {v['ai_oznaka']} | *{v['naslov']}*")
                st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💼 MOJE OTVORENE POZICIJE", "📈 Geopolitika & Makro", "🪙 Penny / Mali Radari", "⚡ Catalyst Dionice", "🏛️ Globalni Divovi"])

with tab1:
    st.header("💼 Vaš Portfolio i Praćenje Zarade (Sigurna GitHub sinkronizacija)")
    if not st.session_state.kupljene_dionice:
        st.info("Trenutno nemate otvorenih pozicija. Unesite kupnju unutar ostalih tabova.")
    else:
        portfolio_podaci, ukupno_investirano, ukupna_trenutna_vrijednost = [], 0.0, 0.0
        for t, detalji in st.session_state.kupljene_dionice.items():
            trenutni_podaci = dohvati_podatke(t)
            if trenutni_podaci:
                trenutna_cijena = trenutni_podaci["Cijena ($)"]
                investirano = detalji["kolicina"] * detalji["cijena"]
                trenutna_vrijednost = detalji["kolicina"] * trenutna_cijena
                pnl_usd = trenutna_vrijednost - investirano
                ukupno_investirano += investirano
                ukupna_trenutna_vrijednost += trenutna_vrijednost
                portfolio_podaci.append({"Ticker": t, "Količina": detalji["kolicina"], "Prosječna Ulazna ($)": detalji["cijena"], "Trenutna Cijena ($)": trenutna_cijena, "Ukupno Investirano ($)": round(investirano, 2), "Trenutna Vrijednost ($)": round(trenutna_vrijednost, 2), "Dobit / Gubitak ($)": round(pnl_usd, 2), "Dobit / Gubitak (%)": round((pnl_usd / investirano) * 100, 2) if investirano > 0 else 0})
        
        if portfolio_podaci:
            uk_pnl_usd = ukupna_trenutna_vrijednost - ukupno_investirano
            c1, c2, c3 = st.columns(3)
            c1.metric("Ukupno Investirano", f"${round(ukupno_investirano, 2)}")
            c2.metric("Trenutna Vrijednost", f"${round(ukupna_trenutna_vrijednost, 2)}")
            c3.metric("Ukupni P&L", f"${round(uk_pnl_usd, 2)}", f"{round((uk_pnl_usd / ukupno_investirano) * 100, 2) if ukupno_investirano > 0 else 0}%")
            
            st.dataframe(pd.DataFrame(portfolio_podaci).style.format({"Količina": "{:.2f}", "Prosječna Ulazna ($)": "{:.3f}", "Trenutna Cijena ($)": "{:.3f}", "Ukupno Investirano ($)": "${:.2f}", "Trenutna Vrijednost ($)": "${:.2f}", "Dobit / Gubitak ($)": "{:+.2f}", "Dobit / Gubitak (%)": "{:+.2f}%"}).map(lambda v: f'color: {"green" if v > 0 else "red"}; font-weight: bold;', subset=["Dobit / Gubitak ($)", "Dobit / Gubitak (%)"]), use_container_width=True, hide_index=True)
        
        if st.button("🗑️ OBRIŠI SVE POZICIJE I RESETIRAJ PORTFOLIO", use_container_width=True):
            st.session_state.kupljene_dionice, st.session_state.povijest_trejdova = {}, []
            spremi_trajne_podatke({}, [])
            st.rerun()
            
    if st.session_state.povijest_trejdova:
        with st.expander("📜 Povijest zapisanih transakcija"):
            for log in st.session_state.povijest_trejdova: st.text(log)

with tab2: prikazi_tablicu_i_graf(kat_makro, "makro")
with tab3: prikazi_tablicu_i_graf(kat_penny, "penny")
with tab4: prikazi_tablicu_i_graf(kat_catalyst, "catalyst")
with tab5: prikazi_tablicu_i_graf(kat_divovi, "divovi")
