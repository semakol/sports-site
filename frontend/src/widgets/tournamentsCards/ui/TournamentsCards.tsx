import styles from './TournamentsCards.module.scss'
import { TOURNAMENTS_ROUTE } from "@shared/const/router-path";
import TournamentCard from "@entities/tournamentCard";
import SectionHeaderCards from '@/shared/ui/sectionHeaderCards';

import TrophyIcon from "@shared/assets/icons/trophy.svg?react";

const MOCK_TOURNAMENTS = [
    {
        id: 1,
        title: 'Студенческая лига',
        year: 2026,
        status: 'Идет',
        teamsCount: 12,
        format: 'Чемпионат',
    },
    {
        id: 2,
        title: 'Студенческая лига',
        year: 2026,
        status: 'Идет',
        teamsCount: 12,
        format: 'Групповой этап',
    },
    {
        id: 3,
        title: 'Студенческая лига',
        year: 2026,
        status: 'Регистрация',
        teamsCount: 12,
        format: '8 туров',
    },
    {
        id: 4,
        title: 'Первенство Екатеринбурга',
        year: 2026,
        status: 'Скоро',
        teamsCount: 8,
        format: 'Плей-офф',
    },
];

const TournamentsCards = () => {
    return (
        <div className={styles.upcomingMatches}>
            <SectionHeaderCards 
                icon={<TrophyIcon />}
                title="Турниры"
                linkTo={TOURNAMENTS_ROUTE}
                linkText="Все турниры"
            />
            <div className={styles.grid}>
                {MOCK_TOURNAMENTS.map((tournament) => (
                    <TournamentCard key={tournament.id} {...tournament} />
                ))}
            </div>
        </div>
    )
}

export default TournamentsCards;