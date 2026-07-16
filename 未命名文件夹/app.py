import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="评论清洗器", page_icon="🧹")
st.title("🧹 nan的独家秘制数据清洗助手")

uploaded_file = st.file_uploader("上传 Excel/CSV", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    
    # 自动锁定包含 '서버' 或 'S' 开头的列
    target_col = None
    for col in df.columns:
        if df[col].astype(str).str.contains(r'서버|S\d+', regex=True).any():
            target_col = col
            break
    
    if target_col:
        st.write(f"正在清洗列: {target_col}")
        
        def parse_row(text):
            text = str(text).strip()
            # 提取区服
            srv = re.search(r'([A-Za-z0-9]+서버|S\d+)', text, re.IGNORECASE)
            srv_name = srv.group(1) if srv else "未知"
            # 移除区服
            clean = text.replace(srv_name, "", 1).strip()
            clean = re.sub(r'^[/:\s]+', '', clean)
            # 分割用户名和评论
            parts = re.split(r'[\s/:]+', clean, maxsplit=1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            return pd.Series([srv_name, name, comm])
        
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        st.dataframe(res)
        
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("下载清洗结果", towrite.getvalue(), "cleaned.xlsx")
    else:
        st.error("未能识别数据列，请确保文件中包含区服信息。")
