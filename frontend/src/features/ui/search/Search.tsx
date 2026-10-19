import styles from './Search.module.scss'

import SearchIcon from "@shared/assets/icons/search.svg?react";

const Search = () => {
  return (
    <div className={styles.search}>
      <input 
            type="text" 
            placeholder="Найти турнир, команду, игрока..." 
            className={styles.searchInput}
        />
        <SearchIcon />
    </div>
  )
}

export default Search;
