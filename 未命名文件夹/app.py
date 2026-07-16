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
        
        # 自动锁定包含 '서버' 或 'S' 开头的列
        target_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains(r'서버|S\d+', regex=True).any():
                target_col = col
                break
        
        if target_col:
            def parse_row(text):
                text = str(text).strip()
                
                # A. 提取区服
                srv = re.search(r'([A-Za-z0-9]+서버|S\d+)', text, re.IGNORECASE)
                srv_name = srv.group(1) if srv else "未知"
                clean = text.replace(srv_name, "", 1).strip()
                
                # B. 强力清洗：剔除 10 位以上数字 ID 和 ID 标签
                clean = re.sub(r'\d{10,}', '', clean)
                clean = re.sub(r'(ID[:\s]*|닉넴)', ' ', clean, flags=re.IGNORECASE)
                
                # C. 符号归一化
                clean = re.sub(r'[/:\s]+', ' ', clean).strip()
                
                # D. 分割处理
                parts = clean.split(' ', 1)
                name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
                comm = parts[1] if len(parts) > 1 else "无内容"
                
                # E. 纠偏层：处理名字误判
                if name == "." and len(comm) < 3:
                    name = "匿名"
                elif name.upper() in ["ID", "닉넴"]:
                    comm = f"{name} {comm}".strip()
                    name = "匿名"
                    
                return pd.Series([srv_name, name, comm])

            res = df[target_col].apply(parse_row)
            res.columns = ['区服', '玩家名', '评论内容']
            st.dataframe(res)
            
            towrite = io.BytesIO()
            res.to_excel(towrite, index=False)
            st.download_button("📥 下载清洗报表", towrite.getvalue(), "cleaned_data.xlsx")
        else:
            st.error("未能识别数据列。")
    except Exception as e:
        st.error(f"处理错误: {e}")
