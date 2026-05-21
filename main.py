#!/usr/bin/env python3
import asyncio
import logging
import sys

from kuaishou_sig4.api_client import KuaishouAPIClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def request_sms(phone: str):
    async with KuaishouAPIClient(headless=True) as client:
        result = await client.request_sms_code(phone)
        return result


def main():
    if len(sys.argv) < 2:
        phone = input("请输入手机号: ")
    else:
        phone = sys.argv[1]

    if not phone.isdigit() or len(phone) != 11:
        logger.error("请输入正确的11位手机号")
        sys.exit(1)

    logger.info(f"正在为手机号 {phone} 发送验证码...")

    try:
        result = asyncio.run(request_sms(phone))
        if result.get("result") == 1:
            logger.info("验证码发送成功!")
        else:
            logger.error(f"验证码发送失败: {result}")
        print(result)
    except Exception as e:
        logger.error(f"请求失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
