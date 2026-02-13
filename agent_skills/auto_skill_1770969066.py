
import subprocess
import json


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "get_beijing_weather",
            "description": "获取北京天气数据",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }


def run(arguments: dict):
    cmd = ["curl", "-k", "-s", "https://weather-api.metaweather.com/api/location/2151330/"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return {"success": False, "error": result.stderr}
    
    try:
        data = json.loads(result.stdout)
        return {"success": True, "data": data}
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse JSON"}


if __name__ == "__main__":
    print(json.dumps(run({})))
