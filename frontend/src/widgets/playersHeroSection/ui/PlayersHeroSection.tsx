import Search from '@features/ui/search/Search';
import styles from './PlayersHeroSection.module.scss'
import CustomSelect from '@shared/ui/customSelect';

const PlayersHeroSection = () => {
    return (
        <div className={styles.playersHeroSection}>
            <h1 className={styles.title}>Игроки</h1>
            <span className={styles.subtitle}>Найди своего любимого игрока и следи за его статистикой</span>
            <div className={styles.filter}>
                <Search placeholder='Найти игрока по ФИО или номеру' className={styles.search} />
                <CustomSelect value='За все время' />
                <CustomSelect value='Все команды' />
            </div>
        </div>
    )
}

export default PlayersHeroSection;