from dataclasses import dataclass
from typing import List

SORT_DICT = {
    "Player": lambda x: x.name,
    "Team": lambda x: x.team,
    "K": lambda x: x.kills,
    "D": lambda x: x.deaths,
    "A": lambda x: x.assists,
    "ACC": lambda x: x.acc,
    "HS": lambda x: x.hs,
    "ADR": lambda x: x.adr,
    "UD": lambda x: x.ud,
    "KAST": lambda x: x.kast,
    "RAT": lambda x: x.rat2_0
}
COUNTER_TERRORIST = "CT"
TERRORIST = "T"
PERCENT = 100
INVALID_STEAM_ID = 0
GRENADES = ["Molotov", "Smoke Grenade", "HE Grenade", "Incendiary Grenade", "Flashbang", "Decoy Grenade"]


@dataclass
class WeaponFire:
    player_team: str
    player_name: str
    weapon: str

    @classmethod
    def from_data(cls, data: dict) -> "WeaponFire":
        return WeaponFire(
            player_name=data["playerName"],
            player_team=data["playerTeam"],
            weapon=data["weapon"]
        )

    @classmethod
    def is_grenade(cls, weapon: str):
        return weapon in GRENADES


@dataclass
class Kill:
    attacker_team: str
    attacker_name: str
    attacker_side: str
    victim_team: str
    victim_name: str
    victim_side: str
    assister_name: str
    suicide: bool
    headshot: bool
    is_trade: bool
    player_traded_name: str

    @classmethod
    def from_data(cls, data: dict) -> "Kill":
        return Kill(
            attacker_team=data["attackerTeam"],
            attacker_name=data["attackerName"],
            attacker_side=data["attackerSide"],
            victim_team=data["victimTeam"],
            victim_name=data["victimName"],
            victim_side=data["victimSide"],
            assister_name=data["assisterName"],
            suicide=data["isSuicide"],
            headshot=data["isHeadshot"],
            is_trade=data["isTrade"],
            player_traded_name=data["playerTradedName"],
        )


@dataclass
class Damage:
    friendly_fire: bool
    hp_damage_taken: int
    weapon: str
    attacker_name: str
    victim_name: str

    @classmethod
    def from_data(cls, data: dict) -> "Damage":
        return Damage(
            attacker_name=data["attackerName"],
            victim_name=data["victimName"],
            weapon=data["weapon"],
            hp_damage_taken=data["hpDamageTaken"],
            friendly_fire=data["isFriendlyFire"]
        )


@dataclass
class Round:
    num: int
    is_warmup: bool
    t_score: int
    ct_score: int
    winner_team: str
    winner_side: str
    loser_team: str
    kills: List[Kill]
    damages: List[Damage]
    weapon_fires: List[WeaponFire]

    @classmethod
    def from_data(cls, data: dict) -> "Round":
        kills = [Kill.from_data(it) for it in data["kills"]]
        damages = [Damage.from_data(it) for it in data["damages"]]
        weapon_fires = [WeaponFire.from_data(it) for it in data["weaponFires"]]
        return Round(
            num=data["roundNum"],
            is_warmup=data["isWarmup"],
            t_score=data["tScore"],
            ct_score=data["ctScore"],
            winner_team=data["winningTeam"],
            winner_side=data["winningSide"],
            loser_team=data["losingTeam"],
            kills=kills,
            damages=damages,
            weapon_fires=weapon_fires
        )


@dataclass
class Player:
    name: str
    team: str

    @classmethod
    def from_data(cls, name: str, rounds: List[Round]) -> "Player":
        team = cls.get_player_team(rounds, name)
        return Player(
            name=name,
            team=team
        )

    @staticmethod
    def get_player_team(rounds: List[Round], name: str):
        for game_round in rounds:
            kills = game_round.kills
            for kill in kills:
                if kill.attacker_name == name:
                    return kill.attacker_team
                if kill.victim_name == name:
                    return kill.victim_team


