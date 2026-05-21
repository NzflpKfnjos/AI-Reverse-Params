# 有道翻译 Web 版 - Python 纯算法实现

通过逆向分析有道翻译网页版 (https://fanyi.youdao.com/) 的 API 接口，使用纯 Python 实现翻译功能，无需浏览器自动化。

## 逆向分析

### API 接口

1. **获取密钥接口**: `POST https://dict-trans.youdao.com/translate/key`
   - 用于获取 `secretKey` 和 `token`
   - 需要预先计算的签名

2. **翻译接口 (SSE)**: `POST https://dict-trans.youdao.com/webtranslate/sse`
   - 流式返回翻译结果
   - 使用获取到的 `secretKey` 和 `token` 进行签名

### 签名算法

```
1. 将所有参数（除空字符串外）按 key 字母顺序排序
2. 在排序后的 key 列表末尾添加 "key"
3. 设置 params["key"] = secretKey
4. 拼接为: key1=value1&key2=value2&...&key=secretKey
5. 计算 MD5 得到 sign
6. pointParam = 排序后的 key 列表（不含 "key"），用逗号连接
```

### 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| product | webfanyi | 产品标识 |
| keyfrom | webfanyi.webmain | 来源标识 |
| client | webmain | 客户端类型 |
| keyid | translate-webfanyi-webmain | 密钥 ID |
| keyid (获取密钥) | translate-webmain-key-getter | 获取密钥的 keyid |
| targetKeyid | translate-webfanyi-webmain | 目标密钥 ID |
| sign (获取密钥) | kSy5gtKA4yRUxAVPJPrdYKZ0jBKyd3t1 | 固定签名密钥 |

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 基本用法

```python
from youdao_translate import YoudaoTranslator

translator = YoudaoTranslator()

# 英译中
result = translator.translate("Hello World", "auto", "zh-CHS")
print(result)  # 你好世界

# 中译英
result = translator.translate("你好世界", "auto", "en")
print(result)
```

### 运行示例

```bash
python youdao_translate.py
```

## 支持的语言

- `auto`: 自动检测
- `zh-CHS`: 简体中文
- `en`: 英语
- `ja`: 日语
- `ko`: 韩语
- `fr`: 法语
- `de`: 德语
- `es`: 西班牙语
- `ru`: 俄语
- 等更多语言...

## 免责声明

本项目仅用于学习研究目的，请勿用于商业用途。
