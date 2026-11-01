import styles from './TeamCard.module.scss'
import type { FC } from 'react';
import type { TeamCardProps } from '../model/type';

import ArrowRightCircle from "@shared/assets/icons/arrowRightCircle.svg?react";
import UsersIcon from "@shared/assets/icons/users.svg?react";
import TrophyIcon from "@shared/assets/icons/trophy.svg?react";
import TeamImage from "@shared/assets/images/team.png"

const TeamCard: FC<TeamCardProps> = ({
    logo,
    name,
    teamsCount,
    tournamentsCount
}) => {
  return (
    <div className={`${styles.teamCard}`}>
        <div className={`${styles.cardCover}`}> 
            <img 
                src={TeamImage}
                className={styles.image}
                alt="Картинка команды"
            />
        </div>
        <div className={`${styles.team} ${styles.teamRight}`}>
            {logo ? (
                <img 
                    src={logo}
                    className={styles.logo}
                    alt='Логотип команды'
                />
            ) : (
                <div className={styles.logoPlaceholder} />
            )}
            <span className={styles.teamName}>{name}</span>
        </div>
        <div className={styles.footer}>
            <div className={styles.teamsGroup}>
                <UsersIcon className={styles.icon} />
                <span className={styles.teamsCount}>{teamsCount} команд</span>
            </div>
            <div className={styles.tournamentsGroup}>
                <TrophyIcon className={styles.icon} />
                <span className={styles.tournamentsCount}>{tournamentsCount} турнира</span>
            </div>
            <ArrowRightCircle className={styles.arrow} />
        </div>
    </div>
  )
}

export default TeamCard;
