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
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 自动锁定数据列
        target_col = None
        # 匹配逻辑：优先匹配 S7+空格+서버 等组合
        server_regex = r'((?:S\s*\d+|[0-9]+)\s*(?:서버|섭))'
        
        for col in df.columns:
            if df[col].astype(str).str.contains(server_regex, regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[0]
        
        st.info(f"正在清洗列: **{target_col}**")

        def parse_row(text):
            text = str(text).strip()
            
            # 强化正则：确保 S7 서버 或 7 서버 作为一个整体被匹配
            server_pattern = r'((?:S\s*\d+|[0-9]+)\s*(?:서버|섭)|S\s*\d+)'
            
            # 1. 提取区服
            matches = re.findall(server_pattern, text, re.IGNORECASE)
            # 取第一个匹配项作为区服，并清理多余空格
            srv_name = matches[0].strip() if matches else "未知"
            
            # 2. 从原文本中彻底移除匹配到的整个区服字符串
            clean_text = re.sub(server_pattern, ' ', text, flags=re.IGNORECASE)
            
            # 3. 过滤干扰项
            clean_text = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', clean_text, flags=re.IGNORECASE)
            
            # 4. 符号标准化：去除头部特殊符号，压缩空格
            clean_text = re.sub(r'^[./:\s]+', '', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # 5. 分割用户名与评论
            parts = clean_text.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # 纠偏
            if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 执行清洗
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        # 显示预览
        st.dataframe(res.head(10))
        
        # 下载：不使用 xlsxwriter，直接用 pandas 原生导出
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        
        st.download_button(
            label="📥 下载清洗结果", 
            data=towrite.getvalue(), 
            file_name="cleaned_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"处理失败: {e}")
