import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from playwright.async_api import async_playwright


@dataclass
class StepResult:
    step: str
    status: str  # "success", "fail"
    data: Dict[str, Any]
    error: Optional[str] = None


class BrowserDriver:
    def __init__(self, headless: bool = False, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.page = None
        self.playwright = None
    
    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
        self.page = await self.browser.new_page()
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def login(self, username: str = "demo", password: str = "password123", username_selector: Optional[str] = None, password_selector: Optional[str] = None) -> StepResult:
        try:
            await self.page.goto("http://127.0.0.1:5000/login")
            await self.page.wait_for_load_state("domcontentloaded")
            
            u_sel = username_selector or 'input[name="username"]'
            p_sel = password_selector or 'input[name="password"]'
            
            try:
                await self.page.fill(u_sel, username, timeout=2000)
            except Exception:
                for alt in ['input[name="login_"]', 'input[type="text"]', '[placeholder*="User" i]']:
                    try:
                        await self.page.fill(alt, username, timeout=2000)
                        break
                    except Exception:
                        pass
            
            try:
                await self.page.fill(p_sel, password, timeout=2000)
            except Exception:
                for alt in ['input[name="pass_"]', 'input[type="password"]', '[placeholder*="Pass" i]']:
                    try:
                        await self.page.fill(alt, password, timeout=2000)
                        break
                    except Exception:
                        pass

            await self.page.click('button[type="submit"]')
            await self.page.wait_for_url("**/search**", timeout=10000)
            
            return StepResult(
                step="login",
                status="success",
                data={"username": username, "url": self.page.url}
            )
        except Exception as e:
            return StepResult(
                step="login",
                status="fail",
                data={},
                error=str(e)
            )
    
    async def search(self, query: str = "widget", search_selector: Optional[str] = None) -> StepResult:
        try:
            await self.page.goto("http://127.0.0.1:5000/search")
            await self.page.wait_for_load_state("domcontentloaded")
            
            if query:
                s_sel = search_selector or 'input[name="q"]'
                try:
                    await self.page.fill(s_sel, query, timeout=2000)
                except Exception:
                    await self.page.fill('input[type="text"]', query, timeout=2000)
                await self.page.click('button[type="submit"]')
                await self.page.wait_for_load_state("domcontentloaded")
            
            products = await self.page.evaluate("""() => {
                const items = document.querySelectorAll('.product');
                return Array.from(items).map(item => ({
                    name: item.querySelector('h3')?.textContent?.trim(),
                    price: item.querySelector('.product-price')?.textContent?.trim()
                }));
            }""")
            
            return StepResult(
                step="search",
                status="success",
                data={"query": query, "products_found": len(products), "products": products}
            )
        except Exception as e:
            return StepResult(
                step="search",
                status="fail",
                data={},
                error=str(e)
            )
    
    async def add_to_cart(self, product_name: str = "Blue Widget") -> StepResult:
        try:
            await self.page.wait_for_selector('.product', timeout=5000)
            
            try:
                await self.page.click(f'.product:has-text("{product_name}") button', timeout=3000)
            except Exception:
                await self.page.click('button.add-cart, button[type="submit"]', timeout=3000)
            
            await self.page.wait_for_load_state("domcontentloaded")
            
            cart_count = await self.page.evaluate("""() => {
                const link = document.querySelector('a[href*="cart"]');
                if (link) {
                    const match = link.textContent.match(/\\((\\d+)\\)/);
                    return match ? parseInt(match[1]) : 0;
                }
                return 0;
            }""")
            
            return StepResult(
                step="add_to_cart",
                status="success",
                data={"product": product_name, "cart_count": cart_count}
            )
        except Exception as e:
            return StepResult(
                step="add_to_cart",
                status="fail",
                data={},
                error=str(e)
            )
    
    async def go_to_cart(self) -> StepResult:
        try:
            await self.page.goto("http://127.0.0.1:5000/cart")
            await self.page.wait_for_load_state("domcontentloaded")
            
            cart_items = await self.page.evaluate("""() => {
                const items = document.querySelectorAll('.cart-item');
                return Array.from(items).map(item => ({
                    name: item.querySelector('h3')?.textContent?.trim(),
                    price: item.querySelector('.item-price')?.textContent?.trim(),
                    quantity: item.querySelector('.item-qty')?.value || 1
                }));
            }""")
            
            total = await self.page.evaluate("""() => {
                const el = document.querySelector('.total');
                return el?.textContent?.trim() || '0';
            }""")
            
            return StepResult(
                step="go_to_cart",
                status="success",
                data={"items": cart_items, "total": total}
            )
        except Exception as e:
            return StepResult(
                step="go_to_cart",
                status="fail",
                data={},
                error=str(e)
            )
    
    async def go_to_checkout(self) -> StepResult:
        try:
            await self.page.goto("http://127.0.0.1:5000/checkout")
            await self.page.wait_for_load_state("domcontentloaded")
            
            return StepResult(
                step="go_to_checkout",
                status="success",
                data={"url": self.page.url, "page_title": await self.page.title()}
            )
        except Exception as e:
            return StepResult(
                step="go_to_checkout",
                status="fail",
                data={},
                error=str(e)
            )
    
    async def confirm_order(self) -> StepResult:
        try:
            await self.page.click('button.confirm, button[type="submit"]')
            await self.page.wait_for_selector('.order-id', timeout=10000)
            
            order_id = await self.page.evaluate("""() => {
                const el = document.querySelector('.order-id');
                return el?.textContent?.trim() || '';
            }""")
            
            return StepResult(
                step="confirm_order",
                status="success",
                data={"order_id": order_id, "url": self.page.url}
            )
        except Exception as e:
            return StepResult(
                step="confirm_order",
                status="fail",
                data={},
                error=str(e)
            )


async def test_driver():
    driver = BrowserDriver(headless=False)
    await driver.start()
    
    try:
        print(await driver.login())
        print(await driver.search("widget"))
        print(await driver.add_to_cart("Blue Widget"))
        print(await driver.go_to_cart())
        print(await driver.go_to_checkout())
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(test_driver())