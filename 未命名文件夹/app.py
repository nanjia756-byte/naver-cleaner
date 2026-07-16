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
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 2. 自动锁定包含区服特征的列
        target_col = None
        # 匹配 S+数字+后缀 或 数字+后缀
        pattern_str = r'(S\d+(?:서버|섭)?|[0-9]+(?:서버|섭)?)'
        
        for col in df.columns:
            if df[col].astype(str).str.contains(pattern_str, regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            st.warning(f"⚠️ 未检测到标准区服，默认处理列: {target_col}")

        # 3. 深度清洗逻辑
        def parse_row(text):
            text = str(text).strip()
            
            # 正则：匹配 S1서버, S1섭, S1, 1서버, 1섭
            server_pattern = r'(S\d+(?:서버|섭)?|[0-9]+(?:서버|섭)?)'
            
            # 提取区服
            match = re.search(server_pattern, text, re.IGNORECASE)
            srv_name = match.group(1) if match else "未知"
            
            # 原位移除区服，防止干扰
            text_cleaned = re.sub(server_pattern, ' ', text, count=1, flags=re.IGNORECASE)
            
            # 过滤长ID(10位以上)、ID标记、닉넴关键词
            text_cleaned = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', text_cleaned, flags=re.IGNORECASE)
            
            # 符号标准化：清理开头无效符号、统一空格
            text_cleaned = re.sub(r'^[./:\s]+', '', text_cleaned)
            text_cleaned = re.sub(r'[/|:\s]+', ' ', text_cleaned).strip()
            
            # 分割提取
            parts = text_cleaned.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # 最终纠偏：防止无效符号被判定为名字
            if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 4. 执行并显示
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        st.dataframe(res)
        
        # 5. 下载功能
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button(
            label="📥 下载最终版清洗报表",
            data=towrite.getvalue(),
            file_name="cleaned_report.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"处理失败，请检查文件格式: {e}")
