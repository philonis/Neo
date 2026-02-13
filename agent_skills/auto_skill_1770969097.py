
import subprocess
import json

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "get_beijing_weather",
            "description": "查询北京天气信息",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }

def run(arguments: dict):
    try:
        cmd = ["curl", "-k", "-s", "https://weather-api.metaweather.com/api/location/2151330/"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        
        data = json.loads(result.text)
        
        weather_info = {
            "城市": data.get("title", "北京"),
            "天气": data.get("consolidated_weather", [{}])[0].get("weather_state_name", "未知"),
            "温度": round(data.get("consolidated_weather", [{}])[0].get("the_temp", 0), 1),
            "湿度": data.get("consolidated_weather", [{}])[0].get("humidity", 0),
            "风速": round(data.get("consolidated_weather", [{}])[0].get("wind_speed", 0), 1)
        }
        
        return {"success": True, "data": weather_info}
    except Exception as e:
        return {"success": False, "error": str(e)}
