import styles from './Header.module.scss'
import { NavLink, useLocation } from 'react-router-dom'
import {
    MAIN_ROUTE,
    TOURNAMENTS_ROUTE,
    MATCHES_ROUTE,
    TEAMS_ROUTE,
    PLAYERS_ROUTE
} from "@shared/const/router-path";
import Button from '@shared/ui/button';

import SportsIcon from "@shared/assets/icons/sports_soccer.svg?react";

const Header = () => {
    const { pathname } = useLocation();
    const isMatchesActive = pathname.startsWith(MATCHES_ROUTE.path);

    return (
        <div className={styles.header}>
            <div className={styles.leftSide}>
                <div className={styles.logo}>
                    <SportsIcon className={styles.iconLogo} />
                    <span className={styles.textLogo}>Уральский спорт</span>
                </div>
                <nav className={styles.navigation}>
                    <NavLink to={`${MAIN_ROUTE}`} className={({isActive}) => `${styles.navItem} ${isActive && styles.active}`}>Главная</NavLink>
                    <NavLink to={`${TOURNAMENTS_ROUTE}`} className={({isActive}) => `${styles.navItem} ${isActive && styles.active}`}>Турниры</NavLink>
                    <NavLink to={`${MATCHES_ROUTE.path}/${MATCHES_ROUTE.children.BY_DATES}`} className={`${styles.navItem} ${isMatchesActive && styles.active}`}>Матчи</NavLink>
                    <NavLink to={`${TEAMS_ROUTE}`} className={({isActive}) => `${styles.navItem} ${isActive && styles.active}`}>Команды</NavLink>
                    <NavLink to={`${PLAYERS_ROUTE}`} className={({isActive}) => `${styles.navItem} ${isActive && styles.active}`}>Игроки</NavLink>
                </nav>
            </div>
            <Button 
                className={styles.loginButton}
                isFilling={false}
            >
                Войти
            </Button>
        </div>
    )
}

export default Header;