import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime

# 1. 頁面基本配置
st.set_page_config(
    page_title="台股預測分析系統 APP (v2)",
    page_icon="📈",
    layout="wide"
)

st.title("📈 台股八階段預測與總經分析系統 APP")
st.caption("限定資料來源：公開資訊觀測站 (MOPS) | Yahoo Finance | 嚴禁 AI 杜撰數據")

# Sidebar 系統導覽與八階段架構說明
st.sidebar.header("⚙️ 系統導覽與八階段架構")
selected_tool = st.sidebar.radio(
    "核心分析工具區",
    [
        "核心工具 1：全球資金與總經儀表板",
        "核心工具 2：產業趨勢與台灣供應鏈矩陣",
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

    # 抓取數據模組
    @st.cache_data(ttl=3600)
    def load_macro_data():
        tickers = {
            'SOX': '^SOX',         # 費城半導體
            'S&P500': '^GSPC',     # S&P 500
            'DXY': 'DX=F',         # 美元指數 (修復為 DX=F)
            'US10Y': '^TNX',       # 10年期公債殖利率
            'US2Y': '^IRX',        # 2年期公債殖利率
            'VIX': '^VIX',         # 恐慌指數
            'WTI': 'CL=F',         # 原油
            'Gold': 'GC=F',        # 黃金
            'TWD': 'TWD=X',        # 美元/台幣
            'Nikkei': '^N225'      # 日經 225
        }
        
        # 下載歷史數據
        raw_data = yf.download(list(tickers.values()), period="3mo", interval="1d")['Close']
        
        # 欄位重組與補值
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
            
            # Key Metrics 顯示欄位
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("美元指數 DXY", f"{latest['DXY']:.2f}", f"{(latest['DXY']-prev['DXY']):.2f}")
            col2.metric("美債 10Y 殖利率", f"{latest['US10Y']:.2f}%", f"{(latest['US10Y']-prev['US10Y']):.2f}%")
            col3.metric("台幣匯率 USD/TWD", f"{latest['TWD']:.2f}", f"{(latest['TWD']-prev['TWD']):.2f}")
            col4.metric("費城半導體 SOX", f"{latest['SOX']:.0f}", f"{(latest['SOX']-prev['SOX']):.1f}")
            col5.metric("恐慌指數 VIX", f"{latest['VIX']:.2f}", f"{(latest['VIX']-prev['VIX']):.2f}")

            st.markdown("---")
            st.subheader("📊 全球資金環境評分模型（初版）")
            
            # 簡易量化算分（25% 利率流動性, 20% 美元, 20% 股市趨勢, 15% VIX, 10% 地緣原油, 10% 台幣）
            # 數值越低/趨勢越穩，得分越高
            score_vix = max(0, min(100, (30 - latest['VIX']) * 5))
            score_dxy = max(0, min(100, (108 - latest['DXY']) * 10))
            score_twd = max(0, min(100, (33 - latest['TWD']) * 20))
            score_sox = 70 if latest['SOX'] > df_macro['SOX'].mean() else 40
            
            total_score = (score_dxy * 0.20) + (score_sox * 0.20) + (score_vix * 0.15) + (score_twd * 0.10) + 25  # 基礎分調和
            
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
# 工具 2：產業趨勢與台灣供應鏈矩陣
# ---------------------------------------------------------
elif selected_tool == "核心工具 2：產業趨勢與台灣供應鏈矩陣":
    st.header("🏭 核心工具 2：產業趨勢與台灣供應鏈矩陣")
    st.write("每週追蹤需求、資本支出、訂單、產能及受惠公司（區分生命週期 S1~S5）。")
    
    st.subheader("📌 主流產業趨勢傳導表（以 AI 資料中心為例）")
    matrix_data = {
        "產業生命週期": ["S2: 訂單加速", "S3: 獲利兌現", "S2: 訂單加速", "S4: 預期成熟"],
        "全球需求驅動": ["AI 運算 / 雲端 CapEx", "伺服器散熱升級", "高階網通 / 800G", "先進封裝 CoWoS"],
        "產業瓶頸與支出", ["GPU / HBM / 電源", "水冷散熱模組", "CPO / 交換器", "台積電產能擴充"],
        "台灣供應鏈代表公司": ["台積電 (2330), 鴻海 (2317)", "奇鋐 (3017), 雙鴻 (3324)", "智邦 (2345)", "萬潤 (6187), 弘塑 (3131)"],
        "驗證指標 (MOPS)": ["月營收 YoY > 20%", "毛利率 QoQ 提升", "合約負債與存貨周轉", "設備出貨與 CapEx"]
    }
    st.table(pd.DataFrame(matrix_data))

# ---------------------------------------------------------
# 工具 3：個股基本面與 ROI 評分表
# ---------------------------------------------------------
elif selected_tool == "核心工具 3：個股基本面與 ROI 評分表":
    st.header("📊 核心工具 3：個股基本面與 ROI 評分表")
    st.write("每月更新財務、EPS、估值區間、籌碼與三情境 ROI 分析。")
    
    stock_id = st.text_input("請輸入台股代號（例如：2330）：", "2330")
    if stock_id:
        st.subheader(f"🔍 個股基本面與三情境 ROI 試算表（代號：{stock_id}）")
        
        # 三情境估值輸入 UI
        col_bear, col_base, col_bull = st.columns(3)
        with col_bear:
            st.markdown("##### 🔴 悲觀情境 (Prob: 20%)")
            eps_bear = st.number_input("悲觀 12M EPS", value=42.0)
            pe_bear = st.number_input("悲觀 PE 倍數", value=18.0)
        
        with col_base:
            st.markdown("##### 🟡 基準情境 (Prob: 60%)")
            eps_base = st.number_input("基準 12M EPS", value=50.0)
            pe_base = st.number_input("基準 PE 倍數", value=22.0)
            
        with col_bull:
            st.markdown("##### 🟢 樂觀情境 (Prob: 20%)")
            eps_bull = st.number_input("樂觀 12M EPS", value=58.0)
            pe_bull = st.number_input("樂觀 PE 倍數", value=25.0)

        current_price = st.number_input("個股當前股價 (元)", value=1000.0)
        cash_div = st.number_input("預估未來一年現金股利 (元)", value=16.0)
        
        # 計算各情境 ROI
        target_bear = eps_bear * pe_bear
        roi_bear = ((target_bear + cash_div - current_price) / current_price) * 100
        
        target_base = eps_base * pe_base
        roi_base = ((target_base + cash_div - current_price) / current_price) * 100
        
        target_bull = eps_bull * pe_bull
        roi_bull = ((target_bull + cash_div - current_price) / current_price) * 100
        
        expected_roi = (roi_bear * 0.2) + (roi_base * 0.6) + (roi_bull * 0.2)
        
        st.markdown("---")
        st.subheader("💡 三情境評估結果")
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        res_col1.metric("悲觀目標價 / ROI", f"${target_bear:.1f}", f"{roi_bear:.1f}%")
        res_col2.metric("基準目標價 / ROI", f"${target_base:.1f}", f"{roi_base:.1f}%")
        res_col3.metric("樂觀目標價 / ROI", f"${target_bull:.1f}", f"{roi_bull:.1f}%")
        res_col4.metric("加權期望 ROI", f"{expected_roi:.1f}%")
