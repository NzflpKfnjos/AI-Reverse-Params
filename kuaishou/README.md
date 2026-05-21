# 快手 __NS_hxfalcon 签名算法

## 项目简介

本项目用于生成快手网页版登录时的 `__NS_hxfalcon` 签名参数，并调用发送短信验证码接口。

## 签名算法分析

### 接口信息

- URL: `https://id.kuaishou.com/pass/kuaishou/sms/requestMobileCode`
- Method: POST
- Content-Type: `application/x-www-form-urlencoded`

### 请求参数

Query Parameters:
- `__NS_hxfalcon`: SIG4签名值 (格式: `HUDR_<base64>$HE_<hex>`)
- `caver`: 签名版本号 (通常为 `2`)

Form Data:
- `sid`: 会话ID (默认: `kuaishou.server.webday7`)
- `type`: 类型 (固定: `53`)
- `countryCode`: 国家代码 (默认: `+86`)
- `phone`: 手机号
- `channelType`: 渠道类型 (默认: `UNKNOWN`)
- `isWebSig4`: 是否使用Web Sig4 (固定: `true`)

### 签名算法架构

快手的 `__NS_hxfalcon` 签名使用了一个复杂的基于虚拟机的签名系统 (SIG4):

1. **Jose VM**: 一个自定义的 JavaScript 虚拟机，用于执行混淆的字节码
2. **字节码**: 嵌入在 JS 文件中的混淆代码，包含签名生成逻辑
3. **浏览器指纹**: 收集浏览器环境信息 (stack trace, timing 等)
4. **输出格式**: `HUDR_<encoded_data>$HE_<hash>`

签名生成流程:
```
请求参数 → sig4Adapter → getSig4 → Jose.call("$encode") → 字节码执行 → HUDR_...$HE_...
```

### 实现方式

由于签名算法使用了复杂的 VM 和浏览器指纹，本项目采用 **Playwright 浏览器自动化** 的方式来生成签名:

1. 启动 Chromium 浏览器 (支持 headless 模式)
2. 加载快手页面，初始化 SIG4 SDK
3. 通过页面内的 XHR 调用 API，浏览器自动处理签名生成
4. 返回 API 响应结果

## 安装

```bash
pip3 install -r requirements.txt
playwright install chromium
```

## 使用

### 命令行

```bash
python3 main.py 13800138000
```

### 代码调用

```python
import asyncio
from kuaishou_sig4.api_client import KuaishouAPIClient

async def main():
    async with KuaishouAPIClient() as client:
        result = await client.request_sms_code("13800138000")
        print(result)

asyncio.run(main())
```

## 项目结构

```
快手/
├── kuaishou_sig4/
│   ├── __init__.py
│   ├── api_client.py       # API客户端
│   ├── config.py           # 配置
│   └── utils.py            # 工具函数
├── main.py                 # 入口
├── requirements.txt
└── README.md
```

## 注意事项

1. 需要安装 Playwright 和 Chromium 浏览器
2. 首次运行会自动下载 Chromium (~170MB)
3. 签名生成依赖浏览器环境，需要保持网络连接
4. 支持 headless 模式，适合服务器环境运行
