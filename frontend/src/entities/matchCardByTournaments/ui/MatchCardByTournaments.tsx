import styles from './MatchCardByTournaments.module.scss'
import type { FC } from 'react';
import type { MatchCardByTournamentsProps } from '../model/type';

import LocationIcon from "@shared/assets/icons/location.svg?react"

const MatchCardByTournaments: FC<MatchCardByTournamentsProps> = ({datetime, group, tour, location, team1, team2}) => {
  return (
    <div className={styles.matchCardByTournaments}>
        <div className={styles.matchData}>
            <div className={styles.leagueGroup}>
                <span className={styles.datetime}>{datetime}</span>
                <span className={styles.tour}>Группа {group} | {tour} тур</span>
            </div>
            <div className={styles.location}>
                <LocationIcon />
                <span>{location}</span>
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

export default MatchCardByTournaments;