@dataclass
class Statistics:
    name: str
    team: str
    kills: int
    deaths: int
    assists: int
    acc: float
    hs: float
    adr: float
    ud: int
    kast: float
    rat2_0: float

    @classmethod
    def from_data(cls, name: str, rounds: List[Round]) -> "Statistics":
        rounds_count = len(rounds)
        kills, deaths, assists = cls.get_player_kda(rounds, name)
        acc = cls.get_player_acc(rounds, name)
        hs = cls.get_player_hs(rounds, name, kills)
        adr = cls.get_player_adr(rounds, name)
        ud = cls.get_player_ud(rounds, name)
        kast_count = cls.get_player_kast(rounds, name)
        kast = kast_count / rounds_count * PERCENT
        rat2_0 = cls.get_player_rat2_0(kast_count, kills, deaths, assists, adr, len(rounds))
        team = Player.get_player_team(rounds, name)
        return Statistics(
            name=name,
            team=team,
            kills=kills,
            deaths=deaths,
            assists=assists,
            acc=round(acc, 2),
            hs=round(hs, 2),
            adr=round(adr, 2),
            ud=ud,
            kast=round(kast, 2),
            rat2_0=round(rat2_0, 2)
        )

    @staticmethod
    def get_player_kda(rounds: List[Round], name: str):
        count_kills = 0
        count_deaths = 0
        count_assists = 0
        for game_round in rounds:
            kills = game_round.kills
            for kill in kills:
                if kill.suicide and kill.attacker_name == name:
                    count_kills -= 1
                    count_deaths += 1
                elif kill.attacker_name == name:
                    count_kills += 1
                elif kill.victim_name == name:
                    count_deaths += 1
                if kill.assister_name == name:
                    count_assists += 1
        return count_kills, count_deaths, count_assists

    @staticmethod
    def get_player_hs(rounds: List[Round], name: str, kills: int) -> float:
        if kills == 0:
            return 0
        hs_count = 0
        for game_round in rounds:
            headshots = list(filter(lambda kill: kill.attacker_name == name and kill.headshot, game_round.kills))
            hs_count += len(headshots)
        percent_hs = hs_count / kills * PERCENT
        return percent_hs

    @staticmethod
    def get_player_acc(rounds: List[Round], name: str):
        hits_count = 0
        fires_count = 0
        for game_round in rounds:
            hits = list(filter(lambda damage: damage.attacker_name == name, game_round.damages))
            fires = list(
                filter(lambda fire: fire.player_name == name and not WeaponFire.is_grenade(fire.weapon),
                       game_round.weapon_fires))
            hits_count += len(hits)
            fires_count += len(fires)
        return hits_count / fires_count * PERCENT if fires_count != 0 else 0

    @staticmethod
    def get_player_adr(rounds: List[Round], name: str) -> float:
        damage_count = 0
        rounds_count = len(rounds)
        for game_round in rounds:
            damages = game_round.damages
            for damage in damages:
                if damage.attacker_name == name:
                    damage_count += damage.hp_damage_taken
        return damage_count / rounds_count

    @staticmethod
    def get_player_ud(rounds: List[Round], name: str) -> int:
        damage_count = 0
        for game_round in rounds:
            damages = game_round.damages
            for damage in damages:
                if damage.attacker_name == name and WeaponFire.is_grenade(damage.weapon):
                    damage_count += damage.hp_damage_taken
        return damage_count

    @staticmethod
    def get_player_kast(rounds: List[Round], name: str) -> float:
        kast_count = 0
        for game_round in rounds:
            useful = False
            survive = True
            trade_after_death = False
            for kill in game_round.kills:
                if kill.attacker_name == name or kill.assister_name == name:
                    useful = True
                elif kill.victim_name == name:
                    survive = False
                elif kill.player_traded_name == name:
                    trade_after_death = True
            if useful or survive or trade_after_death:
                kast_count += 1
        return kast_count

    @staticmethod
    def get_player_rat2_0(kast_count: float, kills: int, deaths: int, assists: int, adr: float, count_of_rounds: int):
        kpr = kills / count_of_rounds
        dpr = deaths / count_of_rounds
        apr = assists / count_of_rounds
        impact = 2.13 * kpr + 0.42 * apr - 0.41
        rat2_0 = 0.0073 * kast_count + 0.3591 * kpr - 0.5329 * dpr + 0.2372 * impact + 0.0032 * adr + 0.1587
        return rat2_0


