import HeroSection from '@widgets/heroSection';
import UpcomingMatchesCards from '@widgets/upcomingMatchesCards';
import TournamentsCards from "@widgets/tournamentsCards"
import styles from './MainPage.module.scss'

const MainPage = () => {
  return (
    <div className={styles.mainPage}>
      <HeroSection />
      <UpcomingMatchesCards />
      <TournamentsCards />
    </div>
  )
}

export default MainPage;
