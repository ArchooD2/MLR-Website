from flask import request
from flask_restful import Resource, abort, fields, marshal
from .calculator import calculate_hitting_stats, calculate_pitching_stats
from .models import GameData, PlateAppearance, Player, TeamData

pa_resource_fields = {
    'paID': fields.Integer,
    'league': fields.String,
    'season': fields.Integer,
    'session': fields.Integer,
    'gameID': fields.Integer,
    'inning': fields.String,
    'inningID': fields.Integer,
    'playNumber': fields.Integer,
    'outs': fields.Integer,
    'obc': fields.Integer,
    'awayScore': fields.Integer,
    'homeScore': fields.Integer,
    'pitcherTeam': fields.String,
    'pitcherName': fields.String,
    'pitcherID': fields.Integer,
    'hitterTeam': fields.String,
    'hitterName': fields.String,
    'hitterID': fields.Integer,
    'pitch': fields.Integer,
    'swing': fields.Integer,
    'diff': fields.Integer,
    'exactResult': fields.String,
    'oldResult': fields.String,
    'resultAtNeutral': fields.String,
    'resultAllNeutral': fields.String,
    'rbi': fields.Integer,
    'run': fields.Boolean,
    'batterWPA': fields.String,
    'pitcherWPA': fields.String,
    'pr3B': fields.Integer,
    'pr2B': fields.Integer,
    'pr1B': fields.Integer,
    'prAB': fields.Integer
}
player_resource_fields = {
    'playerID': fields.Integer,
    'playerName': fields.String,
    'Team': fields.String,
    'batType': fields.String,
    'pitchType': fields.String,
    'pitchBonus': fields.String,
    'hand': fields.String,
    'priPos': fields.String,
    'secPos': fields.String,
    'tertPos': fields.String,
    'redditName': fields.String,
    'discordName': fields.String,
    'discordID': fields.Integer,
    'status': fields.Integer,
    'posValue': fields.Integer
}
game_resource_fields = {
    'league': fields.String,
    'season': fields.Integer,
    'session': fields.Integer,
    'gameID': fields.Integer,
    'sheetID': fields.String,
    'threadURL': fields.String,
    'umpires': fields.String,
    'awayTeam': fields.String,
    'homeTeam': fields.String,
    'awayScore': fields.Integer,
    'homeScore': fields.Integer,
    'inning': fields.String,
    'outs': fields.Integer,
    'obc': fields.Integer,
    'complete': fields.Boolean,
    'winningPitcher': fields.Integer,
    'losingPitcher': fields.Integer,
    'save': fields.Integer,
    'potg': fields.Integer
}
team_resource_fields = {
    'name': fields.String,
    'abb': fields.String,
    'color': fields.String,
    'logo_url': fields.String,
    'league': fields.String,
    'division': fields.String,
    'gm': fields.Integer,
    'cogm': fields.Integer,
    'captain1': fields.Integer,
    'captain2': fields.Integer,
    'captain3': fields.Integer,
    'affiliate': fields.String
}

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


def integer_arg(name, default=None):
    value = request.args.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        abort(400, message=f'{name} must be an integer')


def pagination_args():
    page = max(integer_arg('page', 1), 1)
    per_page = integer_arg('per_page', DEFAULT_PAGE_SIZE)
    if per_page < 1 or per_page > MAX_PAGE_SIZE:
        abort(400, message=f'per_page must be between 1 and {MAX_PAGE_SIZE}')
    return page, per_page


def paginate(query, resource_fields):
    page, per_page = pagination_args()
    total = query.order_by(None).count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return {
        'items': marshal(items, resource_fields),
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    }


def plate_appearance_query():
    query = PlateAppearance.query
    filters = {
        'league': request.args.get('league'),
        'season': integer_arg('season'),
        'session': integer_arg('session'),
        'gameID': integer_arg('game_id'),
        'pitcherID': integer_arg('pitcher_id'),
        'hitterID': integer_arg('hitter_id'),
    }
    return query.filter_by(**{key: value for key, value in filters.items() if value is not None})


