import styles from './PlayerCard.module.scss'
import type { FC } from 'react';
import type { PlayerCardProps } from '../model/type';

import ArrowRightCircle from "@shared/assets/icons/arrowRightCircle.svg?react";

const PlayerCard: FC<PlayerCardProps> = ({
    logo,
    team,
    role,
    num,
    name
}) => {
  return (
    <div className={`${styles.playerCard}`}>
        <div className={`${styles.imgCover}`}> 
            
        </div>
        <div className={`${styles.content}`}> 
            <div className={`${styles.header}`}>
                {logo ? (
                    <img 
                        src={logo}
                        className={styles.logo}
                        alt='Логотип команды'
                    />
                ) : (
                    <div className={styles.logoPlaceholder} />
                )}
                <span className={styles.teamName}>{team}</span>
                <div className={styles.num}>
                    {num}
                </div>
            </div>
            <div className={`${styles.footer}`}>
                <span className={styles.name}>{name}</span>
                <span className={styles.role}>{role}</span>
            </div>
            <ArrowRightCircle className={styles.arrow} />
        </div>
    </div>
  )
}

export default PlayerCard;