@dataclass
class Match:
    match_id: str
    map_name: str
    team_a: list
    team_b: list
    rounds: List[Round]
    max_rounds: int
    nicknames: list

    @classmethod
    def from_data(cls, data: dict, fix_rounds: bool = True) -> "Match":
        rounds = cls.fix_rounds([Round.from_data(it) for it in data["gameRounds"]])
        nicknames = list(cls.get_players_nicknames(data))
        max_rounds = data["serverVars"]["maxRounds"]
        team_a, team_b = cls.get_match_score(rounds, max_rounds / 2)
        return Match(
            match_id=data["matchID"],
            map_name=data["mapName"],
            rounds=rounds if not fix_rounds else cls.fix_rounds(rounds),
            team_a=team_a,
            team_b=team_b,
            max_rounds=max_rounds,
            nicknames=nicknames
        )

    @staticmethod
    def get_players_nicknames(data: dict):
        steam_ids = set()
        player_connections = data["playerConnections"]
        for player_connection in player_connections:
            steam_id = player_connection["steamID"]
            if steam_id != INVALID_STEAM_ID:
                steam_ids.add(steam_id)
        player_count = len(steam_ids)
        nicknames = set()
        game_rounds = data["gameRounds"]
        for game_round in game_rounds:
            kills = game_round["kills"]
            for kill in kills:
                attacker = kill["attackerName"]
                victim = kill["victimName"]
                nicknames.add(attacker)
                nicknames.add(victim)
                if len(nicknames) == player_count:
                    return nicknames

    @staticmethod
    def _game_start_index(rounds: List[Round]):
        for index, it in enumerate(reversed(rounds)):
            if it.t_score == 0 and it.ct_score == 0:
                return len(rounds) - index - 1

    @classmethod
    def fix_rounds(cls, rounds: List[Round]) -> List[Round]:
        start_index = cls._game_start_index(rounds)
        start_number = rounds[start_index].num - 1
        result = rounds[start_index:]
        for it in result:
            it.num -= start_number
        return list(it for it in result if it.winner_team is not None)

    @staticmethod
    def get_match_score(rounds: List[Round], half_score: int):
        first_half = half_score
        score_team_a = 0
        score_team_b = 0
        first_half_score_team_a = 0
        first_half_score_team_b = 0
        game_round = []
        for game_round in rounds:
            sum_score = score_team_a + score_team_b
            if sum_score == first_half:
                first_half_score_team_a = score_team_a
                first_half_score_team_b = score_team_b
            if sum_score < first_half:
                if game_round.winner_side == COUNTER_TERRORIST:
                    score_team_a += 1
                else:
                    score_team_b += 1
            elif sum_score < first_half * 2:
                if game_round.winner_side == TERRORIST:
                    score_team_a += 1
                else:
                    score_team_b += 1
        second_half_score_team_a = score_team_a - first_half_score_team_a
        second_half_score_team_b = score_team_b - first_half_score_team_b
        team_a_info = [score_team_a, first_half_score_team_a, second_half_score_team_a]
        team_b_info = [score_team_b, first_half_score_team_b, second_half_score_team_b]
        if score_team_a > score_team_b:
            team_a_info.append(game_round.winner_team)
            team_b_info.append(game_round.loser_team)
        else:
            team_a_info.append(game_round.loser_team)
            team_b_info.append(game_round.winner_team)
        return team_a_info, team_b_info


@dataclass
class MapStatistics:
    stats: List[Statistics]
    match_id: str
    map_name: str
    team_a: list
    team_b: list
    max_rounds: int

    @classmethod
    def from_data(cls, data: dict, sort: str):
        match_info = Match.from_data(data)
        rounds = match_info.rounds
        nicknames = match_info.nicknames
        stats = [Statistics.from_data(it, rounds) for it in nicknames]
        if sort in SORT_DICT:
            stats = reversed(sorted(stats, key=SORT_DICT[sort]))
        return MapStatistics(
            stats=stats,
            match_id=match_info.match_id,
            team_a=match_info.team_a,
            team_b=match_info.team_b,
            max_rounds=match_info.max_rounds,
            map_name=match_info.map_name
        )

    def print_statistics(self):
        filling = len(self.team_a[3]) - 4
        print(f"Match: {self.match_id}      MAP: {self.map_name}")
        print(f"Teams:       {self.team_a[3]} : {self.team_b[3]}")
        print("First half:    {f}{w:2d} : {l:d}".format(f=" " * filling, w=self.team_a[1], l=self.team_b[1]))
        print("Second half:   {f}{w:2d} : {l:d}".format(f=" " * filling, w=self.team_a[2], l=self.team_b[2]))
        print("Final score:   {f}{w:2d} : {l:d}".format(f=" " * filling, w=self.team_a[0], l=self.team_b[0]))
        print("-" * 100)
        print("%12s  %10s  %9s  %3s  %3s  %7s  %6s  %6s  %5s  %7s  %7s" %
              ("Player", "Team", "K", "D", "A", "ACC%", "HS%", "ADR", "UD", "KAST%", "Rat2.0"))
        print("-" * 100)
        for player in self.stats:
            print("%12s  %16s  %3d  %3d  %3d  %7.2f  %7.2f  %6.2f  %5d  %6.2f  %6.2f" %
                  (player.name, player.team, player.kills, player.deaths, player.assists, player.acc,
                   player.hs, player.adr, player.ud, player.kast, player.rat2_0))
