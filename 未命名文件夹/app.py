import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 运营数据一键清洗助手")
st.write("请上传导出的 CSV 或 Excel 文件，系统会自动抓取包含'서버'的列进行清洗。")

# 1. 文件上传
uploaded_file = st.file_uploader("拖入你的采集数据文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 读取文件
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # 2. 智能锁定包含有用数据的列
        target_column = None
        for col in df.columns:
            # 检查列中是否存在包含 '서버' 的非空值
            sample = df[col].dropna().astype(str).head(10)
            if sample.str.contains('서버', regex=False).any():
                target_column = col
                break
        
        if target_column:
            st.success(f"✅ 已自动识别数据列: **{target_column}**")
        else:
            st.warning("⚠️ 未检测到包含 '서버' 的列，将默认使用第 3 列作为数据源。")
            target_column = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            
        # 3. 定义清洗函数
        def parse_row(text):
            text = str(text)
            # 提取区服 (如 29서버 或 S1서버)
            server_match = re.search(r'([A-Za-z0-9]+서버)', text)
            server_name = server_match.group(1) if server_match else "未知"
            
            # 移除区服文字，清除前后的干扰符
            clean = text.replace(server_name, "", 1).strip()
            
            # 使用正则分割：寻找第一个空格、冒号、斜杠作为用户名结束点
            # 这样即使用户名里有奇怪字符，也能通过这个逻辑强行拆分
            parts = re.split(r'[\s/:]+', clean, maxsplit=1)
            
            player_name = parts[0] if len(parts) > 0 and parts[0] != "" else "匿名"
            comment = parts[1] if len(parts) > 1 else "无内容"
            
            return pd.Series([server_name, player_name, comment])

        # 4. 执行清洗
        result_df = df[target_column].apply(parse_row)
        result_df.columns = ['区服', '玩家名', '评论内容']
        
        st.dataframe(result_df)
        
        # 5. 下载逻辑
        towrite = io.BytesIO()
        result_df.to_excel(towrite, index=False)
        towrite.seek(0)
        
        st.download_button(
            label="📥 下载整理好的 Excel 报表",
            data=towrite,
            file_name="整理后的玩家评论.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"处理出错，请检查文件格式是否正确。错误信息: {e}")
