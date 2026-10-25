import styles from './MatchesByDates.module.scss'
import SectionHeaderCards from "@shared/ui/sectionHeaderCards"
import MatchCardByDates from "@entities/matchCardByDates"

import CalendarIcon from "@shared/assets/icons/calendar.svg?react";

const matchesData = [
    {
        date: 'Сегодня, 1 октября, понедельник',
        matches: [
            { id: 1, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Манеж Уралмаш', team1: 'Урал', team2: 'Политех' },
            { id: 2, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Манеж Уралмаш', team1: 'Урал', team2: 'Политех' },
            { id: 3, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Манеж Уралмаш', team1: 'Урал', team2: 'Политех' },
            { id: 4, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Манеж Уралмаш', team1: 'Урал', team2: 'Политех' },
        ]
    },
    {
        date: 'Завтра, 2 октября, вторник',
        matches: [
            { id: 5, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Москва, Ураллани', team1: 'Урал', team2: 'Полтава' },
            { id: 6, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Москва, Ураллани', team1: 'Урал', team2: 'Полтава' },
            { id: 7, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Москва, Ураллани', team1: 'Урал', team2: 'Полтава' },
            { id: 8, time: '19:00', league: 'Студенческая лига', group: 'А', tour: 1, location: 'Москва, Ураллани', team1: 'Урал', team2: 'Полтава' },
        ]
    }
];

const MatchesByDates = () => {
    return (
        <div className={styles.matchesByDates}>
            {matchesData.map((day, index) => (
                <div key={index} className={styles.dayGroup}>
                    <SectionHeaderCards icon={<CalendarIcon />} title={day.date} />
                    <div className={styles.grid}>
                        {day.matches.map((match) => (
                            <MatchCardByDates key={match.id} {...match} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    )
}

export default MatchesByDates;