import styles from './Search.module.scss'
import type { FC } from 'react';
import type { SearchProps } from './type';

import SearchIcon from "@shared/assets/icons/search.svg?react";

const Search: FC<SearchProps> = ({placeholder, className}) => {
  return (
    <div className={`${styles.search} ${className}`}>
      <input 
            type="text" 
            placeholder={placeholder} 
            className={styles.searchInput}
        />
        <SearchIcon className={styles.icon} />
    </div>
  )
}

export default Search;
