import styles from './TeamHeroSection.module.scss'
import { useMemo } from 'react';
import SegmentedControl from "@shared/ui/segmentedControl";
import { 
    TEAM_ROUTE
} from "@shared/const/router-path";
import { useLocation, useParams } from 'react-router-dom';
import CustomSelect from '@shared/ui/customSelect';

import HeroImage from "@shared/assets/images/heroImage.png";
import UrFUIK from "@shared/assets/images/UrFUIK.png"
import LocationIcon from "@shared/assets/icons/location.svg?react"

const TeamHeroSection = () => {
    const location = useLocation();
    const { id } = useParams();

    const routes = useMemo(() => [
        { path: `${TEAM_ROUTE.path}/${id}`, label: 'Обзор' },
        {
            path: `${TEAM_ROUTE.path}/${id}/${TEAM_ROUTE.children.STRUCTURE}`,
            label: 'Состав',
        },
        {
            path: `${TEAM_ROUTE.path}/${id}/${TEAM_ROUTE.children.TEAM_MATCHES}`,
            label: 'Матчи',
        },
    ], [id]);

    const isMatchesPage = location.pathname === `${TEAM_ROUTE.path}/${id}/${TEAM_ROUTE.children.TEAM_MATCHES}`;

    return (
        <div className={styles.teamHeroSection}>
            <div className={styles.content}>
                <div className={styles.teamInfo}>
                    <img 
                        src={UrFUIK}
                        className={styles.logo}
                        alt='Логотип команды'
                    />
                    <div className={styles.textInfo}>
                        <h1 className={styles.teamName}>УрФУ</h1>
                        <div className={styles.locationGroup}>
                            <LocationIcon className={styles.iconLocation} />
                            <span className={styles.location}>Екатеринбург</span>
                        </div>
                    </div>
                </div>
                <div className={styles.controlsRow}>
                    <SegmentedControl className={styles.segmentedControl} routes={routes} />
                    {isMatchesPage && <CustomSelect value='2026' />}
                </div>
            </div>
            <div className={styles.imageWrapper}>
                <img 
                    className={styles.image}
                    src={HeroImage}
                    alt="Футбольный мяч на траве"
                />
            </div>
        </div>
    )
}

export default TeamHeroSection;