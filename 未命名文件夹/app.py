import streamlit as st
import pandas as pd
import re
import io

# 页面配置
st.set_page_config(page_title="Naver 评论清洗器", page_icon="🧹")
st.title("🧹 nan的秘制运营数据一键清洗助手")
st.write("请上传导出的 Excel 或 CSV 文件，系统将自动识别数据列并进行深度清洗。")

# 1. 文件上传
uploaded_file = st.file_uploader("拖入采集到的数据文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 读取文件
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 2. 智能锁定包含有用数据的列
        target_col = None
        for col in df.columns:
            # 搜索包含服务器关键词的列
            if df[col].astype(str).str.contains(r'서버|S\d+', regex=True).any():
                target_col = col
                break
        
        if not target_col:
            target_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            st.warning(f"⚠️ 未检测到标准区服格式，默认处理列: {target_col}")
        else:
            st.success(f"✅ 已自动识别数据列: {target_col}")

        # 3. 深度清洗逻辑 (最终完整版)
        def parse_row(text):
            text = str(text).strip()
            
            # A. 提取区服 (兼容 29서버, S26, s1 等)
            srv = re.search(r'([A-Za-z0-9]+서버|S\d+)', text, re.IGNORECASE)
            srv_name = srv.group(1) if srv else "未知"
            
            # B. 移除区服文字
            clean = text.replace(srv_name, "", 1).strip()
            
            # C. 强力清洗：剔除 10 位以上长数字ID 和 ID 标签
            clean = re.sub(r'\d{10,}', '', clean)
            clean = re.sub(r'ID[:\s]*', '', clean, flags=re.IGNORECASE)
            
            # D. 符号归一化：将所有分隔符统一转化为空格
            clean = re.sub(r'[/:\s]+', ' ', clean).strip()
            
            # E. 分割用户名与评论 (以第一个空格为界)
            parts = clean.split(' ', 1)
            name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
            comm = parts[1] if len(parts) > 1 else "无内容"
            
            # F. 用户名二次防错：如果 name 看起来像垃圾，则归入评论
            # (如识别出了“ID”、“닉넴” 或无效符号)
            if name.upper() in ["ID", "닉넴", ".", "/"] or len(name) < 1:
                comm = f"{name} {comm}".strip()
                name = "匿名"
                
            return pd.Series([srv_name, name, comm])

        # 4. 执行清洗
        res = df[target_col].apply(parse_row)
        res.columns = ['区服', '玩家名', '评论内容']
        
        # 显示结果
        st.dataframe(res)
        
        # 5. 提供下载
        towrite = io.BytesIO()
        res.to_excel(towrite, index=False)
        st.download_button(
            label="📥 下载清洗后的报表",
            data=towrite.getvalue(),
            file_name="清洗完成_玩家评论.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"处理失败，请确认文件格式是否标准: {e}")
