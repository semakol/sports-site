import styles from './HeroSection.module.scss'
import HeroImage from "@shared/assets/images/heroImage.png";
import Search from "@features/index"

const HeroSection = () => {
    return (
        <div className={styles.heroSection}>
            <div className={styles.content}>
                <div className={styles.text}>
                    <span className={styles.tag}>ЛЮБИТЕЛЬСКИЙ СПОРТ</span>
                    <h1 className={styles.title}>
                        Футбольные турниры Екатеринбурга в одном месте
                    </h1>
                    <p className={styles.subtitle}>
                        Следи за матчами, результатами и статистикой
                    </p>
                </div>
                <Search />
            </div>
            <div className={styles.imageWrapper}>
                <img 
                    className={styles.image}
                    src={HeroImage}
                    alt="Футбольный мяч на траве"
                />
            </div>
        </div>
    )
}

export default HeroSection;