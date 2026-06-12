import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🚀 Moj Sveobuhvatni Financijski Terminal V4")

# Stvaramo tri kartice na vrhu ekrana
tab1, tab2, tab3 = st.tabs([
    "🤖 Živi Radar (Automatski Skokovi < $25)", 
    "🎯 Catalyst (Niska cijena & Papiri - uključujući TMC)", 
    "🌍 Globalni Growth & Boom"
])

# ==========================================
# KARTICA 1: POTPUNO AUTOMATSKI LIVE RADAR
# ==========================================
with tab1:
    st.header("Živi Radar: Najveći skokovi volumena na burzi")
    st.write("Ovaj program automatski skenira trenutno najaktivnije dionice na američkim burzama s cijenom ispod 25$ i pronalazi anomalije u volumenu.")

    @st.cache_data(ttl=3600)  # Osvježavanje popisa svakih sat vremena
    def dohvati_live_aktivne_dionice():
        try:
            url = "https://finance.yahoo.com/markets/stocks/most-active/"
            tablice = pd.read_html(url)
            df_aktivne = tablice[0]
            return df_aktivne['Symbol'].dropna().tolist()
        except:
            return ["PLTR", "SOFI", "HOOD", "AFRM", "MARA", "RIOT", "CLSK", "ASTS", "LAC", "CRBP", "NU", "TMC"]

    @st.cache_data
    def scan_live_market(tickers):
        results = []
        if not tickers: return pd.DataFrame()
        data_all = yf.download(tickers, period="2mo", progress=False)
        volume_data = data_all['Volume']
        close_data = data_all['Close']
        
        for ticker in tickers:
            try:
                if isinstance(volume_data, pd.DataFrame) and ticker in volume_data.columns:
                    ticker_volume = volume_data[ticker].dropna()
                    ticker_close = close_data[ticker].dropna()
                else: continue
                
                if len(ticker_volume) > 20 and len(ticker_close) > 20:
                    trenutna_cijena = float(ticker_close.iloc[-1])
                    if trenutna_cijena < 25.0:
                        avg_volume = float(ticker_volume.tail(20).mean())
                        last_volume = float(ticker_volume.iloc[-1])
                        volume_score = round(last_volume / avg_volume, 2) if avg_volume > 0 else 0
                        
                        if volume_score > 1.0:
                            cijena_prije_mjesec = float(ticker_close.iloc[-20])
                            mjesečni_rast = round(((trenutna_cijena - cijena_prije_mjesec) / cijena_prije_mjesec) * 100, 2)
                            results.append({
                                "Dionica": ticker, "Trenutna Cijena ($)": round(trenutna_cijena, 2),
                                "Volume Score (Skok)": volume_score, "Mjesečni Rast (%)": mjesečni_rast
                            })
            except: pass
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values(by="Volume Score (Skok)", ascending=False).reset_index(drop=True)
        return df

    live_popis = dohvati_live_aktivne_dionice()
    df_live = scan_live_market(live_popis)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📋 Pronađene dionice u ekspanziji")
        if not df_live.empty:
            st.dataframe(df_live, use_container_width=True)
        else:
            st.write("Trenutno nema dionica ispod 25$ sa skokom volumena.")
    with col2:
        st.subheader("📊 Vizualni Prikaz Eksplozije Volumena")
        if not df_live.empty:
            fig_live = px.bar(df_live, x="Dionica", y="Volume Score (Skok)", color="Mjesečni Rast (%)", color_continuous_scale="Reds")
            st.plotly_chart(fig_live, use_container_width=True)

