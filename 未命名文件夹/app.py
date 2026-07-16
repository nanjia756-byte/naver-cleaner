import streamlit as st
import pandas as pd
import re
import io

# 设置页面
st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 运营数据一键清洗助手")

uploaded_file = st.file_uploader("请上传 CSV 或 Excel 文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 1. 智能锁定数据列：查找包含区服特征的列
        # 正则涵盖：S数字、数字서버、数字섭、S数字서버/섭 等
        target_col = None
        server_pattern = r'(S\d+(?:서버|섭)?|[0-9]+(?:서버|섭)?)'
        
        for col in df.columns:
            if df[col].astype(str).str.contains(server_pattern, regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            st.warning(f"未自动检测到标准区服列，已默认选中: {target_col}")

        # 2. 清洗逻辑
        def parse_row(text):
            text = str(text).strip()
            
            # A. 提取区服 (如 S1, S26, 29서버, 1서버, 29섭)
            match = re.search(server_pattern, text, re.IGNORECASE)
            srv_name = match.group(1) if match else "未知"
            
            # 将提取到的区服信息从原文本中挖空（只挖掉第一个匹配项）
            text_cleaned = re.sub(server_pattern, ' ', text, count=1, flags=re.IGNORECASE)
            
            # B. 过滤干扰项：ID、长数字串、닉넴关键词
            text_cleaned = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', text_cleaned, flags=re.IGNORECASE)
            
            # C. 符号标准化：清理开头无效点号/符号，统一空格
            text_cleaned = re.sub(r'^[./:\s]+', '', text_cleaned)
            text_cleaned = re.sub(r'[/|:\s]+', ' ', text_cleaned).strip()
            
            # D. 切分名字与内容
            parts = text_cleaned.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # E. 纠偏逻辑：如果用户名是 "." 或 "ID" 或 "닉넴"，且内容存在，则强制修正为匿名
            if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 执行清洗
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        st.dataframe(res)
        
        # 导出
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("📥 下载清洗报表", towrite.getvalue(), "cleaned_data.xlsx")
        
    except Exception as e:
        st.error(f"处理错误: {e}")
