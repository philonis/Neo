"""
浏览器控制器 - Playwright浏览器自动化控制

核心功能:
1. 浏览器生命周期管理
2. 页面导航和操作
3. 内容提取和截图
4. DOM分析
5. 人类行为模拟
"""

import asyncio
import random
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path


class BrowserController:
    """
    浏览器控制器
    
    使用Playwright实现浏览器自动化
    支持Headless和有界面模式
    """
    
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        headless: bool = True,
        user_agent: str = None,
        viewport: Dict = None,
        slow_mo: int = 0,
        screenshots_dir: str = "browser_agent/screenshots"
    ):
        self.headless = headless
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.slow_mo = slow_mo
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        self.browser = None
        self.context = None
        self.page = None
        self.current_url = ""
        self.session_id = None
        
        self._playwright = None
    
    async def initialize(self) -> bool:
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            self.browser = await self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport=self.viewport,
                user_agent=self.user_agent,
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            
            await self._inject_stealth_scripts()
            
            self.page = await self.context.new_page()
            
            return True
            
        except ImportError:
            print("[BrowserController] Playwright未安装，请运行: pip install playwright && playwright install")
            return False
        except Exception as e:
            print(f"[BrowserController] 初始化失败: {e}")
            return False
    
    async def _inject_stealth_scripts(self):
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
        """)
    
    async def close(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        self.page = None
        self.context = None
        self.browser = None
        self._playwright = None
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            await self.human_like_delay(0.5, 1.5)
            
            response = await self.page.goto(url, wait_until=wait_until, timeout=30000)
            
            self.current_url = self.page.url
            
            await self.human_like_delay(0.3, 0.8)
            
            return {
                "success": True,
                "url": self.current_url,
                "status": response.status if response else None,
                "title": await self.page.title()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_page_info(self) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "content": await self._get_page_content()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_page_content(self, max_length: int = 5000) -> str:
        content = await self.page.content()
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) > max_length:
            text = text[:max_length] + "\n... (内容已截断)"
        
        return text
    
    async def get_dom_structure(self) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            interactive_elements = await self.page.evaluate("""
                () => {
                    const elements = [];
                    const selectors = ['a', 'button', 'input', 'select', 'textarea', '[onclick]', '[role="button"]'];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach((el, index) => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                elements.push({
                                    tag: el.tagName.toLowerCase(),
                                    type: el.type || null,
                                    text: (el.innerText || el.value || el.placeholder || '').substring(0, 100),
                                    id: el.id || null,
                                    className: el.className || null,
                                    name: el.name || null,
                                    href: el.href || null,
                                    placeholder: el.placeholder || null,
                                    index: index,
                                    visible: rect.width > 0 && rect.height > 0
                                });
                            }
                        });
                    });
                    
                    return elements;
                }
            """)
            
            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "interactive_elements": interactive_elements[:50]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def find_element(self, description: str) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            selector = await self._description_to_selector(description)
            
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    return {
                        "success": True,
                        "selector": selector,
                        "found": True
                    }
            
            elements = await self.page.evaluate(f"""
                () => {{
                    const searchText = "{description.lower()}";
                    const elements = [];
                    
                    document.querySelectorAll('a, button, input, select, textarea, [onclick], [role="button"]').forEach((el, i) => {{
                        const text = (el.innerText || el.value || el.placeholder || el.name || el.id || '').toLowerCase();
                        if (text.includes(searchText)) {{
                            elements.push({{
                                tag: el.tagName.toLowerCase(),
                                text: el.innerText || el.value || '',
                                index: i
                            }});
                        }}
                    }});
                    
                    return elements.slice(0, 10);
                }}
            """)
            
            if elements:
                return {
                    "success": True,
                    "found": True,
                    "elements": elements,
                    "selector": None
                }
            
            return {"success": True, "found": False, "message": f"未找到匹配 '{description}' 的元素"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _description_to_selector(self, description: str) -> Optional[str]:
        desc_lower = description.lower()
        
        text_selectors = [
            f'text="{description}"',
            f'text="{desc_lower}"',
            f'[placeholder*="{description}"]',
            f'[aria-label*="{description}"]',
            f'[title*="{description}"]',
        ]
        
        for selector in text_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    return selector
            except:
                continue
        
        return None
    
    async def click(self, target: str) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            find_result = await self.find_element(target)
            
            if not find_result.get("found"):
                return {"success": False, "error": f"未找到元素: {target}"}
            
            if find_result.get("selector"):
                await self.human_like_delay(0.3, 0.8)
                await self.page.click(find_result["selector"])
            else:
                elements = find_result.get("elements", [])
                if elements:
                    first = elements[0]
                    selector = f"{first['tag']}:has-text('{first['text'][:50]}')"
                    await self.human_like_delay(0.3, 0.8)
                    await self.page.click(selector)
            
            await self.human_like_delay(0.5, 1.0)
            
            return {
                "success": True,
                "message": f"已点击: {target}",
                "new_url": self.page.url
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fill(self, target: str, value: str) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            find_result = await self.find_element(target)
            
            if not find_result.get("found"):
                return {"success": False, "error": f"未找到输入框: {target}"}
            
            if find_result.get("selector"):
                await self.human_like_delay(0.2, 0.5)
                await self.page.fill(find_result["selector"], value)
            else:
                elements = find_result.get("elements", [])
                if elements:
                    first = elements[0]
                    selector = f"{first['tag']}[name*='{first.get('name', '') or first.get('text', '')[:20]}']"
                    try:
                        await self.page.fill(selector, value)
                    except:
                        await self.page.type(f"{first['tag']}:nth-of-type({first['index'] + 1})", value)
            
            await self.human_like_delay(0.1, 0.3)
            
            return {
                "success": True,
                "message": f"已输入内容到: {target}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def scroll(self, direction: str = "down", amount: int = 300) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            
            await self.human_like_delay(0.3, 0.6)
            
            return {"success": True, "message": f"已滚动 {direction} {amount}px"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, name: str = None) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            if not name:
                name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            filepath = self.screenshots_dir / f"{name}.png"
            
            await self.page.screenshot(path=str(filepath), full_page=False)
            
            return {
                "success": True,
                "message": "截图成功",
                "path": str(filepath)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_text(self, selector: str = None) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                else:
                    return {"success": False, "error": f"未找到选择器: {selector}"}
            else:
                text = await self._get_page_content(max_length=10000)
            
            return {
                "success": True,
                "text": text,
                "url": self.page.url
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def wait_for(self, selector: str = None, timeout: int = 10000) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            if selector:
                await self.page.wait_for_selector(selector, timeout=timeout)
            else:
                await self.page.wait_for_load_state("networkidle", timeout=timeout)
            
            return {"success": True, "message": "等待完成"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_login_required(self) -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            login_indicators = await self.page.evaluate("""
                () => {
                    const loginKeywords = ['登录', '注册', 'login', 'sign in', 'signin', 'log in'];
                    const pageText = document.body.innerText.toLowerCase();
                    
                    const hasLoginForm = document.querySelector('input[type="password"]') !== null;
                    
                    const hasLoginButton = loginKeywords.some(keyword => 
                        pageText.includes(keyword.toLowerCase())
                    );
                    
                    const hasLoginFormElements = document.querySelectorAll('input[type="password"], input[name*="login"], input[name*="email"]').length > 0;
                    
                    return {
                        hasLoginForm: hasLoginForm,
                        hasLoginButton: hasLoginButton,
                        hasLoginFormElements: hasLoginFormElements,
                        likelyRequiresLogin: hasLoginForm || (hasLoginButton && hasLoginFormElements)
                    };
                }
            """)
            
            return {
                "success": True,
                "requires_login": login_indicators.get("likelyRequiresLogin", False),
                "details": login_indicators
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_cookies(self) -> List[Dict]:
        if not self.context:
            return []
        
        cookies = await self.context.cookies()
        return [dict(c) for c in cookies]
    
    async def set_cookies(self, cookies: List[Dict]):
        if not self.context:
            return
        
        await self.context.add_cookies(cookies)
    
    async def human_like_delay(self, min_seconds: float = 0.1, max_seconds: float = 0.5):
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def human_like_type(self, selector: str, text: str):
        await self.page.click(selector)
        
        for char in text:
            await self.page.keyboard.type(char)
            await self.human_like_delay(0.05, 0.15)
    
    async def human_like_mouse_move(self, x: int, y: int):
        await self.page.mouse.move(x, y, steps=random.randint(5, 10))
