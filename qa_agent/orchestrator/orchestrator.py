import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env'))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser_driver.steps import BrowserDriver, StepResult

# Configuration from environment
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')


class StepStatus(Enum):
    SUCCESS = "success"
    FAIL = "fail"
    RECOVERED = "recovered"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"


@dataclass
class LogEntry:
    run_id: str
    step: str
    timestamp: str
    status: str
    detection_reason: Optional[str] = None
    recovery_action: Optional[str] = None
    recovery_duration_ms: Optional[int] = None
    old_selector: Optional[str] = None
    new_selector: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RecipeCache:
    def __init__(self, cache_file: str = "recipe_cache.json"):
        self.cache_file = cache_file
        self.recipe = self._load()
    
    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.recipe, f, indent=2)
    
    def get_step_selector(self, step: str) -> Optional[str]:
        return self.recipe.get(step, {}).get('selector')
    
    def set_step_selector(self, step: str, selector: str, metadata: Dict = None):
        self.recipe[step] = {'selector': selector, 'metadata': metadata or {}, 'updated': datetime.now().isoformat()}
        self.save()
    
    def has_recipe(self) -> bool:
        return bool(self.recipe)


class FailureDetector:
    @staticmethod
    def detect(result: StepResult, expected_schema: Dict = None) -> Optional[str]:
        if result.status == "fail":
            error = result.error or ""
            if "not found" in error.lower() or "selector" in error.lower() or "timeout" in error.lower():
                return f"selector missing: {error}"
            if "schema" in error.lower() or "expected" in error.lower():
                return f"schema mismatch: {error}"
            return f"step failed: {error}"
        
        if expected_schema and result.data:
            for key, expected_type in expected_schema.items():
                if key not in result.data:
                    return f"missing expected field: {key}"
                if not isinstance(result.data[key], expected_type):
                    return f"type mismatch for {key}: expected {expected_type}, got {type(result.data[key])}"
        
        return None


