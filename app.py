import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import json
import google.generativeai as genai

# ---------------------------------------------------------
# 1. 頁面基本配置
# ---------------------------------------------------------
st.set_page_config(
    page_title="台股預測分析系統 APP (v2)",
    page_icon="📈",
    layout="wide"
)

st.title("📈 台股八階段預測與總經分析系統 APP")
st.caption("限定資料來源：公開資訊觀測站 (MOPS) | Yahoo Finance | Gemini AI 總經推論 | 嚴禁 AI 杜撰行情數據")

# ---------------------------------------------------------
# 2. 側邊欄（Sidebar）API Key 讀取邏輯
# ---------------------------------------------------------
st.sidebar.header("⚙️ 系統導覽與 API 設定")

default_api_key = st.secrets.get("GEMINI_API_KEY", "")

if default_api_key:
    st.sidebar.success("🔑 已自動載入背景 API Key")
    api_key = default_api_key
else:
    api_key = st.sidebar.text_input("Gemini API Key (用於工具2 AI動態推論)", type="password")

selected_tool = st.sidebar.radio(
    "核心分析工具區",
    [
        "核心工具 1：全球資金與總經儀表板",
        "核心工具 2：產業趨勢與台灣供應鏈矩陣 (AI 推論)",
        "核心工具 3：個股基本面與 ROI 評分表"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 八階段動態反饋流程")
st.sidebar.caption(
    "1. 全球總經 ➔ 2. 資金風險偏好 ➔ 3. 產業主流(S1-S5) ➔ 4. 台灣供應鏈 ➔ "
    "5. 基本面與估值 ➔ 6. 技術籌碼 ➔ 7. 事件與風控 ➔ 8. 追蹤驗證與修正"
)

# ---------------------------------------------------------
# 工具 1：全球資金與總經儀表板
# ---------------------------------------------------------
if selected_tool == "核心工具 1：全球資金與總經儀表板":
    st.header("🌐 核心工具 1：全球資金與總經儀表板")
    st.write("每日追蹤主要市場、美元、殖利率、VIX、台幣與外資流向，計算全球資金環境評分。")

    @st.cache_data(ttl=3600)
    def load_macro_data():
        tickers = {
            'SOX': '^SOX',         # 費城半導體
            'S&P500': '^GSPC',     # S&P 500
            'DXY': 'DX=F',         # 美元指數
            'US10Y': '^TNX',       # 10年期公債殖利率
            'US2Y': '^IRX',        # 2年期公債殖利率
            'VIX': '^VIX',         # 恐慌指數
            'WTI': 'CL=F',         # 原油
            'Gold': 'GC=F',        # 黃金
            'TWD': 'TWD=X',        # 美元/台幣
            'Nikkei': '^N225'      # 日經 225
        }
        
        raw_data = yf.download(list(tickers.values()), period="3mo", interval="1d")['Close']
        df = pd.DataFrame()
        for name, symbol in tickers.items():
            if symbol in raw_data.columns:
                df[name] = raw_data[symbol]
        
        df = df.ffill().bfill()
        return df

    with st.spinner("連線 Yahoo Finance 抓取真實市場數據中..."):
        try:
            df_macro = load_macro_data()
            latest = df_macro.iloc[-1]
            prev = df_macro.iloc[-2]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("美元指數 DXY", f"{latest['DXY']:.2f}", f"{(latest['DXY']-prev['DXY']):.2f}")
            col2.metric("美債 10Y 殖利率", f"{latest['US10Y']:.2f}%", f"{(latest['US10Y']-prev['US10Y']):.2f}%")
            col3.metric("台幣匯率 USD/TWD", f"{latest['TWD']:.2f}", f"{(latest['TWD']-prev['TWD']):.2f}")
            col4.metric("費城半導體 SOX", f"{latest['SOX']:.0f}", f"{(latest['SOX']-prev['SOX']):.1f}")
            col5.metric("恐慌指數 VIX", f"{latest['VIX']:.2f}", f"{(latest['VIX']-prev['VIX']):.2f}")

            st.markdown("---")
            st.subheader("📊 全球資金環境評分模型（初版）")
            
            score_vix = max(0, min(100, (30 - latest['VIX']) * 5))
            score_dxy = max(0, min(100, (108 - latest['DXY']) * 10))
            score_twd = max(0, min(100, (33 - latest['TWD']) * 20))
            score_sox = 70 if latest['SOX'] > df_macro['SOX'].mean() else 40
            
            total_score = (score_dxy * 0.20) + (score_sox * 0.20) + (score_vix * 0.15) + (score_twd * 0.10) + 25
            
            st.metric("全球資金環境綜合評分 (0-100)", f"{total_score:.1f} 分")
            if total_score >= 65:
                st.success("🟢 目前資金環境偏向「風險承擔 (Risk-On)」，有利於科技股與台股表現。")
            elif total_score >= 45:
                st.warning("🟡 目前資金環境偏向「風險中性」，宜關注個股基本面營收與季報表現。")
            else:
                st.error("🔴 目前資金環境偏向「風險規避 (Risk-Off)」，建議提高防禦持股與現金比重。")

            st.subheader("📈 國際重要指標近期走勢圖")
            st.line_chart(df_macro[['SOX', 'DXY', 'VIX', 'TWD']].tail(30))

        except Exception as e:
            st.error(f"全球總經數據讀取失敗: {e}")

# ---------------------------------------------------------
# 工具 2：產業趨勢與台灣供應鏈矩陣 (AI 動態推論 - 最新 Model API)
# ---------------------------------------------------------
elif selected_tool == "核心工具 2：產業趨勢與台灣供應鏈矩陣 (AI 推論)":
    st.header("🏭 核心工具 2：產業趨勢與台灣供應鏈矩陣")
    st.write("根據國際大盤、殖利率、匯率、VIX 與國際情勢，由 AI 動態推論主流產業傳導矩陣，並連線 Yahoo Finance 驗證行情。")

    mode = st.radio("模式選擇：", ["🤖 AI 總經即時動態推論", "📌 預設主流產業清單"])
    
    selected_matrix = []
    
    if mode == "🤖 AI 總經即時動態推論":
        if not api_key:
            st.info("💡 請在左側欄位輸入 Gemini API Key（或至 Streamlit Secrets 設定），即可啟用 AI 總經動態推論功能。")
        else:
            if st.button("🚀 執行 AI 總經推論分析"):
                with st.spinner("AI 正在分析全球總經數據、Fed 利率與國際情勢並進行 Top-Down 推論..."):
                    try:
                        macro_df = yf.download(["DX=F", "^TNX", "^VIX", "CL=F", "GC=F", "^SOX"], period="5d")['Close'].ffill()
                        latest_m = macro_df.iloc[-1]
                        
                        summary_prompt = f"""
                        最新市場情勢數據：
                        - 美元指數 DXY: {latest_m.get('DX=F', 103):.2f}
                        - 美國10年期公債殖利率: {latest_m.get('^TNX', 4.0):.2f}%
                        - 恐慌指數 VIX: {latest_m.get('^VIX', 15):.2f}
                        - 原油 CL=F: ${latest_m.get('CL=F', 75):.1f}
                        - 黃金 GC=F: ${latest_m.get('GC=F', 2600):.1f}
                        - 費城半導體 SOX: {latest_m.get('^SOX', 5000):.0f}
                        
                        請扮演頂尖法人的總經策略師，根據上述總經背景與資金偏好，推論當前最受惠的 3 個主流產業與台灣供應鏈。
                        務必嚴格僅輸出標準 JSON 格式（不要包含 markdown 標籤或其餘文字），格式範例如下：
                        [
                          {{
                            "industry": "產業名稱",
                            "cycle": "S2: 訂單加速",
                            "driver": "全球需求驅動說明",
                            "bottleneck": "瓶頸與CapEx焦點",
                            "stocks": [["台積電", "2330"], ["萬潤", "6187"]]
                          }}
                        ]
                        """
                        
                        genai.configure(api_key=api_key)
                        
                        # 使用最新版本的 Gemini 模型名稱與自動降級備援機制
                        try:
                            model = genai.GenerativeModel('gemini-3.5-flash')
                            res = model.generate_content(summary_prompt)
                        except Exception:
                            model = genai.GenerativeModel('gemini-2.0-flash')
                            res = model.generate_content(summary_prompt)
                            
                        clean_text = res.text.replace("```json", "").replace("```", "").strip()
                        selected_matrix = json.loads(clean_text)
                        st.session_state['ai_matrix'] = selected_matrix
                    except Exception as e:
                        st.error(f"AI 推論失敗: {e}")
            
            if 'ai_matrix' in st.session_state:
                selected_matrix = st.session_state['ai_matrix']

    else:
        # 預設範例清單
        selected_matrix = [
            {"industry": "AI 資料中心與先進封裝", "cycle": "S2: 訂單加速", "driver": "AI 晶片 / 雲端 CapEx", "bottleneck": "先進封裝 CoWoS", "stocks": [["台積電", "2330"], ["萬潤", "6187"], ["弘塑", "3131"]]},
            {"industry": "高效能水冷散熱", "cycle": "S3: 獲利兌現", "driver": "高功耗伺服器散熱", "bottleneck": "水冷板 / CDP / 分歧管", "stocks": [["奇鋐", "3017"], ["雙鴻", "3324"], ["高力", "8996"]]},
            {"industry": "強韌電網與重電設備", "cycle": "S3: 獲利兌現", "driver": "美國電網更新 / 台灣電網", "bottleneck": "大型變壓器", "stocks": [["華城", "1519"], ["士電", "1503"]]}]

    if selected_matrix:
        st.markdown("---")
        st.subheader("📌 主流產業鏈傳導與受惠股即時行情驗證")
        
        for row in selected_matrix:
            with st.expander(f"🔹 【{row.get('cycle', 'S2')}】{row.get('industry', '主流產業')} ➔ 驅動：{row.get('driver', '')}", expanded=True):
                st.markdown(f"**產業生命週期**：`{row.get('cycle')}`")
                st.markdown(f"**全球需求驅動**：{row.get('driver')}")
                st.markdown(f"**關鍵瓶頸與 CapEx**：{row.get('bottleneck')}")
                
                stocks = row.get('stocks', [])
                if stocks:
                    cols = st.columns(len(stocks))
                    for idx, s_item in enumerate(stocks):
                        s_name, s_code = s_item[0], s_item[1]
                        with cols[idx]:
                            price, chg_pct = None, None
                            for suffix in [".TW", ".TWO"]:
                                try:
                                    t = yf.Ticker(f"{s_code}{suffix}")
                                    h = t.history(period="1mo")
                                    if not h.empty:
                                        price = float(h['Close'].iloc[-1])
                                        chg_pct = float(((price - h['Close'].iloc[0]) / h['Close'].iloc[0]) * 100)
                                        break
                                except Exception:
                                    pass
                            
                            if price:
                                st.metric(
                                    label=f"{s_name} ({s_code})",
                                    value=f"${price:.1f} 元",
                                    delta=f"近1月 {chg_pct:+.1f}%"
                                )
                            else:
                                st.metric(label=f"{s_name} ({s_code})", value="讀取中...")

# ---------------------------------------------------------
# 工具 3：個股基本面與 ROI 評分表
# ---------------------------------------------------------
elif selected_tool == "核心工具 3：個股基本面與 ROI 評分表":
    st.header("📊 核心工具 3：個股基本面與 ROI 評分表")
    st.write("每月更新財務、EPS、估值區間、籌碼與三情境 ROI 分析。")
    
    stock_code = st.text_input("請輸入台股代號（例如：6187 或 2330）：", "6187")
    
    if stock_code:
        fetched_price = None
        trailing_eps = None
        
        with st.spinner(f"連線 Yahoo Finance 擷取 {stock_code} 最新真實財務數據中..."):
            for suffix in [".TWO", ".TW"]:
                try:
                    ticker = yf.Ticker(f"{stock_code}{suffix}")
                    info = ticker.info
                    hist = ticker.history(period="5d")
                    if not hist.empty:
                        fetched_price = float(hist['Close'].iloc[-1])
                        trailing_eps = info.get('trailingEps', None)
                        break
                except Exception:
                    pass
        
        if fetched_price:
            st.success(f"✅ 連線成功！{stock_code} 最新真實收盤價： **${fetched_price:.2f} 元**")
            current_price = fetched_price
        else:
            st.warning("⚠️ 未能自動取得股價，請手動確認。")
            current_price = 1000.0

        base_eps_val = float(trailing_eps) if trailing_eps and trailing_eps > 0 else round(current_price / 25.0, 2)
        base_pe_val = round(current_price / base_eps_val, 1) if base_eps_val > 0 else 25.0
        
        st.subheader(f"🔍 個股基本面與三情境 ROI 試算表（代號：{stock_code}）")
        
        col_bear, col_base, col_bull = st.columns(3)
        with col_bear:
            st.markdown("##### 🔴 悲觀情境 (Prob: 20%)")
            eps_bear = st.number_input("悲觀 12M EPS", value=round(base_eps_val * 0.85, 2))
            pe_bear = st.number_input("悲觀 PE 倍數", value=max(10.0, round(base_pe_val * 0.85, 1)))
        
        with col_base:
            st.markdown("##### 🟡 基準情境 (Prob: 60%)")
            eps_base = st.number_input("基準 12M EPS", value=round(base_eps_val, 2))
            pe_base = st.number_input("基準 PE 倍數", value=round(base_pe_val, 1))
            
        with col_bull:
            st.markdown("##### 🟢 樂觀情境 (Prob: 20%)")
            eps_bull = st.number_input("樂觀 12M EPS", value=round(base_eps_val * 1.20, 2))
            pe_bull = st.number_input("樂觀 PE 倍數", value=round(base_pe_val * 1.15, 1))

        real_price_input = st.number_input("個股當前股價 (元) [自動同步最新價]", value=current_price)
        cash_div = st.number_input("預估未來一年現金股利 (元)", value=round(base_eps_val * 0.6, 1))
        
        target_bear = eps_bear * pe_bear
        roi_bear = ((target_bear + cash_div - real_price_input) / real_price_input) * 100
        
        target_base = eps_base * pe_base
        roi_base = ((target_base + cash_div - real_price_input) / real_price_input) * 100
        
        target_bull = eps_bull * pe_bull
        roi_bull = ((target_bull + cash_div - real_price_input) / real_price_input) * 100
        
        expected_roi = (roi_bear * 0.2) + (roi_base * 0.6) + (roi_bull * 0.2)
        
        st.markdown("---")
        st.subheader("💡 三情境評估結果")
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        res_col1.metric("悲觀目標價 / ROI", f"${target_bear:.1f}", f"{roi_bear:.1f}%")
        res_col2.metric("基準目標價 / ROI", f"${target_base:.1f}", f"{roi_base:.1f}%")
        res_col3.metric("樂觀目標價 / ROI", f"${target_bull:.1f}", f"{roi_bull:.1f}%")
        res_col4.metric("加權期望 ROI", f"{expected_roi:.1f}%")
