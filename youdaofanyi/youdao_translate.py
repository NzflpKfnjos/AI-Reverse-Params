import hashlib
import time
import uuid
import requests
from urllib.parse import quote
from typing import Optional


class YoudaoTranslator:
    """有道翻译 Web 版接口逆向实现"""

    # 获取密钥的接口配置
    KEY_GETTER_KEYID = "translate-webmain-key-getter"
    TARGET_KEYID = "translate-webfanyi-webmain"
    KEY_GETTER_SIGN = "kSy5gtKA4yRUxAVPJPrdYKZ0jBKyd3t1"

    # 翻译接口配置
    PRODUCT = "webfanyi"
    KEYFROM = "webfanyi.webmain"
    CLIENT = "webmain"
    APP_VERSION = "12.0.0"
    VENDOR = "web"
    NETWORK = "wifi"
    ABTEST = 0

    # API 端点
    BASE_URL = "https://dict-trans.youdao.com"
    KEY_URL = f"{BASE_URL}/translate/key"
    TRANSLATE_URL = f"{BASE_URL}/webtranslate/sse"

    def __init__(self, yduuid: Optional[str] = None):
        self.yduuid = yduuid or str(uuid.uuid4()).replace("-", "")
        self.secret_key = None
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            "Referer": "https://fanyi.youdao.com/",
            "Origin": "https://fanyi.youdao.com",
            "Accept": "application/json, text/plain, */*",
        })

    @staticmethod
    def md5(text: str) -> str:
        """计算 MD5 哈希值"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def generate_sign(self, params: dict, secret_key: str) -> tuple:
        """
        生成签名和 pointParam

        算法:
        1. 过滤掉空字符串值
        2. 按 key 字母顺序排序
        3. 拼接为 key1=value1&key2=value2&...&key=secretKey
        4. 计算 MD5

        Returns:
            (sign, pointParam) 元组
        """
        filtered = {k: v for k, v in params.items() if v != ""}
        sorted_keys = sorted([k for k, v in filtered.items() if v is not None])
        sorted_keys.append("key")
        filtered["key"] = secret_key

        sign_str = "&".join([f"{k}={filtered[k]}" for k in sorted_keys])
        sign = self.md5(sign_str)
        point_param = ",".join([k for k in sorted_keys if k != "key"])

        return sign, point_param

    def get_secret_key(self) -> dict:
        """
        获取翻译接口所需的 secretKey 和 token

        Returns:
            {"secretKey": str, "token": str}
        """
        mystic_time = int(time.time() * 1000)

        params = {
            "product": self.PRODUCT,
            "appVersion": self.APP_VERSION,
            "client": self.CLIENT,
            "mid": 1,
            "vendor": self.VENDOR,
            "screen": 1,
            "model": 1,
            "imei": 1,
            "network": self.NETWORK,
            "keyfrom": self.KEYFROM,
            "keyid": self.KEY_GETTER_KEYID,
            "mysticTime": mystic_time,
            "yduuid": self.yduuid,
            "abtest": self.ABTEST,
            "targetKeyid": self.TARGET_KEYID,
        }

        sign, point_param = self.generate_sign(params, self.KEY_GETTER_SIGN)
        params["sign"] = sign
        params["pointParam"] = point_param

        response = self.session.post(self.KEY_URL, params=params)
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"获取密钥失败: {result.get('msg', '未知错误')}")

        self.secret_key = result["data"]["secretKey"]
        self.token = result["data"]["token"]

        return {"secretKey": self.secret_key, "token": self.token}

    def translate(self, text: str, from_lang: str = "auto", to_lang: str = "zh-CHS", model_name: str = "llmLite") -> str:
        """
        翻译文本

        Args:
            text: 待翻译文本
            from_lang: 源语言 (auto 表示自动检测)
            to_lang: 目标语言
            model_name: 模型名称 (llmLite 或 llm)

        Returns:
            翻译结果
        """
        if not self.secret_key or not self.token:
            self.get_secret_key()

        mystic_time = int(time.time() * 1000)

        params = {
            "product": self.PRODUCT,
            "appVersion": "1",
            "client": self.CLIENT,
            "mid": 1,
            "vendor": self.VENDOR,
            "screen": 1,
            "model": 1,
            "imei": 1,
            "network": self.NETWORK,
            "keyfrom": self.KEYFROM,
            "keyid": self.TARGET_KEYID,
            "mysticTime": mystic_time,
            "yduuid": self.yduuid,
            "modelName": model_name,
            "useTerm": "false",
            "i": text,
            "from": from_lang,
            "to": to_lang,
            "signSecretKey": self.secret_key,
            "keyId": self.TARGET_KEYID,
            "token": self.token,
            "source": self.CLIENT,
        }

        sign, point_param = self.generate_sign(params, self.secret_key)
        params["sign"] = sign
        params["pointParam"] = point_param

        form_data = {}
        for k, v in params.items():
            form_data[k] = str(v)

        response = self.session.post(self.TRANSLATE_URL, data=form_data, stream=True)

        result = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data:"):
                    data_str = line_str[5:].strip()
                    if data_str.startswith("{"):
                        import json
                        try:
                            data = json.loads(data_str)
                            if "transIncre" in data:
                                result.append(data["transIncre"])
                        except json.JSONDecodeError:
                            pass

        return "".join(result)

    def translate_enhanced(self, text: str, from_lang: str = "auto", to_lang: str = "zh-CHS") -> dict:
        """
        获取增强翻译结果（包含词典、例句等）

        Args:
            text: 待翻译文本
            from_lang: 源语言
            to_lang: 目标语言

        Returns:
            包含翻译结果的字典
        """
        if not self.secret_key or not self.token:
            self.get_secret_key()

        mystic_time = int(time.time() * 1000)

        params = {
            "srcArticle": text,
            "tgtArticle": "",
            "from": from_lang,
            "to": to_lang,
            "product": self.PRODUCT,
            "appVersion": self.APP_VERSION,
            "client": self.CLIENT,
            "mid": 1,
            "vendor": self.VENDOR,
            "screen": 1,
            "model": 1,
            "imei": 1,
            "network": self.NETWORK,
            "keyfrom": self.KEYFROM,
            "keyid": self.TARGET_KEYID,
            "mysticTime": mystic_time,
            "yduuid": self.yduuid,
            "abtest": self.ABTEST,
            "signSecretKey": self.secret_key,
            "keyId": self.TARGET_KEYID,
            "token": self.token,
            "source": self.CLIENT,
        }

        sign, point_param = self.generate_sign(params, self.secret_key)
        params["sign"] = sign
        params["pointParam"] = point_param

        form_data = {}
        for k, v in params.items():
            form_data[k] = str(v)

        enhance_url = f"{self.BASE_URL}/translate/enhance"
        response = self.session.post(enhance_url, data=form_data)
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"翻译失败: {result.get('msg', '未知错误')}")

        return result.get("data", {})


def main():
    """示例用法"""
    translator = YoudaoTranslator()

    print("=" * 50)
    print("有道翻译 Web 版 - Python 纯算法实现")
    print("=" * 50)

    test_cases = [
        ("Hello World", "auto", "zh-CHS"),
        ("你好世界", "auto", "en"),
        ("The quick brown fox jumps over the lazy dog", "auto", "zh-CHS"),
        ("人工智能正在改变世界", "auto", "en"),
    ]

    for text, from_lang, to_lang in test_cases:
        try:
            result = translator.translate(text, from_lang, to_lang)
            print(f"\n原文: {text}")
            print(f"翻译: {result}")
            print("-" * 50)
        except Exception as e:
            print(f"\n翻译失败: {e}")


if __name__ == "__main__":
    main()
