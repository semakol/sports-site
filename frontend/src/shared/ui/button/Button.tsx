import styles from './Button.module.scss'
import type { FC } from 'react';
import type { ButtonProps } from './type';

const Button: FC<ButtonProps> = ({className, children, isWidthGriddy=false}) => {
    return (
        <button className={`${styles.button} ${className || ''} ${isWidthGriddy ? styles.griddyWidth : ''} `}>
            <p className={styles.textContent}>{children}</p>
        </button>
    )
}

export default Button;