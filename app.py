import streamlit as st
import pandas as pd
try:
    import yfinance as yf
except:
    yf = None

st.set_page_config(page_title="AI Financijski Terminal V21", layout="wide")

st.title("🤖 Moj AI Financijski Terminal V21")
st.caption("Verzija V21: Potpuno očišćena memorija, resetirana povijest i vraćen originalni V17 izgled.")

# --- KORAK 1: PRISILNO RESTARTANJE SVEGA PREKO NOVOG KLJUČA (portfolio_v21) ---
# Ovo odmah uništava staru povijest i stare cacheirane podatke u pregledniku!
if "portfolio_v21" not in st.session_state:
    st.session_state.portfolio_v21 = {
        "cash": 10000.0,
        "kupljene_dionice": {
            "ASTS": {"kolicina": 5.0, "cijena": 82.92},
            "NIO": {"kolicina": 20.0, "cijena": 5.03}
        },
        "povijest_trejdova": []  # Potpuno prazno i očišćeno!
    }

# --- KORAK 2: RUČNO URĐIVANJE FIKTIVNOG NOVCA NA EKRANU ---
st.markdown("### ⚙️ Kontrola fiktivnog računa uživo")
col_input1, col_input2 = st.columns(2)

with col_input1:
    # Ovdje sada možeš upisati bilo koji iznos i on će se odmah primijeniti na cijeli sustav
    trenutni_cash = st.session_state.portfolio_v21["cash"]
    novi_cash = st.number_input("Uredi iznos fiktivnog novca ($):", value=float(trenutni_cash), step=500.0)
    if novi_cash != trenutni_cash:
        st.session_state.portfolio_v21["cash"] = novi_cash
        st.rerun()

with col_input2:
    if st.button("🗑️ TVORNIČKI RESETIRAJ PORTFOLIO I POVIJEST"):
        st.session_state.portfolio_v21 = {
            "cash": 10000.0,
            "kupljene_dionice": {
                "ASTS": {"kolicina": 5.0, "cijena": 82.92},
                "NIO": {"kolicina": 20.0, "cijena": 5.03}
            },
            "povijest_trejdova": []
        }
        st.rerun()

st.markdown("---")

# --- KORAK 3: LIVE RAČUNANJE I VRAĆANJE TOČNIH STUPACA IZ V17 ---
cash = st.session_state.portfolio_v21["cash"]
kupljene = st.session_state.portfolio_v21["kupljene_dionice"]
povijest = st.session_state.portfolio_v21["povijest_trejdova"]

ukupno_investirano = 0.0
trenutna_vrijednost_dionica = 0.0
redovi_tablice = []

for ticker, detalji in kupljene.items():
    kolicina = detalji["kolicina"]
    ulazna_cijena = detalji["cijena"]
    u_investirano = kolicina * ulazna_cijena
    ukupno_investirano += u_investirano
    
    # Live cijena preko yfinance
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
    
    # Stupci su mapirani točno prema tvojoj slici iz V17 verzije
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

ukupni_pnl_usd = trenutna_vrijednost_dionica - ukupno_investirano
ukupni_pnl_pct = (ukupni_pnl_usd / ukupno_investirano) * 100 if ukupno_investirano > 0 else 0.0

# --- KORAK 4: METRIKE NA VRHU (IDENTIČNO KAO V17) ---
st.markdown("### 💼 Vaš Portfolio i Praćenje Zarade (Sigurna GitHub sinkronizacija)")
c1, c2, c3 = st.columns(3)
c1.metric("Ukupno Investirano", f"${round(ukupno_investirano, 2)}")
c2.metric("Trenutna Vrijednost", f"${round(trenutna_vrijednost_dionica, 2)}")
c3.metric("Ukupni P&L", f"${round(ukupni_pnl_usd, 2)}", f"{round(ukupni_pnl_pct, 2)}%")

st.markdown(f"**Dostupan fiktivni novac:** `${round(cash, 2)}` | **Ukupna vrijednost računa:** `${round(cash + trenutna_vrijednost_dionica, 2)}`")

# --- KORAK 5: VRAĆENI SVI ORIGINALNI TABOVI IZ V17 ---
t1, t2, t3, t4, t5, t6 = st.tabs([
    "📸 MOJE OTVORENE POZICIJE", 
    "🌍 Geopolitika & Makro", 
    "🟡 Penny / Mali Radari", 
    "⚡ Catalyst Dionice", 
    "🏦 Globalni Divovi",
    "📜 ČISTA POVIJEST LOGOVA"
])

with t1:
    if redovi_tablice:
        df = pd.DataFrame(redovi_tablice)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Trenutno nema otvorenih pozicija dionica.")

with t2:
    st.subheader("🌍 Geopolitika & Makro")
    st.write("Praćenje makroekonomskih indikatora.")

with t3:
    st.subheader("🟡 Penny / Mali Radari")
    st.write("Skener za visoko volatilne dionice.")

with t4:
    st.subheader("⚡ Catalyst Dionice")
    st.write("Dionice s nadolazećim katalizatorima i vijestima.")

with t5:
    st.subheader("🏦 Globalni Divovi")
    st.write("Pregled dionica velike tržišne kapitalizacije.")

with t6:
    st.subheader("📜 Dnevnik rada bota (Resetiran)")
    if povijest:
        for log in povijest:
            st.text(log)
    else:
        st.info("Povijest trgovanja je uspješno očišćena iz memorije terminala. Dnevnik je prazan.")
