# 猎聘 (Liepin) 短信验证码登录

猎聘手机验证码登录接口的 Python 纯算还原，基于 webpack 源码逆向分析，无需浏览器自动化。

## 功能

- Session 初始化（自动获取 XSRF-TOKEN、`__uuid` 等 Cookies）
- Smart Captcha 获取（无需图形验证码场景）
- 短信验证码发送
- 手机验证码登录
- 协议日志记录（提高成功率）

## API 流程

```
init_session → save_agreement_log → get_smart_captcha → send_sms → mobile_login
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 命令行

```bash
# 发送短信验证码
python liepin_sms.py 13800138000 --debug

# 不带调试输出
python liepin_sms.py 13800138000
```

### 代码调用

```python
from liepin_sms import LiepinSMS

lp = LiepinSMS(debug=True)

# 发送短信验证码
success, result = lp.request_sms_code("13800138000")
if success:
    print("验证码发送成功")
else:
    print(f"发送失败: {result}")

# 使用验证码登录
login_result = lp.mobile_login("13800138000", "123456")
if login_result.get("flag") == 1:
    print("登录成功")
```

## 依赖

- Python >= 3.7
- requests >= 2.28.0

## 注意事项

- 当 `captchaMode=2` 时需通过腾讯 TCaptcha SDK 完成滑块验证，纯算无法处理
- 首次请求可能触发阿里云 WAF，返回 `acw_tc` cookie 后即可正常请求

## 文件结构

```
liepin/
├── liepin_sms.py      # 主程序
├── requirements.txt   # 依赖
└── README.md          # 项目说明
```
