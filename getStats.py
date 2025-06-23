from leagueManager import LeagueManager
import json
from collections import OrderedDict

# Constants
STAT_ORDER = ['R', 'HR', 'RBI', 'OBP', 'SB', 'K', 'W', 'SV', 'ERA', 'WHIP']
AVERAGE_STATS = {'OBP'}

def compute_team_stats():
    manager = LeagueManager(league_id=121531, year=2025)
    league = manager.get_league()

    max_period = league.currentMatchupPeriod
    team_stats = {}
    matchup_counts = {}

    for period in range(1, max_period + 1):
        box_scores = league.box_scores(matchup_period=period)

        for box in box_scores:
            for team_obj, stats in [(box.home_team, box.home_stats), (box.away_team, box.away_stats)]:
                if not team_obj or not stats:
                    continue

                team_name = team_obj.team_name
                if team_name not in team_stats:
                    team_stats[team_name] = {stat: 0 for stat in STAT_ORDER}
                    team_stats[team_name].update({'ER': 0, 'P_BB': 0, 'P_H': 0, 'OUTS': 0})
                    matchup_counts[team_name] = 0

                matchup_counts[team_name] += 1

                for stat, data in stats.items():
                    value = data['value']
                    if value is None:
                        continue
                    try:
                        value = float(value)
                    except (TypeError, ValueError):
                        print(f"⚠️ Skipping non-numeric stat '{stat}' with value: {value} for {team_name}")
                        continue

                    if stat in team_stats[team_name]:
                        team_stats[team_name][stat] += value
                    elif stat in {'ER', 'P_BB', 'P_H', 'OUTS'}:
                        team_stats[team_name][stat] += value

    # Format and normalize
    ordered_output = OrderedDict()
    for team, stats in sorted(team_stats.items()):
        count = matchup_counts[team]
        updated_stats = {}

        # Derived stats
        ip = stats['OUTS'] / 3 if stats['OUTS'] else 0
        era = round((stats['ER'] * 9 / ip), 3) if ip else 0
        whip = round(((stats['P_BB'] + stats['P_H']) / ip), 3) if ip else 0

        for stat in STAT_ORDER:
            if stat == 'ERA':
                updated_stats['ERA'] = era
            elif stat == 'WHIP':
                updated_stats['WHIP'] = whip
            elif stat in AVERAGE_STATS:
                updated_stats[stat] = round(stats[stat] / count, 3) if count else 0
            else:
                updated_stats[stat] = int(stats.get(stat, 0))

        ordered_output[team] = updated_stats

    return ordered_output


if __name__ == "__main__":
    final_stats = compute_team_stats()

    with open("team_stats.json", "w") as f:
        json.dump(final_stats, f, indent=4)

    print(json.dumps(final_stats, indent=4))
