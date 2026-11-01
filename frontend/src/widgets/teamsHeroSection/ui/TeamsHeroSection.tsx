import styles from './TeamsHeroSection.module.scss'
import Search from "@features/index"
import CustomSelect from "@shared/ui/customSelect"

const TeamsHeroSection = () => {
    return (
        <div className={styles.teamsHeroSection}>
            <h1 className={styles.title}>Команды</h1>
            <span className={styles.subtitle}>Найди свою любимую команду и следи за ее статистикой</span>
            <div className={styles.filter}>
                <Search placeholder='Найти команду' className={styles.search} />
                <CustomSelect value='За все время' />
            </div>
        </div>
    )
}

export default TeamsHeroSection;