import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from textblob import TextBlob

# 1. Postavke stranice
st.set_page_config(page_title="AI Financijski Terminal V13", layout="wide", initial_sidebar_state="collapsed")

# --- STABILNA INICIJALIZACIJA MEMORIJE ---
if "kupljene_dionice" not in st.session_state:
    st.session_state.kupljene_dionice = {}
if "povijest_trejdova" not in st.session_state:
    st.session_state.povijest_trejdova = []
# -----------------------------------------------------

# 2. Naslov i gumb za osvježavanje
st.title("🤖 Moj AI Financijski Terminal V13")
st.caption("Profesionalni radar s ugrađenim RSI indikatorom, pametnim probojima i stabilnom memorijom.")

if st.button("🔄 RESTARTAJ TERMINAL I OSVJEŽI ANALIZU", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 3. Popis imovine po grupama
kat_makro = ["GC=F", "CL=F"]
kat_penny = ["TMC", "TRVN", "SOUN", "GFAI", "OTLK"]
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
        
        # --- ROBUZNIJI POPRAVAK ZA DOHVAT VIJESTI ---
        try:
            vijesti_izvor = dionica.news
            if vijesti_izvor and isinstance(vijesti_izvor, list) and len(vijesti_izvor) > 0:
                for v in vijesti_izvor[:5]:  # Povećano na max 5 vijesti
                    naslov = v.get('title', '').strip()
                    izvor = v.get('publisher', 'Yahoo Finance')
                    link = v.get('link', '#')
                    
                    if naslov:
                        score, oznaka = analiziraj_sentiment(naslov)
                        ukupni_sentiment_score += score
                        broj_pravih_vijesti += 1
                        pokupljene_vijesti.append({
                            "naslov": naslov, 
                            "izvor": izvor, 
                            "link": link,
                            "ai_oznaka": oznaka
                        })
        except Exception as e:
            pass
        
        if len(pokupljene_vijesti) == 0:
            pokupljene_vijesti.append({
                "naslov": "Nema novih objava na Yahoo Finance za ovaj ticker u zadnja 24h.",
                "izvor": "Sustav Radara",
                "link": "#",
                "ai_oznaka": "🟡 Neutralno"
            })
        
        if broj_pravih_vijesti > 0:
            prosjek = ukupni_sentiment_score / broj_pravih_vijesti
            konacni_sentiment = "🟢 POZITIVAN" if prosjek > 0.05 else ("🔴 NEGATIVAN" if prosjek < -0.05 else "🟡 NEUTRALAN")
        else:
            konacni_sentiment = "🟡 NEUTRALAN"
            
        # --- NOVI PAMETNIJI I SIGURNIJI UVJETI ZA STATUS ---
        if rsi_vrijednost is not None:
            if rsi_vrijednost > 70:
                status = "⚠️ RISK (PREKUPLJENO)"
            elif rsi_vrijednost < 33:  # BABA će sada odmah uloviti ovaj signal!
                status = "🔥 SIGNAL KUPNJE"
            elif volume_score > 2.0 and postotak > 2:
                if rsi_vrijednost < 60:
                    status = "🚀 PROBOJ (MOŽE SE KUPITI)"
                else:
                    status = "⚠️ PROBOJ (RIZIK VRHA)"
            elif rsi_vrijednost < 38:
                status = "🛒 JEFTINO (PRATI)"
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

# --- FUNKCIJA ZA PRIKAZ I UPIS KUPNJE ---
def prikazi_tablicu_i_graf(lista_tickera, kljuc_grafikona):
    podaci_lista = []
    with st.spinner("🤖 AI povlači podatke s burze..."):
        for t in lista_tickera:
            rezultat = dohvati_podatke(t)
            if rezultat:
                podaci_lista.append(rezultat)
            
    if podaci_lista:
        df = pd.DataFrame(podaci_lista)
        
        stupci_za_prikaz = ["Ticker", "Cijena ($)", "Promjena (%)", "Volume Score", "RSI (14)", "AI Status", "52-Tjedni Raspon"]
        st.dataframe(
            df[stupci_za_prikaz].style.format({
                "Cijena ($)": "{:.3f}",
                "Promjena (%)": "{:+.2f}%",
                "Volume Score": "{:.2f}x"
            }),
            use_container_width=True, hide_index=True
        )
        
        st.markdown("### 📊 Brzi pregled dnevnih promjena")
        fig_promjena = px.bar(
            df, 
            x="Ticker", 
            y="Promjena (%)", 
            color="Promjena (%)",
            color_continuous_scale=["red", "gray", "green"],
            title="Dnevni postotni pomak dionica u ovoj grupi"
        )
        st.plotly_chart(fig_promjena, use_container_width=True)

        st.markdown("### 🛒 Unesi kupljene pozicije:")
        mini_kolone = st.columns(len(df))
        
        for i, redak in df.iterrows():
            with mini_kolone[i]:
                ticker = redak['Ticker']
                with st.popover(f"Kupi {ticker}", use_container_width=True):
                    st.write(f"**Nova transakcija za {ticker}**")
                    kolicina_unos = st.number_input("Količina dionica:", min_value=0.001, value=1.0, step=1.0, key=f"qty_{kljuc_grafikona}_{ticker}")
                    cijena_unos = st.number_input("Kupljeno po cijeni ($):", min_value=0.0, value=float(redak['Cijena ($)']), step=0.01, format="%.3f", key=f"prc_{kljuc_grafikona}_{ticker}")
                    
                    if st.button("Potvrdi i spremi", key=f"btn_{kljuc_grafikona}_{ticker}", use_container_width=True):
                        if ticker in st.session_state.kupljene_dionice:
                            stara_kol = st.session_state.kupljene_dionice[ticker]['kolicina']
                            stara_cij = st.session_state.kupljene_dionice[ticker]['cijena']
                            
                            nova_ukupna_kol = stara_kol + kolicina_unos
                            nova_prosjecna_cijena = ((stara_kol * stara_cij) + (kolicina_unos * cijena_unos)) / nova_ukupna_kol
                            
                            st.session_state.kupljene_dionice[ticker] = {
                                'cijena': round(nova_prosjecna_cijena, 3), 
                                'kolicina': round(nova_ukupna_kol, 3)
                            }
                        else:
                            st.session_state.kupljene_dionice[ticker] = {
                                'cijena': round(cijena_unos, 3), 
                                'kolicina': round(kolicina_unos, 3)
                            }
                        
                        st.session_state.povijest_trejdova.append(f"Kupljeno {kolicina_unos} komada {ticker} po ${cijena_unos}")
                        st.success(f"Uspješno spremljeno: {ticker}")
                        st.rerun()
                    
        with st.expander("📰 Pogledaj AI vijesti i sentiment za ove dionice"):
            for dionica_info in podaci_lista:
                st.write(f"**{dionica_info['Ticker']}** | Ukupni AI Sentiment: **{dionica_info['AI Sentiment']}**")
                for v in dionica_info['Vijesti']:
                    st.write(f"- {v['ai_oznaka']} | [{v['izvor']}]({v['link']}): *{v['naslov']}*")
                st.markdown("---")
    else:
        st.error("Nije moguće dohvatiti podatke.")

# 4. Kreiranje tabova u aplikaciji
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💼 MOJE OTVORENE POZICIJE", 
    "📈 Geopolitika & Makro", 
    "🪙 Penny / Mali Radari", 
    "⚡ Catalyst Dionice", 
    "🏛️ Globalni Divovi"
])

