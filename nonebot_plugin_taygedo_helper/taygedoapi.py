from nonebot.log import logger

import httpx
import urllib.parse as qs
import time
import traceback

from .calculate import Calculate

DEVICETYPE = 'LGE-AN10'
TYPE = "16"
DEVICENAME = "LGE-AN10"
VERSIONCODE = "1"
AREACODEID = "1"
APPID = "10550"
USERCENTERAPPID = "10551"
DEVICESYS = "12"
DEVICEMODEL = "LGE-AN10"
SDKVERSION = "4.129.0"
BID = "com.pwrd.htassistant"
CHANNELID = "1"
GAMEID = "1256"
COMMUNITYID = "1"
APPVERSION = "1.1.0"

CONSTANTS = {
    'SENDCAPTCHA': 'https://user.laohu.com/m/newApi/sendPhoneCaptchaWithOutLogin',
    'CHECKCAPTCHA': 'https://user.laohu.com/m/newApi/checkPhoneCaptchaWithOutLogin',
    'LOGIN': 'https://user.laohu.com/openApi/sms/new/login',
    'USERCENTERLOGIN': 'https://bbs-api.tajiduo.com/usercenter/api/login',
    'REFRESHTOKEN': 'https://bbs-api.tajiduo.com/usercenter/api/refreshToken',
    'SIGNINSTATE': 'https://bbs-api.tajiduo.com/apihub/wapi/signin/state',
    'SIGNREWARD': 'https://bbs-api.tajiduo.com/apihub/wapi/sign/rewards',
    'GETBINDROLE': 'https://bbs-api.tajiduo.com/apihub/api/getGameBindRole',
    'GETGAMEROLES': 'https://bbs-api.tajiduo.com/usercenter/api/v2/getGameRoles',
    'BINDROLE': 'https://bbs-api.tajiduo.com/usercenter/api/bindGameRole',
    'APPSIGNIN': 'https://bbs-api.tajiduo.com/apihub/api/signin',
    'GAMESIGNIN': 'https://bbs-api.tajiduo.com/apihub/awapi/sign',
    'GETSIGNINSTATE': 'https://bbs-api.tajiduo.com/apihub/awapi/signin/state',
    'GETSIGNINREWARDS': 'https://bbs-api.tajiduo.com/apihub/awapi/sign/rewards',

    'REQUEST_HEADERS_BASE': {
        "platform": "android",
        'Content-Type': 'application/x-www-form-urlencoded'
    }
}

