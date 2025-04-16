import asyncio
from nonebot import get_plugin_config, on_command, require, on_regex
from nonebot.adapters.onebot.v11 import Message, Bot
from nonebot.plugin import PluginMetadata
from nonebot.log import logger
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgPlainText, Arg
from nonebot.typing import T_State
from nonebot.exception import FinishedException
from nonebot.params import RegexGroup
from nonebot.permission import SUPERUSER
import httpx
import random
import time
import traceback
import re

require("nonebot_plugin_orm")
require("nonebot_plugin_saa")
require("nonebot_plugin_apscheduler")

from nonebot_plugin_orm import async_scoped_session, get_session
from nonebot_plugin_saa import AggregatedMessageFactory, Text, TargetQQGroup
from nonebot_plugin_apscheduler import scheduler

from .config import Config
from .model import UserData
from .db import UserDataDatabase
from .taygedoapi import TaygedoApi
from .calculate import Calculate

__plugin_meta__ = PluginMetadata(
    name="塔吉多助手",
    description="主要用于塔吉多APP签到和信息查询等功能",
    usage="使用\"塔吉多登录\"命令进行登录并自动签到",

    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。

    homepage="https://github.com/BraveCowardp/nonebot-plugin-taygedo-helper",
    # 发布必填。

    config=Config,
    # 插件配置项类，如无需配置可不填写。

    supported_adapters={"~onebot.v11"},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)

config = get_plugin_config(Config)
auto_sign_time = config.taygedo_helper_auto_sign_time

bind_taygedo_login = on_command("塔吉多登录", aliases={"塔吉多登陆"})
bind_taygedo_signin = on_command("塔吉多签到")
bind_signall_handle = on_command("塔吉多群签到", permission=SUPERUSER)

@scheduler.scheduled_job('cron', hour=int(auto_sign_time.split(':')[0]), minute=int(auto_sign_time.split(':')[1]), id='taygedo_auto_sign')
async def auto_sign():
    session = get_session()
    user_data_database = UserDataDatabase(session)
    user_data_list = await user_data_database.get_auto_signed_on_user_data_list()
    auto_sign_dict: dict[int, list[UserData]] = {}
    for user_data in user_data_list:
        if user_data.group_id not in auto_sign_dict:
            auto_sign_dict[user_data.group_id] = []
        auto_sign_dict[user_data.group_id].append(user_data)

    sign_res_dict = {}
    for group_id, user_data_list in auto_sign_dict.items():
        sign_res_dict[group_id] = {}
        sign_res_dict[group_id]['success'] = []
        sign_res_dict[group_id]['fail'] = []
        for user_data in user_data_list:
            taygedoapi = TaygedoApi()
            res = await taygedoapi.refresh_token(refresh_token=user_data.refresh_token, device_id=user_data.device_id)
            if not res['status']:
                sign_res_dict[group_id]['fail'].append({
                    'roleName': user_data.role_name,
                    'msg': f"{res['message']}，请重新登录"
                })
                continue

            access_token = res['data']['accessToken']
            user_data.refresh_token = res['data']['refreshToken']

            # 更新绑定角色数据
            res = await taygedoapi.get_bind_role(access_token=access_token, uid=user_data.uid)
            if res['status']:
                user_data.role_id = str(res['data']['roleId'])
                user_data.role_name = res['data']['roleName']


            # APP签到
            res = await taygedoapi.app_signin(access_token=access_token, uid=user_data.uid, device_id=user_data.device_id)
            if not res['status']:
                app_signin_flag = False
                app_signin_msg = f"APP签到失败：{res['message']}"
            else:
                app_signin_flag = True
                exp = res['data']['exp']
                gold_coin = res['data']['goldCoin']
                app_signin_msg = f"APP签到成功，获得{exp}经验，{gold_coin}金币"

            # 获取签到状态
            res = await taygedoapi.get_signin_state(access_token=access_token)
            if not res['status']:
                signin_state_flag = False
                signin_state_msg = f"获取签到状态失败：{res['message']}"
            else:
                signin_state_flag = True
                days = res['data']['days']

            # 获取签到奖励列表
            res = await taygedoapi.get_signin_rewards(access_token=access_token)
            if not res['status']:
                signin_rewards_flag = False
                signin_rewards_msg = f"获取签到奖励列表失败：{res['message']}"
            else:
                signin_rewards_flag = True
                signin_rewards = res['data']

            # 游戏签到
            res = await taygedoapi.game_signin(access_token=access_token, role_id=user_data.role_id)
            if not res['status']:
                game_signin_flag = False
                game_signin_msg = f"游戏签到失败：{res['message']}"
            else:
                if signin_state_flag and signin_rewards_flag:
                    game_signin_flag = True
                    reward =signin_rewards[days]
                    game_signin_msg = f"游戏签到成功，获得{reward['name']}*{reward['num']}"
                else:
                    game_signin_flag = False
                    fail_msg = ""
                    if not signin_state_flag:
                        fail_msg += f" {signin_state_msg}"
                    if not signin_rewards_flag:
                        fail_msg += f" {signin_rewards_msg}"
                    game_signin_msg = f"游戏签到成功，查询奖励信息失败：{fail_msg}"

            role_name = user_data.role_name
            await user_data_database.update_user_data(user_data)
            
                
            if app_signin_flag and game_signin_flag:
                sign_res_dict[group_id]['success'].append({'roleName':role_name, 'msg':f"{app_signin_msg}\n{game_signin_msg}"})
            else:
                sign_res_dict[group_id]['fail'].append({'roleName':role_name, 'msg':f"{app_signin_msg}\n{game_signin_msg}"})

        msgs = []

        msg_str = "塔吉多签到失败："
        for fail_info in sign_res_dict[group_id]['fail']:
            msg_str += f"\n{fail_info['roleName']}：\n{fail_info['msg']}"
        fail_msg = Text(msg_str)
        if len(sign_res_dict[group_id]['fail']) > 0:
            msgs.append(fail_msg)

        msg_str = "塔吉多签到成功："
        for success_info in sign_res_dict[group_id]['success']:
            msg_str += f"\n{success_info['roleName']}：\n{success_info['msg']}"
        success_msg = Text(msg_str)
        if len(sign_res_dict[group_id]['success']) > 0:
            msgs.append(success_msg)

        if len(msgs) > 0:
            await AggregatedMessageFactory(msgs).send_to(target=TargetQQGroup(group_id=group_id))
    await user_data_database.commit()
    await session.close()

