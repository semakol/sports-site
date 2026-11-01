import styles from './TournamentsHeroSection.module.scss'
import Search from "@features/index"
import CustomSelect from "@shared/ui/customSelect"

const TournamentsHeroSection = () => {
    return (
        <div className={styles.tournamentsHeroSection}>
            <h1 className={styles.title}>Турниры</h1>
            <span className={styles.subtitle}>Следи за матчами, результатами и статистикой</span>
            <div className={styles.filter}>
                <Search placeholder='Найти турнир' className={styles.search} />
                <CustomSelect value='2026' />
            </div>
        </div>
    )
}

export default TournamentsHeroSection;