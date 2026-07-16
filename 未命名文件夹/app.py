import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 运营数据一键清洗助手")

uploaded_file = st.file_uploader("上传采集的 Excel/CSV 文件", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        target_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains(r'(S\d+|[0-9]+(?:서버|섭|버서)?)', regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]

        def parse_row(text):
            text = str(text).strip()
            
            # 升级版正则：匹配 S数字、数字+서버/섭/버서 或仅数字(作为区服)
            # 增加了对버서的容错，并允许匹配仅数字的情况
            server_pattern = r'([Ss]\d+|[0-9]+(?:서버|섭|버서)?)'
            
            # 提取区服
            match = re.search(server_pattern, text, re.IGNORECASE)
            srv_name = match.group(1) if match else "未知"
            
            # 移除已匹配的区服部分，使用正则替换以保持结构
            clean_text = re.sub(server_pattern, ' ', text, count=1, flags=re.IGNORECASE)
            
            # 过滤长ID (10位以上数字)、ID标记、닉넴关键词
            clean_text = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', clean_text, flags=re.IGNORECASE)
            
            # 统一分隔符并清理多余空格
            clean_text = re.sub(r'[/|:\s]+', ' ', clean_text).strip()
            
            # 分割用户名与评论内容
            parts = clean_text.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # 纠偏：如果是“ID”关键词或无效单字符，修正为匿名
            if (name.upper() in ["ID", "닉넴", "."] or len(name) < 2) and len(comm) > 0:
                # 如果发现名字是无效的，但comm里包含了疑似名字的信息，可以进一步处理
                if name == "ID": name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 执行清洗
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        st.dataframe(res)
        
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("📥 下载清洗结果", towrite.getvalue(), "cleaned_data.xlsx")
        
    except Exception as e:
        st.error(f"处理失败: {e}")
