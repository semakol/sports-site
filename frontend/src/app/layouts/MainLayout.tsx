import styles from './MainLayout.module.scss'
import { Outlet } from "react-router-dom";

import Header from "@widgets/header";
import Footer from "@widgets/footer";

const MainLayout = () => {
    return (
        <div className={styles.wrapper}>
            <Header />
            <main className={styles.container}>
                <Outlet />
            </main>
            <Footer />
        </div>
    )
}

export default MainLayout;