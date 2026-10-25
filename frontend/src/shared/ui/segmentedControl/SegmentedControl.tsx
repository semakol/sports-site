import styles from './SegmentedControl.module.scss'
import type { FC } from 'react';
import type { SegmentedControlProps } from './type';
import { NavLink } from 'react-router-dom';

const SegmentedControl: FC<SegmentedControlProps> = ({className, routes}) => {
    return (
        <div className={`${styles.segmentedControl} ${className || ''}`}>
            {routes.map((route) => (
                <NavLink 
                    key={route.path}
                    to={route.path}
                    className={({isActive}) => `${styles.buttonControl} ${className || ''} ${isActive && styles.active}`}
                >
                    <span className={styles.text}>{route.label}</span>
                </NavLink>
            ))}
        </div>
    )
}

export default SegmentedControl;