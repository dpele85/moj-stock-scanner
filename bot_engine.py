import yfinance as yf
import pandas as pd
from textblob import TextBlob
import json
import os
from datetime import datetime

FILE_PATH = "portfolio.json"

# --- 1. UCITAJ TRENUTNO STANJE ---
if os.path.exists(FILE_PATH):
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        try:
            podaci = json.load(f)
        except:
            podaci = {"cash": 10000.0, "kupljene_dionice": {}, "povijest_trejdova": []}
else:
    podaci = {"cash": 10000.0, "kupljene_dionice": {}, "povijest_trejdova": []}

# Osiguranje osnovnih ključeva
if "cash" not in podaci: podaci["cash"] = 10000.0
if "kupljene_dionice" not in podaci: podaci["kupljene_dionice"] = {}
if "povijest_trejdova" not in podaci: podaci["povijest_trejdova"] = []

# Postavke agresivnosti
MAX_SREDSTVA_PO_TREJDU = 1500.0
kat_makro = ["GC=F", "CL=F"]
kat_penny = ["TMC", "TRVN", "SOUN", "GFAI", "OTLK"]
kat_catalyst = ["ASTS", "LAC", "CHPT", "NIO", "MARA"]
kat_divovi = ["PLTR", "SOFI", "HOOD", "BABA", "TSM"]
svi_tickerima = kat_makro + kat_penny + kat_catalyst + kat_divovi

def izracunaj_rsi(history_df, period=14):
    if len(history_df) < period + 1: return None
    delta = history_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.fillna(0)))
    return rsi.iloc[-1]

def analiziraj_sentiment(dionica):
    ukupni_score, broj_vijesti = 0, 0
    try:
        for v in dionica.news[:3]:
            naslov = v.get('title', '')
            if naslov:
                score = TextBlob(naslov).sentiment.polarity
                ukupni_score += score
                broj_vijesti += 1
    except: pass
    avg_score = ukupni_score / broj_vijesti if broj_vijesti > 0 else 0
    return "NEGATIVAN" if avg_score < -0.05 else ("POZITIVAN" if avg_score > 0.05 else "NEUTRALAN")

# --- 2. SKENIRANJE I IZVRŠAVANJE ---
izmjena = False
trenutno_vrijeme = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("🤖 Pokrećem pozadinsko AI skeniranje tržišta...")

for t in svi_tickerima:
    try:
        dionica = yf.Ticker(t)
        povijest = dionica.history(period="30d")
        if len(povijest) < 15: continue
        
        if isinstance(povijest.columns, pd.MultiIndex):
            povijest.columns = [col[0] for col in povijest.columns]
            
        cijena = round(povijest['Close'].iloc[-1], 3)
        prethodno_zatvaranje = povijest['Close'].iloc[-2]
        postotak = ((cijena - prethodno_zatvaranje) / prethodno_zatvaranje) * 100
        volumen_score = povijest['Volume'].iloc[-1] / dionica.info.get('averageVolume', 1)
        rsi = izracunaj_rsi(povijest)
        sentiment = analiziraj_sentiment(dionica)
        
        # Agresivne strategije donošenja odluka
        if rsi is not None:
            # PRODAJA (RSI prekupljen ili loš sentiment)
            if t in podaci["kupljene_dionice"] and (rsi > 65 or sentiment == "NEGATIVAN"):
                detalji = podaci["kupljene_dionice"][t]
                kolicina = detalji["kolicina"]
                iznos_prodaje = kolicina * cijena
                podaci["cash"] += iznos_prodaje
                pnl = (cijena - detalji["cijena"]) * kolicina
                
                podaci["povijest_trejdova"].insert(0, f"[{trenutno_vrijeme}] 🔴 AUTO-SELL: Prodan {t} ({kolicina} kom) po ${cijena}. P&L: ${round(pnl, 2)}")
                del podaci["kupljene_dionice"][t]
                izmjena = True
            
            # KUPNJA (RSI jeftin ili snažan proboj s volumenom)
            elif t not in podaci["kupljene_dionice"] and (rsi < 40 or (volumen_score > 1.8 and postotak > 1.5 and rsi < 60)):
                if podaci["cash"] >= 200.0:
                    iznos_kupnje = min(MAX_SREDSTVA_PO_TREJDU, podaci["cash"])
                    kolicina = round(iznos_kupnje / cijena, 3)
                    podaci["cash"] -= (kolicina * cijena)
                    podaci["kupljene_dionice"][t] = {"cijena": cijena, "kolicina": kolicina}
                    
                    podaci["povijest_trejdova"].insert(0, f"[{trenutno_vrijeme}] 🟢 AUTO-BUY: Kupljen {t} ({kolicina} kom) po ${cijena} ($Iznos: {round(iznos_kupnje, 2)})")
                    izmjena = True
    except Exception as e:
        print(f"Greška na {t}: {e}")

# --- 3. SPREMI AKO IMA IZMJENA ---
if izmjena:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(podaci, f, indent=4, ensure_ascii=False)
    print("✅ Portfelj uspješno ažuriran i spremljen.")
else:
    print("⏳ Skeniranje završeno. Nema profitabilnih signala za izvršavanje.")
