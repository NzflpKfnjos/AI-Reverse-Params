"""
猎聘 (Liepin) 手机验证码登录接口 Python 纯算还原

API流程:
  1. 初始化Session → 访问 liepin.com 获取Cookies (XSRF-TOKEN, __uuid等)
  2. POST get-smart-captcha → 获取 captchaSign
     - captchaMode="1": 无需图形验证码, captchaData="{}"
     - captchaMode="2": 需要腾讯验证码, 需要额外处理
  3. POST send-sms → 发送短信验证码

源码分析来源: webpack模块 #52642 (API层) + #87874 (smart captcha) + #79985 (login API)
"""

import requests
import uuid
import json
from typing import Optional, Dict, Tuple


class LiepinSMS:
    """猎聘短信验证码接口"""

    TENANT_ID = "liepin"
    BUSINESS_ID = "1100100012"
    CLIENT_ID = "40108"

    API_PASSPORT = "https://api-passport.liepin.com"
    API_SECURITY = "https://api-security-liepin.liepin.com"

    # 接口映射 (来自模块#52642的s对象)
    ENDPOINTS = {
        "smartCaptchaInitialUrl": "/api/com.liepin.passport.captcha.get-smart-captcha",
        "getTelCode": "/api/com.liepin.passport.captcha.send-sms",
        "mobileLogin": "/api/com.liepin.passport.account.tel-sms-login",
        "accountLogin": "/api/com.liepin.passport.account.account-pwd-login",
        "logout": "/api/com.liepin.passport.account.logout",
        "ticketLogin": "/api/com.liepin.passport.account.ticket-login",
        "agreementLog": "/api/com.liepin.security.agreement.unlogin.save-agreement-log",
    }

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.session = requests.Session()
        self.cookies: Dict[str, str] = {}

        # 基础请求头 (浏览器通用)
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "sec-ch-ua": (
                '"Chromium";v="148", "Google Chrome";v="148", '
                '"Not/A)Brand";v="99"'
            ),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        })

    def _api_headers(self, **extra) -> Dict[str, str]:
        """构建API请求头 (每次调用动态生成, 避免污染页面请求)"""
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-Client-Type": "web",
            "X-Fscp-Version": "1.1",
            "X-Fscp-Std-Info": json.dumps({"client_id": self.CLIENT_ID}),
            "X-Fscp-Trace-Id": self._trace_id(),
            "X-Fscp-Bi-Stat": self._bi_stat(),
            "X-Xsrf-Token": self.cookies.get("XSRF-TOKEN", ""),
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.liepin.com/",
            "Origin": "https://www.liepin.com",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }
        headers.update(extra)
        return headers

    def _trace_id(self) -> str:
        """生成 x-fscp-trace-id (UUID v4)"""
        return str(uuid.uuid4())

    def _bi_stat(self, location: str = "") -> str:
        """生成 x-fscp-bi-stat"""
        if not location:
            location = "https://www.liepin.com/login"
        return json.dumps({"location": location})

    def _log(self, msg: str):
        if self.debug:
            print(f"[*] {msg}")

    # ==================== Session 初始化 ====================

    def init_session(self) -> Dict[str, str]:
        """
        初始化Session，访问猎聘首页获取必要Cookies
        
        服务端会设置:
          - XSRF-TOKEN: CSRF防护token (必需)
          - __gc_id: 访客ID (32位hex) (必需)
          - acw_tc: 阿里云WAF反爬cookie (必需)
          - __uuid: 用户唯一标识 (JS生成, 非必需)
          - __sessionId: 会话ID (JS生成, 非必需)
        """
        headers = {
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "sec-ch-ua": (
                '"Chromium";v="148", "Google Chrome";v="148", '
                '"Not/A)Brand";v="99"'
            ),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        resp = self.session.get(
            "https://www.liepin.com/",
            headers=headers,
            timeout=30,
            allow_redirects=True,
        )
        self.cookies.update(self.session.cookies.get_dict())
        self._log(f"init_session: status={resp.status_code}")
        self._log(f"init_session: cookies={self.cookies}")
        return self.cookies

    # ==================== 协议记录 (非必须) ====================

    def save_agreement_log(self, phone: str = "", account: str = ""):
        """
        保存协议同意记录 (源码函数N)
        非核心流程，但前端在发验证码前会调用
        """
        url = f"{self.API_SECURITY}/api/com.liepin.security.agreement.unlogin.save-agreement-log"
        headers = {
            "Content-Type": "application/json;charset=utf-8;",
            "X-Xsrf-Token": self.cookies.get("XSRF-TOKEN", ""),
        }
        data = {
            "sceneTypeCode": "S0023",
            "confirmMode": "1",
            "linkBusinessInfos": {},
            "agreementTypes": ["A0001", "A0002"],
        }
        if phone:
            data["linkBusinessInfos"]["phone"] = phone
        if account:
            data["linkBusinessInfos"]["account"] = account

        resp = self.session.post(url, json=data, headers=headers, timeout=30)
        self._log(f"save_agreement_log: status={resp.status_code} body={resp.text}")
        return resp.json() if resp.text else {}

    # ==================== Smart Captcha ====================

    def get_smart_captcha(self, phone: str, business_id: str = None) -> Dict:
        """
        第一步: 获取smart captcha (源码方法captcha/smartCaptcha)

        POST {base}/api/com.liepin.passport.captcha.get-smart-captcha
        Body: tel={phone}&businessId={bizId}&type=1&version=1

        返回:
          {
            "flag": 1,
            "data": {
              "config": {"appId": ""},
              "captchaMode": "1",  // "1"=无需验证码 "2"=需要腾讯验证码
              "captchaSign": "..."   // 用于后续send-sms
            }
          }
        """
        url = f"{self.API_PASSPORT}{self.ENDPOINTS['smartCaptchaInitialUrl']}"
        biz_id = business_id or self.BUSINESS_ID

        headers = self._api_headers()
        data = {
            "tel": phone,
            "businessId": biz_id,
            "type": "1",
            "version": "1",
        }

        resp = self.session.post(url, data=data, headers=headers, timeout=30)

        # 更新cookies (acw_tc会在此接口返回)
        self.cookies.update(self.session.cookies.get_dict())

        result = resp.json() if resp.text else {}
        self._log(f"get_smart_captcha: status={resp.status_code}")
        self._log(f"get_smart_captcha: response={json.dumps(result, ensure_ascii=False)}")

        return result

    # ==================== Send SMS ====================

    def send_sms(
        self,
        phone: str,
        captcha_sign: str,
        captcha_data: str = "{}",
        business_id: str = None,
    ) -> Dict:
        """
        第二步: 发送短信验证码 (源码方法sendRequest → send)

        POST {base}/api/com.liepin.passport.captcha.send-sms
        Body: businessId={bizId}&backurl=&tel={phone}
              &captchaData={captchaData}&captchaSign={captchaSign}

        返回:
          {"flag": 1, "data": {}}
        """
        url = f"{self.API_PASSPORT}{self.ENDPOINTS['getTelCode']}"
        biz_id = business_id or self.BUSINESS_ID

        headers = self._api_headers()
        data = {
            "businessId": biz_id,
            "backurl": "",
            "tel": phone,
            "captchaData": captcha_data,
            "captchaSign": captcha_sign,
        }

        resp = self.session.post(url, data=data, headers=headers, timeout=30)
        result = resp.json() if resp.text else {}
        self._log(f"send_sms: status={resp.status_code}")
        self._log(f"send_sms: response={json.dumps(result, ensure_ascii=False)}")

        return result

    # ==================== 完整流程 ====================

    def request_sms_code(self, phone: str) -> Tuple[bool, Dict]:
        """
        完整流程: 初始化 → 获取captcha → 发送验证码

        返回:
          (success, result)
            success=True  → result是send-sms的响应
            success=False → result是错误信息
        """
        # 1. 初始化session
        self._log(f"=== 初始化Session ===")
        cookies = self.init_session()
        if not cookies.get("XSRF-TOKEN"):
            return False, {"error": "未获取到XSRF-TOKEN, 初始化失败", "cookies": cookies}

        # 2. 协议日志 (非必须但有助于提高成功率)
        self._log(f"=== 保存协议日志 ===")
        self.save_agreement_log(phone=phone)

        # 3. 获取smart captcha
        self._log(f"=== 获取SmartCaptcha ===")
        captcha_resp = self.get_smart_captcha(phone)

        if captcha_resp.get("flag") != 1:
            return False, {"error": "get_smart_captcha失败", "response": captcha_resp}

        captcha_data = captcha_resp.get("data", {})
        captcha_mode = captcha_data.get("captchaMode", "1")
        captcha_sign = captcha_data.get("captchaSign", "")

        if not captcha_sign:
            return False, {"error": "未获取到captchaSign", "response": captcha_resp}

        # 4. 判断验证码模式
        if captcha_mode == "2":
            return False, {
                "error": "需要腾讯图形验证码(captchaMode=2), 纯算无法处理",
                "data": captcha_data,
                "hint": "需要通过腾讯TCaptcha SDK完成滑块验证后, 将ticket传给send-sms"
            }

        # captchaMode == "1": 无需图形验证码
        captcha_data_str = captcha_data.get("captchaData", "{}")

        # 5. 发送短信验证码
        self._log(f"=== 发送短信验证码 ===")
        sms_resp = self.send_sms(
            phone=phone,
            captcha_sign=captcha_sign,
            captcha_data=captcha_data_str,
        )

        if sms_resp.get("flag") == 1:
            return True, sms_resp
        return False, {"error": "send_sms失败", "response": sms_resp}

    # ==================== 手机验证码登录 ====================

    def mobile_login(self, phone: str, sms_code: str, bi_role: int = 0, bi_source: str = "") -> Dict:
        """
        手机验证码登录 (源码函数I / BZ - mobileLogin)

        POST /api/com.liepin.passport.account.tel-sms-login
        Body: tel={phone}&smsCode={code}&_bi_role={role}&_bi_source={source}
        """
        url = f"{self.API_PASSPORT}{self.ENDPOINTS['mobileLogin']}"
        headers = self._api_headers(
            **{"X-Fscp-Bi-Stat": json.dumps({
                "bi_source": bi_source,
                "bi_role": bi_role,
            })}
        )
        data = {
            "tel": phone,
            "smsCode": sms_code,
            "_bi_role": str(bi_role),
            "_bi_source": bi_source,
        }

        resp = self.session.post(url, data=data, headers=headers, timeout=30)
        result = resp.json() if resp.text else {}
        self._log(f"mobile_login: status={resp.status_code}")
        self._log(f"mobile_login: response={json.dumps(result, ensure_ascii=False)}")

        # 登录成功后通常返回token/cookie
        if result.get("flag") == 1:
            self.cookies.update(self.session.cookies.get_dict())
        return result

    # ==================== 便捷方法 ====================

    def get_session_cookies(self) -> Dict[str, str]:
        """获取当前session的所有cookies"""
        return self.session.cookies.get_dict()

    def set_cookies_manually(self, cookies: Dict[str, str]):
        """
        手动设置cookies (跳过初始化)
        用于已知cookie的场景, 如:
          {"XSRF-TOKEN": "xxx", "__uuid": "xxx.xx", ...}
        """
        for key, value in cookies.items():
            self.session.cookies.set(key, value, domain=".liepin.com")
        self.cookies.update(cookies)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python liepin_sms.py <手机号> [--debug]")
        print("示例: python liepin_sms.py 13800138000 --debug")
        sys.exit(1)

    phone = sys.argv[1]
    debug = "--debug" in sys.argv

    lp = LiepinSMS(debug=debug)
    success, result = lp.request_sms_code(phone)

    if success:
        print(f"\n[+] 验证码发送成功!")
        print(f"   响应: {json.dumps(result, ensure_ascii=False)}")
    else:
        print(f"\n[-] 发送失败: {result}")
