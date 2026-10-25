import MatchesHeroSection from '@widgets/matchesHeroSection';
import styles from './MatchesPage.module.scss'
import { Outlet } from 'react-router-dom';

const MatchesPage = () => {
  return (
    <div className={styles.matchesPage}>
      <MatchesHeroSection />
      <Outlet />
    </div>
  )
}

export default MatchesPage;
