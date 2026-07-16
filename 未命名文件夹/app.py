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
    
    # 1. 提取区服：兼容 23서버, 1서버, s26, S1 等
    srv = re.search(r'([A-Za-z0-9]+서버|s\d+|S\d+)', text, re.IGNORECASE)
    srv_name = srv.group(1) if srv else "未知"
    
    # 2. 移除区服，得到剩余内容
    clean = text.replace(srv_name, "", 1).strip()
    
    # 3. 极强力垃圾过滤：
    # 过滤掉：长串数字 ID (如 781621482881286560) 和 ID: 标签
    # 规则：匹配 10 位以上的连续数字
    clean = re.sub(r'\d{10,}', '', clean) 
    clean = re.sub(r'ID[:\s]*', '', clean, flags=re.IGNORECASE)
    
    # 4. 符号归一化：将斜杠、冒号、多余空格统一处理
    clean = re.sub(r'[/:\s]+', ' ', clean).strip()
    
    # 5. 分割用户名和评论
    # 以第一个空格为界：第一部分给名字，后面全部给评论
    parts = clean.split(' ', 1)
    
    name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
    comm = parts[1] if len(parts) > 1 else "无内容"
    
    # 6. 防误判修正：如果名字提取出来像个数字或特殊符号，且后面有内容
    # 且 name 长度小于 1，强制处理
    if len(name) < 1 or name in ["/", ".", "닉넴"]:
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
