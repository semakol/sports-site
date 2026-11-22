import styles from './MatchesHeroSection.module.scss'
import MatchesHeroImage from "@shared/assets/images/matchesHeroImage.png";
import Search from "@features/index";
import SegmentedControl from "@shared/ui/segmentedControl";
import CustomSelect from "@shared/ui/customSelect";
import { 
    MATCHES_ROUTE
} from "@shared/const/router-path";

const routes = [
    { path: `${MATCHES_ROUTE.path}/${MATCHES_ROUTE.children.BY_DATES}`, label: 'По датам' },
    { path: `${MATCHES_ROUTE.path}/${MATCHES_ROUTE.children.BY_TOURNAMENTS}`, label: 'По турнирам' }
];

const MatchesHeroSection = () => {
    return (
        <div className={styles.matchesHeroSection}>
            <div className={styles.content}>
                <div className={styles.text}>
                    <h1 className={styles.title}>
                        Матчи
                    </h1>
                    <p className={styles.subtitle}>
                        Следи за матчами, результатами и статистикой
                    </p>
                </div>
                <div className={styles.groupSearchControl}>
                    <Search placeholder='Найти матч' />
                    <SegmentedControl className={styles.segmentedControl} routes={routes} />
                </div>
                <div className={styles.filter}>
                    <CustomSelect value='1 октября - 7 октября' />
                    <CustomSelect value='Все турниры' />
                    <CustomSelect value='Все команды' />
                    <CustomSelect value='Все локации' />
                </div>
            </div>
            <div className={styles.imageWrapper}>
                <img 
                    className={styles.image}
                    src={MatchesHeroImage}
                    alt="Футбольный мяч на траве"
                />
            </div>
        </div>
    )
}

export default MatchesHeroSection;