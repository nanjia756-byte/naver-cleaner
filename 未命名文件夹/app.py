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
        server_regex = r'((?:S\s*\d+|[0-9]+)\s*(?:서버|섭)|S\s*\d+)'
        
        for col in df.columns:
            if df[col].astype(str).str.contains(server_regex, regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[0]
        
        st.info(f"正在清洗列: **{target_col}**")

        def parse_row(text):
            text = str(text).strip()
            
            # 1. 提取区服 (识别 S7, 7서버, 7 서버 等)
            server_pattern = r'((?:S\s*\d+|[0-9]+)\s*(?:서버|섭)|S\s*\d+)'
            matches = re.findall(server_pattern, text, re.IGNORECASE)
            srv_name = matches[0].strip() if matches else "未知"
            
            # 2. 移除区服字符串
            clean_text = re.sub(server_pattern, ' ', text, flags=re.IGNORECASE)
            
            # 3. 过滤干扰项 (ID, 10位数字等)
            clean_text = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', clean_text, flags=re.IGNORECASE)
            
            # 4. 彻底清理开头和中间多余的标点符号（如 , / : .）
            clean_text = re.sub(r'^[.,/:\s]+', '', clean_text)
            clean_text = re.sub(r'\s*[.,/:]\s*', ' ', clean_text)
            
            # 5. 压缩多余空格
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # 6. 分割用户名与评论
            parts = clean_text.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # 7. 纠偏：若名字仍为无效标点或保留词，则修正为匿名
            if re.match(r'^[.,/:\s]+$', name) or name.upper() in ["ID", "닉넴"]:
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 执行清洗
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        # 显示预览
        st.dataframe(res.head(10))
        
        # 下载：直接使用 pandas 原生导出，无需额外安装 xlsxwriter
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
