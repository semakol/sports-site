import styles from './TeamStatistics.module.scss'

import CircleWarning from "@shared/assets/icons/CircleWarning.svg?react"
import CircleCheck from "@shared/assets/icons/CircleCheck.svg?react"
import Calendar from "@shared/assets/icons/calendar.svg?react"
import Flag from "@shared/assets/icons/flag.svg?react"
import UrFUIK from "@shared/assets/images/UrFUIK.png"
import PolytechnicIK from "@shared/assets/images/PolytechnicIK.png"

const TeamStatistics = () => {
    return (
        <div className={styles.teamStatistics}>
            <div className={styles.leftColumn}>
                <div className={styles.about}>
                    <div className={styles.title}>
                        <CircleWarning />
                        <span>О команде</span>
                    </div>
                    <p className={styles.text}>
                        Главная футбольная сила УрФУ. Бьемся за каждый мяч, задаем темп в любительских лигах Екатеринбурга и всегда 
                        нацелены только на верхнюю строчку турнирной таблицы.
                    </p>
                </div>
                <div className={styles.about}>
                    <div className={styles.title}>
                        <CircleCheck />
                        <span>Общие результаты</span>
                    </div>
                    <div className={styles.generalResults}>
                        <div className={styles.resultsElements}>
                            <span className={styles.label}>Победы</span>
                            <span className={styles.value}>10</span>
                        </div>
                        <div className={styles.resultsElements}>
                            <span className={styles.label}>Игры</span>
                            <span className={styles.value}>40</span>
                        </div>
                        <div className={styles.resultsElements}>
                            <span className={styles.label}>Голы</span>
                            <span className={styles.value}>160</span>
                        </div>
                        <div className={styles.resultsElements}>
                            <span className={styles.label}>Турниры</span>
                            <span className={styles.value}>4</span>
                        </div>
                    </div>
                </div>
                <div className={styles.about}>
                    <div className={styles.title}>
                        <Calendar className={styles.icon} />
                        <span>Последние результаты</span>
                    </div>
                    <div className={styles.recentResults}>
                        <div className={styles.resultsItem}>
                            <span className={styles.time}>29.10.2026</span>
                            <div className={styles.matchInfo}>
                                <img 
                                    src={UrFUIK}
                                    className={styles.logo}
                                    alt='Логотип команды'
                                />
                                <span className={styles.score}>2:1</span>
                                <img 
                                    src={PolytechnicIK}
                                    className={styles.logo}
                                    alt='Логотип команды'
                                />
                            </div>
                        </div>
                        <div className={styles.devider} />
                        <div className={styles.resultsItem}>
                            <span className={styles.time}>30.10.2026</span>
                            <div className={styles.matchInfo}>
                                <img 
                                    src={UrFUIK}
                                    className={styles.logo}
                                    alt='Логотип команды'
                                />
                                <span className={styles.score}>5:6</span>
                                <img 
                                    src={PolytechnicIK}
                                    className={styles.logo}
                                    alt='Логотип команды'
                                />
                            </div>
                        </div>
                        <div className={styles.devider} />
                        <div className={styles.resultsItem}>
                            <span className={styles.time}>05.11.2026</span>
                            <div className={styles.matchInfo}>
                                <img 
                                    src={UrFUIK}
                                    className={styles.logo}
                                    alt='Логотип команды'
                                />
                                <span className={styles.score}>1:2</span>
                                <img 
                                    src={PolytechnicIK}
                                    className={styles.logo}
                                    alt='Логотип команды'
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div className={styles.rightColumn}>
                <div className={styles.title}>
                    <Flag />
                    <span>Лучшие бомбардиры</span>
                </div>
                <div className={styles.playersList}>
                    <div className={styles.playerItem}>
                        <div className={styles.avatar}></div>
                        <div className={styles.details}>
                            <h3 className={styles.name}>Петров Дмитрий</h3>
                            <span className={styles.meta}>№ 10 | Нападающий</span>
                        </div>
                        <div className={styles.stat}>
                            <span className={styles.statNumber}>7</span>
                            <span className={styles.statLabel}>Голов</span>
                        </div>
                    </div>
                    <div className={styles.playerItem}>
                        <div className={styles.avatar}></div>
                        <div className={styles.details}>
                            <h3 className={styles.name}>Смирнов Денис</h3>
                            <span className={styles.meta}>№ 11 | Полузащитник</span>
                        </div>
                        <div className={styles.stat}>
                            <span className={styles.statNumber}>6</span>
                            <span className={styles.statLabel}>Голов</span>
                        </div>
                    </div>
                    <div className={styles.playerItem}>
                        <div className={styles.avatar}></div>
                        <div className={styles.details}>
                            <h3 className={styles.name}>Петров Дмитрий</h3>
                            <span className={styles.meta}>№ 33 | Полузащитник</span>
                        </div>
                        <div className={styles.stat}>
                            <span className={styles.statNumber}>5</span>
                            <span className={styles.statLabel}>Голов</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default TeamStatistics;