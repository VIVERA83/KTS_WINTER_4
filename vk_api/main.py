from aiohttp.web import run_app
from core.app import make_app

if __name__ == "__main__":
    app = make_app()
    if all([app.settings.vk.token,
            app.settings.vk.group_id,
            app.settings.rabbitmq.host,
            app.settings.rabbitmq.user,
            app.settings.rabbitmq.password]):
        run_app(app, host=app.settings.host, port=app.settings.port)
    else:
        app.logger.error(f"""
                One of the required parameters is not specified in the environment variables::
                VK__TOKEN
                VK__GROUP_ID
                RABBITMQ__USER
                RABBITMQ__PASSWORD
                RABBITMQ__HOST
        """)
