import typing

if typing.TYPE_CHECKING:
    from core.app import Application


def setup_routes(app: "Application"):
    from game.views import (
        GameSessionAddViews,
        QuestionAddView,
        UserAddView,
        UserGetByIdViews,
        UserGetByVkIdViews,
        RoundAddViews,
        QuestionGetView,
        QuestionGeRandomView,

    )

    app.router.add_view("/get_user_by_id", UserGetByIdViews)
    app.router.add_view("/get_user_by_vk_id", UserGetByVkIdViews)
    app.router.add_view("/add_user", UserAddView)
    app.router.add_view("/add_question", QuestionAddView)
    app.router.add_view("/add_game_session", GameSessionAddViews)
    app.router.add_view("/add_game_round", RoundAddViews)
    app.router.add_view("/get_questions", QuestionGetView)
    app.router.add_view("/get_random_question", QuestionGeRandomView)
