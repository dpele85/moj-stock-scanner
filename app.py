import streamlit as st
import pandas as pd
from datetime import datetime

# Pokušaj uvoza yfinance za live cijene
try:
    import yfinance as yf
except:
    yf = None

st.set_page_config(page_title="AI Financijski Terminal V20", layout="wide")

st.title("🤖 Moj AI Financijski Terminal V20")
st.caption("Čista verzija: Resetirana povijest, otključane tablice dionica i slobodno uređivanje novca.")

# --- KORAK 1: PRISILNA INICIJALIZACIJA BAZE (ČIST STRIKTAN START) ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {
        "cash": 10000.0,
        "kupljene_dionice": {
            "ASTS": {"kolicina": 5.0, "cijena": 82.92},
            "NIO": {"kolicina": 20.0, "cijena": 5.03}
        },
        "povijest_trejdova": []  # POVIJEST JE POTPUNO OBRISANA I PRAZNA
    }

# --- KORAK 2: UPRAVLJANJE NOVACEM KOJE RADI ODMAH ---
st.markdown("### ⚙️ Kontrola fiktivnog računa uživo")
col_brzi_1, col_brzi_2 = st.columns(2)

with col_brzi_1:
    trenutni_cash = st.session_state.portfolio["cash"]
    # Polje u kojem slobodno možeš upisati i promijeniti iznos novca na ekranu
    novi_cash = st.number_input("Promijeni iznos slobodnog fiktivnog novca ($):", value=float(trenutni_cash), step=500.0)
    if novi_cash != trenutni_cash:
        st.session_state.portfolio["cash"] = novi_cash
        st.rerun()

with col_brzi_2:
    if st.button("🗑️ RESETIRAJ SVE NA POČETNE POSTAVKE"):
        st.session_state.portfolio = {
            "cash": 10000.0,
            "kupljene_dionice": {
                "ASTS": {"kolicina": 5.0, "cijena": 82.92},
                "NIO": {"kolicina": 20.0, "cijena": 5.03}
            },
            "povijest_trejdova": []
        }
        st.toast("Sve pozicije i novac su vraćeni na početno stanje!", icon="🔄")
        st.rerun()

st.markdown("---")

# --- KORAK 3: RAČUNANJE IZRADE TABLICE I LIVE CIJENA ---
cash = st.session_state.portfolio["cash"]
kupljene = st.session_state.portfolio["kupljene_dionice"]
povijest = st.session_state.portfolio["povijest_trejdova"]

ukupno_investirano = 0.0
trenutna_vrijednost_dionica = 0.0
redovi_tablice = []

for ticker, detalji in kupljene.items():
    kolicina = detalji["kolicina"]
    ulazna_cijena = detalji["cijena"]
    u_investirano = kolicina * ulazna_cijena
    ukupno_investirano += u_investirano
    
    # Povuci pravu live cijenu s burze
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
        "Kupovna Cijena ($)": round(ulazna_cijena, 2),
        "Trenutna Cijena ($)": round(live_cijena, 2),
        "Ukupno Investirano ($)": round(u_investirano, 2),
        "Trenutna Vrijednost ($)": round(t_vrijednost, 2),
        "Dobit/Gubitak ($)": round(pnl_usd, 2),
        "Dobit/Gubitak (%)": f"{'+' if pnl_usd > 0 else ''}{round(pnl_pct, 2)}%"
    })

ukupni_pnl_usd = trenutna_vrijednost_dionica - ukupno_investirano
ukupni_pnl_pct = (ukupni_pnl_usd / ukupno_investirano) * 100 if ukupno_investirano > 0 else 0.0

# --- KORAK 4: METRIKE NA VRHU ---
st.markdown("### 💼 Pregled tvog Portfolija")
c1, c2, c3 = st.columns(3)
c1.metric("Ukupno Investirano", f"${round(ukupno_investirano, 2)}")
c2.metric("Trenutna Vrijednost", f"${round(trenutna_vrijednost_dionica, 2)}")
c3.metric("Ukupni P&L", f"${round(ukupni_pnl_usd, 2)}", f"{round(ukupni_pnl_pct, 2)}%")

st.markdown(f"**Dostupan fiktivni novac:** `${round(cash, 2)}` | **Ukupna vrijednost računa:** `${round(cash + trenutna_vrijednost_dionica, 2)}`")

# --- KORAK 5: KARTICE (TABS) ---
t1, t2, t3, t4 = st.tabs(["📊 TRENUTNE OTVORENE POZICIJE", "📜 POVIJEST LOGOVA", "🌍 Makro Analize", "🚀 Penny Radari"])

with t1:
    # Tablica se sada prikazuje prisilno jer su podaci uvijek generirani u session stateu
    if redovi_tablice:
        df = pd.DataFrame(redovi_tablice)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nema otvorenih pozicija.")

with t2:
    st.subheader("📜 Povijest rada bota")
    if povijest:
        for log in povijest:
            st.text(log)
    else:
        st.info("Povijest trgovanja je uspješno očišćena. Dnevnik je prazan i spreman za nove zapise bota.")

with t3:
    st.subheader("🌍 Geopolitički i Makroekonomski Radari")
    st.write("Praćenje DXY indeksa, zlata, srebra i odluka FED-a.")

with t4:
    st.subheader("🚀 Visoko volatilne dionice i Penny Stocks")
    st.write("Skener za dionice: ASTS, MARA, NIO, ATOS.")