class PitcherData(Resource):
    def get(self, league, player_id):
        query = PlateAppearance.query.filter_by(pitcherID=player_id, league=league)
        return paginate(query.order_by(PlateAppearance.season, PlateAppearance.paID), pa_resource_fields)


class HitterData(Resource):
    def get(self, league, player_id):
        query = PlateAppearance.query.filter_by(hitterID=player_id, league=league)
        return paginate(query.order_by(PlateAppearance.season, PlateAppearance.paID), pa_resource_fields)


class AllPlateAppearances(Resource):
    def get(self):
        return paginate(plate_appearance_query().order_by(PlateAppearance.paID), pa_resource_fields)


class PlateAppearnacesByLeague(Resource):
    def get(self, league):
        query = PlateAppearance.query.filter_by(league=league)
        return paginate(query.order_by(PlateAppearance.season, PlateAppearance.paID), pa_resource_fields)

class PlateAppearancesByGame(Resource):
    def get(self, league, game_id):
        query = (
            PlateAppearance.query
            .filter_by(
                league=league,
                gameID=game_id
            )
            .order_by(
                PlateAppearance.inningID,
                PlateAppearance.playNumber,
                PlateAppearance.paID
            )
        )
        return paginate(query, pa_resource_fields)

class AllPlayers(Resource):
    def get(self):
        query = Player.query
        name = request.args.get('name')
        team = request.args.get('team')
        if name:
            query = query.filter(Player.playerName.ilike(f'%{name}%'))
        if team:
            query = query.filter_by(Team=team)
        return paginate(query.order_by(Player.playerName, Player.playerID), player_resource_fields)


class PlayerID(Resource):
    def get(self, playerID):
        player = Player.query.filter_by(playerID=playerID).first()
        if player is None:
            abort(404, message='Player not found')
        return marshal(player, player_resource_fields)


class PlayerName(Resource):
    def get(self, player_name):
        player = Player.query.filter_by(playerName=player_name).first()
        if player is None:
            abort(404, message='Player not found')
        return marshal(player, player_resource_fields)


class Games(Resource):
    def get(self):
        query = GameData.query
        league = request.args.get('league')
        season = integer_arg('season')
        session = integer_arg('session')
        if league:
            query = query.filter_by(league=league)
        if season is not None:
            query = query.filter_by(season=season)
        if session is not None:
            query = query.filter_by(session=session)
        return paginate(query.order_by(GameData.season.desc(), GameData.session.desc(), GameData.gameID.desc()), game_resource_fields)


class GameByID(Resource):
    def get(self, league, game_id):
        game = GameData.query.filter_by(league=league, gameID=game_id).first()
        if game is None:
            abort(404, message='Game not found')
        return marshal(game, game_resource_fields)


class GamesByLeague(Games):
    def get(self, league):
        query = GameData.query.filter_by(league=league)
        return paginate(query.order_by(GameData.season.desc(), GameData.session.desc(), GameData.gameID.desc()), game_resource_fields)


class Teams(Resource):
    def get(self):
        query = TeamData.query
        league = request.args.get('league')
        division = request.args.get('division')
        if league:
            query = query.filter_by(league=league)
        if division:
            query = query.filter_by(division=division)
        return paginate(query.order_by(TeamData.name, TeamData.abb), team_resource_fields)


class TeamByAbbreviation(Resource):
    def get(self, team_abb):
        team = TeamData.query.filter_by(abb=team_abb).first()
        if team is None:
            abort(404, message='Team not found')
        return marshal(team, team_resource_fields)


class PlayerGames(Resource):
    def get(self, player_id):
        game_ids = PlateAppearance.query.with_entities(PlateAppearance.league, PlateAppearance.gameID).filter(
            (PlateAppearance.hitterID == player_id) | (PlateAppearance.pitcherID == player_id)
        ).distinct().subquery()
        query = GameData.query.join(
            game_ids,
            (GameData.league == game_ids.c.league) & (GameData.gameID == game_ids.c.gameID)
        )
        return paginate(query.order_by(GameData.season.desc(), GameData.session.desc(), GameData.gameID.desc()), game_resource_fields)


