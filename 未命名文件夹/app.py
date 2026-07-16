import streamlit as st
import pandas as pd
import re
import io

# 页面配置
st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 运营数据一键清洗助手")

# 1. 文件上传
uploaded_file = st.file_uploader("请上传 CSV 或 Excel 文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 读取文件
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 2. 自动锁定包含区服特征的列
        target_col = None
        for col in df.columns:
            # 正则匹配：S+数字, 数字+서버, 数字+섭
            if df[col].astype(str).str.contains(r'(S[0-9]+|[0-9]+(?:서버|섭))', regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            st.warning(f"⚠️ 未检测到标准区服，默认处理列: {target_col}")

        # 3. 深度清洗逻辑
        def parse_row(text):
            text = str(text).strip()
            
            # A. 提取区服：支持 S1, 29서버, 29섭
            server_pattern = r'(S[0-9]+|[0-9]+(?:서버|섭))'
            match = re.search(server_pattern, text, re.IGNORECASE)
            srv_name = match.group(1) if match else "未知"
            
            # 原位移除区服，防止干扰
            text_cleaned = re.sub(server_pattern, '', text, flags=re.IGNORECASE).strip()
            
            # B. 过滤 ID、长数字ID、닉넴关键词
            text_cleaned = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', text_cleaned, flags=re.IGNORECASE)
            
            # C. 符号标准化：清理多余符号
            text_cleaned = re.sub(r'^[./:\s]+', '', text_cleaned) # 清理开头无效符号
            text_cleaned = re.sub(r'[/|:\s]+', ' ', text_cleaned).strip()
            
            # D. 分割提取
            parts = text_cleaned.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # E. 最终纠偏：只有当用户名是纯点号或无效标识且无实际内容时，修正为匿名
            if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 4. 执行清洗
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        # 显示结果
        st.dataframe(res)
        
        # 5. 下载功能
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button(
            label="📥 下载最终版清洗报表",
            data=towrite.getvalue(),
            file_name="清洗结果.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"处理失败，请检查文件格式: {e}")
