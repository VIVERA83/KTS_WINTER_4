from aiohttp.web import run_app
from core.app import make_app

if __name__ == "__main__":
    app = make_app()
    run_app(app=app, host=app.settings.host, port=app.settings.port)
