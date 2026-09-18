import urllib.request
import concurrent.futures
import time
import os
import datetime

# 候选源池配置（按频道组织候选地址）
CANDIDATE_POOL = {
    "CCTV5": [
        "http://112.30.73.119:9901/tsfile/live/0005_2.m3u8?key=txiptv&playlive=0&authid=0",
        "https://live.264788.xyz/channel/cctv5?livekey=01WgOR41rriMmMkzNsd0UoaxJRwetZdxIvtVk",
        "http://gslbserv.itv.cmvideo.cn/1000000005000025222/1.m3u8?channel-id=ystenlive&Contentid=1000000005000025222&livemode=1&stbId=3",
        "http://iptv.huuc.edu.cn/hls/cctv5hd.m3u8"
    ],
    "CCTV5+": [
        "http://112.30.73.119:9901/tsfile/live/0006_1.m3u8?key=txiptv&playlive=1&authid=0",
        "http://112.30.73.119:9901/tsfile/live/0006_2.m3u8?key=txiptv&playlive=0&authid=0",
        "https://live.264788.xyz/channel/cctv5plus?livekey=01WgOR41rriMmMkzNsd0UoaxJRwetZdxIvtVk",
        "http://gslbserv.itv.cmvideo.cn/6000000001000015875/1.m3u8?channel-id=wasusyt&Contentid=6000000001000015875&livemode=1&stbId=3"
    ],
    "广东体育": [
        "http://r.jdshipin.com/LiYdg",
        "https://epg.pw/stream/7b470f9fc5c305db0c8622117b7b25ca00eb35ba3e93e865cf0ff9df5c736681.m3u8"
    ],
    "纬来体育": [
        "https://epg.pw/stream/8855a9936e37e608a0ec8a014cce1673dee9c5d68d560da376cc92e5edef2b25.m3u8"
    ],
    "翡翠台 1080P": [
        "http://103.172.187.30:12000/stream/mytv/null-1/master.m3u8"
    ],
    "翡翠台 4K": [
        "http://r.jdshipin.com/n90gt"
    ],
    "翡翠台": [
        "http://r.jdshipin.com/qClQf",
        "http://r.jdshipin.com/qrfbg",
        "http://r.jdshipin.com/62WM7",
        "http://r.jdshipin.com/GeWKr",
        "http://r.jdshipin.com/thuYX",
        "http://php.jdshipin.com:8880/TVOD/iptv.php?id=fct3",
        "http://php.jdshipin.com:8880/TVOD/iptv.php?id=fct4"
    ],
    "无线新闻台": [
        "http://r.jdshipin.com/CkuBd",
        "http://php.jdshipin.com:8880/TVOD/iptv.php?id=wxxw",
        "http://cdn9.163189.xyz/smt1.1.php?id=inews_twn"
    ],
    "TVB Plus": [
        "http://r.jdshipin.com/Nr5jq",
        "http://r.jdshipin.com/ndGgS"
    ],
    "TVB 星河": [
        "http://r.jdshipin.com/sXuuD",
        "http://r.jdshipin.com/Voac4",
        "http://php.jdshipin.com/TVOD/iptv.php?id=xinghe"
    ],
    "TVBS 新闻台": [
        "http://61.221.215.25:8800/hls/9/index.m3u8"
    ],
    "TVBS Asia": [
        "http://38.64.72.148/hls/modn/list/4005/playlist.m3u8"
    ],
    "台视新闻": [
        "http://38.64.72.148/hls/modn/list/4013/chunklist1.m3u8"
    ],
    "三立戏剧台": [
        "http://61.221.215.25:8800/hls/41/index.m3u8"
    ],
    "八大戏剧台": [
        "http://61.221.215.25:8800/hls/39/index.m3u8"
    ],
    "纬来精采台": [
        "http://61.221.215.25:8800/hls/48/index.m3u8"
    ],
    "人间卫视": [
        "https://5ddce30eb4b55.streamlock.net/bltvhd/bltv1/chunklist_w511254805.m3u8"
    ]
}

def check_stream(url, timeout=3.0):
    """
    测试流地址是否可用，并返回 (是否可用, 延迟秒数)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    start = time.time()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            if resp.status == 200:
                head = resp.read(200).decode('utf-8', errors='ignore')
                if '#EXTM3U' in head or resp.headers.get('Content-Type', '').startswith('application/') or resp.headers.get('Content-Type', '').startswith('video/'):
                    return True, elapsed
    except:
        pass
    return False, 999.0

def update_all_sources():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行直播源全量并发测活...")

    # 收集待测列表并去重
    unique_urls = set()
    for urls in CANDIDATE_POOL.values():
        unique_urls.update(urls)

    # 并发测活
    url_status = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = {executor.submit(check_stream, u): u for u in unique_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            u = future_to_url[future]
            try:
                ok, latency = future.result()
                url_status[u] = (ok, latency)
            except:
                url_status[u] = (False, 999.0)

    # 筛选各频道可用的源并按延迟升序排序
    active_pool = {}
    for ch_name, urls in CANDIDATE_POOL.items():
        valid_list = []
        for u in urls:
            ok, latency = url_status.get(u, (False, 999.0))
            if ok:
                valid_list.append((u, latency))
        # 按延迟排序
        valid_list.sort(key=lambda x: x[1])
        active_urls = [x[0] for x in valid_list]
        # 如果当前测活没有通过的，回退保留原第一条，避免列表完全清空
        if not active_urls and urls:
            active_urls = [urls[0]]
        active_pool[ch_name] = active_urls
        print(f"  * {ch_name}: {len(active_urls)} 条可用源")

    # 构建 favorites.txt
    fav_groups = [
        ("体育精选", ["CCTV5", "CCTV5+", "广东体育", "纬来体育"]),
        ("香港专区", ["翡翠台 1080P", "翡翠台 4K", "翡翠台", "无线新闻台", "TVB Plus", "TVB 星河"]),
        ("台湾专区", ["TVBS 新闻台", "TVBS Asia", "台视新闻", "三立戏剧台", "八大戏剧台", "纬来精采台", "人间卫视"])
    ]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tv_dir = os.path.join(base_dir, 'tv')
    fav_txt_path = os.path.join(tv_dir, 'favorites.txt')

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    fav_txt_lines = []
    for g_title, ch_list in fav_groups:
        fav_txt_lines.append(f"{g_title},#genre#")
        for ch in ch_list:
            for u in active_pool.get(ch, []):
                fav_txt_lines.append(f"{ch},{u}")
        fav_txt_lines.append("")

    with open(fav_txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fav_txt_lines).strip() + '\n')
    print(f"已更新 {fav_txt_path}")

    # 调用 merge_custom.py 重新生成所有 M3U 和合并到 iptv4
    from merge_custom import merge_custom_channels
    merge_custom_channels()
    print(f"[{now_str}] 全部直播源测活与自动重构完成！")

if __name__ == '__main__':
    update_all_sources()
