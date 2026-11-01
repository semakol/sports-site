import styles from './TournamentsPage.module.scss'
import TournamentsHeroSection from "@widgets/tournamentsHeroSection"
import TournamentCard from "@entities/tournamentCard";

const MOCK_TOURNAMENTS = [
    {
        id: 1,
        title: 'Студенческая лига',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Идет',
        teamsCount: 12,
        format: 'Чемпионат',
    },
    {
        id: 2,
        title: 'Студенческая лига',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Идет',
        teamsCount: 12,
        format: 'Групповой этап',
    },
    {
        id: 3,
        title: 'Студенческая лига',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Регистрация',
        teamsCount: 12,
        format: '8 туров',
    },
    {
        id: 4,
        title: 'Первенство Екатеринбурга',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Скоро',
        teamsCount: 8,
        format: 'Плей-офф',
    },
    {
        id: 5,
        title: 'Студенческая лига',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Идет',
        teamsCount: 12,
        format: 'Чемпионат',
    },
    {
        id: 6,
        title: 'Студенческая лига',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Идет',
        teamsCount: 12,
        format: 'Групповой этап',
    },
    {
        id: 7,
        title: 'Студенческая лига',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Регистрация',
        teamsCount: 12,
        format: '8 туров',
    },
    {
        id: 8,
        title: 'Первенство Екатеринбурга',
        year: '13 июля 2026 - 30 сентября 2026',
        status: 'Скоро',
        teamsCount: 8,
        format: 'Плей-офф',
    },
];

const TournamentsPage = () => {
  return (
    <div className={styles.tournamentsPage}>
        <TournamentsHeroSection />
        <div className={styles.grid}>
            {MOCK_TOURNAMENTS.map((tournament) => (
                <TournamentCard 
                    key={tournament.id} 
                    isLarge 
                    {...tournament} 
                />
            ))}
        </div>
    </div>
  )
}

export default TournamentsPage;
