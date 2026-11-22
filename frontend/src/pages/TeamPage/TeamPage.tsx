import styles from './TeamPage.module.scss'
import { Outlet } from 'react-router-dom';
import TeamHeroSection from '@widgets/teamHeroSection';

const TeamPage = () => {
  return (
    <div className={styles.teamPage}>
        <TeamHeroSection />
        <Outlet />
    </div>
  )
}

export default TeamPage;
