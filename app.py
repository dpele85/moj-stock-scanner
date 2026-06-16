import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime

st.set_page_config(page_title="AI Bot Monitor V18", layout="wide")

# --- PAMETNO ČITANJE DIREKTNO S REPOZITORIJA ---
URL_DATA = "https://raw.githubusercontent.com/dpele85/moj-stock-scanner/main/portfolio.json"

def ucitaj_live_stanje():
    # Dodajemo timestamp na URL da prisilimo server da uvijek povuče najnoviji file
    res = requests.get(f"{URL_DATA}?v={int(datetime.now().timestamp())}")
    if res.status_code == 200:
        try:
            return res.json()
        except: pass
    return {"cash": 10000.0, "kupljene_dionice": {}, "povijest_trejdova": []}

podaci = ucitaj_live_stanje()

st.title("🤖 AI Algoritamski Monitor V18")
st.caption("Ovaj ekran prikazuje što tvoj robot radi 24/7 u pozadini putem GitHub Actions-a.")

# Gornje metrike
cash = podaci.get("cash", 10000.0)
kupljene = podaci.get("kupljene_dionice", {})
povijest = podaci.get("povijest_trejdova", [])

c1, c2, c3 = st.columns(3)
c1.metric("Dostupan fiktivni novac (Cash)", f"${round(cash, 2)}")
c2.metric("Broj aktivnih pozicija", f"{len(kupljene)}")
c3.metric("Ukupno izvršenih operacija", f"{len(povijest)}")

st.markdown("---")

t1, t2 = st.tabs(["💼 TRENUTNI PORTFOLIO", "📜 POVIJEST LOGOVA TRANSAKCIJA"])

with t1:
    st.subheader("💼 Pozicije koje bot trenutno drži na burzi")
    if kupljene:
        prikaz_lista = []
        for ticker, detalji in kupljene.items():
            prikaz_lista.append({
                "Ticker": ticker,
                "Količina (Komada)": detalji["kolicina"],
                "Kupovna Cijena ($)": detalji["cijena"]
            })
        st.dataframe(pd.DataFrame(prikaz_lista), use_container_width=True, hide_index=True)
    else:
        st.info("Bot trenutno drži 100% sredstava u cashu i čeka signale na tržištu.")

with t2:
    st.subheader("📜 Dnevnik rada (Što je bot napravio dok nisi gledao?)")
    if povijest:
        for log in povijest:
            if "🟢" in log: st.success(log)
            elif "🔴" in log: st.error(log)
            else: st.text(log)
    else:
        st.write("Dnevnik je trenutno prazan. Kada pokreneš Actions na GitHubu, ovdje će se stvoriti zapisi.")
