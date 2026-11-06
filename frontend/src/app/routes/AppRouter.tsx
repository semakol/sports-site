import { Routes, Route, Navigate  } from 'react-router-dom';
import MainLayout from "@app/layouts/MainLayout"
import { authRoutes, publicRoutes } from "./routeConfig";
import { 
    MAIN_ROUTE, 
    MATCHES_ROUTE, 
    TOURNAMENTS_ROUTE,
    TEAMS_ROUTE,
    PLAYERS_ROUTE
} from "@shared/const/router-path";
import MainPage from "@pages/MainPage/MainPage";
import TournamentsPage from "@pages/TournamentsPage/TournamentsPage"
import MatchesPage from "@pages/MatchesPage/MatchesPage";
import TeamsPage from "@pages/TeamsPage/TeamsPage"
import PlayersPage from "@pages/PlayersPage/PlayersPage"
import MatchesByDates from "@widgets/matchesByDates"
import MatchesByTournaments from "@widgets/matchesByTournaments"

const AppRouter = () => {
    const isAuth = false;

    return (
        <Routes>
            <Route element={<MainLayout />}>
                {/* {isAuth && authRoutes.map(({ path, Component }) =>
                    <Route key={path} path={path} element={<Component/>} />
                )} */}
                {/* {publicRoutes.map(({ path, Component }) =>
                    <Route key={path} path={path} element={<Component/>} />
                )} */}

                <Route path={MAIN_ROUTE} element={<MainPage />}/>
                <Route path={TOURNAMENTS_ROUTE} element={<TournamentsPage />}/>
                <Route path={MATCHES_ROUTE.path} element={<MatchesPage />}>
                    <Route path={MATCHES_ROUTE.children.BY_DATES} element={<MatchesByDates />}/>
                    <Route path={MATCHES_ROUTE.children.BY_TOURNAMENTS} element={<MatchesByTournaments />}/>
                </Route>
                <Route path={TEAMS_ROUTE} element={<TeamsPage />}/>
                <Route path={PLAYERS_ROUTE} element={<PlayersPage />}/>


                {/* <Route path="*" element={<Navigate to={ MAIN_ROUTE } />}/> */}
            </Route>
        </Routes>
    )
}

export default AppRouter;