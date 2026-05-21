import asyncio
import logging
import json
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright

from kuaishou_sig4.config import BASE_URL

logger = logging.getLogger(__name__)


class KuaishouAPIClient:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        await self.context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        self.page = await self.context.new_page()

        await self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        await self.page.wait_for_timeout(5000)

        self._initialized = True

    async def request_sms_code(self, phone: str) -> Dict[str, Any]:
        await self.initialize()

        result = await self.page.evaluate(
            """
            async ({ phone }) => {
                return new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => reject(new Error('Timeout')), 15000);

                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', 'https://id.kuaishou.com/pass/kuaishou/sms/requestMobileCode', true);
                    xhr.withCredentials = true;
                    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

                    xhr.onload = function() {
                        clearTimeout(timeout);
                        try {
                            resolve(JSON.parse(xhr.responseText));
                        } catch(e) {
                            reject(new Error('Parse error: ' + e.message));
                        }
                    };
                    xhr.onerror = function() {
                        clearTimeout(timeout);
                        reject(new Error('XHR error'));
                    };

                    const params = `sid=kuaishou.server.webday7&type=53&countryCode=%2B86&phone=${phone}&channelType=UNKNOWN&isWebSig4=true`;
                    xhr.send(params);
                });
            }
            """,
            {"phone": phone},
        )

        logger.info(f"SMS request result: {result}")
        return result

    async def close(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def main():
    logging.basicConfig(level=logging.INFO)
    phone = input("请输入手机号: ")
    async with KuaishouAPIClient(headless=True) as client:
        result = await client.request_sms_code(phone)
        print(f"请求结果: {result}")


if __name__ == "__main__":
    asyncio.run(main())
