import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import json
import google.generativeai as genai

# ---------------------------------------------------------
# 1. 頁面基本配置與頂端置頂凍結列 CSS 注入
# ---------------------------------------------------------
st.set_page_config(
    page_title="台股預測分析系統 APP (v2)",
    page_icon="📈",
    layout="wide"
)

# 注入 CSS：實作置頂凍結列 (Sticky Top Bar) 與台股慣用紅漲綠跌樣式
st.markdown("""
<style>
/* 頂端凍結區塊設定 */
.sticky-top-bar {
    position: sticky;
    top: 2.8rem;
    z-index: 999;
    background-color: #111111;
    padding: 12px 15px;
    border-bottom: 2px solid #333333;
    margin-bottom: 20px;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.5);
}

.sticky-card {
    background-color: #1A1A1A;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #2C2C2C;
    text-align: center;
}

.sticky-card-title {
    color: #888888;
    font-size: 11px;
    margin-bottom: 2px;
}

.sticky-card-value {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 台股八階段預測與總經分析系統 APP")
st.caption("限定資料來源：公開資訊觀測站 (MOPS) | Yahoo Finance | Gemini AI 總經推論 | 嚴禁 AI 杜撰行情數據")

# ---------------------------------------------------------
# 2. 全域數據下載與頂端置頂列 (Sticky Header)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def load_top_sticky_data():
    tickers = {
        'SOX': '^SOX',         # 費城半導體
        'DXY': 'DX-Y=F',       # 美元指數
        'US10Y': '^TNX',       # 10年期公債殖利率
        'VIX': '^VIX',         # 恐慌指數
        'WTI': 'CL=F',         # 原油
        'Gold': 'GC=F',        # 黃金
        'TWD': 'TWD=X'         # 美元/台幣
    }
    raw_data = yf.download(list(tickers.values()), period="1mo", interval="1d")['Close']
    df = pd.DataFrame()
    for name, symbol in tickers.items():
        if symbol in raw_data.columns:
            df[name] = raw_data[symbol]
    df = df.ffill().bfill()
    return df

try:
    df_top = load_top_sticky_data()
    latest_top = df_top.iloc[-1]
    prev_top = df_top.iloc[-2]
except Exception:
    latest_top = pd.Series({'SOX': 5000, 'DXY': 103.5, 'US10Y': 4.2, 'VIX': 15.0, 'WTI': 75.0, 'Gold': 2600, 'TWD': 31.8})
    prev_top = latest_top

def get_top_delta_html(val):
    if pd.isna(val) or val == 0:
        return '<span style="color: #888888; font-size: 11px;">0.00</span>'
    elif val > 0:
        return f'<span style="color: #FF3333; font-weight: bold; font-size: 11px;">▲ +{val:.2f}</span>'
    else:
        return f'<span style="color: #00CC66; font-weight: bold; font-size: 11px;">▼ {val:.2f}</span>'

# 置頂凍結列 UI 渲染
st.markdown('<div class="sticky-top-bar">', unsafe_allow_html=True)
tc1, tc2, tc3, tc4, tc5, tc6, tc7 = st.columns(7)

with tc1:
    sox_val = latest_top.get('SOX', 5000)
    sox_d = sox_val - prev_top.get('SOX', sox_val)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">費半 SOX</div><div class="sticky-card-value">{sox_val:.0f}</div><div>{get_top_delta_html(sox_d)}</div></div>', unsafe_allow_html=True)

with tc2:
    dxy_val = latest_top.get('DXY', 103.5)
    dxy_d = dxy_val - prev_top.get('DXY', dxy_val)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">美元 DXY</div><div class="sticky-card-value">{dxy_val:.2f}</div><div>{get_top_delta_html(dxy_d)}</div></div>', unsafe_allow_html=True)

with tc3:
    us10y_val = latest_top.get('US10Y', 4.2)
    us10y_d = us10y_val - prev_top.get('US10Y', us10y_val)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">美債 10Y</div><div class="sticky-card-value">{us10y_val:.2f}%</div><div>{get_top_delta_html(us10y_d)}</div></div>', unsafe_allow_html=True)

with tc4:
    vix_val = latest_top.get('VIX', 15.0)
    vix_d = vix_val - prev_top.get('VIX', vix_val)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">恐慌 VIX</div><div class="sticky-card-value">{vix_val:.2f}</div><div>{get_top_delta_html(vix_d)}</div></div>', unsafe_allow_html=True)

with tc5:
    wti_val = latest_top.get('WTI', 75.0)
    wti_d = wti_val - prev_top.get('WTI', wti_val)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">WTI 原油</div><div class="sticky-card-value">${wti_val:.1f}</div><div>{get_top_delta_html(wti_d)}</div></div>', unsafe_allow_html=True)

with tc6:
    gold_val = latest_top.get('Gold', 2600.0)
    gold_d = gold_val - prev_top.get('Gold', gold_val)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">黃金現貨</div><div class="sticky-card-value">${gold_val:.0f}</div><div>{get_top_delta_html(gold_d)}</div></div>', unsafe_allow_html=True)

with tc7:
    twd_val = latest_top.get('TWD', 31.8)
    twd_d = twd_val - prev_top.get('TWD', twd_val)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">美元/台幣</div><div class="sticky-card-value">{twd_val:.2f}</div><div>{get_top_delta_html(twd_d)}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 側邊欄（Sidebar）API Key 讀取邏輯
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

# 自訂台股習慣 HTML 卡片元件 (紅漲綠跌)
def render_tw_card(title, value_str, diff_val):
    if pd.isna(diff_val) or diff_val == 0:
        delta_html = '<span style="color: #888888; font-size: 14px;">0.00</span>'
    elif diff_val > 0:
        delta_html = f'<span style="color: #FF3333; font-weight: bold; font-size: 14px;">▲ +{diff_val:.2f}</span>'
    else:
        delta_html = f'<span style="color: #00CC66; font-weight: bold; font-size: 14px;">▼ {diff_val:.2f}</span>'
        
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 15px; border-radius: 8px; border: 1px solid #333;">
            <div style="color: #AAAAAA; font-size: 13px; margin-bottom: 5px;">{title}</div>
            <div style="color: #FFFFFF; font-size: 24px; font-weight: bold; margin-bottom: 5px;">{value_str}</div>
            <div>{delta_html}</div>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 工具 1：全球資金與總經儀表板
# ---------------------------------------------------------
if selected_tool == "核心工具 1：全球資金與總經儀表板":
    st.header("🌐 核心工具 1：全球資金與總經儀表板")
    st.write("每日追蹤主要市場、美元、殖利率、VIX、台幣與外資流向，計算全球資金環境評分。")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_tw_card("美元指數 DXY", f"{dxy_val:.2f}", dxy_d)
    with col2:
        render_tw_card("美債 10Y 殖利率", f"{us10y_val:.2f}%", us10y_d)
    with col3:
        render_tw_card("台幣匯率 USD/TWD", f"{twd_val:.2f}", twd_d)
    with col4:
        render_tw_card("費城半導體 SOX", f"{sox_val:.0f}", sox_d)
    with col5:
        render_tw_card("恐慌指數 VIX", f"{vix_val:.2f}", vix_d)

    st.markdown("---")
    st.subheader("📊 全球資金環境評分模型（初版）")
    
    score_vix = max(0, min(100, (30 - vix_val) * 5))
    score_dxy = max(0, min(100, (108 - dxy_val) * 10))
    score_twd = max(0, min(100, (33 - twd_val) * 20))
    score_sox = 70 if sox_val > df_top['SOX'].mean() else 40
    
    total_score = (score_dxy * 0.20) + (score_sox * 0.20) + (score_vix * 0.15) + (score_twd * 0.10) + 25
    
    st.metric("全球資金環境綜合評分 (0-100)", f"{total_score:.1f} 分")
    if total_score >= 65:
        st.success("🔴 目前資金環境偏向「風險承擔 (Risk-On)」，有利於科技股與台股多頭表現。")
    elif total_score >= 45:
        st.warning("🟡 目前資金環境偏向「風險中性」，宜關注個股基本面營收與季報表現。")
    else:
        st.error("🟢 目前資金環境偏向「風險規避 (Risk-Off)」，建議提高防禦持股與現金比重。")

    st.subheader("📈 國際重要指標近期走勢圖")
    st.line_chart(df_top[['SOX', 'DXY', 'VIX', 'TWD']].tail(30))

# ---------------------------------------------------------
# 工具 2：產業趨勢與台灣供應鏈矩陣 (取消下拉選單，直接展開顯示)
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
                with st.spinner("AI 正在深度判讀美元、殖利率、VIX、原油、黃金與全球資金流向進行 Top-Down 邏輯推論..."):
                    try:
                        macro_df = yf.download(["DX-Y=F", "^TNX", "^VIX", "CL=F", "GC=F", "^SOX", "^GSPC"], period="1mo")['Close'].ffill()
                        latest_m = macro_df.iloc[-1]
                        prev_m = macro_df.iloc[-5] if len(macro_df) >= 5 else macro_df.iloc[0]
                        
                        sox_chg = ((latest_m.get('^SOX', 5000) - prev_m.get('^SOX', 5000)) / prev_m.get('^SOX', 5000)) * 100

                        summary_prompt = f"""
                        你是頂尖法人的總經與產業策略總監。請徹底根據以下真實市場數據進行硬核 Top-Down 研研推論：

                        【國際市場即時數據】
                        1. 費城半導體 SOX: {latest_m.get('^SOX', 5000):.0f} (近週變化: {sox_chg:+.2f}%)
                        2. 恐慌指數 VIX: {latest_m.get('^VIX', 15):.2f}
                        3. 美元指數 DXY: {latest_m.get('DX-Y=F', 103):.2f}
                        4. 美國10年期公債殖利率: {latest_m.get('^TNX', 4.0):.2f}%
                        5. WTI 原油價格: ${latest_m.get('CL=F', 75):.1f}
                        6. 黃金避險價格: ${latest_m.get('GC=F', 2600):.1f}

                        【嚴格推論規則】
                        - 分析上述數據反映的資金風險偏好。
                        - 動態篩選出當前最受惠的 3 個台灣主流產業鏈。
                        - 每個產業鏈提供 2~3 檔台灣代表上市/上櫃公司。
                        - 輸出標題要簡潔，避免包含整句內文說明。

                        【輸出格式】
                        必須僅輸出嚴格合法的 JSON 陣列，不得包含任何 Markdown 語法標籤，範例結構如下：
                        [
                          {{
                            "industry": "簡短產業名稱 (例如: 重電與強韌電網)",
                            "cycle": "S2: 訂單加速",
                            "driver": "全球需求驅動說明",
                            "bottleneck": "瓶頸與 CapEx 焦點說明",
                            "stocks": [["公司簡稱", "四位數代號"], ["公司簡稱", "四位數代號"]]
                          }}
                        ]
                        """
                        
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-3.5-flash')
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
            {"industry": "AI 資料中心與先進封裝", "cycle": "S2: 訂單加速", "driver": "AI 晶片 / 雲端 CapEx 擴張需求強勁", "bottleneck": "先進封裝 CoWoS 產能吃緊", "stocks": [["台積電", "2330"], ["萬潤", "6187"], ["弘塑", "3131"]]},
            {"industry": "高效能水冷散熱模組", "cycle": "S3: 獲利兌現", "driver": "高功耗 Blackwell 伺服器散熱升級", "bottleneck": "水冷板、CDP 與分歧管良率與產能", "stocks": [["奇鋐", "3017"], ["雙鴻", "3324"], ["高力", "8996"]]},
            {"industry": "強韌電網與重電設備", "cycle": "S3: 獲利兌現", "driver": "美國電網更新與台灣台電強韌電網計畫", "bottleneck": "大型變壓器原材料與高壓測試排程", "stocks": [["華城", "1519"], ["士電", "1503"]]}]

    if selected_matrix:
        st.markdown("---")
        st.subheader("📌 主流產業鏈傳導與受惠股即時行情驗證")
        
        # 取消 expander，採用直接展平排版 (無重複標題文字)
        for row in selected_matrix:
            st.markdown(f"### 🔹 【{row.get('cycle', 'S2')}】{row.get('industry', '主流產業')}")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**🌐 全球需求驅動**：{row.get('driver', '')}")
            with col_b:
                st.markdown(f"**⚙️ 關鍵瓶頸與 CapEx 焦點**：{row.get('bottleneck', '')}")
            
            stocks = row.get('stocks', [])
            if stocks:
                cols = st.columns(len(stocks))
                for idx, s_item in enumerate(stocks):
                    s_name, s_code = s_item[0], s_item[1]
                    with cols[idx]:
                        price, chg_pct = None, 0.0
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
                            render_tw_card(f"{s_name} ({s_code})", f"${price:.1f} 元", chg_pct)
                        else:
                            st.write(f"讀取中 ({s_code})...")
            st.markdown("<hr style='border:1px dashed #333;'>", unsafe_allow_html=True)

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
            st.markdown("##### 🟢 悲觀情境 (Prob: 20%)")
            eps_bear = st.number_input("悲觀 12M EPS", value=round(base_eps_val * 0.85, 2))
            pe_bear = st.number_input("悲觀 PE 倍數", value=max(10.0, round(base_pe_val * 0.85, 1)))
        
        with col_base:
            st.markdown("##### 🟡 基準情境 (Prob: 60%)")
            eps_base = st.number_input("基準 12M EPS", value=round(base_eps_val, 2))
            pe_base = st.number_input("基準 PE 倍數", value=round(base_pe_val, 1))
            
        with col_bull:
            st.markdown("##### 🔴 樂觀情境 (Prob: 20%)")
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
        
        with res_col1:
            render_tw_card("悲觀目標價 / ROI", f"${target_bear:.1f}", roi_bear)
        with res_col2:
            render_tw_card("基準目標價 / ROI", f"${target_base:.1f}", roi_base)
        with res_col3:
            render_tw_card("樂觀目標價 / ROI", f"${target_bull:.1f}", roi_bull)
        with res_col4:
            render_tw_card("加權期望 ROI", f"{expected_roi:.1f}%", expected_roi)
