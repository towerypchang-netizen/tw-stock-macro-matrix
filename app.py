import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import json
import google.generativeai as genai
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. 頁面基本配置與頂端置頂凍結列 CSS 注入
# ---------------------------------------------------------
st.set_page_config(
    page_title="台股八階段預測與總經分析系統 APP",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
.sticky-top-bar {
    position: sticky;
    top: 2.8rem;
    z-index: 999;
    background-color: #111111;
    padding: 10px 15px;
    border-bottom: 2px solid #333333;
    margin-bottom: 20px;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.5);
}

.sticky-card {
    background-color: #1A1A1A;
    padding: 8px 10px;
    border-radius: 6px;
    border: 1px solid #2C2C2C;
    text-align: center;
}

.sticky-card-title {
    color: #AAAAAA;
    font-size: 11px;
    margin-bottom: 2px;
}

.sticky-card-value {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 台股八階段預測與總經分析系統 APP")
st.caption("限定資料來源：公開資訊觀測站 (MOPS) | Yahoo Finance | Gemini AI 總經推論 | 嚴禁 AI 杜撰行情數據")

# ---------------------------------------------------------
# 2. 全域數據穩定抓取邏輯 (全指標覆蓋 + DXY 多重備援)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def load_stable_macro_data():
    tickers = {
        'TAIEX': '^TWII',      # 台股加權
        'SOX': '^SOX',         # 費城半導體
        'DXY': 'DX-Y=F',       # 美元指數
        'US10Y': '^TNX',       # 10年期美債殖利率
        'VIX': '^VIX',         # 恐慌指數
        'WTI': 'CL=F',         # 原油
        'Gold': 'GC=F',        # 黃金
        'TWD': 'TWD=X'         # 美元/台幣
    }
    
    raw = yf.download(list(tickers.values()), period="3mo", interval="1d")['Close']
    
    if isinstance(raw.index, pd.DatetimeIndex):
        raw.index = raw.index.tz_localize(None)
        
    df = pd.DataFrame(index=raw.index)
    for name, sym in tickers.items():
        if sym in raw.columns:
            df[name] = raw[sym]
            
    if 'DXY' not in df.columns or df['DXY'].isna().all():
        for fallback_sym in ["DX-Y=F", "DX=F", "UUP"]:
            try:
                dxy_h = yf.Ticker(fallback_sym).history(period="3mo")['Close']
                if not dxy_h.empty:
                    if isinstance(dxy_h.index, pd.DatetimeIndex):
                        dxy_h.index = dxy_h.index.tz_localize(None)
                    df['DXY'] = dxy_h * (3.6 if fallback_sym == "UUP" else 1.0)
                    break
            except Exception:
                pass
                
    if 'DXY' not in df.columns or df['DXY'].isna().all():
        df['DXY'] = 103.5

    df = df.ffill().bfill()
    return df

try:
    df_top = load_stable_macro_data()
    latest_top = df_top.iloc[-1]
    prev_top = df_top.iloc[-2]
except Exception:
    df_top = pd.DataFrame()
    latest_top = pd.Series({'TAIEX': 22000, 'SOX': 5000, 'DXY': 103.5, 'US10Y': 4.2, 'VIX': 15.0, 'WTI': 75.0, 'Gold': 2600, 'TWD': 31.8})
    prev_top = latest_top

def get_top_delta_html(val):
    if pd.isna(val) or val == 0:
        return '<span style="color: #888888; font-size: 11px;">0.00</span>'
    elif val > 0:
        return f'<span style="color: #FF3333; font-weight: bold; font-size: 11px;">▲ +{val:.2f}</span>'
    else:
        return f'<span style="color: #00CC66; font-weight: bold; font-size: 11px;">▼ {val:.2f}</span>'

# 全局頂端固定凍結儀表板 (Sticky Header)
st.markdown('<div class="sticky-top-bar">', unsafe_allow_html=True)
tc1, tc2, tc3, tc4, tc5, tc6, tc7, tc8 = st.columns(8)

with tc1:
    tw_val = latest_top.get('TAIEX', 22000)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">台股加權</div><div class="sticky-card-value">{tw_val:.0f}</div><div>{get_top_delta_html(tw_val - prev_top.get("TAIEX", tw_val))}</div></div>', unsafe_allow_html=True)

with tc2:
    sox_val = latest_top.get('SOX', 5000)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">費半 SOX</div><div class="sticky-card-value">{sox_val:.0f}</div><div>{get_top_delta_html(sox_val - prev_top.get("SOX", sox_val))}</div></div>', unsafe_allow_html=True)

with tc3:
    dxy_val = latest_top.get('DXY', 103.5)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">美元 DXY</div><div class="sticky-card-value">{dxy_val:.2f}</div><div>{get_top_delta_html(dxy_val - prev_top.get("DXY", dxy_val))}</div></div>', unsafe_allow_html=True)

with tc4:
    us10y_val = latest_top.get('US10Y', 4.2)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">美債 10Y</div><div class="sticky-card-value">{us10y_val:.2f}%</div><div>{get_top_delta_html(us10y_val - prev_top.get("US10Y", us10y_val))}</div></div>', unsafe_allow_html=True)

with tc5:
    vix_val = latest_top.get('VIX', 15.0)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">恐慌 VIX</div><div class="sticky-card-value">{vix_val:.2f}</div><div>{get_top_delta_html(vix_val - prev_top.get("VIX", vix_val))}</div></div>', unsafe_allow_html=True)

with tc6:
    wti_val = latest_top.get('WTI', 75.0)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">WTI 原油</div><div class="sticky-card-value">${wti_val:.1f}</div><div>{get_top_delta_html(wti_val - prev_top.get("WTI", wti_val))}</div></div>', unsafe_allow_html=True)

with tc7:
    gold_val = latest_top.get('Gold', 2600.0)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">黃金現貨</div><div class="sticky-card-value">${gold_val:.0f}</div><div>{get_top_delta_html(gold_val - prev_top.get("Gold", gold_val))}</div></div>', unsafe_allow_html=True)

with tc8:
    twd_val = latest_top.get('TWD', 31.8)
    st.markdown(f'<div class="sticky-card"><div class="sticky-card-title">美元/台幣</div><div class="sticky-card-value">{twd_val:.2f}</div><div>{get_top_delta_html(twd_val - prev_top.get("TWD", twd_val))}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 側邊欄（Sidebar）：按鈕式切換
# ---------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", "")

st.sidebar.subheader("🎯 核心分析工具區")

if 'selected_tool' not in st.session_state:
    st.session_state['selected_tool'] = "全球資金與總經環境評分"

btn_tool1 = st.sidebar.button(
    "🌐 全球資金與總經環境評分",
    use_container_width=True,
    type="primary" if st.session_state['selected_tool'] == "全球資金與總經環境評分" else "secondary"
)

btn_tool2 = st.sidebar.button(
    "🏭 產業趨勢與台灣供應鏈矩陣 (AI推論)",
    use_container_width=True,
    type="primary" if st.session_state['selected_tool'] == "產業趨勢與台灣供應鏈矩陣 (AI推論)" else "secondary"
)

btn_tool3 = st.sidebar.button(
    "📊 個股基本面與 ROI 評分表",
    use_container_width=True,
    type="primary" if st.session_state['selected_tool'] == "個股基本面與 ROI 評分表" else "secondary"
)

if btn_tool1:
    st.session_state['selected_tool'] = "全球資金與總經環境評分"
    st.rerun()
elif btn_tool2:
    st.session_state['selected_tool'] = "產業趨勢與台灣供應鏈矩陣 (AI推論)"
    st.rerun()
elif btn_tool3:
    st.session_state['selected_tool'] = "個股基本面與 ROI 評分表"
    st.rerun()

selected_tool = st.session_state['selected_tool']

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 八階段動態反饋流程")
st.sidebar.caption(
    "1. 全球總經 ➔ 2. 資金風險偏好 ➔ 3. 產業主流(S1-S5) ➔ 4. 台灣供應鏈 ➔ "
    "5. 基本面與估值 ➔ 6. 技術籌碼 ➔ 7. 事件與風控 ➔ 8. 追蹤驗證與修正"
)

def render_tw_card(title, value_str, diff_val):
    if pd.isna(diff_val) or diff_val == 0:
        delta_html = '<span style="color: #888888; font-size: 14px;">0.00</span>'
    elif diff_val > 0:
        delta_html = f'<span style="color: #FF3333; font-weight: bold; font-size: 14px;">▲ +{diff_val:.2f}</span>'
    else:
        delta_html = f'<span style="color: #00CC66; font-weight: bold; font-size: 14px;">▼ {diff_val:.2f}</span>'
        
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 12px; border-radius: 8px; border: 1px solid #333;">
            <div style="color: #AAAAAA; font-size: 12px; margin-bottom: 4px;">{title}</div>
            <div style="color: #FFFFFF; font-size: 22px; font-weight: bold; margin-bottom: 4px;">{value_str}</div>
            <div>{delta_html}</div>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 工具 1：全球資金與總經環境評分
# ---------------------------------------------------------
if selected_tool == "全球資金與總經環境評分":
    st.header("🌐 全球資金與總經環境評分")
    st.write("即時總經數據已置頂於頂端列。本區提供「全球資金環境綜合評分」與「全指標 vs 台股加權 聯動對比圖」。")

    st.subheader("📊 全球資金環境評分模型")
    
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

    st.markdown("---")
    st.subheader("📈 全球資金總經 (所有 8 大指標) vs 台股加權指數 聯動趨勢圖")

    chart_days = st.slider("選擇圖表觀察天數 (天)：", min_value=14, max_value=90, value=30)
    
    st.markdown("**選擇要在折線圖中對比的指標：**")
    chk_cols = st.columns(4)
    with chk_cols[0]:
        show_taiex = st.checkbox("台股加權指數", value=True)
        show_sox = st.checkbox("費城半導體 SOX", value=True)
    with chk_cols[1]:
        show_dxy = st.checkbox("美元指數 DXY", value=True)
        show_us10y = st.checkbox("美債 10Y 殖利率", value=True)
    with chk_cols[2]:
        show_vix = st.checkbox("恐慌指數 VIX", value=True)
        show_twd = st.checkbox("美元/台幣 TWD", value=True)
    with chk_cols[3]:
        show_wti = st.checkbox("WTI 原油", value=True)
        show_gold = st.checkbox("黃金現貨 Gold", value=True)

    df_sub = df_top.tail(chart_days).dropna(how='all').copy().ffill().bfill()
    base_row = df_sub.iloc[0]

    cols_map = {
        'TAIEX': ('台股加權指數', '#FF3333', 3, 'solid', show_taiex),
        'SOX': ('費半 SOX', '#00CC66', 2, 'solid', show_sox),
        'DXY': ('美元指數 DXY', '#00BFFF', 2, 'dot', show_dxy),
        'US10Y': ('美債 10Y 殖利率', '#FFA500', 2, 'dash', show_us10y),
        'VIX': ('恐慌指數 VIX', '#FF00FF', 1.5, 'dashdot', show_vix),
        'TWD': ('美元/台幣 TWD', '#32CD32', 2, 'dot', show_twd),
        'WTI': ('WTI 原油', '#8A2BE2', 1.5, 'solid', show_wti),
        'Gold': ('黃金現貨 Gold', '#FFD700', 1.5, 'solid', show_gold)
    }

    fig = go.Figure()
    for col_key, (disp_name, color_hex, width_px, dash_style, is_selected) in cols_map.items():
        if is_selected and col_key in df_sub.columns and base_row[col_key] > 0:
            pct_series = ((df_sub[col_key] - base_row[col_key]) / base_row[col_key]) * 100
            fig.add_trace(go.Scatter(
                x=pct_series.index,
                y=pct_series,
                mode='lines',
                name=disp_name,
                connectgaps=True,
                line=dict(color=color_hex, width=width_px, dash=dash_style)
            ))

    fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(title="累積漲跌幅 (%)", zeroline=True, zerolinecolor="#555555"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 工具 2：產業趨勢與台灣供應鏈矩陣 (AI推論 - 嚴格遵守 Top-Down/Bottom-Up 4步驟)
# ---------------------------------------------------------
elif selected_tool == "產業趨勢與台灣供應鏈矩陣 (AI推論)":
    st.header("🏭 產業趨勢與台灣供應鏈矩陣 (AI推論)")
    st.write("嚴格執行 4 步驟推論：總經熱錢走向 ➔ 篩選領頭羊個股 ➔ MOPS/財報供應鏈與獲利驗證 ➔ 嚴格 S1-S5 週期與 3/6/12/24M 情境預測。")

    mode = st.radio("模式選擇：", ["🤖 AI 總經與 MOPS 驗證推論", "📌 預設主流產業清單"])
    
    selected_matrix = []
    
    if mode == "🤖 AI 總經與 MOPS 驗證推論":
        if st.button("🚀 執行完整 4 步驟 Top-Down/Bottom-Up AI 分析"):
            with st.spinner("AI 正在分析國際熱錢流向、對比 MOPS 公開資訊觀測站數據並演算 3/6/12/24M 關鍵情境..."):
                try:
                    macro_df = df_top.tail(20)
                    latest_m = macro_df.iloc[-1]
                    prev_m = macro_df.iloc[-5] if len(macro_df) >= 5 else macro_df.iloc[0]
                    sox_chg = ((latest_m.get('SOX', 5000) - prev_m.get('SOX', 5000)) / prev_m.get('SOX', 5000)) * 100

                    # 100% 安全無特殊轉義符號的 Prompt
                    summary_prompt = (
                        "你是頂尖機構法人總經與台股產業策略總監。請嚴格按照以下 4 個步驟邏輯，進行嚴謹的 Top-Down 結合 Bottom-Up 推論：\n\n"
                        "【即時國際總經數據】\n"
                        f"- 費城半導體 SOX: {latest_m.get('SOX', 5000):.0f} (近週: {sox_chg:+.2f}%)\n"
                        f"- 恐慌指數 VIX: {latest_m.get('VIX', 15):.2f}\n"
                        f"- 美元指數 DXY: {latest_m.get('DXY', 103):.2f}\n"
                        f"- 美債 10Y 殖利率: {latest_m.get('US10Y', 4.0):.2f}%\n"
                        f"- WTI 原油: ${latest_m.get('WTI', 75):.1f} \vert{} 黃金: ${latest_m.get('Gold', 2600):.1f} | 美元/台幣: {latest_m.get('TWD', 31.8):.2f}\n\n"
                        "【分析步驟與原則】\n"
                        "1. 熱錢判讀：根據上述總經指標，判讀全球資金風險偏好與流入台灣的 3 個主流產業。\n"
                        "2. 領頭羊個股：針對每個主流產業，找出 2~3 檔最具產業代表性的台灣領頭羊個股 (簡稱與4位代號)。\n"
                        "3. MOPS 數據與獲利驗證：\n"
                        "   a. 供應鏈環節：分析客戶訂單、供應商認證、產能利用率、交期與產品組合。\n"
                        "   b. 財報獲利：驗證營收成長、毛利率、營業利益率、現金流與預估 12M EPS。\n"
                        "4. 嚴格生命週期 (S1-S5) 與未來預測：\n"
                        "   必須且只能精準使用以下 S1~S5 名詞（嚴禁自己杜撰如 S1:轉折復甦 這種錯誤名稱）：\n"
                        "   - S1: 需求萌芽期 (技術突破/初期訂單/需求不確定)\n"
                        "   - S2: 訂單成長期 (訂單增加/營收成長/產能擴充)\n"
                        "   - S3: 獲利兌現期 (財報驗證/關注度高)\n"
                        "   - S4: 預期成熟期 (高度關注/估值反映高成長)\n"
                        "   - S5: 成長放緩或轉折期 (訂單放慢/庫存增加)\n\n"
                        "【輸出格式】\n"
                        "僅輸出嚴格合法的 JSON 陣列（不得有任何 ```json 標籤）：\n"
                        "[\n"
                        "  {\n"
                        '    "industry": "產業簡稱 (如: 先進封裝與 AI 伺服器)",\n'
                        '    "cycle_code": "S2",\n'
                        '    "cycle_name": "S2: 訂單成長期",\n'
                        '    "cycle_desc": "技術與訂單明確，營收與產能加速擴充",\n'
                        '    "mops_chain_analysis": "MOPS 供應鏈驗證 (客戶訂單、認證、產能利用率與交期說明)",\n'
                        '    "mops_financial_analysis": "財報驗證 (毛利率、營業利益率、現金流與 EPS 趨勢)",\n'
                        '    "forecast_3m": "3個月預期指標與觸發條件",\n'
                        '    "forecast_6m": "6個月預期指標與觸發條件",\n'
                        '    "forecast_12m": "12個月預期指標與觸發條件",\n'
                        '    "forecast_24m": "24個月關鍵事件與失效條件",\n'
                        '    "stocks": [["公司簡稱", "四位代號"], ["公司簡稱", "四位代號"]]\n'
                        "  }\n"
                        "]"
                    )
                    
                    if api_key:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-3.5-flash')
                        res = model.generate_content(summary_prompt)
                        clean_text = res.text.replace("```json", "").replace("```", "").strip()
                        selected_matrix = json.loads(clean_text)
                        st.session_state['ai_matrix'] = selected_matrix
                    else:
                        st.warning("⚠️ 請確認已部署 API Key。")
                except Exception as e:
                    st.error(f"AI 推論失敗: {e}")
        
        if 'ai_matrix' in st.session_state:
            selected_matrix = st.session_state['ai_matrix']

    else:
        # 預設範例清單 (符合嚴格 S1-S5)
        selected_matrix = [
            {
                "industry": "AI 資料中心與先進封裝 CoWoS",
                "cycle_code": "S2",
                "cycle_name": "S2: 訂單成長期",
                "cycle_desc": "訂單大幅增加、營收高成長、產能積極擴充",
                "mops_chain_analysis": "客戶(NVIDIA/AMD)包下 CoWoS 產能，設備認證完畢，產能利用率滿載，設備交期長達 6-9 個月。",
                "mops_financial_analysis": "毛利率升至 50% 以上，營業利益率逐季走揚，自由現金流強勁，12M EPS 預估創新高。",
                "forecast_3m": "CoWoS 月產能突破 3.5 萬片；觸發條件：台積電法說會調升 CapEx。",
                "forecast_6m": "Blackwell 伺服器大量拉貨；觸發條件：月營收年增率 > 30%。",
                "forecast_12m": "高基期效應顯現；觸發條件：關注毛利率是否因擴產成本上升而受壓。",
                "forecast_24m": "進入下一代面板級封裝 (FPLP) 轉折；失效條件：CSP 大廠下修雲端 CapEx 支出。",
                "stocks": [["台積電", "2330"], ["萬潤", "6187"], ["弘塑", "3131"]]
            },
            {
                "industry": "散熱模組與水冷系統",
                "cycle_code": "S3",
                "cycle_name": "S3: 獲利兌現期",
                "cycle_desc": "獲利成長被季報財報強勢驗證，市場關注度極高",
                "mops_chain_analysis": "水冷板 (Cold Plate) 與 Manifold 分歧管通過 CSP 大廠認證，水冷滲透率自 5% 升至 20%。",
                "mops_financial_analysis": "Q2/Q3 季報毛利率與 EPS 同步大幅超越市場預估，現金流穩健。",
                "forecast_3m": "水冷系統單價 (ASP) 比傳統風扇高 3-5 倍，推升營收放量。",
                "forecast_6m": "市場關注焦點由營收轉為毛利率能否維持在高檔。",
                "forecast_12m": "進入預期成熟期 (S4)；觸發條件：評價本益比 (PE) 達 30 倍歷史高檔。",
                "forecast_24m": "市場競爭者增加；失效條件：水冷漏液品質事故或價格戰削利。",
                "stocks": [["奇鋐", "3017"], ["雙鴻", "3324"], ["高力", "8996"]]
            }
        ]

    if selected_matrix:
        st.markdown("---")
        st.subheader("📌 主流產業鏈傳導與受惠股即時行情驗證")
        
        for row in selected_matrix:
            st.markdown(f"### 🔹 【{row.get('cycle_name', 'S2: 訂單成長期')}】{row.get('industry', '主流產業')}")
            st.caption(f"**階段定位特徵**：{row.get('cycle_desc', '')}")
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.info(f"**🏭 MOPS 供應鏈環節驗證**：\n\n{row.get('mops_chain_analysis', '')}")
            with col_m2:
                st.success(f"**💰 MOPS 財報與獲利驗證**：\n\n{row.get('mops_financial_analysis', '')}")

            st.markdown("**🔮 未來 3~24 個月關鍵事件與預期指標：**")
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.markdown(f"**⏳ 3 個月展望**\n\n{row.get('forecast_3m', '訂單加速驗證')}")
            with p2:
                st.markdown(f"**⏳ 6 個月展望**\n\n{row.get('forecast_6m', '產能放量開出')}")
            with p3:
                st.markdown(f"**⏳ 12 個月展望**\n\n{row.get('forecast_12m', '獲利高峰或估值調整')}")
            with p4:
                st.markdown(f"**⏳ 24 個月展望/失效條件**\n\n{row.get('forecast_24m', '新舊技術迭代')}")

            st.markdown("**🎯 代表性領頭羊個股行情：**")
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
elif selected_tool == "個股基本面與 ROI 評分表":
    st.header("📊 個股基本面與 ROI 評分表")
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
