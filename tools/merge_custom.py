import os
import re

def merge_custom_channels():
    # 获取根目录及路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tv_dir = os.path.join(base_dir, 'tv')
    custom_txt_path = os.path.join(tv_dir, 'custom.txt')
    iptv4_txt_path = os.path.join(tv_dir, 'iptv4.txt')
    iptv4_m3u_path = os.path.join(tv_dir, 'iptv4.m3u')
    custom_m3u_path = os.path.join(tv_dir, 'custom.m3u')
    favorites_txt_path = os.path.join(tv_dir, 'favorites.txt')
    favorites_m3u_path = os.path.join(tv_dir, 'favorites.m3u')

    if not os.path.exists(custom_txt_path):
        print(f"自定义源文件不存在: {custom_txt_path}")
        return

    with open(custom_txt_path, 'r', encoding='utf-8') as f:
        custom_content = f.read().strip()

    if not os.path.exists(iptv4_txt_path):
        print(f"目标源文件不存在: {iptv4_txt_path}")
        return

    with open(iptv4_txt_path, 'r', encoding='utf-8') as f:
        iptv_lines = f.readlines()

    # 解析 custom.txt 中的分组名称
    custom_genres = set()
    for line in custom_content.splitlines():
        line = line.strip()
        if line.endswith('#genre#'):
            genre = line.split(',')[0].strip()
            custom_genres.add(genre)

    # 过滤掉 iptv4.txt 中已有的这些 custom 分组，防止重复追加
    cleaned_lines = []
    skip_current_genre = False
    for line in iptv_lines:
        stripped = line.strip()
        if stripped.endswith('#genre#'):
            genre = stripped.split(',')[0].strip()
            if genre in custom_genres:
                skip_current_genre = True
                continue
            else:
                skip_current_genre = False
        if skip_current_genre:
            continue
        cleaned_lines.append(line)

    cleaned_text = ''.join(cleaned_lines)

    # 找到更新时间标记或末尾，将 custom_content 插入到更新时间之前
    update_time_marker = "更新时间,#genre#"
    if update_time_marker in cleaned_text:
        parts = cleaned_text.split(update_time_marker)
        merged_txt = parts[0].rstrip() + "\n\n\n" + custom_content + "\n\n\n" + update_time_marker + parts[1]
    else:
        merged_txt = cleaned_text.rstrip() + "\n\n\n" + custom_content + "\n"

    with open(iptv4_txt_path, 'w', encoding='utf-8') as f:
        f.write(merged_txt)
    print(f"已成功将自定义源合并到: {iptv4_txt_path}")

    # 生成各 M3U 文件
    generate_m3u_from_txt(iptv4_txt_path, iptv4_m3u_path)
    generate_m3u_from_txt(custom_txt_path, custom_m3u_path)
    if os.path.exists(favorites_txt_path):
        generate_m3u_from_txt(favorites_txt_path, favorites_m3u_path)

def generate_m3u_from_txt(txt_path, m3u_path):
    epg_url = 'http://epg.51zmt.top:8000/e.xml'
    m3u_content = [f'#EXTM3U x-tvg-url="{epg_url}"']
    channel_genre = '未分类'

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.endswith('#genre#'):
                channel_genre = line.split(',')[0].replace('#genre#', '').strip()
                continue

            if ',' not in line:
                continue

            channel_name, channel_url = map(str.strip, line.split(',', 1))

            # 规范化 tvg-name 以便完美匹配 EPG 和台标 Logo
            base_name = channel_name
            if '翡翠台' in channel_name:
                base_name = '翡翠台'
            elif '无线新闻' in channel_name or '無綫新聞' in channel_name:
                base_name = '无线新闻台'
            elif 'TVB Plus' in channel_name:
                base_name = 'TVB Plus'
            elif 'TVB 星河' in channel_name or 'TVB星河' in channel_name:
                base_name = 'TVB星河'
            elif channel_name.upper() == 'CCTV5':
                base_name = 'CCTV5'
            elif 'CCTV5+' in channel_name.upper():
                base_name = 'CCTV5+'
            elif '广东体育' in channel_name:
                base_name = '广东体育'
            elif 'TVBS' in channel_name:
                base_name = 'TVBS'
            elif '台视' in channel_name:
                base_name = '台视'
            elif '三立' in channel_name:
                base_name = '三立'
            elif '八大' in channel_name:
                base_name = '八大'
            elif '纬来' in channel_name:
                base_name = '纬来体育' if '体育' in channel_name else '纬来精采'

            tvg_logo = f'https://tb.zbds.top/logo/{base_name}.png'
            m3u_entry = f'#EXTINF:-1 tvg-name="{channel_name}" tvg-id="{base_name}" tvg-logo="{tvg_logo}" group-title="{channel_genre}", {channel_name}\n{channel_url}'
            m3u_content.append(m3u_entry)

    with open(m3u_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(m3u_content) + '\n')
    print(f"已成功生成 M3U 文件: {m3u_path}")

if __name__ == '__main__':
    merge_custom_channels()
