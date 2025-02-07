from nonebot_plugin_orm import async_scoped_session, AsyncSession
from nonebot.log import logger
from .model import UserData
from sqlalchemy.future import select
import traceback

class UserDataDatabase:
    def __init__(self, session: async_scoped_session|AsyncSession) -> None:
        self.session = session

    async def get_user_data(self, qq: int) -> UserData|None:
        return await self.session.get(UserData, qq)
    
    async def add_user_data(self, external_user_data: UserData) -> bool:
        try:
            await self.session.merge(external_user_data)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f'插入信息表时发生错误:\n{e}')
            await self.session.rollback()
            return False
        else:
            return True
        
    async def update_user_data(self, external_user_data: UserData) -> bool:
        try:
            await self.session.merge(external_user_data)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f'更新信息表时发生错误:\n{e}')
            await self.session.rollback()
            return False
        else:
            return True
        
    async def get_auto_signed_on_user_data_list(self) -> list[UserData]:
        stmt = select(UserData).where(UserData.isAutoSigned == True)
        return list((await self.session.execute(statement=stmt)).scalars().all())
        
    async def commit(self) -> None:
        await self.session.commit()