class PlayerSearch(Resource):
    def get(self):
        search = request.args.get('q', '').strip()
        if not search:
            abort(400, message='q is required')
        query = Player.query.filter(Player.playerName.ilike(f'%{search}%'))
        return paginate(query.order_by(Player.playerName, Player.playerID), player_resource_fields)


class PlayerStats(Resource):
    def get(self, player_id):
        player = Player.query.filter_by(playerID=player_id).first()
        if player is None:
            abort(404, message='Player not found')
        filters = {'season': integer_arg('season'), 'session': integer_arg('session'), 'league': request.args.get('league')}
        common_filters = {key: value for key, value in filters.items() if value is not None}
        batting = PlateAppearance.query.filter_by(hitterID=player_id, **common_filters).order_by(PlateAppearance.paID).all()
        pitching = PlateAppearance.query.filter_by(pitcherID=player_id, **common_filters).order_by(PlateAppearance.paID).all()
        return {
            'player': marshal(player, player_resource_fields),
            'filters': common_filters,
            'batting': calculate_hitting_stats(batting),
            'pitching': calculate_pitching_stats(pitching)
        }


class Standings(Resource):
    def get(self):
        league = request.args.get('league')
        season = integer_arg('season')
        query = GameData.query.filter(GameData.awayScore.isnot(None), GameData.homeScore.isnot(None))
        if league:
            query = query.filter_by(league=league)
        if season is not None:
            query = query.filter_by(season=season)
        records = {}
        for game in query.all():
            for team in (game.awayTeam, game.homeTeam):
                if team:
                    records.setdefault(team, {'team': team, 'wins': 0, 'losses': 0, 'ties': 0, 'runs_for': 0, 'runs_against': 0})
            if game.awayTeam and game.homeTeam:
                away = records[game.awayTeam]
                home = records[game.homeTeam]
                away['runs_for'] += game.awayScore
                away['runs_against'] += game.homeScore
                home['runs_for'] += game.homeScore
                home['runs_against'] += game.awayScore
                if game.awayScore > game.homeScore:
                    away['wins'] += 1
                    home['losses'] += 1
                elif game.homeScore > game.awayScore:
                    home['wins'] += 1
                    away['losses'] += 1
                else:
                    away['ties'] += 1
                    home['ties'] += 1
        standings = list(records.values())
        for row in standings:
            row['games'] = row['wins'] + row['losses'] + row['ties']
            row['run_diff'] = row['runs_for'] - row['runs_against']
        standings.sort(key=lambda row: (-row['wins'], row['losses'], -row['run_diff'], row['team']))
        return {'league': league, 'season': season, 'standings': standings}


class Health(Resource):
    def get(self):
        return {'status': 'ok'}


def add_resources(api):
    api.add_resource(PitcherData, '/api/plateappearances/pitching/<string:league>/<int:player_id>')
    api.add_resource(HitterData, '/api/plateappearances/batting/<string:league>/<int:player_id>')
    api.add_resource(AllPlateAppearances, '/api/plateappearances')
    api.add_resource(PlateAppearancesByGame, '/api/plateappearances/game/<string:league>/<int:game_id>')
    api.add_resource(PlateAppearnacesByLeague, '/api/plateappearances/<string:league>')
    api.add_resource(AllPlayers, '/api/players')
    api.add_resource(PlayerID, '/api/players/id/<int:playerID>')
    api.add_resource(PlayerName, '/api/players/name/<string:player_name>')
    api.add_resource(Games, '/api/games')
    api.add_resource(GameByID, '/api/games/<string:league>/<int:game_id>')
    api.add_resource(GamesByLeague, '/api/games/<string:league>')
    api.add_resource(Teams, '/api/teams')
    api.add_resource(TeamByAbbreviation, '/api/teams/<string:team_abb>')
    api.add_resource(PlayerGames, '/api/players/id/<int:player_id>/games')
    api.add_resource(PlayerSearch, '/api/players/search')
    api.add_resource(PlayerStats, '/api/players/id/<int:player_id>/stats')
    api.add_resource(Standings, '/api/standings')
    api.add_resource(Health, '/api/health')
