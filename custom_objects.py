from discord.utils import get

import config

class PlayerObject(object):
    def __init__(self, info):
        self.id, self.name, self.mmr, self.team, self.logo = info

class TeamObject(object):
    def __init__(self, info):
        Team.id, Team.name, Team.abbrev, Team.p1, Team.p2, Team.p3, Team.p4, Team.p5, Team.mmr, Team.wins, Team.losses, Team.logo = info

        server = self.bot.get_guild(config.server_id)

        ids = [Team.p1, Team.p2, Team.p3, Team.p4, Team.p5]
        members = []

        ids = list(filter(ids, None))

        for id in ids:
            member = get(server.members, id=id)
            members.append(member)

        Team.roster = members
