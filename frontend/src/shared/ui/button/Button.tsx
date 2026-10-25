import styles from './Button.module.scss'
import type { FC } from 'react';
import type { ButtonProps } from './type';

const Button: FC<ButtonProps> = ({className, children, isWidthGriddy=false, isFilling=true}) => {
    return (
        <button className={`${styles.button} ${className || ''} ${isWidthGriddy && styles.griddyWidth} ${!isFilling && styles.noFill} `}>
            <p className={styles.textContent}>{children}</p>
        </button>
    )
}

export default Button;