class RecoveryEngine:
    def __init__(self, driver: BrowserDriver, recipe_cache: RecipeCache):
        self.driver = driver
        self.recipe_cache = recipe_cache
    
    async def _find_alternative_selector(self, step: str) -> Optional[str]:
        """Inspect the DOM and find alternative selectors when the cached one fails."""
        try:
            # Get all input/button/element selectors that could be alternatives
            alternatives = await self.driver.page.evaluate(f"""() => {{
                const results = [];
                const elements = document.querySelectorAll('input, button, [role], [id], [name]');
                for (const el of elements) {{
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {{
                        const text = el.textContent?.trim() || '';
                        const role = el.getAttribute('role');
                        const name = el.getAttribute('name');
                        const id = el.getAttribute('id');
                        const placeholder = el.getAttribute('placeholder');
                        const ariaLabel = el.getAttribute('aria-label');
                        results.push({{
                            selector: id ? '#' + id : null,
                            name: name ? '[name="' + name + '"]' : null,
                            text: text ? el.innerHTML.substring(0, 30) : null,
                            role: role ? '[role="' + role + '"]' : null,
                            placeholder: placeholder ? '[placeholder="' + placeholder + '"]' : null,
                            ariaLabel: ariaLabel ? '[aria-label="' + ariaLabel + '"]' : null,
                            visible: el.offsetParent !== null
                        }};
                    }}
                }}
                return results;
            }}""")
            
            # Filter to visible elements with meaningful text or attributes
            viable = [a for a in alternatives if a['visible'] and 
                     (a['text'] or a['name'] or a['role'] or a['ariaLabel'])]
            
            # Prioritize: input with name, button with text, element with role
            for a in viable:
                if a['name']:
                    return a['name']
                if a['text']:
                    return a['text']
                if a['role']:
                    return a['role']
            
            return None
        except Exception:
            return None
    
    async def recover(self, step: str, detection_reason: str) -> StepResult:
        print(f"  [RECOVERY] Attempting recovery for step: {step}")
        print(f"     Reason: {detection_reason}")
        
        start_time = time.time()
        
        # Step-specific recovery
        if step == "login":
            return await self._recover_login()
        elif step == "search":
            return await self._recover_search()
        elif step == "add_to_cart":
            return await self._recover_add_to_cart()
        elif step == "go_to_cart":
            return await self._recover_go_to_cart()
        elif step == "go_to_checkout":
            return await self._recover_go_to_checkout()
        elif step == "confirm_order":
            return await self._recover_confirm_order()
        
        return StepResult(step=step, status="fail", data={}, error="No recovery strategy for this step")
    
    async def _heal_selector(self, step: str) -> Optional[str]:
        """Find an alternative DOM selector when the cached one fails."""
        try:
            alt = await self.driver.page.evaluate(f"""() => {{
                // Try to find elements with meaningful text or attributes
                const candidates = [];
                const elements = document.querySelectorAll('input, button, [role], [id], [name]');
                for (const el of elements) {{
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {{
                        const t = el.textContent?.trim();
                        const r = el.getAttribute('role');
                        const n = el.getAttribute('name');
                        const i = el.getAttribute('id');
                        const p = el.getAttribute('placeholder');
                        const a = el.getAttribute('aria-label');
                        candidates.push({{
                            sel: i ? '#' + i : null,
                            nm: n ? '[name="' + n + '"]' : null,
                            txt: t ? el.innerHTML.substring(0, 30) : null,
                            rl: r ? '[role="' + r + '"]' : null,
                            ph: p ? '[placeholder="' + p + '"]' : null,
                            al: a ? '[aria-label="' + a + '"]' : null
                        }});
                    }}
                }}
                return candidates;
            }}""")
            
            # Prioritize selectors
            for c in alt:
                if c['nm']:
                    return c['nm']
                if c['sel']:
                    return c['sel']
                if c['rl']:
                    return c['rl']
                if c['al']:
                    return c['al']
            
            return None
        except Exception:
            return None
    
    async def _recover_login(self) -> StepResult:
        await self.driver.page.goto(f"{BASE_URL}/login")
        await self.driver.page.wait_for_load_state("domcontentloaded")
        # Try to heal the selector if login fails
        new_selector = await self._heal_selector("login")
        if new_selector:
            self.recipe_cache.set_step_selector("login", new_selector)
        return await self.driver.login(username_selector=new_selector)
    
    async def _recover_search(self) -> StepResult:
        await self.driver.page.goto(f"{BASE_URL}/search")
        await self.driver.page.wait_for_load_state("domcontentloaded")
        new_selector = await self._heal_selector("search")
        if new_selector:
            self.recipe_cache.set_step_selector("search", new_selector)
        return await self.driver.search(search_selector=new_selector)
    
    async def _recover_add_to_cart(self) -> StepResult:
        await self.driver.page.goto(f"{BASE_URL}/search")
        await self.driver.page.wait_for_load_state("domcontentloaded")
        new_selector = await self._heal_selector("add_to_cart")
        if new_selector:
            self.recipe_cache.set_step_selector("add_to_cart", new_selector)
        return await self.driver.add_to_cart()
    
    async def _recover_go_to_cart(self) -> StepResult:
        await self.driver.page.goto(f"{BASE_URL}/cart")
        await self.driver.page.wait_for_load_state("domcontentloaded")
        new_selector = await self._heal_selector("go_to_cart")
        if new_selector:
            self.recipe_cache.set_step_selector("go_to_cart", new_selector)
        return await self.driver.go_to_cart()
    
    async def _recover_go_to_checkout(self) -> StepResult:
        await self.driver.page.goto(f"{BASE_URL}/checkout")
        await self.driver.page.wait_for_load_state("domcontentloaded")
        new_selector = await self._heal_selector("go_to_checkout")
        if new_selector:
            self.recipe_cache.set_step_selector("go_to_checkout", new_selector)
        return await self.driver.go_to_checkout()
    
    async def _recover_confirm_order(self) -> StepResult:
        return await self.driver.confirm_order()


class ApprovalGate:
    def __init__(self, mode: str = "cli"):
        self.mode = mode
    
    async def request_approval(self, step: str, details: Dict) -> bool:
        if self.mode == "cli":
            # Run blocking input() in a thread executor to avoid blocking asyncio event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: input(f"\n{'='*60}\n⚠ HUMAN APPROVAL REQUIRED\nStep: {step}\nDetails: {json.dumps(details, indent=2)}\n{'='*60}\nApprove? [y/n]: ").strip().lower()
            )
            return response == 'y'
        return False


