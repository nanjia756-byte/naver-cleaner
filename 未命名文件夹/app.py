def parse_row(text):
    text = str(text)
    
    # 1. 提取区服：寻找“数字 + 서버”
    server_match = re.search(r'(\d+서버)', text)
    server_name = server_match.group(1) if server_match else "未知"
    
    # 2. 移除区服和任何潜在的起始干扰字符
    # 假设区服后面紧跟着用户名
    remaining = text
    if server_match:
        remaining = remaining.replace(server_match.group(0), "", 1).strip()
    
    # 3. 核心难点：用户名和评论分离
    # 运营数据通常有一个明显的特征：用户名后会有分隔符号（如空格、/、:、| 等）
    # 我们匹配第一个遇到的特殊分隔符作为用户名结束的标志
    # 或者如果评论内容是韩语/符号混合，我们匹配用户名长度（假设用户名不超过 12 个字符）
    
    # 这里定义常见的用户名结束符，你可以根据实际导出的数据添加
    split_pattern = r'[\s/:|]+' 
    parts = re.split(split_pattern, remaining, maxsplit=1)
    
    if len(parts) >= 2:
        player_name = parts[0]
        comment = parts[1]
    else:
        # 如果没找到分隔符，说明数据质量极差，全部归为评论
        player_name = "未知"
        comment = remaining
        
    return pd.Series([server_name, player_name, comment])