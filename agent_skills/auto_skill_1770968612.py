
import json
import urllib.request
from urllib.parse import quote

def get_weather(city: str) -> dict:
    """获取实时天气信息"""
    try:
        url = f"https://wttr.in/{quote(city)}?format=j1"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        current = data["current_condition"][0]
        return {
            "success": True,
            "data": {
                "city": city,
                "temperature": current["temp_C"],
                "feels_like": current["FeelsLikeC"],
                "humidity": current["humidity"],
                "weather": current["weatherDesc"][0]["value"],
                "wind_speed": current["windspeedKmph"],
                "uv_index": current["UVIndex"]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def run(arguments: dict) -> dict:
    """入口函数"""
    city = arguments.get("city", "Beijing")
    return get_weather(city)

def get_tool_definition() -> dict:
    """返回 OpenAI 标准的工具定义"""
    return {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的实时天气信息，包括温度、湿度、天气状况等",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，默认为 Beijing"
                    }
                },
                "required": []
            }
        }
    }
