import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 nan的秘制数据一键清洗助手")
st.write("上传数据文件，系统将自动识别列并进行深度清洗。")

uploaded_file = st.file_uploader("请上传 CSV 或 Excel 文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 1. 读取文件
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 2. 智能锁定数据列
        target_col = None
        for col in df.columns:
            # 搜索包含常见区服特征的列
            if df[col].astype(str).str.contains(r'서버|S\d+', regex=True).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            st.warning(f"⚠️ 未检测到标准区服格式，默认处理列: {target_col}")
        else:
            st.success(f"✅ 已自动识别数据列: {target_col}")

        # 3. 深度清洗逻辑
        def parse_row(text):
            text = str(text).strip()
            
            # A. 提取区服
            srv = re.search(r'([A-Za-z0-9]+서버|S\d+)', text, re.IGNORECASE)
            srv_name = srv.group(1) if srv else "未知"
            clean = text.replace(srv_name, "", 1).strip()
            
            # B. 过滤 ID/垃圾信息
            # 剔除 ID:数字, ID数字, 或者纯粹的长串数字ID
            clean = re.sub(r'ID[:\s]*\d+', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'^[/:\s]+', '', clean)
            
            # C. 符号归一化 (将分隔符统一转换为空格)
            clean = re.sub(r'[/:]', ' ', clean)
            
            # D. 分割用户名与评论
            parts = clean.split(maxsplit=1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # E. 用户名逻辑二次修正 (防误判)
            # 如果提取出的“用户名”是 ID 或者数字，强制将其归为评论内容
            if name.upper() == "ID" or name.isdigit():
                comm = f"{name} {comm}".strip()
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 4. 执行并下载
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        st.dataframe(res)
        
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button("📥 下载清洗后的报表", towrite.getvalue(), "cleaned_report.xlsx")
        
    except Exception as e:
        st.error(f"处理失败，请检查文件格式: {e}")
