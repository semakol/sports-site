import styles from './Header.module.scss'
import { NavLink } from 'react-router-dom'
import {
    TOURNAMENTS_ROUTE,
    MATCHES_ROUTE,
    TEAMS_ROUTE,
    PLAYERS_ROUTE
} from "@shared/const/router-path";
import Button from '@shared/ui/button';

import SportsIcon from "@shared/assets/icons/sports_soccer.svg?react";

const Header = () => {
    return (
        <div className={styles.header}>
            <div className={styles.leftSide}>
                <div className={styles.logo}>
                    <SportsIcon className={styles.iconLogo} />
                    <span className={styles.textLogo}>Уральский спорт</span>
                </div>
                <nav className={styles.navigation}>
                    <NavLink to={`${TOURNAMENTS_ROUTE}`} className={styles.navItem}>Турниры</NavLink>
                    <NavLink to={`${MATCHES_ROUTE}`} className={styles.navItem}>Матчи</NavLink>
                    <NavLink to={`${TEAMS_ROUTE}`} className={styles.navItem}>Команды</NavLink>
                    <NavLink to={`${PLAYERS_ROUTE}`} className={styles.navItem}>Игроки</NavLink>
                </nav>
            </div>
            <Button className={styles.loginButton} >Войти</Button>
        </div>
    )
}

export default Header;