@bind_taygedo_login.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    phone = args.extract_plain_text()
    pattern = r'^\d{11}$'
    msg_id = event.message_id

    if phone != "":
        if not bool(re.match(pattern, phone)):
            await bind_taygedo_login.finish("手机号格式错误，应为11位数字")
        else:
            matcher.set_arg("phone", args)
            # logger.info(f"删除消息: {msg_id}")
            # await bot.delete_msg(message_id=msg_id)

@bind_taygedo_login.got("phone", prompt="请输入手机号")
async def _(state: T_State, phone: str = ArgPlainText()):
    pattern = r'^\d{11}$'
    taygedoapi = TaygedoApi()

    if not bool(re.match(pattern, phone)):
        await bind_taygedo_login.finish("手机号格式错误，应为11位数字")

    device_id = Calculate.get_random_device_id()
    res = await taygedoapi.send_captcha(phone=phone, device_id=device_id)
    if not res['status']:
        await bind_taygedo_login.finish(f"发送验证码失败：{res['message']}")
    
    state['check_captcha_count'] = 0
    state['phone'] = phone
    state['device_id'] = device_id

@bind_taygedo_login.got("captcha", prompt="请输入验证码")
async def _(state: T_State, session: async_scoped_session, event: GroupMessageEvent, captcha: str = ArgPlainText()):
    pattern = r'^\d{6}$'
    taygedoapi = TaygedoApi()

    if not bool(re.match(pattern, captcha)):
        if state['check_captcha_count'] <= 3:
            state['check_captcha_count'] += 1
            await bind_taygedo_login.reject("验证码格式错误，应为6位数字")
        else:
            await bind_taygedo_login.finish("验证码错误次数过多，请重新登录")
    
    # 验证验证码
    res = await taygedoapi.check_captcha(phone=state['phone'], captcha=captcha, device_id=state['device_id'])
    if not res['status']:
        await bind_taygedo_login.finish(f"验证验证码失败：{res['message']}，请重新登录")

    # 登录, 获取token
    res = await taygedoapi.login(phone=state['phone'], captcha=captcha, device_id=state['device_id'])
    if not res['status']:
        await bind_taygedo_login.finish(f"登录失败：{res['message']}，请重新登录")
    
    token = res['result']['token']
    userId = str(res['result']['userId'])

    # 用户中心登录，获取access_token
    res = await taygedoapi.user_center_login(token=token, userId=userId, device_id=state['device_id'])
    if not res['status']:
        await bind_taygedo_login.finish(f"用户中心登录失败：{res['message']}，请重新登录")
    
    access_token = res['data']['accessToken']
    refresh_token = res['data']['refreshToken']
    uid = str(res['data']['uid'])

    # 获取绑定角色
    res = await taygedoapi.get_bind_role(access_token=access_token, uid=uid)
    if not res['status']:
        await bind_taygedo_login.finish(f"获取绑定角色失败：{res['message']}，请重新登录")

    if 'roleId' not in res['data']:
        await bind_taygedo_login.finish("尚未绑定游戏角色，请先登录塔吉多APP绑定角色，否则无法签到")
    
    role_id = str(res['data']['roleId'])
    role_name = res['data']['roleName']

    # 保存用户数据
    user_data = UserData(qq_id=event.user_id, group_id=event.group_id, role_name=role_name, uid=uid, device_id=state['device_id'], refresh_token=refresh_token, role_id=role_id, isAutoSigned=True)
    user_data_database = UserDataDatabase(session)
    if not await user_data_database.add_user_data(user_data):
        await bind_taygedo_login.finish("保存用户数据失败，请稍查看日志")
    
    # APP签到
    res = await taygedoapi.app_signin(access_token=access_token, uid=uid, device_id=state['device_id'])
    if not res['status']:
        app_signin_msg = f"APP签到失败：{res['message']}"
    else:
        exp = res['data']['exp']
        gold_coin = res['data']['goldCoin']
        app_signin_msg = f"APP签到成功，获得{exp}经验，{gold_coin}金币"

    # 获取签到状态
    res = await taygedoapi.get_signin_state(access_token=access_token)
    if not res['status']:
        signin_state_flag = False
        signin_state_msg = f"获取签到状态失败：{res['message']}"
    else:
        signin_state_flag = True
        days = res['data']['days']

    # 获取签到奖励列表
    res = await taygedoapi.get_signin_rewards(access_token=access_token)
    if not res['status']:
        signin_rewards_flag = False
        signin_rewards_msg = f"获取签到奖励列表失败：{res['message']}"
    else:
        signin_rewards_flag = True
        signin_rewards = res['data']

    # 游戏签到
    res = await taygedoapi.game_signin(access_token=access_token, role_id=role_id)
    if not res['status']:
        game_signin_msg = f"游戏签到失败：{res['message']}"
    else:
        if signin_state_flag and signin_rewards_flag:
            reward =signin_rewards[days]
            game_signin_msg = f"游戏签到成功，获得{reward['name']}*{reward['num']}"
        else:
            fail_msg = ""
            if not signin_state_flag:
                fail_msg += f" {signin_state_msg}"
            if not signin_rewards_flag:
                fail_msg += f" {signin_rewards_msg}"
            game_signin_msg = f"游戏签到成功，查询奖励信息失败：{fail_msg}"

    await user_data_database.commit()
    await bind_taygedo_login.finish(f"{role_name}数据已保存\n{app_signin_msg}\n{game_signin_msg}\n自动签到已开启，将于每天{auto_sign_time}自动签到")