class Orchestrator:
    def __init__(self, headless: bool = False, slow_mo: int = 2000, approval_mode: str = "cli"):
        self.driver = BrowserDriver(headless=headless, slow_mo=slow_mo)
        self.recipe_cache = RecipeCache()
        self.failure_detector = FailureDetector()
        self.recovery_engine = RecoveryEngine(self.driver, self.recipe_cache)
        self.approval_gate = ApprovalGate(approval_mode)
        self.logs: List[LogEntry] = []
        self.run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.max_retries = 2
    
    def _log(self, entry: LogEntry):
        self.logs.append(entry)
        self._write_logs()
        print(f"  [LOG] Logged: {entry.step} - {entry.status}")
    
    def _write_logs(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        log_file = os.path.join(log_dir, f"{self.run_id}.json")
        os.makedirs(log_dir, exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump([asdict(log) for log in self.logs], f, indent=2)
    
    async def run_step(self, step_name: str, step_func: Callable, 
                       expected_schema: Dict = None, 
                       requires_approval: bool = False) -> StepResult:
        print(f"\n>> Executing step: {step_name}")
        
        result = await step_func()
        
        detection_reason = self.failure_detector.detect(result, expected_schema)
        
        if detection_reason:
            print(f"  [FAILED] Failure detected: {detection_reason}")
            
            for attempt in range(self.max_retries):
                print(f"  [RETRY] Recovery attempt {attempt + 1}/{self.max_retries}")
                recovery_start = time.time()
                recovered_result = await self.recovery_engine.recover(step_name, detection_reason)
                recovery_duration = int((time.time() - recovery_start) * 1000)
                
                if recovered_result.status == "success":
                    self._log(LogEntry(
                        run_id=self.run_id,
                        step=step_name,
                        timestamp=datetime.now().isoformat(),
                        status=StepStatus.RECOVERED.value,
                        detection_reason=detection_reason,
                        recovery_action=f"Re-explored and found new path (attempt {attempt + 1})",
                        recovery_duration_ms=recovery_duration,
                        data=recovered_result.data
                    ))
                    print(f"  [SUCCESS] Recovery success")
                    return recovered_result
            
            self._log(LogEntry(
                run_id=self.run_id,
                step=step_name,
                timestamp=datetime.now().isoformat(),
                status=StepStatus.FAIL.value,
                detection_reason=detection_reason,
                error=result.error
            ))
            return result
        
        if requires_approval:
            print(f"  [APPROVAL] Triggered for: {step_name}")
            self._log(LogEntry(
                run_id=self.run_id,
                step=step_name,
                timestamp=datetime.now().isoformat(),
                status=StepStatus.APPROVAL_PENDING.value,
                data=result.data
            ))
            
            approved = await self.approval_gate.request_approval(step_name, result.data)
            
            if approved:
                self._log(LogEntry(
                    run_id=self.run_id,
                    step=step_name,
                    timestamp=datetime.now().isoformat(),
                    status=StepStatus.APPROVED.value,
                    data=result.data
                ))
                print(f"  [APPROVED] Approved")
            else:
                self._log(LogEntry(
                    run_id=self.run_id,
                    step=step_name,
                    timestamp=datetime.now().isoformat(),
                    status=StepStatus.FAIL.value,
                    error="Human approval denied"
                ))
                print(f"  [DENIED] Denied")
                result.status = "fail"
                result.error = "Human approval denied"
            return result
        
        self._log(LogEntry(
            run_id=self.run_id,
            step=step_name,
            timestamp=datetime.now().isoformat(),
            status=StepStatus.SUCCESS.value,
            data=result.data
        ))
        print(f"  [SUCCESS] Step success")
        return result
    
    async def run_flow(self):
        print(f"\n==== QA Agent Run: {self.run_id} =====")
        print(f"Run started successfully")
        print(f"================================")
        
        await self.driver.start()
        
        try:
            steps = [
                ("login", self.driver.login, {"username": str, "url": str}),
                ("search", lambda: self.driver.search("widget"), {"query": str, "products_found": int, "products": list}),
                ("add_to_cart", lambda: self.driver.add_to_cart("Blue Widget"), {"product": str, "cart_count": int}),
                ("go_to_cart", self.driver.go_to_cart, {"items": list, "total": str}),
                ("go_to_checkout", self.driver.go_to_checkout, {"url": str, "page_title": str}, True),
            ]
            
            for i, step_info in enumerate(steps):
                step_name = step_info[0]
                step_func = step_info[1]
                expected_schema = step_info[2] if len(step_info) > 2 else None
                requires_approval = step_info[3] if len(step_info) > 3 else False
                
                result = await self.run_step(step_name, step_func, expected_schema, requires_approval)
                
                if result.status == "fail" and not requires_approval:
                    print(f"\n❌ Flow stopped at step: {step_name}")
                    break
            
            print(f"\n==== Run completed: {self.run_id} ====")
            print(f"All steps finished")
            
        finally:
            await self.driver.close()


async def main():
    orchestrator = Orchestrator(headless=False, approval_mode="cli")
    await orchestrator.run_flow()


if __name__ == "__main__":
    print("Starting QA Agent...")
    asyncio.run(main())
    print("QA Agent run completed")