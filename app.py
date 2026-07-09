import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="中間樁進度管理系統")
st.title("防疫中心興建工程: 中間樁施工紀錄")

# 1. 模擬載入 CAD 萃取的座標與基礎資料
@st.cache_data
def load_pile_data():
    # 實際應用將替換為讀取 CSV/Excel
    data = {
        "樁號": ["P1", "P2", "P3", "P4"],
        "X座標": [10, 20, 10, 20],
        "Y座標": [10, 10, 20, 20],
        "樁型": ["中間樁", "中間樁", "共構樁", "共構樁"],
        "規格": ["H350*350 L:15m", "H350*350 L:15m", "H350*350 L:15m", "H350*350 L:15m"],
        "狀態": ["已完成", "施工中", "未施工", "未施工"]
    }
    return pd.DataFrame(data)

df_piles = load_pile_data()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("工地樁位圖")
    # 2. 繪製互動式平面圖
    fig = px.scatter(
        df_piles, x="X座標", y="Y座標", color="狀態", text="樁號",
        color_discrete_map={"已完成": "green", "施工中": "orange", "未施工": "gray"},
        title="中間樁及共構樁打設進度"
    )
    fig.update_traces(textposition='top center', marker=dict(size=12))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("施工紀錄輸入")
    # 3. 紀錄填寫表單
    selected_pile = st.selectbox("選擇樁號", df_piles["樁號"])
    pile_info = df_piles[df_piles["樁號"] == selected_pile].iloc[0]
    
    st.write(f"**目前型態**: {pile_info['樁型']} | **規格**: {pile_info['規格']}")
    
    with st.form("record_form"):
        date = st.date_input("施工日期")
        vendor = st.selectbox("施工廠商", ["國廣營造", "其他"])
        drill_depth = st.number_input("鑽掘深度 (m)", min_value=0.0, format="%.2f")
        steel_length = st.number_input("型鋼長度 (m)", min_value=0.0, format="%.2f")
        deviation = st.number_input("偏位誤差 (cm)", min_value=0.0, format="%.1f")
        photo = st.file_uploader("上傳查驗照片", type=["jpg", "png"])
        
        submitted = st.form_submit_button("儲存紀錄")
        if submitted:
            st.success(f"樁號 {selected_pile} 紀錄已暫存。")
