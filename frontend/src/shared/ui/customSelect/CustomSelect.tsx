import styles from './CustomSelect.module.scss'
import type { FC } from 'react';
import type { CustomSelectProps } from './type';

import CaretIcon from "@shared/assets/icons/caret.svg?react"

const CustomSelect: FC<CustomSelectProps> = ({value}) => {
    return (
        <div className={styles.customSelect}>
            <span className={styles.value}>{value}</span>
            <CaretIcon />
        </div>
    )
}

export default CustomSelect;