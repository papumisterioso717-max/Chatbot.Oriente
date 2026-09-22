from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.controllers.chat_controller import ChatController
from app.routes.chat import router
from app.services.chatbot_engine import ChatError, ChatbotEngine
from app.services.yaml_manager import YamlManager
from app.controllers.file_controller import FileController
from app.services.file_manager import FileManager
from app.routes.files import router as files_router
from app.routes.admin import router as admin_router
from app.services.admin_service import AdminService
from app.controllers.admin_controller import AdminController
from app.services.diagram_catalog import DiagramCatalog
from starlette.middleware.trustedhost import TrustedHostMiddleware

ROOT = Path(__file__).resolve().parent.parent


def create_app(knowledge_path: Path | None = None, storage_path: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yaml_manager = DiagramCatalog(YamlManager(knowledge_path or ROOT / "data" / "knowledge.yaml"))
        knowledge = yaml_manager.load()
        manager = FileManager(storage_path or ROOT / "storage", knowledge)
        manager.validate()
        app.state.file_controller = FileController(manager)
        app.state.chat_controller = ChatController(ChatbotEngine(knowledge))
        app.state.admin_controller = AdminController(AdminService(
            yaml_manager, app.state.chat_controller.engine, app.state.file_controller))
        yield

    app = FastAPI(title="Chatbot de decisiones", version="0.5.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"])
    app.include_router(router)
    app.include_router(files_router)
    app.include_router(admin_router)
    app.mount("/static", StaticFiles(directory=ROOT / "app" / "views" / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def chat_page():
        return FileResponse(ROOT / "app" / "views" / "chat.html")

    @app.get("/admin", include_in_schema=False)
    def admin_page():
        return FileResponse(ROOT / "app" / "views" / "admin.html")

    @app.exception_handler(ChatError)
    async def chat_error(request: Request, error: ChatError):
        return JSONResponse(status_code=error.status_code, content={"detail": str(error)})

    @app.middleware("http")
    async def prevent_session_cache(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


app = create_app()
