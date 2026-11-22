import styles from './TeamMatches.module.scss'

import CircleWarning from "@shared/assets/icons/CircleWarning.svg?react"
import UrFUIK from "@shared/assets/images/UrFUIK.png"
import PolytechnicIK from "@shared/assets/images/PolytechnicIK.png"

const mockMatchHistory = [
    {
        month: "Ноябрь 2026",
        matches: [
            {
                id: 1,
                date: "01.11.2026",
                time: "17:00",
                homeTeam: "УрФУ",
                homeLogo: UrFUIK,
                homeScore: 2,
                awayScore: 1,
                awayTeam: "Политех",
                awayLogo: PolytechnicIK,
                tournament: "Студенческая лига",
                status: "win",
                statusText: "Победа"
            },
            {
                id: 2,
                date: "12.11.2026",
                time: "18:00",
                homeTeam: "УрФУ",
                homeLogo: UrFUIK,
                homeScore: 1,
                awayScore: 1,
                awayTeam: "Политех",
                awayLogo: PolytechnicIK,
                tournament: "Студенческая лига",
                status: "draw",
                statusText: "Ничья"
            }
        ]
    },
    {
        month: "Октябрь 2026",
        matches: [
            {
                id: 3,
                date: "01.10.2026",
                time: "17:00",
                homeTeam: "УрФУ",
                homeLogo: UrFUIK,
                homeScore: 3,
                awayScore: 8,
                awayTeam: "Политех",
                awayLogo: PolytechnicIK,
                tournament: "Студенческая лига",
                status: "loss",
                statusText: "Поражение"
            },
            {
                id: 4,
                date: "10.10.2026",
                time: "18:00",
                homeTeam: "УрФУ",
                homeLogo: UrFUIK,
                homeScore: 1,
                awayScore: 1,
                awayTeam: "Политех",
                awayLogo: PolytechnicIK,
                tournament: "Студенческая лига",
                status: "draw",
                statusText: "Ничья"
            },
            {
                id: 5,
                date: "12.10.2026",
                time: "18:00",
                homeTeam: "УрФУ",
                homeLogo: UrFUIK,
                homeScore: 1,
                awayScore: 1,
                awayTeam: "Политех",
                awayLogo: PolytechnicIK,
                tournament: "Студенческая лига",
                status: "draw",
                statusText: "Ничья"
            }
        ]
    }
];

const TeamMatches = () => {
    return (
        <div className={styles.teamMatches}>
            <div className={styles.title}>
                <CircleWarning />
                <span>Матчи команды</span>
            </div>
            <div className={styles.grid}>
                {mockMatchHistory.map((group) => (
                    <div key={group.month} className={styles.monthGroup}>
                        <h3 className={styles.monthTitle}>{group.month}</h3>
                        <div className={styles.matchesList}>
                            {group.matches.map((match) => (
                                <div key={match.id} className={styles.matchRow}>
                                    <div className={styles.dateTime}>
                                        <span>{match.date}</span>
                                        <span>{match.time}</span>
                                    </div>
                                    <div className={styles.matchInfo}>
                                        <div className={styles.teamHome}>
                                            <img src={match.homeLogo} alt={match.homeTeam} className={styles.logo} />
                                            <span className={styles.teamName}>{match.homeTeam}</span>
                                        </div>

                                        <div className={styles.score}>
                                            {match.homeScore} : {match.awayScore}
                                        </div>

                                        <div className={styles.teamAway}>
                                            <img src={match.awayLogo} alt={match.awayTeam} className={styles.logo} />
                                            <span className={styles.teamName}>{match.awayTeam}</span>
                                        </div>
                                    </div>
                                    <span className={styles.tournament}>
                                        {match.tournament}
                                    </span>
                                    <div className={`${styles.status} ${styles[match.status]}`}>
                                        {match.statusText}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default TeamMatches;