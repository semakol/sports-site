import { Routes, Route, Navigate  } from 'react-router-dom';
import MainLayout from "@app/layouts/MainLayout"
import { authRoutes, publicRoutes } from "./routeConfig";
import { MAIN_ROUTE } from "@shared/const/router-path";

const AppRouter = () => {
    const isAuth = false;

    return (
        <Routes>
            <Route element={<MainLayout />}>
                {/* {isAuth && authRoutes.map(({ path, Component }) =>
                    <Route key={path} path={path} element={<Component/>} />
                )} */}
                {publicRoutes.map(({ path, Component }) =>
                    <Route key={path} path={path} element={<Component/>} />
                )}
                <Route path="*" element={<Navigate to={ MAIN_ROUTE } />}/>
            </Route>
        </Routes>
    )
}

export default AppRouter;