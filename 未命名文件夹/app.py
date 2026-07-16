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
        
        # --- 1. 深度定位数据列 ---
        # 优化正则：不仅匹配 S+数字，还匹配数字+서버/섭，通过更宽泛的特征锁定含有服务器信息的列
        server_indicator_pattern = r'(S\d+|[0-9]+(?:서버|섭|버서))'
        target_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains(server_indicator_pattern, regex=True, flags=re.IGNORECASE).any():
                target_col = col
                break
        
        if not target_col:
            st.error("无法自动识别含有区服信息的列，请检查数据格式是否包含 'S1' 或 '서버' 等标识。")
        else:
            st.success(f"已锁定数据列: **{target_col}**")

            # --- 2. 核心清洗函数 ---
            def parse_row(text):
                text = str(text).strip()
                
                # 定义完整服务器特征：支持 S1, S1서버, 29서버, 29섭, 27버서
                server_pattern = r'([Ss]?\d+(?:서버|섭|버서)?|S\d+)'
                
                # 优先提取区服
                match = re.search(server_pattern, text, re.IGNORECASE)
                srv_name = match.group(1) if match else "未知"
                
                # 挖空处理：只移除提取到的区服信息，防止剩余文本错位
                clean_text = re.sub(server_pattern, ' ', text, count=1, flags=re.IGNORECASE)
                
                # 清理长数字ID (10位以上) 和其他干扰信息
                clean_text = re.sub(r'\d{10,}', ' ', clean_text)
                
                # 符号标准化：清理开头无效点号、统一空白符
                clean_text = re.sub(r'^[./:\s]+', '', clean_text)
                clean_text = re.sub(r'[/|:\s]+', ' ', clean_text).strip()
                
                # 切分名字与内容
                parts = clean_text.split(' ', 1)
                name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
                comm = parts[1] if len(parts) > 1 else "无内容"
                
                # 最终纠偏
                if name.upper() in ["ID", "닉넴", "."] and len(comm) > 0:
                    name = "匿名"
                    
                return pd.Series([srv_name, name, comm])

            # 执行清洗
            res = df[target_col].apply(parse_row)
            res.columns = ['区服', '玩家名', '评论内容']
            
            st.dataframe(res)
            
            # 下载
            towrite = io.BytesIO()
            res.to_excel(towrite, index=False)
            st.download_button("📥 下载清洗报表", towrite.getvalue(), "cleaned_report.xlsx")
            
    except Exception as e:
        st.error(f"处理失败: {e}")
