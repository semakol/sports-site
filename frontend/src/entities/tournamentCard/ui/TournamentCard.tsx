import styles from './TournamentCard.module.scss'
import type { FC } from 'react';
import type { TournamentCardProps } from '../model/type';

import UsersIcon from "@shared/assets/icons/users.svg?react";
import FormatIcon from "@shared/assets/icons/format.svg?react";
import ArrowRightCircle from "@shared/assets/icons/arrowRightCircle.svg?react";

const TournamentCard: FC<TournamentCardProps> = ({
    title,
    year,
    status,
    teamsCount,
    format
}) => {
    const statusClassMap: Record<string, string> = {
        'Идет': styles.statusActive,
        'Регистрация': styles.statusRegistration,
        'Скоро': styles.statusSoon,
    };

    const currentStatusClass = statusClassMap[status] || '';
    
  return (
    <div className={styles.tournamentCard}>
      <span className={styles.title}>{title}</span>
      <span className={styles.year}>{year}</span>
      <div className={`${styles.statusWrapper} ${currentStatusClass}`}>
        <span className={styles.status}>{status}</span>
      </div>
      <div className={styles.footer}>
        <div className={styles.teamsGroup}>
            <UsersIcon />
            <span className={styles.teamsCount}>{teamsCount} команд</span>
        </div>
        <div className={styles.formatGroup}>
            <FormatIcon />
            <span className={styles.format}>{format}</span>
        </div>
        <ArrowRightCircle className={styles.arrow} />
      </div>
    </div>
  )
}

export default TournamentCard;
