from fastapi import APIRouter

from app.api.routes import auth, health, matches, players, teams, tournaments, users

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(tournaments.router)
api_router.include_router(matches.router)
