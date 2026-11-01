import styles from './TeamsPage.module.scss'
import TeamsHeroSection from "@widgets/teamsHeroSection"
import TeamCard from "@entities/teamCard"
import UrFUIK from "@shared/assets/images/UrFUIK.png"

const MOCK_TEAMS = [
    {
        id: 1,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
    {
        id: 2,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
    {
        id: 3,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
    {
        id: 4,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
    {
        id: 5,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
    {
        id: 6,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
    {
        id: 7,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
    {
        id: 8,
        logo: UrFUIK,
        name: 'УрФУ',
        teamsCount: 12,
        tournamentsCount: 2
    },
];

const TeamsPage = () => {
  return (
    <div className={styles.teamsPage}>
        <TeamsHeroSection />
        <div className={styles.grid}>
            {MOCK_TEAMS.map((team) => (
                <TeamCard 
                  key={team.id}
                  {...team} 
                />
            ))}
        </div>
    </div>
  )
}

export default TeamsPage;
