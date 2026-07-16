import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 运营数据一键清洗助手")

uploaded_file = st.file_uploader("请上传 CSV 或 Excel 文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        target_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains(r'[Ss]?[0-9]+(?:서버|섭)?', regex=True).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]

        def parse_row(text):
            text = str(text).strip()
            # 匹配 S1서버, 29섭, S1 等完整组合
            server_pattern = r'([Ss]?[0-9]+(?:서버|섭)?)'
            match = re.search(server_pattern, text, re.IGNORECASE)
            srv_name = match.group(1) if match else "未知"
            
            text_cleaned = re.sub(server_pattern, ' ', text, count=1, flags=re.IGNORECASE)
            text_cleaned = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', text_cleaned, flags=re.IGNORECASE)
            text_cleaned = re.sub(r'^[./:\s]+', '', text_cleaned)
            text_cleaned = re.sub(r'[/|:\s]+', ' ', text_cleaned).strip()
            
            parts = text_cleaned.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        st.dataframe(res)
        
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("📥 下载清洗报表", towrite.getvalue(), "cleaned_report.xlsx")
        
    except Exception as e:
        st.error(f"处理失败: {e}")
