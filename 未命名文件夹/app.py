import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 nan的秘制运营数据一键清洗助手")

# 1. 文件上传
uploaded_file = st.file_uploader("请上传 CSV 或 Excel 文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 读取文件
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 2. 智能锁定数据列
        target_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains(r'서버|S\d+', regex=True).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            st.warning(f"⚠️ 未检测到标准区服格式，默认处理列: {target_col}")

        # 3. 深度清洗逻辑 (最终整合版)
        def parse_row(text):
            text = str(text).strip()
            
            # A. 提取区服
            srv = re.search(r'([A-Za-z0-9]+서버|S\d+)', text, re.IGNORECASE)
            srv_name = srv.group(1) if srv else "未知"
            clean = text.replace(srv_name, "", 1).strip()
            
            # B. 过滤长数字ID 和 关键词 (닉넴/ID)
            clean = re.sub(r'\d{10,}', '', clean)
            clean = re.sub(r'(ID[:\s]*|닉넴)', ' ', clean, flags=re.IGNORECASE)
            
            # C. 符号清理 (将符号转为空格)
            clean = re.sub(r'[/:\s]+', ' ', clean).strip()
            
            # D. 分割用户名与评论
            parts = clean.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # E. 最终纠偏层
            # 只有当名字是“纯点号”且“评论内容极其简短”时，才判定为噪音并设为匿名
            if name == "." and len(comm) < 3:
                name = "匿名"
            # 拦截掉名字识别为 ID 的情况，将其修正
            elif name.upper() in ["ID", "닉넴"]:
                comm = f"{name} {comm}".strip()
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 4. 执行并显示
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        st.dataframe(res)
        
        # 5. 下载功能
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("📥 下载清洗报表", towrite.getvalue(), "cleaned_data.xlsx")
        
    except Exception as e:
        st.error(f"处理错误: {e}")
