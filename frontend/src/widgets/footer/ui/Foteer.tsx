import styles from './Footer.module.scss'

import VkIcon from "@shared/assets/icons/vk.svg?react"
import TelegramIcon from "@shared/assets/icons/telegram.svg?react"


const Footer = () => {
    return (
        <div className={styles.footer}>
            <div className={styles.content}>
                <span className={styles.title}>Любительский спорт. Ближе, чем кажется</span>
                <div className={styles.socialGroup}>
                    <span className={styles.aboutProject}>О проекте</span>
                    <VkIcon className={styles.vk}/>
                    <TelegramIcon className={styles.telegram} />
                </div>
            </div>
        </div>
    )
}

export default Footer;