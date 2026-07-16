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
        
        # 2. 智能锁定数据列
        target_col = None
        for col in df.columns:
            # 兼容识别서버, 섭, S开头的区服
            if df[col].astype(str).str.contains(r'[0-9]+(?:서버|섭)|S[0-9]+', regex=True).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            st.warning(f"⚠️ 未检测到标准区服格式，默认处理列: {target_col}")

        # 3. 深度清洗逻辑 (最终整合版)
        def parse_row(text):
            text = str(text).strip()
            
            # A. 提取区服 (兼容 29서버, 29섭, S26 等)
            server_pattern = r'([0-9]+(?:서버|섭)|S[0-9]+)'
            match = re.search(server_pattern, text, re.IGNORECASE)
            srv_name = match.group(1) if match else "未知"
            # 临时占位，防止切分干扰
            temp_text = text.replace(srv_name, "|||", 1)
            
            # B. 过滤长数字ID(10位以上)、ID标记、닉넴关键词
            clean_text = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', temp_text, flags=re.IGNORECASE)
            
            # C. 符号标准化：将所有分隔符（/, |, :, 空格）统一转为空格
            clean_text = re.sub(r'[/|:\s]+', ' ', clean_text).strip()
            
            # D. 分割用户名与评论 (以第一个空格为界)
            parts = clean_text.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # E. 最终纠偏层
            # 1. 如果用户名是纯点号或无效标识，且评论区有内容，修正为匿名
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
            label="📥 下载清洗报表",
            data=towrite.getvalue(),
            file_name="清洗结果.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"处理失败，请确认文件格式是否标准: {e}")
