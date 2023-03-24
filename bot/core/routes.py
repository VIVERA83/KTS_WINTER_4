import typing

if typing.TYPE_CHECKING:
    from core.componets import Application


def setup_routes(app: "Application"):
    from web.views import UserNameView

    app.router.add_view("/get_user_name", UserNameView)
