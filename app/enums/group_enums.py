"""Group enums"""

from enum import Enum


class GroupMemberRoleEnum(str, Enum):
	"""Member role enumeration"""

	LEADER = 'leader'
	MEMBER = 'member'
 
class GroupMemberStatus(str, Enum):
    """Member status enumeration"""
    
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
