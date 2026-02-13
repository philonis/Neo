import requests
from bs4 import BeautifulSoup

class SearchSkill:
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "网络搜索工具。用于查询信息、获取最新数据、查找资料等需要从网络获取信息的任务。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词或问题。"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "返回结果数量，默认3条。",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict):
        """
        运行网络搜索工具。
        使用百度搜索API获取结果。
        """
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 3)
        
        if not query:
            return {
                "status": "error",
                "message": "搜索关键词不能为空"
            }
        
        try:
            # 使用百度搜索（简单实现）
            search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 解析搜索结果
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # 查找搜索结果（百度的搜索结果结构可能会变化）
            for item in soup.select('.result')[:max_results]:
                title_elem = item.select_one('.t a')
                content_elem = item.select_one('.c-abstract')
                link_elem = item.select_one('.t a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "content": content
                    })
            
            if not results:
                # 如果没有找到结果，尝试另一种选择器
                for item in soup.select('.c-container')[:max_results]:
                    title_elem = item.select_one('h3.t a')
                    content_elem = item.select_one('.c-abstract')
                    link_elem = item.select_one('h3.t a')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href', '')
                        content = content_elem.get_text(strip=True) if content_elem else ""
                        
                        results.append({
                            "title": title,
                            "url": url,
                            "content": content
                        })
            
            return {
                "status": "success",
                "message": f"搜索完成，找到 {len(results)} 条结果",
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"搜索失败: {str(e)}"
            }
