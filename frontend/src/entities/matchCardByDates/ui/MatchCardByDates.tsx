import styles from './MatchCardByDates.module.scss'
import type { FC } from 'react';
import type { MatchCardByDatesProps } from '../model/type';

import LocationIcon from "@shared/assets/icons/location.svg?react"

const MatchCardByDates: FC<MatchCardByDatesProps> = ({time, league, group, tour, team1, team2, location}) => {
  return (
    <div className={styles.matchCardByDates}>
        <div className={styles.leftColumn}>
            <span className={styles.time}>{time}</span>
            <div className={styles.matchData}>
                <div className={styles.leagueGroup}>
                    <span className={styles.league}>{league}</span>
                    <span className={styles.tour}>Группа {group} | {tour} тур</span>
                </div>
                <div className={styles.location}>
                    <LocationIcon />
                    <span>{location}</span>
                </div>
            </div>
        </div>
        <div className={styles.teams}>
            <div className={styles.team}>
                <div className={styles.logoPlaceholder}></div>
                <span className={styles.teamName}>{team1}</span>
            </div>
            
            <span className={styles.score}>—</span>
            
            <div className={`${styles.team} ${styles.teamRight}`}>
                <div className={styles.logoPlaceholder}></div>
                <span className={styles.teamName}>{team2}</span>
            </div>
        </div>
    </div>
  )
}

export default MatchCardByDates;
