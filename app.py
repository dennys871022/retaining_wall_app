import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide", page_title="中間樁管理系統")
st.title("防疫中心興建工程：中間樁與共構樁打設紀錄系統")

@st.cache_data
def process_cad_csv(file_path):
    df = pd.read_csv(file_path)
    
    # 抓取文字作為樁號
    texts = df[df['名稱'].isin(['文字', '多行文字']) & df['內容'].notnull()][['內容', '位置 X', '位置 Y']].copy()
    texts.rename(columns={'位置 X': 'X', '位置 Y': 'Y'}, inplace=True)
    texts.dropna(subset=['X', 'Y'], inplace=True)

    # 僅抓取 HH3 作為所有 253 支樁的基準
    piles = df[df['名稱'] == 'HH3'][['位置 X', '位置 Y']].copy()
    piles.rename(columns={'位置 X': 'X', '位置 Y': 'Y'}, inplace=True)
    piles.dropna(subset=['X', 'Y'], inplace=True)

    def get_nearest_text(px, py):
        if len(texts) == 0: return "未命名"
        dist = np.sqrt((texts['X'] - px)**2 + (texts['Y'] - py)**2)
        nearest_idx = dist.idxmin()
        if dist[nearest_idx] < 800:
            return str(texts.loc[nearest_idx, '內容']).strip()
        return "未命名"

    piles['樁號'] = piles.apply(lambda row: get_nearest_text(row['X'], row['Y']), axis=1)
    
    # 初始化狀態與施工星期
    piles['狀態'] = '未施工'
    piles['施工星期'] = '無'
    return piles

if 'pile_data' not in st.session_state:
    if os.path.exists("中間樁.csv"):
        st.session_state.pile_data = process_cad_csv("中間樁.csv")
    else:
        st.error("找不到 中間樁.csv 檔案")
        st.stop()

df_piles = st.session_state.pile_data

col1, col2 = st.columns([2, 1])

# 星期專屬固定顏色
weekday_colors = {
    "星期一": "#FF9999",
    "星期二": "#FFCC99",
    "星期三": "#FFFF99",
    "星期四": "#99FF99",
    "星期五": "#99FFFF",
    "星期六": "#9999FF",
    "星期日": "#FF99FF",
    "無": "#E0E0E0"
}

with col1:
    st.subheader("工地打設平面圖")
    fig = px.scatter(
        df_piles, x="X", y="Y", color="施工星期", text="樁號",
        color_discrete_map=weekday_colors,
        hover_data={"X": False, "Y": False, "狀態": True}
    )
    fig.update_traces(textposition='top center', marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, visible=False)
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_layout(height=600, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("施工紀錄表單")
    
    total_piles = 253
    completed_piles = len(df_piles[df_piles['狀態'] == '已完成'])
    st.progress(completed_piles / total_piles, text=f"總進度： {completed_piles}/{total_piles} 支")

    pile_list = df_piles['樁號'].sort_values().unique()
    
    # 2 支樁循環模式選擇
    st.write("2 支樁循環選取模式")
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        pile_1 = st.selectbox("第一支樁", pile_list, key="p1")
    with col2_2:
        pile_2 = st.selectbox("第二支樁", pile_list, key="p2")
    
    with st.form("record_form"):
        status = st.selectbox("更新施工狀態", ["未施工", "施工中", "已完成"])
        weekday = st.selectbox("施工星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"])
        
        submitted = st.form_submit_button("儲存並更新圖面")
        
        if submitted:
            for p in [pile_1, pile_2]:
                idx = df_piles.index[df_piles['樁號'] == p].tolist()
                if idx:
                    st.session_state.pile_data.at[idx[0], '狀態'] = status
                    st.session_state.pile_data.at[idx[0], '施工星期'] = weekday if status == '已完成' else '無'
            
            st.success(f"樁號 {pile_1}, {pile_2} 紀錄已更新")
            st.rerun()
