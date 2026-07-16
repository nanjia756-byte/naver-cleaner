import streamlit as st
import pandas as pd
import re
import io

st.title("运营数据清洗工具")

uploaded_file = st.file_uploader("上传 CSV/Excel", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    
    def parse_row(text):
        text = str(text)
        server = re.search(r'(\d+서버)', text)
        server_name = server.group(1) if server else "未知"
        # 移除区服信息后切割，只分两部分：用户名 和 评论
        clean = text.replace(server_name, "").strip()
        parts = re.split(r'[\s/:|]+', clean, maxsplit=1)
        player = parts[0] if len(parts) > 0 else "匿名"
        comment = parts[1] if len(parts) > 1 else "无内容"
        return pd.Series([server_name, player, comment])

    new_df = df[df.columns[0]].apply(parse_row)
    new_df.columns = ['区服', '玩家名', '评论内容']
    st.dataframe(new_df)
    
    # 下载逻辑
    towrite = io.BytesIO()
    new_df.to_excel(towrite, index=False)
    st.download_button("下载清洗结果", towrite.getvalue(), "cleaned_data.xlsx")
