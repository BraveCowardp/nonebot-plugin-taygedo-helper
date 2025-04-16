<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-taygedo-helper

_✨ 塔吉多助手插件 ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/BraveCowardp/nonebot-plugin-taygedo-helper.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-taygedo-helper">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-taygedo-helper.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">

</div>

## 📖 介绍

登录塔吉多账号，并且每日定时进行塔吉多签到（包括APP签到和APP内幻塔游戏签到）

## 💿 安装

<details open>
<summary>使用 nb-cli 安装(推荐！)</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-taygedo-helper

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-taygedo-helper
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-taygedo-helper
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-taygedo-helper
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-taygedo-helper
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_taygedo-helper"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| taygedo_helper_auto_sign_time | 否 | 08:30 | 每日定时签到时间 |

## 🎉 使用
### 更新数据模型 <font color=#fc8403 >使用必看！！！！！</font>
本插件使用了官方推荐的`nonebot-plugin-orm`插件操作数据库，安装插件或更新插件版本后，在启动机器人前，都需要执行此命令。
```shell
nb orm upgrade
```
手动执行下列命令检查数据库模式是否与模型定义一致。机器人启动前也会自动运行此命令，并在检查失败时阻止启动。
```shell
nb orm check
```
看到`没有检测到新的升级操作`字样时，表明数据库模型已经成功创建或更新，可以启动机器人
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| 塔吉多登录 | 群员 | 否 | 群聊 | 塔吉多登录，按照提示登录，可选填写手机号，登录后自动签到一次并开启定时签到 |
| 塔吉多签到 | 群员 | 否 | 群聊 | 手动给自己签到 |
| 塔吉多群签到 | SUPERUSER | 否 | 群聊 | 手动给群内所有已登录群员签到 |

## TODO
- [ ] 暂无，欢迎提交issue