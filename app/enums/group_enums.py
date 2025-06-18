"""Group enums"""

from enum import Enum


class GroupMemberRoleEnum(str, Enum):
	"""Member role enumeration"""
	LEADER = 'leader'
	MEMBER = 'member'
 
class GroupRequestType(str, Enum):
    """Loại request"""
    JOIN = "join"          # User request tham gia group
    INVITE = "invite"      # Leader mời user vào group
    PROMOTE = "promote"    # Request phong user lên leader
    TRANSFER = "transfer"  # Chuyển quyền leader

class GroupRequestStatus(str, Enum):
    """Trạng thái request"""
    PENDING = "pending"     # Đang chờ xử lý
    APPROVED = "approved"   # Đã chấp nhận
    REJECTED = "rejected"   # Đã từ chối
    CANCELLED = "cancelled" # Đã hủy