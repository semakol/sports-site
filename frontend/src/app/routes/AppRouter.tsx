import { Routes, Route, Navigate  } from 'react-router-dom';
import MainLayout from "@app/layouts/MainLayout"
import { authRoutes, publicRoutes } from "./routeConfig";
import { MAIN_ROUTE, MATCHES_ROUTE } from "@shared/const/router-path";
import MainPage from "@pages/MainPage/MainPage";
import MatchesPage from "@pages/MatchesPage/MatchesPage";
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
                <Route path={MATCHES_ROUTE.path} element={<MatchesPage />}>
                    <Route path={MATCHES_ROUTE.children.BY_DATES} element={<MatchesByDates />}/>
                    <Route path={MATCHES_ROUTE.children.BY_TOURNAMENTS} element={<MatchesByTournaments />}/>
                </Route>


                <Route path="*" element={<Navigate to={ MAIN_ROUTE } />}/>
            </Route>
        </Routes>
    )
}

export default AppRouter;