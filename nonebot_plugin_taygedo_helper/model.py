from sqlalchemy.orm import Mapped, mapped_column
from nonebot_plugin_orm import Model

class UserData(Model):
    qq_id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column()
    role_name: Mapped[str] = mapped_column()
    uid: Mapped[str] = mapped_column()
    device_id: Mapped[str] = mapped_column()
    refresh_token: Mapped[str] = mapped_column()
    role_id: Mapped[str] = mapped_column()
    isAutoSigned: Mapped[bool] = mapped_column(default=False)