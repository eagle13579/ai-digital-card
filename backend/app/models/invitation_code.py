"""邀请码模型 — 1000人内测准入控制"""
from datetime import datetime, timedelta
import secrets
import string
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database import Base


class InvitationCode(Base):
    __tablename__ = "invitation_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(8), unique=True, index=True, nullable=False)
    batch_id = Column(String(32), nullable=True, comment="批次ID")
    max_uses = Column(Integer, default=1, comment="最大使用次数")
    used_count = Column(Integer, default=0, comment="已使用次数")
    created_by = Column(Integer, nullable=True, comment="创建者用户ID")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    is_active = Column(Boolean, default=True)
    remark = Column(Text, nullable=True, comment="备注：分配给谁")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_code(length: int = 8) -> str:
        """生成邀请码：排除易混淆字符 O/I/L/0/1"""
        alphabet = string.ascii_uppercase.replace("O", "").replace("I", "").replace("L", "") \
            + string.digits.replace("0", "").replace("1", "")
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def is_valid(self) -> bool:
        """检查邀请码是否可用"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.used_count >= self.max_uses:
            return False
        return True

    def use(self) -> bool:
        """消耗一次使用次数"""
        if not self.is_valid():
            return False
        self.used_count += 1
        return True
