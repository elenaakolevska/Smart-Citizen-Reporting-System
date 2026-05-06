from app.db.base_class import Base  # noqa: F401

from app.models.attachment import Attachment      # noqa: E402,F401
from app.models.category import Category          # noqa: E402,F401
from app.models.comment import Comment            # noqa: E402,F401
from app.models.department import Department      # noqa: E402,F401
from app.models.history import History            # noqa: E402,F401
from app.models.notification import Notification  # noqa: E402,F401
from app.models.rating import Rating              # noqa: E402,F401
from app.models.report import Report              # noqa: E402,F401
from app.models.status import Status              # noqa: E402,F401
from app.models.user import User                  # noqa: E402,F401