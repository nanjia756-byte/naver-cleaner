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
        
        # 自动锁定数据列
        target_col = None
        for col in df.columns:
            # 兼容性匹配：S+数字, 数字+서버, 数字+섭
            if df[col].astype(str).str.contains(r'(S\d+|[0-9]+(?:서버|섭))', regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]

        # 核心：精准提取区服并彻底挖空
        def parse_row(text):
            text = str(text).strip()
            
            # 定义所有可能的服务器正则
            server_pattern = r'(S\d+|[0-9]+(?:서버|섭))'
            
            # 找出文中所有的服务器标记
            matches = re.findall(server_pattern, text, re.IGNORECASE)
            
            # 将找到的所有服务器标记合并为区服列的内容
            srv_name = " ".join(matches) if matches else "未知"
            
            # 从原文本中彻底移除这些标记
            clean_text = re.sub(server_pattern, ' ', text, flags=re.IGNORECASE)
            
            # 过滤长ID (10位以上数字)、ID标记、닉넴关键词
            clean_text = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', clean_text, flags=re.IGNORECASE)
            
            # 符号标准化：将开头点号、/、:、空格统一处理
            clean_text = re.sub(r'^[./:\s]+', '', clean_text)
            clean_text = re.sub(r'[/|:\s]+', ' ', clean_text).strip()
            
            # 分割用户名与评论
            parts = clean_text.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # 纠偏：如果是“无效点号”或“ID”关键词，修正为匿名
            if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 执行清洗
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        st.dataframe(res)
        
        # 下载
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("📥 下载清洗结果", towrite.getvalue(), "cleaned_data.xlsx")
        
    except Exception as e:
        st.error(f"处理失败: {e}")
