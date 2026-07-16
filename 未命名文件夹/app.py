import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 nan的特制独家运营数据一键清洗助手")
st.write("请上传导出的 CSV 或 Excel 文件，系统会自动识别数据进行清洗。")

# 1. 文件上传组件
uploaded_file = st.file_uploader("拖入你的采集数据文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 读取文件
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # 2. 智能锁定包含有用数据的列
        target_column = None
        for col in df.columns:
            # 搜索包含 '서버' 的列
            sample = df[col].dropna().astype(str).head(20)
            if sample.str.contains('서버', regex=False).any():
                target_column = col
                break
        
        if target_column:
            st.success(f"✅ 已自动识别数据列: **{target_column}**")
        else:
            st.warning("⚠️ 未检测到包含 '서버' 的列，尝试使用第 3 列 (索引2) 作为数据源。")
            target_column = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            
        # 3. 核心清洗逻辑 (针对 p1 和 p2 情况优化)
        def parse_row(text):
            text = str(text).strip()
            # 提取区服
            server_match = re.search(r'([A-Za-z0-9]+서버)', text)
            server_name = server_match.group(1) if server_match else "未知"
            
            # 移除区服文字
            clean = text.replace(server_name, "", 1).strip()
            
            # 强化切割逻辑：
            # 以第一个“非字母数字”的界限进行初次切割
            # 这样处理 슈/739... 会切出“슈”和“739...”
            # 处理 🐾 축협... 会切出“🐾”和“축협...”
            parts = re.split(r'[\s/:]+', clean, maxsplit=1)
            
            player_name = parts[0] if len(parts) > 0 and parts[0] != "" else "匿名"
            comment = parts[1] if len(parts) > 1 else "无内容"
            
            return pd.Series([server_name, player_name, comment])

        # 4. 执行清洗
        result_df = df[target_column].apply(parse_row)
        result_df.columns = ['区服', '玩家名', '评论内容']
        
        # 展示结果
        st.dataframe(result_df)
        
        # 5. 下载逻辑
        towrite = io.BytesIO()
        result_df.to_excel(towrite, index=False)
        towrite.seek(0)
        
        st.download_button(
            label="📥 下载整理好的 Excel 报表",
            data=towrite,
            file_name="清洗后的玩家评论.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"处理出错: {e}")
