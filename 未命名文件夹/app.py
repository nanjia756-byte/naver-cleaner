import streamlit as st
import pandas as pd
import re
import io

def parse_row(text):
    text = str(text).strip()
    
    # 1. 强力区服捕获：涵盖 S1, 29서버, 29섭, 1서버 等所有已知变体
    # 这里的正则优先级最高，确保区服被优先剥离
    server_pattern = r'([Ss]?[0-9]+(?:서버|섭)?|S[0-9]+)'
    match = re.search(server_pattern, text, re.IGNORECASE)
    
    srv_name = match.group(1) if match else "未知"
    
    # 2. 彻底挖空：在处理名字和内容前，先从原文本中移除区服标记
    # 使用 count=1 仅移除匹配到的第一个区服，保护数据完整性
    clean_text = re.sub(server_pattern, '', text, count=1, flags=re.IGNORECASE).strip()
    
    # 3. 过滤干扰项：ID、长数字串、닉넴关键词
    # 必须先于名字切分进行，防止 ID 被误认为名字
    clean_text = re.sub(r'(ID[:\s]*\d+|닉넴|\d{10,})', ' ', clean_text, flags=re.IGNORECASE)
    
    # 4. 标准化分隔：统一处理 /, :, 点号，将剩余部分切分为名字和内容
    clean_text = re.sub(r'[/|:\s]+', ' ', clean_text).strip()
    
    parts = clean_text.split(' ', 1)
    name = parts[0] if len(parts) > 0 and parts[0] else "匿名"
    comm = parts[1] if len(parts) > 1 else "无内容"
    
    # 5. 最终纠偏层
    if (name == "." or name.upper() in ["ID", "닉넴"]) and len(comm) > 0:
        name = "匿名"
        
    return pd.Series([srv_name, name, comm])
