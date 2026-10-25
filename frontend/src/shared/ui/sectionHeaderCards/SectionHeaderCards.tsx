import styles from './SectionHeaderCards.module.scss'
import type { FC } from 'react';
import type { SectionHeaderCardsProps } from './type';
import { NavLink } from 'react-router-dom'

import ArrowRightIcon from "@shared/assets/icons/arrowRight.svg?react"

const SectionHeaderCards: FC<SectionHeaderCardsProps> = ({ icon, title, linkTo, linkText }) => {
    return (
        <div className={styles.sectionHeaderCards}>
            <div className={styles.titleGroup}>
                {icon}
                <h2 className={styles.title}>
                    {title}
                </h2>
            </div>
            {linkTo && 
                <NavLink to={linkTo} className={styles.navItem}>
                    <span>{linkText}</span>
                    <ArrowRightIcon />
                </NavLink>
            }
        </div>
    )
}

export default SectionHeaderCards;