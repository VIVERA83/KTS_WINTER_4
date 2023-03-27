from aiohttp.web import run_app
from core.app import make_app

if __name__ == "__main__":
    app = make_app()
    if all([app.settings.postgres.db,
            app.settings.postgres.user,
            app.settings.postgres.password]):
        run_app(app, host=app.settings.host, port=app.settings.port)
    else:
        app.logger.error(f"""
                One of the required parameters is not specified in the environment variables:
                POSTGRES__DB
                POSTGRES__USER
                POSTGRES__PASSWORD
        """)


