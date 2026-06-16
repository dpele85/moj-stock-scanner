import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime

# Pokušavamo uvesti yfinance za prave live cijene na ekranu
try:
    import yfinance as yf
except:
    yf = None

st.set_page_config(page_title="AI Financijski Terminal V19", layout="wide")

st.title("🤖 Moj AI Financijski Terminal V19")
st.caption("Profesionalni hibridni sustav: Live praćenje + sinkronizacija s pozadinskim GitHub botom.")

# --- KORAK 1: DOHVAĆANJE PODATAKA ---
URL_DATA = "https://raw.githubusercontent.com/dpele85/moj-stock-scanner/main/portfolio.json"

def povuci_s_githuba():
    try:
        res = requests.get(f"{URL_DATA}?v={int(datetime.now().timestamp())}")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

# Ako tek otvaramo aplikaciju, povuci podatke u memoriju terminala
if "portfolio" not in st.session_state:
    podaci = povuci_s_githuba()
    if not podaci:
        # Fallback na tvoje početno stanje ako GitHub ne odgovori odmah
        podaci = {
            "cash": 10000.0,
            "kupljene_dionice": {
                "ASTS": {"kolicina": 5.0, "cijena": 82.92},
                "NIO": {"kolicina": 20.0, "cijena": 5.03}
            },
            "povijest_trejdova": ["Sustav pokrenut. Čekanje novih signala pozadinskog bota..."]
        }
    st.session_state.portfolio = podaci

# Gumb za prisilno osvježavanje s GitHuba
if st.button("🔄 RESTARTAJ TERMINAL I OSVJEŽI ANALIZU"):
    svjezi_podaci = povuci_s_githuba()
    if svjezi_podaci:
        st.session_state.portfolio = svjezi_podaci
        st.toast("Uspješno povučeno najnovije stanje s GitHuba!", icon="✅")

# --- KORAK 2: INTERAKTIVNE KONTROLE ZA KORISNIKA (Podešavanje Casha) ---
st.markdown("### ⚙️ Ručne simulacije i podešavanje računa")
col_input1, col_input2 = st.columns(2)

with col_input1:
    # Ovdje sada možeš mijenjati fiktivni novac izravno na ekranu!
    trenutni_cash = st.session_state.portfolio.get("cash", 10000.0)
    novi_cash = st.number_input("Uredi iznos fiktivnog novca ($):", value=float(trenutni_cash), step=500.0)
    if novi_cash != trenutni_cash:
        st.session_state.portfolio["cash"] = novi_cash
        st.rerun()

with col_input2:
    if st.button("🗑️ OBRIŠI SVE POZICIJE I RESETIRAJ PORTFOLIO"):
        st.session_state.portfolio["cash"] = 10000.0
        st.session_state.portfolio["kupljene_dionice"] = {}
        st.toast("Portfolio očišćen i vraćen na $10,000 cash!", icon="ℹ️")
        st.rerun()

st.markdown("---")

# --- KORAK 3: LIVE RAČUNANJE I IZRADA TABLICE KAO U V17 ---
cash = st.session_state.portfolio.get("cash", 10000.0)
kupljene = st.session_state.portfolio.get("kupljene_dionice", {})
povijest = st.session_state.portfolio.get("povijest_trejdova", [])

ukupno_investirano = 0.0
trenutna_vrijednost_dionica = 0.0
redovi_tablice = []

for ticker, detalji in kupljene.items():
    kolicina = detalji["kolicina"]
    ulazna_cijena = detalji["cijena"]
    u_investirano = kolicina * ulazna_cijena
    ukupno_investirano += u_investirano
    
    # Dohvati pravu live cijenu preko yfinance za tablicu
    live_cijena = ulazna_cijena  
    if yf:
        try:
            ticker_data = yf.Ticker(ticker)
            live_cijena = ticker_data.fast_info['last_price']
        except:
            pass
            
    t_vrijednost = kolicina * live_cijena
    trenutna_vrijednost_dionica += t_vrijednost
    
    pnl_usd = t_vrijednost - u_investirano
    pnl_pct = (pnl_usd / u_investirano) * 100 if u_investirano > 0 else 0.0
    
    redovi_tablice.append({
        "Ticker": ticker,
        "Količina": kolicina,
        "Prosječna Ulazna ($)": round(ulazna_cijena, 3),
        "Trenutna Cijena ($)": round(live_cijena, 3),
        "Ukupno investirano ($)": round(u_investirano, 2),
        "Trenutna Vrijednost ($)": round(t_vrijednost, 2),
        "Dobit / Gubitak ($)": round(pnl_usd, 2),
        "Dobit / Gubitak (%)": f"{'+' if pnl_usd > 0 else ''}{round(pnl_pct, 2)}%"
    })

# Izračun ukupnog P&L-a za gornje metrike
ukupni_pnl_usd = trenutna_vrijednost_dionica - ukupno_investirano
ukupni_pnl_pct = (ukupni_pnl_usd / ukupno_investirano) * 100 if ukupno_investirano > 0 else 0.0

# --- KORAK 4: PRIKAZ VELIKIH METRIKA KAO U V17 ---
st.markdown("### 💼 Vaš Portfolio i Praćenje Zarade")
c1, c2, c3 = st.columns(3)
c1.metric("Ukupno Investirano", f"${round(ukupno_investirano, 2)}")
c2.metric("Trenutna Vrijednost dionica", f"${round(trenutna_vrijednost_dionica, 2)}")
c3.metric("Ukupni P&L", f"${round(ukupni_pnl_usd, 2)}", f"{round(ukupni_pnl_pct, 2)}%")

st.markdown(f"**Slobodan Cash na računu:** `${round(cash, 2)}` | **Ukupna vrijednost cijelog računa (Cash + Dionice):** `${round(cash + trenutna_vrijednost_dionica, 2)}`")

# --- KORAK 5: ORGANIZACIJA KROZ KARTICE (TABS) ---
t1, t2, t3, t4 = st.tabs(["📊 MOJE OTVORENE POZICIJE", "📜 POVIJEST LOGOVA TRANSAKCIJA", "🌍 Geopolitika & Makro", "🚀 Penny / Mali Radari"])

with t1:
    if redovi_tablice:
        df = pd.DataFrame(redovi_tablice)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Trenutno nema otvorenih pozicija dionica. Sve je u cashu ili bot čeka signal.")

with t2:
    st.subheader("📜 Dnevnik rada bota")
    if povijest:
        for log in reversed(povijest):
            if "🟢" in log or "Kupnja" in log: st.success(log)
            elif "🔴" in log or "Prodaja" in log: st.error(log)
            else: st.info(log)
    else:
        st.write("Nema povijesnih zapisa u datoteci.")

with t3:
    st.subheader("🌍 Geopolitički i Makroekonomski Radari")
    st.write("Praćenje DXY indeksa, zlata, srebra i odluka FED-a o kamatnim stopama.")

with t4:
    st.subheader("🚀 Visoko volatilne dionice i Penny Stocks")
    st.write("Skener za dionice s visokim momentumom (ASTS, MARA, NIO, ATOS...).")
