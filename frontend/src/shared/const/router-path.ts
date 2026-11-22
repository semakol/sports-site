export const MAIN_ROUTE = "/";
export const TOURNAMENTS_ROUTE = "/tournaments";
export const MATCHES_ROUTE = {
    path: "/matches",
    children: {
        BY_DATES: "by-dates",
        BY_TOURNAMENTS: "by-tournaments"
    }
}
export const TEAMS_ROUTE = "/teams";
export const TEAM_ROUTE = {
    path: "/team",
    children: {
        STRUCTURE: "structure",
        TEAM_MATCHES: "team-matches"
    }
};
export const PLAYERS_ROUTE = "/players";