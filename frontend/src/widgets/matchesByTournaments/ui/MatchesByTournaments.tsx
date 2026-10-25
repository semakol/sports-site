import styles from './MatchesByTournaments.module.scss'
import SectionHeaderCards from "@shared/ui/sectionHeaderCards"
import MatchCardByTournaments from "@entities/matchCardByTournaments"

import CalendarIcon from "@shared/assets/icons/calendar.svg?react";

export const matchesByTournamentsData = [
    {
        id: 'league-1',
        title: 'Студенческая лига',
        matches: [
            { 
                id: 1, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
            { 
                id: 2, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
            { 
                id: 3, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
            { 
                id: 4, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
        ]
    },
    {
        id: 'league-2',
        title: 'Первенство Екатеринбурга',
        matches: [
            { 
                id: 5, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
            { 
                id: 6, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
            { 
                id: 7, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
            { 
                id: 8, 
                datetime: '1 октября, СБ, 19:00', 
                group: 'А', 
                tour: 1, 
                location: 'Москва, Ураллани', 
                team1: 'Урал', 
                team2: 'Полтава' 
            },
        ]
    }
];

const MatchesByTournaments = () => {
    return (
        <div className={styles.matchesByTournaments}>
            {matchesByTournamentsData.map((league, index) => (
                <div key={index} className={styles.leagueGroup}>
                    <SectionHeaderCards icon={<CalendarIcon />} title={league.title} />
                    <div className={styles.grid}>
                        {league.matches.map((match) => (
                            <MatchCardByTournaments key={match.id} {...match} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    )
}

export default MatchesByTournaments;
