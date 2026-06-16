import streamlit as st
import pandas as pd
import requests
import json
import base64

try:
    import yfinance as yf
except:
    yf = None

st.set_page_config(page_title="AI Algoritamski Monitor V22", layout="wide")

st.title("🤖 AI Algoritamski Monitor V22")
st.caption("Ovaj ekran prikazuje što tvoj robot radi 24/7 u pozadini putem GitHub Actions-a i omogućuje izravno brisanje baze.")

# --- POSTAVKE GITHUB POVEZNICE ---
REPO = "dpele85/moj-stock-scanner"

# Provjera tokena u Secretsima
if "GITHUB_TOKEN" not in st.secrets:
    st.error("❌ GITHUB_TOKEN nije pronađen u Streamlit Secrets postavama! Provjeri 'Secrets' u aplikaciji.")
    st.stop()

TOKEN = st.secrets["GITHUB_TOKEN"]

# --- SIDEBAR ZA KONTROLU DATOTEKE ---
st.sidebar.header("⚙️ GitHub Sinkronizacija")
ime_datoteke = st.sidebar.text_input("Naziv JSON datoteke bota:", value="portfolio.json")

# --- FUNKCIJE ZA REPOZITORIJ (API) ---
def dohvati_podatke_s_githuba(putanja):
    url = f"https://api.github.com/repos/{REPO}/contents/{putanja}"
    headers = {"Authorization": f"token {TOKEN}"}
    odgovor = requests.get(url, headers=headers)
    if odgovor.status_code == 200:
        sadrzaj = odgovor.json()
        raw_tekst = base64.b64decode(sadrzaj["content"]).decode("utf-8")
        return json.loads(raw_tekst), sadrzaj["sha"]
    return None, None

def spremi_podatke_na_github(putanja, novi_podaci, sha_kljuc, poruka="Reset povijesti s terminala"):
    url = f"https://api.github.com/repos/{REPO}/contents/{putanja}"
    headers = {"Authorization": f"token {TOKEN}"}
    poravnati_json = json.dumps(novi_podaci, indent=4).encode("utf-8")
    kodirano = base64.b64encode(poravnati_json).decode("utf-8")
    
    payload = {
        "message": poruka,
        "content": kodirano,
        "sha": sha_kljuc
    }
    odgovor = requests.put(url, headers=headers, json=payload)
    return odgovor.status_code in [200, 201]

# --- KORAK 1: DOHVAT LIVE PODATAKA ---
podaci_bota, trenutni_sha = dohvati_podatke_s_githuba(ime_datoteke)

# Ako datoteka ne postoji ili je prazna, postavi čistu strukturu
if podaci_bota is None:
    st.warning(f"⚠️ Datoteka '{ime_datoteke}' nije pronađena na GitHubu ili je prazna. Prikazujem privremenu čistu strukturu.")
    podaci_bota = {
        "cash": 10000.0,
        "kupljene_dionice": {"ASTS": {"kolicina": 5.0, "cijena": 82.92}, "NIO": {"kolicina": 20.0, "cijena": 5.03}},
        "povijest_trejdova": []
    }
    trenutni_sha = None

# --- KORAK 2: KLJUČNI GUMB ZA BRISANJE POVIJESTI DIREKTNO NA GITHUB-U ---
st.markdown("### 🛠️ Upravljanje bazom podataka na GitHubu")
col_gumb1, col_gumb2 = st.columns(2)

with col_gumb1:
    if st.button("🗑️ TRAJNO OBRIŠI POVIJEST TRGOVANJA NA GITHUB-U"):
        if trenutni_sha:
            # Zadržavamo dionice i novac, ali čistimo povijest logova u nulu
            podaci_bota["povijest_trejdova"] = []
            uspjeh = spremi_podatke_na_github(ime_datoteke, podaci_bota, trenutni_sha, "Obrisana povijest logova")
            if uspjeh:
                st.success("✅ Povijest trgovanja je uspješno izbrisana iz datoteke na GitHubu!")
                st.rerun()
            else:
                st.error("❌ Greška prilikom spremanja promjena na GitHub.")
        else:
            st.error("Nije moguće obrisati jer datoteka nema važeći SHA ključ na repozitoriju.")

with col_gumb2:
    if st.button("🔄 TVORNIČKI RESET (Briši i dionice i povijest)"):
        if trenutni_sha:
            cisti_reset = {
                "cash": 10000.0,
                "kupljene_dionice": {},
                "povijest_trejdova": []
            }
            uspjeh = spremi_podatke_na_github(ime_datoteke, cisti_reset, trenutni_sha, "Potpuni tvornički reset")
            if uspjeh:
                st.success("✅ Sve je resetirano na nulu direktno na GitHubu!")
                st.rerun()

st.markdown("---")

# --- KORAK 3: MATEMATIKA I PRIKAZ TABLICA ---
cash = podaci_bota.get("cash", 10000.0)
kupljene = podaci_bota.get("kupljene_dionice", {})
povijest = podaci_bota.get("povijest_trejdova", [])

ukupno_investirano = 0.0
trenutna_vrijednost_dionica = 0.0
redovi_tablice = []

for ticker, detalji in kupljene.items():
    kolicina = detalji.get("kolicina", 0)
    ulazna_cijena = detalji.get("cijena", 0)
    u_investirano = kolicina * ulazna_cijena
    ukupno_investirano += u_investirano
    
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
        "Količina (Komada)": kolicina,
        "Kupovna Cijena ($)": round(ulazna_cijena, 2),
        "Trenutna Cijena ($)": round(live_cijena, 2),
        "Ukupno Investirano ($)": round(u_investirano, 2),
        "Trenutna Vrijednost ($)": round(t_vrijednost, 2),
        "Dobit/Gubitak ($)": round(pnl_usd, 2),
        "Dobit/Gubitak (%)": f"{'+' if pnl_usd > 0 else ''}{round(pnl_pct, 2)}%"
    })

# --- KORAK 4: METRIKE NA VRHU (IZ VERZIJE V18) ---
c1, c2, c3 = st.columns(3)
c1.metric("Dostupan fiktivni novac (Cash)", f"${round(cash, 2)}")
c2.metric("Broj aktivnih pozicija", len(kupljene))
c3.metric("Ukupno izvršenih operacija u povijesti", len(povijest))

st.markdown("---")

# --- KORAK 5: KARTICE (TABS) ZASNOVANE NA VAŠIM PODACIMA ---
t1, t2 = st.tabs(["💼 TRENUTNI PORTFOLIO", "📜 POVIJEST LOGOVA TRANSAKCIJA"])

with t1:
    st.subheader("💼 Pozicije koje bot trenutno drži na burzi")
    if redovi_tablice:
        df = pd.DataFrame(redovi_tablice)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Bot trenutno nema otvorenih pozicija (portfelj je prazan).")

with t2:
    st.subheader("📜 Povijest rada i transakcija bota")
    if povijest:
        for log in povijest:
            st.text(log)
    else:
        st.info("Povijest logova je potpuno čista i prazna na GitHubu.")
