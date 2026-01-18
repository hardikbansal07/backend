import sys
import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Add local directories to sys.path
calculation_src_path = os.path.join(os.path.dirname(__file__), "calculation", "calculation-main", "src")
if calculation_src_path not in sys.path:
    sys.path.insert(0, calculation_src_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logging.info("Connecting to MongoDB...")
        from mongo import connect_to_mongo, close_mongo_connection
        await connect_to_mongo()
        
        logging.info("Preloading world city index...")
        from api import service as calc_service
        await calc_service.preload_world_city_index()
        logging.info("World city index loaded successfully.")
        
    except Exception as e:
        logging.error(f"Startup failed: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    try:
        from mongo import close_mongo_connection
        await close_mongo_connection()
        logging.info("Database connection closed.")
    except Exception as e:
        logging.error(f"Shutdown error: {e}")

app = FastAPI(
    title="Astrology Backend API",
    version="1.0.0",
    description="Complete backend: Calculation Engine + Compression + Storage + Authentication",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://astrocareai.com",
        "https://www.astrocareai.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://10.0.2.2:8000",
        "https://astrocare-frontend-vercel.vercel.app",
        "https://frontend-dot-ai-astrology-481805.as.r.appspot.com",
        "https://ai-astrology-481805.as.r.appspot.com"
    ],
    allow_origin_regex=r"https://.*-dot-ai-astrology-481805\.as\.r\.appspot\.com",
    allow_credentials=True,
    allow_methods=["*", "OPTIONS", "GET", "POST", "PUT", "DELETE"],
    allow_headers=["*", "Authorization", "Content-Type"],
)

# Import routers
# Import routers (Auth is critical)
try:
    from user_routes import router as auth_router
    from referral_routes import router as referral_router
    from feedback_routes import router as feedback_router
except ImportError as e:
    logger.critical(f"Critical import failed: {e}")
    raise e

# Global error capture
import_errors = {}

# Import Calculation router safely
calculation_router = None
try:
    from calculation_routes import router as calculation_router
except Exception as e:
    import_errors['calculation'] = str(e)
    logger.error(f"Failed to import Calculation router: {e}")

# Import Agent routers safely (prevent app crash if heavy libs fail)
ai_router = None
deva_router = None
admin_router = None # Initialize admin_router

try:
    from app.admin.routes import router as admin_router
except Exception as e:
    import_errors['admin'] = str(e)
    logger.error(f"Failed to import Admin router: {e}")

try:
    from ai_routes import router as ai_router
except Exception as e:
    import_errors['ai'] = str(e)
    logger.error(f"Failed to import AI router: {e}")

try:
    from deva_routes import router as deva_router
except Exception as e:
    import_errors['deva'] = str(e)
    logger.error(f"Failed to import Deva router: {e}")

admin_auth_router = None
try:
    from app.admin.auth import router as admin_auth_router
except Exception as e:
    import_errors['admin_auth'] = str(e)
    logger.error(f"Failed to import Admin Auth router: {e}")

blog_admin_router = None
blog_public_router = None
try:
    from app.admin.blog_routes import admin_router as blog_admin_router, public_router as blog_public_router
except Exception as e:
    import_errors['blog'] = str(e)
    logger.critical(f"Failed to import Blog routers: {e}")
    raise e

# Register routers
app.include_router(auth_router, prefix="/calc")
# Mount Guest Auth Router
from routers.guest_auth import router as guest_auth_router
app.include_router(guest_auth_router, prefix="/calc/api/v1/auth")

app.include_router(referral_router, prefix="/calc")
app.include_router(feedback_router, prefix="/calc", tags=["Feedback"])

if calculation_router:
    app.include_router(calculation_router, prefix="/calc", tags=["Calculation"])

if ai_router:
    app.include_router(ai_router, prefix="/calc/api/v1/ai", tags=["AI Orchestrator"])
if deva_router:
    app.include_router(deva_router, prefix="/calc/api/v1/deva", tags=["Deva Agent"])

# Register new Admin Auth Router
if admin_auth_router:
    app.include_router(admin_auth_router, prefix="/api/admin", tags=["Admin Auth"])

if blog_admin_router:
    # Mounted at /admin/blogs (prefix defined in router)
    app.include_router(blog_admin_router)

if blog_public_router:
    # Mounted at /calc/api/blogs (prefix defined in router)
    app.include_router(blog_public_router, prefix="/calc")

if admin_router:
    app.include_router(admin_router) # Configured with prefix /admin inside the router itself

@app.get("/")
def home():
    return {
        "message": "Astrology Backend API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "auth": "/api/v1/auth",
            "calculation": "/calc/api",
            "ai": "/api/v1/ai",
            "deva": "/api/v1/deva"
        },
        "deployed_at": "2026-01-18T18:20:00+05:30" # Deployment Marker
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "astrology-backend"}

@app.get("/calc/chk")
def check_imports():
    registered_routes = [route.path for route in app.routes]
    return {
        "status": "debug",
        "errors": import_errors,
        "routers": {
            "calculation": calculation_router is not None,
            "ai": ai_router is not None,
            "deva": deva_router is not None,
            "blog_public": blog_public_router is not None,
            "blog_public_routes": len(blog_public_router.routes) if blog_public_router else 0
        },
        "all_routes": registered_routes
    }

horoscope_frontend_dist = os.path.join(os.path.dirname(__file__), "calculation", "calculation-main", "frontend", "dist")
if os.path.exists(horoscope_frontend_dist):
    app.mount("/horoscope", StaticFiles(directory=horoscope_frontend_dist, html=True), name="horoscope-frontend")
    logger.info(f"Serving horoscope frontend from {horoscope_frontend_dist}")
else:
    logger.warning(f"Horoscope frontend dist not found at {horoscope_frontend_dist}. Build it first with: cd backend/calculation/calculation-main/frontend && npm run build")