# ==========================================
# KARTICA 2: CATALYST (Niska cijena & Papiri - UKLJUČEN TMC i pioniri)
# ==========================================
with tab2:
    st.header("Catalyst Scanner: Spekulativne dionice koje čekaju odobrenja")
    st.write("Ovdje pratiš dionice (poput TMC-a) čija sudbina ovisi o odobrenjima regulatornih tijela, licenci ili ugovora.")
    
    katalizator_dionice = {
        "TMC": "The Metals Company (Rudarenje morskog dna, čeka se ključno odobrenje ISA-e)",
        "LUNR": "Intuitive Machines (Svemirska tehnologija, letovi na Mjesec, ugovori s NASA-om)",
        "AMPX": "Amprius Technologies (Sljedeća generacija baterija, čekaju se vojni i avio certifikati)",
        "LAC": "Lithium Americas (Najveći rudnik litija u SAD-u, čeka se finalna papirologija)",
        "ASTS": "AST SpaceMobile (Satelitski internet izravno na mobitele, čekaju se lansirne dozvole)",
        "CRBP": "Corbus Pharmaceuticals (Lijekovi za pretilost i tumore, klinička ispitivanja)",
        "AVXL": "Anavex Life Sciences (Lijekovi za Alzheimer, čekaju se odobrenja regulatora)",
        "UUUU": "Energy Fuels (Uran, čekaju se ekološke dozvole za proširenje)",
        "BITF": "Bitfarms (Bitcoin rudar, u fazi restrukturiranja i obrane od preuzimanja)"
    }

    @st.cache_data
    def scan_catalyst_stocks(tickers_dict):
        results = []
        tickers = list(tickers_dict.keys())
        data_all = yf.download(tickers, period="2mo", progress=False)
        volume_data = data_all['Volume']
        close_data = data_all['Close']
        
        for ticker in tickers:
            try:
                ticker_volume = volume_data[ticker].dropna()
                ticker_close = close_data[ticker].dropna()
                if len(ticker_volume) > 20 and len(ticker_close) > 20:
                    trenutna_cijena = float(ticker_close.iloc[-1])
                    if trenutna_cijena < 25.0:
                        avg_volume = float(ticker_volume.tail(20).mean())
                        last_volume = float(ticker_volume.iloc[-1])
                        volume_score = round(last_volume / avg_volume, 2) if avg_volume > 0 else 0
                        mjesečni_rast = round(((trenutna_cijena - float(ticker_close.iloc[-20])) / float(ticker_close.iloc[-20])) * 100, 2)
                        results.append({
                            "Dionica": ticker, "Trenutna Cijena ($)": round(trenutna_cijena, 2),
                            "Volume Score (Interes)": volume_score, "Mjesečni Rast (%)": mjesečni_rast,
                            "Glavni Katalizator (Zašto raste?)": tickers_dict[ticker]
                        })
            except: pass
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values(by="Volume Score (Interes)", ascending=False).reset_index(drop=True)
        return df

    df_catalyst = scan_catalyst_stocks(katalizator_dionice)
    col3, col4 = st.columns([1.2, 0.8])
    with col3: st.dataframe(df_catalyst, use_container_width=True)
    with col4:
        if not df_catalyst.empty:
            fig2 = px.bar(df_catalyst, x="Dionica", y="Volume Score (Interes)", color="Mjesečni Rast (%)", color_continuous_scale="Viridis")
            st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# KARTICA 3: GLOBALNI GROWTH & BOOM
# ==========================================
with tab3:
    st.header("Globalni Growth & Boom")
    st.write("Tvoja provjerena lista svjetskih lidera iz Europe, Azije i Amerike za dugoročni rast.")
    
    globalne_perspektivne = [
        "ASML", "SAP", "RACE", "STLA", "CRH", "NVO",
        "TSM", "BABA", "PDD", "SONY", "HMC",
        "NU", "MELI", "HUT", "HBM", "PLTR", "SOFI", "HOOD"
    ]

    @st.cache_data
    def scan_global_stocks(tickers):
        results = []
        data_all = yf.download(tickers, period="2mo", progress=False)
        volume_data = data_all['Volume']
        close_data = data_all['Close']
        
        for ticker in tickers:
            try:
                ticker_volume = volume_data[ticker].dropna()
                ticker_close = close_data[ticker].dropna()
                if len(ticker_volume) > 20:
                    avg_volume = float(ticker_volume.tail(20).mean())
                    last_volume = float(ticker_volume.iloc[-1])
                    volume_score = round(last_volume / avg_volume, 2) if avg_volume > 0 else 0
                    mjesečni_rast = round(((float(ticker_close.iloc[-1]) - float(ticker_close.iloc[-20])) / float(ticker_close.iloc[-20])) * 100, 2)
                    results.append({
                        "Dionica": ticker, "Volume Score (Skok trgovanja)": volume_score,
                        "Mjesečni Rast (%)": mjesečni_rast, "Trenutna Cijena ($)": round(float(ticker_close.iloc[-1]), 2)
                    })
            except: pass
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values(by=["Volume Score (Skok trgovanja)", "Mjesečni Rast (%)"], ascending=[False, False]).reset_index(drop=True)
        return df

    df_global = scan_global_stocks(globalne_perspektivne)
    col5, col6 = st.columns([1, 1])
    with col5: st.dataframe(df_global, use_container_width=True)
    with col6:
        if not df_global.empty:
            df_graf3 = df_global.copy()
            df_graf3['Velicina_Mjehurica'] = df_graf3['Mjesečni Rast (%)'].abs() + 5
            fig3 = px.scatter(df_graf3, x="Volume Score (Skok trgovanja)", y="Mjesečni Rast (%)", size="Velicina_Mjehurica", color="Dionica", hover_name="Dionica", size_max=25)
            st.plotly_chart(fig3, use_container_width=True)
