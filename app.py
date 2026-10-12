import streamlit as st
import pandas as pd
import yfinance as yf

# 網頁基本設定
st.set_page_config(
    page_title="台股八階段預測與總經分析系統",
    page_icon="📈",
    layout="wide"
)

st.title("📈 台股預測分析系統 APP (v2)")
st.caption("結合 Top-Down 總經資金與 Bottom-Up 個股基本面驗證")

st.sidebar.header("系統導覽")
selected_stage = st.sidebar.radio(
    "選擇分析模組",
    [
        "核心工具 1：全球資金與總經儀表板",
        "核心工具 2：產業趨勢與供應鏈矩陣",
        "核心工具 3：個股基本面與 ROI 評分表"
    ]
)

if selected_stage == "核心工具 1：全球資金與總經儀表板":
    st.header("🌐 全球資金與總經儀表板")
    st.info("連線 Yahoo Finance 擷取最新國際指標...")
    
    # 測試連線與資料抓取
    try:
        data = yf.download(["^SOX", "DX-Y=F", "^TNX", "^VIX", "TWD=X"], period="5d")['Close']
        st.subheader("最新市場數據")
        st.dataframe(data.tail())
    except Exception as e:
        st.error(f"數據讀取失敗: {e}")

elif selected_stage == "核心工具 2：產業趨勢與供應鏈矩陣":
    st.header("🏭 產業趨勢與台灣供應鏈矩陣")
    st.write("每週追蹤需求、資本支出、訂單、產能及受惠公司 (生命週期 S1~S5)")

elif selected_stage == "核心工具 3：個股基本面與 ROI 評分表":
    st.header("📊 個股基本面與 ROI 評分表")
    st.write("每月更新財務、EPS、估值區間、籌碼與三情境 ROI 分析")
