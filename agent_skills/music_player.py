import subprocess
import webbrowser
import json
from typing import Dict, List, Optional

def run(params: Dict) -> Dict:
    """
    播放音乐的功能
    支持参数：
    - genre: 音乐类型（如"轻松", "流行", "古典"等）
    - mood: 心情（如"放松", "专注", "快乐"等）
    - platform: 平台（如"youtube", "spotify", "bilibili"等）
    """
    genre = params.get('genre', '轻松')
    mood = params.get('mood', '放松')
    platform = params.get('platform', 'youtube')
    
    # 根据类型和心情生成搜索关键词
    music_map = {
        '轻松': {
            '放松': ['lo-fi音乐', '轻音乐', '钢琴曲', '自然声音'],
            '专注': ['背景音乐', '学习音乐', '无歌词音乐'],
            '快乐': ['轻快音乐', '快乐钢琴曲', '欢快纯音乐']
        },
        '流行': {
            '放松': ['流行轻音乐', '流行钢琴曲'],
            '快乐': ['热门流行歌曲', '抖音热歌']
        },
        '古典': {
            '放松': ['古典钢琴曲', '莫扎特', '巴赫'],
            '专注': ['巴洛克音乐', '古典学习音乐']
        }
    }
    
    # 获取搜索关键词
    keywords = []
    if genre in music_map and mood in music_map[genre]:
        keywords = music_map[genre][mood]
    else:
        keywords = ['放松音乐', '背景音乐', '轻音乐']
    
    # 生成YouTube搜索URL
    search_query = f"{genre} {mood} {keywords[0] if keywords else '音乐'}"
    youtube_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    
    # 生成Spotify搜索URL
    spotify_url = f"https://open.spotify.com/search/{search_query.replace(' ', '%20')}"
    
    # 生成B站搜索URL
    bilibili_url = f"https://search.bilibili.com/all?keyword={search_query.replace(' ', '%20')}"
    
    # 根据平台选择URL
    if platform == 'spotify':
        target_url = spotify_url
        platform_name = 'Spotify'
    elif platform == 'bilibili':
        target_url = bilibili_url
        platform_name = 'B站'
    else:
        target_url = youtube_url
        platform_name = 'YouTube'
    
    # 尝试打开浏览器
    try:
        webbrowser.open(target_url)
        return {
            'success': True,
            'message': f'已为您打开{platform_name}搜索"{search_query}"',
            'search_query': search_query,
            'url': target_url,
            'suggestions': keywords,
            'instructions': f'请在打开的{platform_name}页面中选择您喜欢的音乐播放'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'无法自动打开浏览器，请手动访问：{target_url}',
            'url': target_url,
            'error': str(e)
        }

def get_tool_definition() -> Dict:
    return {
        'name': 'music_player',
        'description': '播放音乐，支持搜索和播放各种类型的音乐',
        'parameters': {
            'type': 'object',
            'properties': {
                'genre': {
                    'type': 'string',
                    'description': '音乐类型，如"轻松", "流行", "古典", "爵士"等',
                    'default': '轻松'
                },
                'mood': {
                    'type': 'string', 
                    'description': '心情或场景，如"放松", "专注", "快乐", "睡眠"等',
                    'default': '放松'
                },
                'platform': {
                    'type': 'string',
                    'description': '音乐平台，如"youtube", "spotify", "bilibili"等',
                    'default': 'youtube'
                }
            },
            'required': []
        }
    }