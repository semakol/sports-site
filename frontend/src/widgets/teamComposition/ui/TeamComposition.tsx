import styles from './TeamComposition.module.scss'

import CircleWarning from "@shared/assets/icons/CircleWarning.svg?react"

const mockPlayers = [
    { id: 1, name: 'Алексей Малыхин', position: 'Полузащитник', number: 18 },
    { id: 2, name: 'Иван Петров', position: 'Нападающий', number: 9 },
    { id: 3, name: 'Сергей Смирнов', position: 'Вратарь', number: 1 },
    { id: 4, name: 'Дмитрий Волков', position: 'Защитник', number: 4 },
    { id: 5, name: 'Никита Соколов', position: 'Полузащитник', number: 7 },
    { id: 6, name: 'Андрей Попов', position: 'Защитник', number: 2 },
    { id: 7, name: 'Максим Лебедев', position: 'Нападающий', number: 11 },
    { id: 8, name: 'Владимир Козлов', position: 'Полузащитник', number: 10 },
    { id: 9, name: 'Олег Новиков', position: 'Защитник', number: 5 },
    { id: 10, name: 'Павел Морозов', position: 'Вратарь', number: 12 },
    { id: 11, name: 'Роман Киселев', position: 'Полузащитник', number: 8 },
    { id: 12, name: 'Алексей Малыхин', position: 'Полузащитник', number: 18 },
];

const TeamComposition = () => {
    return (
        <div className={styles.teamComposition}>
            <div className={styles.title}>
                <CircleWarning />
                <span>Состав команды</span>
            </div>
            <div className={styles.grid}>
                {mockPlayers.map((player) => (
                    <div key={player.id} className={`${styles.playerCard}`}>
                        <div className={`${styles.imgCover}`} /> 
                        <div className={`${styles.content}`}>
                            <span className={styles.name}>{player.name}</span>
                            <span className={styles.role}>{player.position}</span>
                        </div>
                        <span className={styles.num}>{player.number}</span>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default TeamComposition;