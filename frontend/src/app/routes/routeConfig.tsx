import { MAIN_ROUTE, MATCHES_ROUTE } from "@shared/const/router-path";
import MainPage from "@/pages/MainPage/MainPage";
import MatchesPage from "@/pages/MatchesPage/MatchesPage";

export const authRoutes = [

];

export const publicRoutes = [
    {
        path: MAIN_ROUTE,
        Component: MainPage
    },
    {
        path: MATCHES_ROUTE.path + MATCHES_ROUTE.children.BY_DATES,
        Component: MatchesPage
    },
    {
        path: MATCHES_ROUTE.path + MATCHES_ROUTE.children.BY_TOURNAMENTS,
        Component: MatchesPage
    }
];