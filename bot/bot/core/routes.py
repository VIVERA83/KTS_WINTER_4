import typing

from web.views import SetTimeOutKeyboardView

if typing.TYPE_CHECKING:
    from core.componets import Application


def setup_routes(app: "Application"):
    from web.views import UserNameView

    app.router.add_view("/get_user_name", UserNameView)
    app.router.add_view("/set_keyboard_timeout", SetTimeOutKeyboardView)
