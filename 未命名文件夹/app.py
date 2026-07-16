import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 运营数据一键清洗助手")

uploaded_file = st.file_uploader("上传采集的 Excel/CSV 文件", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # 读取文件
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        
        # 自动锁定数据列（优先匹配包含区服特征的列）
        target_col = None
        server_regex = r'(S\s*\d+|[0-9]+\s*(?:서버|섭))'
        
        for col in df.columns:
            if df[col].astype(str).str.contains(server_regex, regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
        
        st.info(f"正在清洗列: **{target_col}**")

        # 核心：精准提取并彻底清除区服标记
        def parse_row(text):
            text = str(text).strip()
            
            # 强化正则：匹配 S数字、S 空格 数字、数字 空格 서버/섭
            server_pattern = r'(S\s*\d+|[0-9]+\s*(?:서버|섭))'
            
            # 1. 提取区服
            matches = re.findall(server_pattern, text, re.IGNORECASE)
            srv_name = " ".join([m.strip() for m in matches]) if matches else "未知"
            
            # 2. 从原文本中彻底移除这些标记
            clean_text = re.sub(server_pattern, ' ', text, flags=re.IGNORECASE)
            
            # 3. 过滤长ID (10位以上数字)、ID标记、닉넴关键词
            clean_text = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', clean_text, flags=re.IGNORECASE)
            
            # 4. 符号标准化：处理多余空格和特殊符号
            clean_text = re.sub(r'^[./:\s]+', '', clean_text)  # 去除开头特殊符号
            clean_text = re.sub(r'\s+', ' ', clean_text).strip() # 将所有多余空格缩减为一个
            
            # 5. 分割用户名与评论
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
        
        # 显示预览
        st.dataframe(res.head(10))
        
        # 下载功能：改为使用 BytesIO 直接导出，不依赖 xlsxwriter
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False) # 直接导出，不指定 engine
        
        st.download_button(
            label="📥 下载清洗结果", 
            data=towrite.getvalue(), 
            file_name="cleaned_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"处理失败: {e}")
