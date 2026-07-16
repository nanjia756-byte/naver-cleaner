import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="运营数据清洗神器", page_icon="🧹")
st.title("🧹 运营数据一键清洗助手")
st.write("将导出的原始数据文件拖入下方，自动整理成标准三列报表。")

# 文件上传组件
uploaded_file = st.file_uploader("请上传 CSV 或 Excel 文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 读取文件
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.write("预览原始数据:", df.head())
        
        # 定义清洗逻辑
        col_name = df.columns[0]
        
        def parse_row(text):
            text = str(text)
            server = re.search(r'(\d+서버)', text)
            server_name = server.group(1) if server else "未知"
            parts = text.split(' ', 2)
            player_name = parts[1] if len(parts) > 1 else "匿名"
            comment = parts[2] if len(parts) > 2 else text
            return pd.Series([server_name, player_name, comment])

        # 执行清洗
        new_df = df[col_name].apply(parse_row)
        new_df.columns = ['区服', '玩家名', '评论内容']
        
        st.success("✅ 清洗成功！")
        st.dataframe(new_df)
        
        # 转换成 Excel 供下载
        towrite = io.BytesIO()
        new_df.to_excel(towrite, index=False)
        towrite.seek(0)
        
        st.download_button(
            label="📥 下载清洗后的 Excel 报表",
            data=towrite,
            file_name="清洗后的玩家评论.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"处理失败，请检查数据格式: {e}")