# --- TAB 1: PORTFOLIO S RAČUNANJEM DOBITI/GUBITKA (P&L) UŽIVO ---
with tab1:
    st.header("💼 Vaš Portfolio i Praćenje Zarade")
    
    if not st.session_state.kupljene_dionice:
        st.info("Trenutno nemate otvorenih pozicija. Unesite kupnju unutar ostalih tabova.")
    else:
        portfolio_podaci = []
        ukupno_investirano = 0.0
        ukupna_trenutna_vrijednost = 0.0
        
        for t, detalji in st.session_state.kupljene_dionice.items():
            trenutni_podaci = dohvati_podatke(t)
            if trenutni_podaci:
                trenutna_cijena = trenutni_podaci["Cijena ($)"]
                kolicina = detalji["kolicina"]
                ulazna_cijena = detalji["cijena"]
                
                investirano = kolicina * ulazna_cijena
                trenutna_vrijednost = kolicina * trenutna_cijena
                pnl_usd = trenutna_vrijednost - investirano
                pnl_postotak = (pnl_usd / investirano) * 100 if investirano > 0 else 0
                
                ukupno_investirano += investirano
                ukupna_trenutna_vrijednost += trenutna_vrijednost
                
                portfolio_podaci.append({
                    "Ticker": t,
                    "Količina": kolicina,
                    "Prosječna Ulazna ($)": ulazna_cijena,
                    "Trenutna Cijena ($)": trenutna_cijena,
                    "Ukupno Investirano ($)": round(investirano, 2),
                    "Trenutna Vrijednost ($)": round(trenutna_vrijednost, 2),
                    "Dobit / Gubitak ($)": round(pnl_usd, 2),
                    "Dobit / Gubitak (%)": round(pnl_postotak, 2)
                })
        
        ukupni_pnl_usd = ukupna_trenutna_vrijednost - ukupno_investirano
        ukupni_pnl_pct = (ukupni_pnl_usd / ukupno_investirano) * 100 if ukupno_investirano > 0 else 0
        
        met1, met2, met3 = st.columns(3)
        met1.metric("Ukupno Investirano", f"${round(ukupno_investirano, 2)}")
        met2.metric("Trenutna Vrijednost", f"${round(ukupna_trenutna_vrijednost, 2)}")
        met3.metric("Ukupni P&L (Zarada/Gubitak)", f"${round(ukupni_pnl_usd, 2)}", f"{round(ukupni_pnl_pct, 2)}%")
        
        st.markdown("---")
        st.subheader("📋 Detaljni pregled otvorenih pozicija:")
        
        df_port = pd.DataFrame(portfolio_podaci)
        
        def obojaj_pnl(val):
            color = 'green' if val > 0 else ('red' if val < 0 else 'black')
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(
            df_port.style.format({
                "Količina": "{:.2f}",
                "Prosječna Ulazna ($)": "{:.3f}",
                "Trenutna Cijena ($)": "{:.3f}",
                "Ukupno Investirano ($)": "${:.2f}",
                "Trenutna Vrijednost ($)": "${:.2f}",
                "Dobit / Gubitak ($)": "{:+.2f}",
                "Dobit / Gubitak (%)": "{:+.2f}%"
            }).map(obojaj_pnl, subset=["Dobit / Gubitak ($)", "Dobit / Gubitak (%)"]),
            use_container_width=True, hide_index=True
        )
        
        if st.button("🗑️ OBRIŠI SVE POZICIJE I RESETIRAJ PORTFOLIO", use_container_width=True):
            st.session_state.kupljene_dionice = {}
            st.session_state.povijest_trejdova = []
            st.rerun()
            
    if st.session_state.povijest_trejdova:
        with st.expander("📜 Povijest zapisanih transakcija"):
            for log in st.session_state.povijest_trejdova:
                st.text(log)

with tab2:
    st.header("📈 Geopolitika i Makro ekonomija")
    prikazi_tablicu_i_graf(kat_makro, "makro")

with tab3:
    st.header("🪙 Penny Dionice / Visoki rizik")
    prikazi_tablicu_i_graf(kat_penny, "penny")

with tab4:
    st.header("⚡ Catalyst Dionice (Rast i vijesti)")
    prikazi_tablicu_i_graf(kat_catalyst, "catalyst")

with tab5:
    st.header("🏛️ Velike stabilne kompanije i HOOD")
    prikazi_tablicu_i_graf(kat_divovi, "divovi")
