import requests
import re
from typing import Dict, Any, Optional

def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    查找播客的RSS订阅地址
    """
    podcast_name = params.get("podcast_name", "")
    
    if not podcast_name:
        return {
            "status": "error",
            "message": "请提供播客名称"
        }
    
    # 尝试从itunes搜索
    try:
        # 使用itunes API搜索播客
        search_url = f"https://itunes.apple.com/search"
        params_search = {
            "term": podcast_name,
            "media": "podcast",
            "country": "CN",
            "limit": 5
        }
        
        response = requests.get(search_url, params=params_search, timeout=10)
        data = response.json()
        
        if data.get("resultCount", 0) > 0:
            results = []
            for result in data["results"]:
                results.append({
                    "title": result.get("collectionName", ""),
                    "artist": result.get("artistName", ""),
                    "feed_url": result.get("feedUrl", ""),
                    "artwork": result.get("artworkUrl600", result.get("artworkUrl100", "")),
                    "genres": result.get("genres", [])
                })
            
            return {
                "status": "success",
                "message": f"找到 {len(results)} 个相关播客",
                "results": results
            }
        else:
            return {
                "status": "error",
                "message": "未找到相关播客"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"搜索失败: {str(e)}"
        }

def get_tool_definition() -> Dict[str, Any]:
    return {
        "name": "podcast_finder",
        "description": "查找播客的RSS订阅地址，支持中文播客名称搜索",
        "parameters": {
            "type": "object",
            "properties": {
                "podcast_name": {
                    "description": "播客名称，如'津津乐道'",
                    "type": "string"
                }
            },
            "required": ["podcast_name"]
        }
    }