class TaygedoApi:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=200)

    async def close(self):
        await self.client.aclose()

    async def send_captcha(self, phone: str, device_id: str):
        data = {
            'deviceType': DEVICETYPE,
            'type': TYPE,
            'deviceId': device_id,
            'deviceName': DEVICENAME,
            'versionCode': VERSIONCODE,
            't': str(int(time.time())),
            'areaCodeId': AREACODEID,
            'appId': APPID,
            'deviceSys': DEVICESYS,
            'cellphone': phone,
            'deviceModel': DEVICEMODEL,
            'sdkVersion': SDKVERSION,
            'bid': BID,
            'channelId': CHANNELID,
        }

        data['sign'] = Calculate.generate_sign(data)

        payload = qs.urlencode(data)
        headers = {**CONSTANTS['REQUEST_HEADERS_BASE']}

        try:
            response = await self.client.post(CONSTANTS['SENDCAPTCHA'], content=payload, headers=headers)
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"发送验证码响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['message'] == '手机短信发送成功':
                return {'status': True, 'message': response_data['data']['message']}
            else:
                logger.error(f"发送验证码失败: {response_data}")
                return {'status': False, 'message': response_data['data']['message']}
        except Exception as e:
            logger.error(f"发送验证码失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '发送验证码失败，详情请查看日志'}

    async def check_captcha(self, phone: str, captcha: str, device_id: str):
        data = {
            'deviceType': DEVICETYPE,
            'deviceId': device_id,
            'deviceName': DEVICENAME,
            'versionCode': VERSIONCODE,
            't': str(int(time.time())),
            'captcha': captcha,
            'appId': APPID,
            'deviceSys': DEVICESYS,
            'cellphone': phone,
            'deviceModel': DEVICEMODEL,
            'sdkVersion': SDKVERSION,
            'bid': BID,
            'channelId': CHANNELID
        }

        data['sign'] = Calculate.generate_sign(data)

        payload = qs.urlencode(data)
        headers = {**CONSTANTS['REQUEST_HEADERS_BASE']}

        try:
            response = await self.client.post(CONSTANTS['CHECKCAPTCHA'], content=payload, headers=headers)
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"验证验证码响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['message'] == '手机验证码正确':
                return {'status': True, 'message': response_data['data']['message']}
            else:
                logger.error(f"验证验证码失败: {response_data}")
                if response_data['data']['message'].find("短信正在发送") != -1:
                    return {'status': False, 'message': "短信正在发送，请等待几分钟后再试"}
                return {'status': False, 'message': response_data['data']['message']}
        except Exception as e:
            logger.error(f"验证验证码失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '验证验证码失败，详情请查看日志'}

    async def login(self, phone: str, captcha: str, device_id: str):
        phone = Calculate.aes_base64_encode(phone)
        captcha = Calculate.aes_base64_encode(captcha)

        data = {
            'deviceType': DEVICETYPE,
            'idfa': '',
            'sign': '',
            'adm': '',
            'type': TYPE,
            'deviceId': device_id,
            'version': VERSIONCODE,
            'deviceName': DEVICENAME,
            'mac': '',
            't': str(int(time.time() * 1000)),
            'areaCodeId': AREACODEID,
            'captcha': captcha,
            'appId': APPID,
            'deviceSys': DEVICESYS,
            'cellphone': phone,
            'deviceModel': DEVICEMODEL,
            'sdkVersion': SDKVERSION,
            'bid': BID,
            'channelId': CHANNELID
        }

        data['sign'] = Calculate.generate_sign(data)
        payload = qs.urlencode(data)
        headers = {**CONSTANTS['REQUEST_HEADERS_BASE']}

        try:
            response = await self.client.post(CONSTANTS['LOGIN'], content=payload, headers=headers)
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"登录响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['message'] == '登录成功':
                return {'status': True, 'message': response_data['data']['message'], 'result': response_data['data']['result']}
            else:
                logger.error(f"登录失败: {response_data}")
                return {'status': False, 'message': response_data['data']['message']}
        except Exception as e:
            logger.error(f"登录失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '登录失败，详情请查看日志'}
        
    async def user_center_login(self, token: str, userId: str, device_id: str):
        data = {
            'token': token,
            'userIdentity': userId,
            'appId': USERCENTERAPPID,
        }

        payload = qs.urlencode(data)
        headers = {**CONSTANTS['REQUEST_HEADERS_BASE'], 'deviceid': device_id, 'authorization': '', 'appversion': APPVERSION, 'uid': '10100300', 'User-Agent': 'okhttp/4.12.0'}

        try:
            response = await self.client.post(CONSTANTS['USERCENTERLOGIN'], content=payload, headers=headers)
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"用户中心登录响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['msg'] == 'ok':
                return {'status': True, 'message': response_data['data']['msg'], 'data': response_data['data']['data']}
            else:
                logger.error(f"headers: {headers}")
                logger.error(f"payload: {payload}")
                logger.error(f"用户中心登录失败: {response_data}")
                return {'status': False, 'message': response_data['data']['msg']}
        except Exception as e:
            logger.error(f"用户中心登录失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '用户中心登录失败，详情请查看日志'}
        
    async def refresh_token(self, refresh_token: str, device_id: str):
        headers = {**CONSTANTS['REQUEST_HEADERS_BASE'], 'deviceid': device_id, 'authorization': refresh_token, 'appversion': APPVERSION, 'uid': '10100300', 'User-Agent': 'okhttp/4.12.0'}

        try:
            response = await self.client.post(CONSTANTS['REFRESHTOKEN'], headers=headers)
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"刷新token响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['msg'] == 'ok':
                return {'status': True, 'message': response_data['data']['msg'], 'data': response_data['data']['data']}
            else:
                logger.error(f"刷新token失败: {response_data}")
                return {'status': False, 'message': response_data['data']['msg']}
        except Exception as e:
            logger.error(f"刷新token失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '刷新token失败，详情请查看日志'}
        
    async def get_bind_role(self, access_token: str, uid: str):
        headers = {'Authorization': access_token}

        try:
            response = await self.client.get(CONSTANTS['GETBINDROLE'], headers=headers, params={'uid': uid, 'gameId': GAMEID})
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"获取绑定角色响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['msg'] == 'ok':
                return {'status': True, 'message': response_data['data']['msg'], 'data': response_data['data']['data']}
            else:
                logger.error(f"获取绑定角色失败: {response_data}")
                return {'status': False, 'message': response_data['data']['msg']}
        except Exception as e:
            logger.error(f"获取绑定角色失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '获取绑定角色失败，详情请查看日志'}
        
    async def app_signin(self, access_token: str, uid: str, device_id: str):
        data = {
            'communityId': COMMUNITYID
        }

        payload = qs.urlencode(data)
        headers = {**CONSTANTS['REQUEST_HEADERS_BASE'], 'authorization': access_token, 'uid': uid, 'deviceid': device_id, 'appversion': APPVERSION, 'User-Agent': 'okhttp/4.12.0'}

        try:
            response = await self.client.post(CONSTANTS['APPSIGNIN'], content=payload, headers=headers)
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"app签到响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['msg'] == 'ok':
                return {'status': True, 'message': response_data['data']['msg'], 'data': response_data['data']['data']}
            else:
                logger.error(f"app签到失败: {response_data}")
                return {'status': False, 'message': response_data['data']['msg']}
        except Exception as e:
            logger.error(f"app签到失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': 'app签到失败，详情请查看日志'}
        
    async def game_signin(self, access_token: str, role_id: str):
        data = {
            'roleId': role_id,
            'gameId': GAMEID
        }

        payload = qs.urlencode(data)
        headers = {**CONSTANTS['REQUEST_HEADERS_BASE'], 'authorization': access_token}

        try:
            response = await self.client.post(CONSTANTS['GAMESIGNIN'], content=payload, headers=headers)
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"游戏签到响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['msg'] == 'ok':
                return {'status': True, 'message': response_data['data']['msg']}
            else:
                logger.error(f"游戏签到失败: {response_data}")
                return {'status': False, 'message': response_data['data']['msg']}
        except Exception as e:
            logger.error(f"游戏签到失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '游戏签到失败，详情请查看日志'}
        
    async def get_signin_state(self, access_token: str):
        headers = {'Authorization': access_token}

        try:
            response = await self.client.get(CONSTANTS['GETSIGNINSTATE'], headers=headers, params={'gameId': GAMEID})
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"获取签到状态响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['msg'] == 'ok':
                return {'status': True, 'message': response_data['data']['msg'], 'data': response_data['data']['data']}
            else:
                logger.error(f"获取签到状态失败: {response_data}")
                return {'status': False, 'message': response_data['data']['msg']}
        except Exception as e:
            logger.error(f"获取签到状态失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '获取签到状态失败，详情请查看日志'}
        
    async def get_signin_rewards(self, access_token: str):
        headers = {'Authorization': access_token}

        try:
            response = await self.client.get(CONSTANTS['GETSIGNINREWARDS'], headers=headers, params={'gameId': GAMEID})
            response_data = {}
            response_data['code'] = response.status_code
            response_data['data'] = response.json()
            logger.debug(f"获取签到奖励响应: {response_data}")

            if response_data['code'] == 200 and response_data['data']['code'] == 0 and response_data['data']['msg'] == 'ok':
                return {'status': True, 'message': response_data['data']['msg'], 'data': response_data['data']['data']}
            else:
                logger.error(f"获取签到奖励失败: {response_data}")
                return {'status': False, 'message': response_data['data']['msg']}
        except Exception as e:
            logger.error(f"获取签到奖励失败: {e}")
            logger.error(traceback.format_exc())
            return {'status': False, 'message': '获取签到奖励失败，详情请查看日志'}
