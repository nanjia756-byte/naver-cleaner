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
        
        # 智能查找包含区服特征的列
        target_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains(r'([Ss]?[0-9]+(?:서버|섭)?)', regex=True).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]

        def parse_row(text):
            text = str(text).strip()
            
            # 改进后的正则：优先匹配带后缀的完整形式，再匹配纯编号
            # 匹配逻辑：可选S/s开头 + 数字 + 可选的(서버/섭)
            server_pattern = r'([Ss]?[0-9]+(?:서버|섭)|[Ss]?[0-9]+)'
            
            # 使用 re.search 提取第一个匹配到的完整区服信息
            match = re.search(server_pattern, text, re.IGNORECASE)
            srv_name = match.group(1) if match else "未知"
            
            # 挖空处理：将提取到的区服信息在原文本中“挖走”，填补为空格
            # count=1 确保只挖掉第一个匹配，防止误伤
            text_cleaned = re.sub(server_pattern, ' ', text, count=1, flags=re.IGNORECASE)
            
            # --- 垃圾信息清洗 ---
            # 过滤长ID(10位以上)、ID标记、닉넴关键词
            text_cleaned = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', text_cleaned, flags=re.IGNORECASE)
            
            # --- 符号标准化 ---
            # 清理开头无效符号、统一空白符
            text_cleaned = re.sub(r'^[./:\s]+', '', text_cleaned)
            text_cleaned = re.sub(r'[/|:\s]+', ' ', text_cleaned).strip()
            
            # --- 分割用户名与评论 ---
            parts = text_cleaned.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # --- 纠偏 ---
            # 如果用户名本身是无效符号，且后面有内容，则标记为匿名
            if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 执行并保存
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        st.dataframe(res)
        
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("📥 下载清洗报表", towrite.getvalue(), "cleaned_report.xlsx")
        
    except Exception as e:
        st.error(f"处理错误: {e}")
