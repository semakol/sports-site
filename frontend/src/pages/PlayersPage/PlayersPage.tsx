import styles from './PlayersPage.module.scss'
import PlayersHeroSection from "@widgets/playersHeroSection"
import UrFUIK from "@shared/assets/images/UrFUIK.png"
import PlayerCard from "@entities/playerCard"

const MOCK_PLAYERS = [
    {
        id: 1,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    },
    {
        id: 2,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    },
    {
        id: 3,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    },
    {
        id: 4,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    },
    {
        id: 5,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    },
    {
        id: 6,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    },
    {
        id: 7,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    },
    {
        id: 8,
        name: 'Алексей Малыхин',
        role: 'Полузащитник',
        num: '18',
        team: 'УрФУ',
        logo: UrFUIK
    }
];

const PlayersPage = () => {
  return (
    <div className={styles.playersPage}>
      <PlayersHeroSection />
      <div className={styles.grid}>
            {MOCK_PLAYERS.map((player) => (
                <PlayerCard 
                  key={player.id}
                  {...player} 
                />
            ))}
        </div>
    </div>
  )
}

export default PlayersPage;
