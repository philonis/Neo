import requests
import json
import re
from typing import Dict, List

class HttpSkill:
    """HTTP 请求工具 - 用于获取网页内容、API 数据等"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "http_request",
                "description": "发送 HTTP 请求获取数据。支持 GET 和 POST 请求，可用于获取网页内容、调用 API、下载 JSON 数据等。当需要从网络获取信息时使用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "请求的 URL 地址"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST"],
                            "description": "HTTP 方法，默认 GET"
                        },
                        "headers": {
                            "type": "object",
                            "description": "请求头，可选"
                        },
                        "data": {
                            "type": "object",
                            "description": "POST 请求的数据，可选"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间（秒），默认 30"
                        }
                    },
                    "required": ["url"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict) -> dict:
        url = arguments.get("url", "")
        method = arguments.get("method", "GET").upper()
        headers = arguments.get("headers", {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        data = arguments.get("data")
        timeout = arguments.get("timeout", 30)
        
        if not url:
            return {"status": "error", "message": "URL 不能为空"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "")
            
            if "application/json" in content_type:
                return {
                    "status": "success",
                    "message": "请求成功",
                    "data": response.json(),
                    "content_type": content_type
                }
            else:
                text = response.text
                if len(text) > 5000:
                    text = text[:5000] + "\n... (内容已截断)"
                return {
                    "status": "success",
                    "message": "请求成功",
                    "content": text,
                    "content_type": content_type,
                    "status_code": response.status_code
                }
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "请求超时"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"请求失败: {str(e)}"}


class RssSkill:
    """RSS/Atom 订阅解析工具"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "rss_fetcher",
                "description": "获取并解析 RSS/Atom 订阅源。可以获取播客、博客等的最新内容。返回标题、链接、发布时间等信息。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "RSS/Atom 订阅地址"
                        },
                        "count": {
                            "type": "integer",
                            "description": "返回条目数量，默认 5"
                        }
                    },
                    "required": ["url"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict) -> dict:
        url = arguments.get("url", "")
        count = arguments.get("count", 5)
        
        if not url:
            return {"status": "error", "message": "RSS 地址不能为空"}
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            items = []
            
            item_pattern = r'<item[^>]*>(.*?)</item>'
            entry_pattern = r'<entry[^>]*>(.*?)</entry>'
            
            if "<item" in content:
                matches = re.findall(item_pattern, content, re.DOTALL)
            elif "<entry" in content:
                matches = re.findall(entry_pattern, content, re.DOTALL)
            else:
                return {"status": "error", "message": "未找到 RSS/Atom 内容"}
            
            for match in matches[:count]:
                item = {}
                
                title_match = re.search(r'<title[^>]*><!\[CDATA\[(.*?)\]\]></title>|<title[^>]*>(.*?)</title>', match, re.DOTALL)
                if title_match:
                    item["title"] = (title_match.group(1) or title_match.group(2) or "").strip()
                
                link_match = re.search(r'<link[^>]*>(.*?)</link>|<link[^>]*href="([^"]*)"', match, re.DOTALL)
                if link_match:
                    item["link"] = (link_match.group(1) or link_match.group(2) or "").strip()
                
                pubdate_match = re.search(r'<pubDate[^>]*>(.*?)</pubDate>|<published[^>]*>(.*?)</published>', match, re.DOTALL)
                if pubdate_match:
                    item["pub_date"] = (pubdate_match.group(1) or pubdate_match.group(2) or "").strip()
                
                desc_match = re.search(r'<description[^>]*><!\[CDATA\[(.*?)\]\]></description>|<description[^>]*>(.*?)</description>|<summary[^>]*><!\[CDATA\[(.*?)\]\]></summary>', match, re.DOTALL)
                if desc_match:
                    item["description"] = (desc_match.group(1) or desc_match.group(2) or desc_match.group(3) or "").strip()[:200]
                
                if item.get("title"):
                    items.append(item)
            
            return {
                "status": "success",
                "message": f"获取到 {len(items)} 条内容",
                "items": items
            }
            
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"请求失败: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"解析失败: {str(e)}"}


class WebScraperSkill:
    """网页内容提取工具"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "web_scraper",
                "description": "从网页中提取文本内容。可以获取网页标题、正文、链接等信息。用于从网页获取特定信息。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "网页地址"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS 选择器，用于提取特定元素，可选"
                        }
                    },
                    "required": ["url"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict) -> dict:
        url = arguments.get("url", "")
        selector = arguments.get("selector")
        
        if not url:
            return {"status": "error", "message": "URL 不能为空"}
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.DOTALL | re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""
            
            text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text) > 3000:
                text = text[:3000] + "\n... (内容已截断)"
            
            return {
                "status": "success",
                "message": "提取成功",
                "title": title,
                "content": text,
                "url": url
            }
            
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"请求失败: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"提取失败: {str(e)}"}
