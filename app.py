import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(layout="wide", page_title="安全支撐工程 - 中間樁管理系統")
st.title("🏗️ 防疫中心興建工程: 中間樁/共構樁打設紀錄系統")

# 1. 自動解析 CAD 萃取檔的函式
@st.cache_data
def process_cad_csv(file_path):
    df = pd.read_csv(file_path)
    
    # 抓取文字作為樁號
    texts = df[df['名稱'].isin(['文字', '多行文字']) & df['內容'].notnull()][['內容', '位置 X', '位置 Y']].copy()
    texts.rename(columns={'位置 X': 'X', '位置 Y': 'Y'}, inplace=True)
    texts.dropna(subset=['X', 'Y'], inplace=True)

    # 抓取 HH3 (共構樁)
    hh3 = df[df['名稱'] == 'HH3'][['位置 X', '位置 Y']].copy()
    hh3.rename(columns={'位置 X': 'X', '位置 Y': 'Y'}, inplace=True)
    hh3['樁型'] = '共構樁'
    hh3.dropna(subset=['X', 'Y'], inplace=True)

    # 抓取 圓 (中間樁)
    circles = df[df['名稱'] == '圓'][['中心 X', '中心 Y']].copy()
    circles.rename(columns={'中心 X': 'X', '中心 Y': 'Y'}, inplace=True)
    circles['樁型'] = '中間樁'
    circles.dropna(subset=['X', 'Y'], inplace=True)

    piles = pd.concat([hh3, circles], ignore_index=True)

    # 將文字標籤對應到最近的樁座標上
    def get_nearest_text(px, py):
        if len(texts) == 0: return "未命名"
        dist = np.sqrt((texts['X'] - px)**2 + (texts['Y'] - py)**2)
        nearest_idx = dist.idxmin()
        if dist[nearest_idx] < 800: # 距離容許值
            return str(texts.loc[nearest_idx, '內容']).strip()
        return "未命名"

    piles['樁號'] = piles.apply(lambda row: get_nearest_text(row['X'], row['Y']), axis=1)
    
    # 建立預設狀態
    piles['狀態'] = '未施工'
    return piles

# 讀取資料並儲存在 Session State 中 (為了能動態更新狀態)
if 'pile_data' not in st.session_state:
    if os.path.exists("中間樁.csv"):
        st.session_state.pile_data = process_cad_csv("中間樁.csv")
    else:
        st.error("找不到 中間樁.csv 檔案，請確認檔案已上傳！")
        st.stop()

df_piles = st.session_state.pile_data

# 2. 建立網頁左右兩欄佈局
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 工地打設平面圖")
    # 利用 plotly 繪製保留正確比例的散佈圖地圖
    fig = px.scatter(
        df_piles, x="X", y="Y", color="狀態", text="樁號", symbol="樁型",
        color_discrete_map={"已完成": "#00CC96", "施工中": "#FFA15A", "未施工": "#636EFA"},
        hover_data={"X": False, "Y": False, "樁型": True}
    )
    fig.update_traces(textposition='top center', marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
    # 設定 scaleanchor 保證 X, Y 軸比例一致，圖面才不會變形
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, visible=False)
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_layout(height=600, plot_bgcolor='rgba(0,0,0,0)')
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 施工紀錄表單")
    
    # 計算進度
    total_piles = len(df_piles)
    completed_piles = len(df_piles[df_piles['狀態'] == '已完成'])
    st.progress(completed_piles / total_piles, text=f"總進度: {completed_piles}/{total_piles} 支")

    # 選擇要輸入紀錄的樁號
    pile_list = df_piles['樁號'].sort_values().unique()
    selected_pile = st.selectbox("請選擇樁號：", pile_list)
    
    pile_info = df_piles[df_piles["樁號"] == selected_pile].iloc[0]
    st.info(f"👉 **型態**: {pile_info['樁型']} | **目前狀態**: {pile_info['狀態']}")
    
    # 紀錄表單
    with st.form("record_form"):
        status = st.selectbox("更新施工狀態", ["未施工", "施工中", "已完成"])
        date = st.date_input("施工日期")
        drill_depth = st.number_input("鑽掘深度 (m)", min_value=0.0, format="%.2f")
        steel_length = st.number_input("H型鋼打設長度 (m)", min_value=0.0, format="%.2f")
        
        submitted = st.form_submit_button("💾 儲存並更新圖面")
        
        if submitted:
            # 更新 Session State 中的狀態
            idx = df_piles.index[df_piles['樁號'] == selected_pile].tolist()[0]
            st.session_state.pile_data.at[idx, '狀態'] = status
            st.success(f"✅ 樁號 {selected_pile} 紀錄已更新！")
            st.rerun() # 重新整理網頁以更新左側地圖顏色
