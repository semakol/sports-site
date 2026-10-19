import styles from './UpcomingMatchesCards.module.scss'
import { MATCHES_ROUTE } from "@shared/const/router-path";
import MatchCard from "@entities/matchCard";
import SectionHeaderCards from '@/shared/ui/sectionHeaderCards';

import CalendarIcon from "@shared/assets/icons/calendar.svg?react";

const MOCK_MATCHES = [
    { id: 1, date: 'Сегодня, 1 октября', time: '19:00', league: 'Студенческая лига', tour: '1 тур', team1: 'УрФУ', team2: 'Политех', location: 'Манеж Уралмаш' },
    { id: 2, date: 'Сегодня, 1 октября', time: '19:00', league: 'Студенческая лига', tour: '1 тур', team1: 'УрФУ', team2: 'Политех', location: 'Манеж Уралмаш' },
    { id: 3, date: 'Сегодня, 1 октября', time: '19:00', league: 'Студенческая лига', tour: '1 тур', team1: 'УрФУ', team2: 'Политех', location: 'Манеж Уралмаш' },
    { id: 4, date: 'Сегодня, 1 октября', time: '19:00', league: 'Студенческая лига', tour: '1 тур', team1: 'УрФУ', team2: 'Политех', location: 'Манеж Уралмаш' },
];

const UpcomingMatchesCards = () => {
    return (
        <div className={styles.upcomingMatches}>
            <SectionHeaderCards 
                icon={<CalendarIcon />}
                title="Ближайшие матчи"
                linkTo={MATCHES_ROUTE}
                linkText="Все матчи"
            />
            <div className={styles.grid}>
                {MOCK_MATCHES.map((match) => (
                    <MatchCard key={match.id} {...match} />
                ))}
            </div>
        </div>
    )
}

export default UpcomingMatchesCards;