import os
import json
from dotenv import load_dotenv
from espn_api.baseball import League
from custom_box_score import H2HCategoryBoxScore
import statsapi

class LeagueManager:
    def __init__(self, league_id: int, year: int):
        load_dotenv()
        self.espn_s2 = os.getenv("ESPN_S2")
        self.swid = os.getenv("SWID")
        self.league_id = league_id
        self.year = year
        self._connect()

    def _connect(self):
        self.league = League(
            league_id=self.league_id,
            year=self.year,
            espn_s2=self.espn_s2,
            swid=self.swid
        )
        self._patch_box_score_class()

    def _patch_box_score_class(self):
        self.league._box_score_class = H2HCategoryBoxScore

    def get_league(self):
        return self.league

    def list_teams(self):
        for team in self.league.teams:
            print(f"{team.team_id}: {team.team_name}")

class FreeAgents:
    def __init__(self, league_manager: LeagueManager):
        self.league = league_manager.get_league()

    def get_free_agents(self):
        positions = {"OF": 5, "DH": 11, "SP": 14, "RP": 15, "IF": 19}
        agents = {}
        for pos, pid in positions.items():
            try:
                fa_pool = self.league.free_agents(size=100, position_id=pid)
                names = [str(p).replace("Player(", "").replace(")", "").strip() for p in fa_pool]
                agents[pos] = {
                    p["id"]: p["fullName"] for p in self.lookup_players(names) if "id" in p and "fullName" in p
                }
            except Exception as e:
                print(f"⚠️ Error fetching FA for {pos}: {e}")
        return agents

    @staticmethod
    def lookup_players(names):
        players = []
        for name in names:
            try:
                players.extend(statsapi.lookup_player(name))
            except Exception as e:
                print(f"⚠️ Lookup failed for '{name}': {e}")
        return players

if __name__ == "__main__":
    manager = LeagueManager(league_id=121531, year=2025)
    league = manager.get_league()
    manager.list_teams()

    with open("teams.json", "w") as f:
        json.dump({team.team_id: team.team_name for team in league.teams}, f, indent=4)
    print("✅ Saved teams.json")

    fa = FreeAgents(manager)
    free_agents = fa.get_free_agents()
    for pos, players in free_agents.items():
        print(f"{pos}: {list(players.values())[:5]}")