@bind_taygedo_signin.handle()
async def _(session: async_scoped_session, event: GroupMessageEvent):
    user_data_database = UserDataDatabase(session)
    user_data = await user_data_database.get_user_data(qq=event.user_id)
    if not user_data:
        await bind_taygedo_signin.finish("未绑定塔吉多账号，请先使用\"塔吉多登录\"命令登录")
    
    taygedoapi = TaygedoApi()

    res = await taygedoapi.refresh_token(refresh_token=user_data.refresh_token, device_id=user_data.device_id)
    if not res['status']:
        await bind_taygedo_signin.finish(f"{res['message']}，请重新登录")

    access_token = res['data']['accessToken']
    user_data.refresh_token = res['data']['refreshToken']

    # 更新绑定角色数据
    res = await taygedoapi.get_bind_role(access_token=access_token, uid=user_data.uid)
    if res['status']:
        user_data.role_id = str(res['data']['roleId'])
        user_data.role_name = res['data']['roleName']

    # APP签到
    res = await taygedoapi.app_signin(access_token=access_token, uid=user_data.uid, device_id=user_data.device_id)
    if not res['status']:
        app_signin_flag = False
        app_signin_msg = f"APP签到失败：{res['message']}"
    else:
        app_signin_flag = True
        exp = res['data']['exp']
        gold_coin = res['data']['goldCoin']
        app_signin_msg = f"APP签到成功，获得{exp}经验，{gold_coin}金币"

    # 获取签到状态
    res = await taygedoapi.get_signin_state(access_token=access_token)
    if not res['status']:
        signin_state_flag = False
        signin_state_msg = f"获取签到状态失败：{res['message']}"
    else:
        signin_state_flag = True
        days = res['data']['days']

    # 获取签到奖励列表
    res = await taygedoapi.get_signin_rewards(access_token=access_token)
    if not res['status']:
        signin_rewards_flag = False
        signin_rewards_msg = f"获取签到奖励列表失败：{res['message']}"
    else:
        signin_rewards_flag = True
        signin_rewards = res['data']

    # 游戏签到
    res = await taygedoapi.game_signin(access_token=access_token, role_id=user_data.role_id)
    if not res['status']:
        game_signin_flag = False
        game_signin_msg = f"游戏签到失败：{res['message']}"
    else:
        if signin_state_flag and signin_rewards_flag:
            game_signin_flag = True
            reward =signin_rewards[days]
            game_signin_msg = f"游戏签到成功，获得{reward['name']}*{reward['num']}"
        else:
            game_signin_flag = False
            fail_msg = ""
            if not signin_state_flag:
                fail_msg += f" {signin_state_msg}"
            if not signin_rewards_flag:
                fail_msg += f" {signin_rewards_msg}"
            game_signin_msg = f"游戏签到成功，查询奖励信息失败：{fail_msg}"

    role_name = user_data.role_name
    await user_data_database.update_user_data(user_data)
    await user_data_database.commit()
    await bind_taygedo_signin.finish(f"{role_name}签到\n{app_signin_msg}\n{game_signin_msg}")

@bind_signall_handle.handle()
async def _():
    await auto_sign()