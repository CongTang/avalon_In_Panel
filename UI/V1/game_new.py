"""
Setup game environment for Avalon with specific requirements and to support multi players.
This version is built on previous beta version.

Change Log:
2023-04-13 ~ V1.0
- Pre-generate game messages and allow player to load the message based on game progress
- Handle user inputs during game
- Allow computer players to join the game
- Add server handle to overview game parameter during the game
- Add help messages for players to check the updated game info
- Add log file features
"""
import inspect
import pprint
import random
import re
import copy
from prettytable import PrettyTable


def display_user_label(nickname, target):
    if target == nickname:
        return target + '(You)'
    return target


class Avalon:
    def __init__(self,
                 nicknames,
                 has_percival=False,
                 has_morgana=False,
                 has_mordred=False,
                 has_oberon=False,
                 has_lake_lady=False,
                 n_ai=None):
        self.stages = ['init', 'proposal', 'vote', 'quest', 'record', 'end']
        self.vote_cards = ['approve', 'reject']
        self.quest_cards = ['success', 'fail']
        self.good_character_cards = ['merlin', 'percival', 'loyal servant']
        self.evil_character_cards = ['assassin', 'mordred', 'morgana', 'oberon', 'minion']
        self.game_record_keys = ['quest',
                                 'round',
                                 'leader',
                                 'members',
                                 'lake_lady',
                                 'lake_lady_target',
                                 'votes',
                                 'n_approve',
                                 'vote_result',
                                 'attempts',
                                 'n_fail',
                                 'quest_result']
        self.end_game = None
        self.human_nicknames = nicknames
        self.nicknames = nicknames
        self.ai_nicknames = []
        if n_ai:
            dummy_names = ['Allan', 'Bob', 'Curtis', 'Danny', 'Evan', 'Frank', 'Gibson', 'Harry', 'Issac', 'Jake']
            self.ai_nicknames = random.sample([n for n in dummy_names if n not in self.nicknames], n_ai)
            self.nicknames = self.nicknames + self.ai_nicknames
        self.n_players = len(self.nicknames)
        self.has_percival = has_percival
        self.has_morgana = has_morgana
        self.has_mordred = has_mordred
        self.has_oberon = has_oberon
        self.has_lake_lady = has_lake_lady
        if self.has_lake_lady:
            self.stages.insert(1, 'lake_lady')
        self.n_good, self.n_evil = self.get_n_sides()
        self.validate_setting()
        self.quests = self.get_quests()
        self.need_2_fail_cards = self.get_need_2_fail_cards()
        self.characters, self.good_characters, self.evil_characters = self.get_characters()
        self.p_positions = self.get_p_positions()
        self.players_info = self.get_players_info()
        self.game_param = self.init_game_param()
        self.game_param_copy = copy.deepcopy(self.game_param)
        self.game_records = {1: []}
        self.msg_packs = self.gen_msg_packs()
        open('../log/log', 'w').close()

    def validate_setting(self):
        if self.n_players not in range(5, 11):
            raise Exception('Have to be 5 to 10 players!')

        if len(self.nicknames) != len(set(self.nicknames)):
            raise Exception('All nicknames must be unique!')

        if self.has_mordred + self.has_oberon + self.has_morgana + 1 > self.n_evil:
            raise Exception('Too many evil characters!')

    def get_n_sides(self):
        """
        To determine the number of good and evil side by following the table below:

        +------+-----+-----+-----+-----+-----+------+
        |Player|  5  |  6  |  7  |  8  |  9  |  10  |
        +------+-----+-----+-----+-----+-----+------+
        | Good |  3  |  4  |  4  |  5  |  6  |  6   |
        +------+-----+-----+-----+-----+-----+------+
        | Bad  |  2  |  2  |  3  |  3  |  3  |  4   |
        +------+-----+-----+-----+-----+-----+------+

        PS: Hardcode this part might be running quicker though
        """
        if self.n_players == 9:
            n_good = 6
        else:
            n_good = int(self.n_players / 2) + 1

        n_evil = self.n_players - n_good
        return n_good, n_evil

    def get_quests(self):
        """
        To determine the number of players to be assigned to do the quest(s) by
        following the table below:

        +-----------+-----+-----+-----+-----+-----+------+
        |   Player  |  5  |  6  |  7  |  8  |  9  |  10  |
        +-----------+-----+-----+-----+-----+-----+------+
        | 1st Quest |  2  |  2  |  2  |  3  |  3  |  3   |
        +-----------+-----+-----+-----+-----+-----+------+
        | 2nd Quest |  3  |  3  |  3  |  4  |  4  |  4   |
        +-----------+-----+-----+-----+-----+-----+------+
        | 3rd Quest |  2  |  4  |  3  |  4  |  4  |  4   |
        +-----------+-----+-----+-----+-----+-----+------+
        | 4th Quest |  3  |  3  |  4* |  5* |  5* |  5*  |
        +-----------+-----+-----+-----+-----+-----+------+
        | 5th Quest |  3  |  4  |  4  |  5  |  5  |  5   |
        +-----------+-----+-----+-----+-----+-----+------+

        * Note that the 4th quest (and only the 4th quest) in games of 7 or more
        players require at least two failed cards to be failed quest.
        """
        quests = []
        if self.n_players == 5:
            quests = [2, 3, 2, 3, 3]

        elif self.n_players == 6:
            quests = [2, 3, 4, 3, 4]

        elif self.n_players == 7:
            quests = [2, 3, 3, 4, 4]

        elif self.n_players in [8, 9, 10]:
            quests = [3, 4, 4, 5, 5]

        return quests

    def get_need_2_fail_cards(self):
        """
        Flag for indicating if the game contains 2 fail cards quest
        """
        if self.n_players > 6:
            return True
        else:
            return False

    def get_characters(self):
        """
        To get a list of characters that would be played in the game based on the game setting.
        It also creates lists for good and evil characters separately.
        If there is more spaces for good/evil characters, normal character 'loyal servant'/'minion' would be filled
        in the lists.
        """

        # Default special characters for each sides
        good_characters = ['merlin']
        evil_characters = ['assassin']

        # More special characters based on game setting
        if self.has_percival:
            good_characters.append('percival')
        if self.has_morgana:
            evil_characters.append('morgana')
        if self.has_mordred:
            evil_characters.append('mordred')
        if self.has_oberon:
            evil_characters.append('oberon')

        # Compare the n of good/evil characters in lists with the n of required good/evil players.
        # If less than the required number, add the normal good/evil characters accordingly to corresponding list.
        while len(good_characters) < self.n_good:
            good_characters.append('loyal servant')

        while len(evil_characters) < self.n_evil:
            evil_characters.append('minion')

        characters = good_characters + evil_characters

        return characters, good_characters, evil_characters

    def get_character_side(self, character):
        if character in self.good_characters:
            return 'good'
        else:
            return 'evil'

    def get_p_positions(self):
        """
        To randomly assign the position of the players. This list still contains all players' nicknames but with
        positional sequence.
        First player of this list will be the initial leader.
        Last player of this list will be the first lady of the lake, if applicable.
        """
        p_position = self.nicknames.copy()
        random.shuffle(p_position)

        return p_position

    def get_players_info(self):
        """
        To generate the players information for this game. Including assigning the character for each player,
        and generating knowledge of players based on their characters.

        All information will be store as dict format. Reference example as shown below:

        {
            'koh': {
                'character': 'merlin',
                'side': 'good',
                'position': 3,
                'knowledge': {
                    'nong': 'good',
                    'victor': 'good',
                    ...
                }
            },
            ...
        }

        To generate the knowledge of the character. There are total 4 status which are
        "good", "evil", "unknown" and "either", where "either" status is specifically
        for character card "percival" which happens to know either morgana/merlin but
        without knowing their identity.

        This knowledge is for the player to refer, where is to replace the 'Everyone
        close your eyes and extend your hand info a fist in front of you' at the beginning
        of the game.

        The game logic for related characters regarding their knowledge are:

        *merlin* normally knows everyone on evil side (which also means he knows
        everyone on good side), except *mordred*. Therefore if *mordred* is included
        in the game, *merlin* could only know [n_evil_players - 1] players are 'evil',
        then the rest (n_good_players + 1) will be 'unknown' as *mordred* is hiding among
        them. Without *mordred* involves in the game, there is no 'unknown' knowledge
        for *merlin*.

        *percival* only knows either *merlin*/*morgana* could be *merlin*, but he doesn't
        know who is who. Therefore, his knowledge shows 'either' on the players who hold
        *merlin*/*morgana* card, and remains 'unknown' to the rest of the players.

        *oberon* doesn't know who are on evil side, he also doesn't reveal to evil players.
        Only *merlin* know he is from evil side. Therefore, if *oberon* involves, evil
        players know (n_evil_players - 1) are evil, and the rest (n_good_players + 1) will
        be 'unknown' as *oberon* is among them. And oberon has no knowledge (all 'unknown').

        All evil players knows each other who are from evil side (except *oberon*).

        All good players (except *merlin* and *percival*) have no knowledge (all 'unknown').
        """

        # Shuffle the characters list, combine with the positional nicknames list to form the dict
        random.shuffle(self.characters)
        players_info = {
            nickname: {
                'character': character,
                'side': self.get_character_side(character),
                'position': position
            }
            for position, nickname, character in zip([i for i in range(self.n_players)],
                                                     self.p_positions,
                                                     self.characters)
        }

        # Iterate the nicknames to define target's character and side
        # Example: if the target's character is Merlin, means all players' side will be revealed in his knowledge,
        # providing Mordred is not included in the game
        for nickname in self.nicknames:
            target_character = players_info[nickname]['character']
            target_side = players_info[nickname]['side']
            knowledge = {}

            for key, info in players_info.items():
                if target_side == 'good':
                    if target_character == 'merlin':
                        # if *mordred* involves, all good players + *mordred* are unknown to *merlin*
                        # Otherwise *merlin* knows everyone's side.
                        if self.has_mordred:
                            if info['character'] == 'mordred' or info['side'] == 'good':
                                knowledge[key] = 'unknown'
                            else:
                                knowledge[key] = info['side']
                        else:
                            knowledge[key] = info['side']

                    # *percival* only has knowledge on either *merlin*/*morgana*
                    # The rest of player's side remain unknown to him.
                    elif target_character == 'percival':
                        if info['character'] in ['merlin', 'morgana']:
                            if self.has_morgana:
                                knowledge[key] = 'either'
                            else:
                                knowledge[key] = info['side']
                        else:
                            knowledge[key] = 'unknown'
                    # all normal good players have no knowledge
                    else:
                        knowledge[key] = 'unknown'

                else:
                    if self.has_oberon:
                        # If *oberon* involves, the player who plays as oberon doesn't have any knowledge
                        # so everyone is unknown to him
                        if target_character == 'oberon':
                            knowledge[key] = 'unknown'
                        # For the rest of evil players, (n_good_players + 1) now are unknown to them as
                        # *oberon* is among them.
                        else:
                            if info['character'] == 'oberon' or info['side'] == 'good':
                                knowledge[key] = 'unknown'
                            # They still know other evil players who are not *oberon*
                            else:
                                knowledge[key] = info['side']
                    # If no *oberon*, evil players know everyone's side
                    else:
                        knowledge[key] = info['side']
                players_info[nickname]['knowledge'] = knowledge

        return players_info

    def init_game_param(self):
        """
        To initiate the value of all game parameters.
        game_param stores all the information of the game, it is for all players, and also the server to determine
        the progress of the game.
        It is also used to determine which game message should be displayed to players.
        """

        game_param = {
            'quest': 1,  # current quest
            'round': 1,  # current round
            'stage': self.stages[0],  # current stage
            'n_members': self.quests[0],  # n of members that is required for completing the quest
            'leader': self.p_positions[0],  # initial leader, first player from the position list
            'members': [],  # players that are selected by leader for quest
            'done_proposal': None,  # indicator for proposal stage is completed
            'votes': {},  # for storing votes details, format is {'player1': 'approve', 'player2': 'rejected', ...}
            'p_no_vote': [],  # for storing the nicknames who haven't voted
            'done_vote': None,  # indicator the vote stage is completed
            'n_approve': None,  # n of approve vote
            'vote_result': None,  # either 'approved' or 'rejected'
            'attempts': {},  # for storing attempts details, format is {'player1': 'fail', 'player2': 'success', ...}
            'p_no_attempt': [],  # for storing the nicknames who haven't attempted to fail or success the quest
            'done_quest': None,  # indicator for quest stage is completed
            'n_fail': None,  # n of fail cards in quest
            'quest_result': None,  # either 'fail' or 'success'
            'quest_results': [],  # to store the previous quest results
            'win_3_quests': None,  # indicator if either good/evil side has won at least 3 quests
            'assassin_target': None,  # the player that assassin picks if good side wins 3 quests
            'assassin_success': None  # indicator if assassin correctly picks Merlin
        }

        if self.has_lake_lady:
            game_param['lake_lady'] = self.p_positions[-1]  # first lady of the lake, last player in position list
            game_param['lake_lady_target'] = None  # the player that lady of the lake picks
            # the nicknames for those never be lady of the lake
            # lady of the lake could not pick any player who was the previous lady of the lake
            p_no_lake_lady = self.nicknames.copy()
            p_no_lake_lady.remove(game_param['lake_lady'])
            game_param['p_no_lake_lady'] = p_no_lake_lady
            game_param['done_lake_lady'] = None  # indicator if lake lady stage is completed

        # To store nicknames in good/evil list based on their characters
        p_good = []
        p_evil = []
        sides = {}
        for nickname, info in self.players_info.items():
            sides[nickname] = info['side']
            if info['side'] == 'good':
                p_good.append(nickname)
            else:
                p_evil.append(nickname)
            if info['character'] not in ['loyal_servant', 'minion']:
                game_param[info['character']] = nickname

        game_param['sides'] = sides
        game_param['p_good'] = p_good
        game_param['p_evil'] = p_evil

        # To store the progress of each player
        # This parameter is to tell the server which game message should be picked and what event should be triggered
        game_param['progress'] = {
            nickname: {
                'stage': self.stages[0],
                'step': 0
            } for nickname in self.nicknames if nickname not in self.ai_nicknames
        }

        return game_param

    def show_game_info(self):
        """
        To show the summary of the game. Could be requested by player.
        """
        info = ''
        info += 'Number of player: Good {}, Evil {}\n'.format(self.n_good, self.n_evil)
        quests_in_str = ', '.join(str(self.quests[i]) + '*' if self.need_2_fail_cards and i == 3
                                  else str(self.quests[i]) for i in range(5))
        info += 'Members for each quest: {}\n'.format(quests_in_str)
        good_characters_in_str = (', '.join(i for i in self.good_characters if i != 'loyal servant'))
        good_characters_in_str += ', loyal servant x{}'.format(self.good_characters.count('loyal servant'))
        info += 'Good Characters: {}\n'.format(good_characters_in_str)
        evil_characters_in_str = (', '.join(i for i in self.evil_characters if i != 'minion'))
        if 'minion' in self.evil_characters:
            evil_characters_in_str += ', minion x{}'.format(self.evil_characters.count('minion'))
        info += 'Evil Characters: {}\n'.format(evil_characters_in_str)
        info += 'Current Quest: {}\n'.format(self.game_param['quest'])
        info += 'Current vote Round: {}\n'.format(self.game_param['round'])
        info += 'Current Leader: {}\n'.format(self.game_param['leader'])
        if self.has_lake_lady:
            info += 'Current Lady of Lake: {}\n'.format(self.game_param['lake_lady'])

        length = 0
        for line in info.splitlines():
            if len(line) > length:
                length = len(line)

        hash_line = '#' * length + '\n'
        info = hash_line + 'Game Info\n' + hash_line + info + hash_line
        return info

    def show_players_info(self, nickname=None):
        """
        To show player info in pretty table. Could be requested by player.
        """
        t = PrettyTable()
        field_names = [i for i in list(self.players_info.values())[0] if i != 'knowledge']
        field_names.insert(0, 'nickname')

        if nickname is not None:
            t.field_names = field_names
            for nn, info in self.players_info.items():
                if nickname == nn:
                    row = [nickname + '(You)'] + [v for k, v in info.items() if k != 'knowledge']
                else:
                    row = [nn]
                    knowledge = self.players_info[nickname]['knowledge']
                    for k, v in info.items():
                        if k == 'character':
                            if self.has_percival and \
                                    nickname == self.game_param['percival'] \
                                    and v in ['merlin', 'morgana']:
                                if self.has_morgana:
                                    row.append('merlin/morgana')
                                else:
                                    row.append(v)
                            else:
                                row.append('unknown')
                        elif k == 'side':
                            row.append(knowledge[nn])
                        elif k != 'knowledge':
                            row.append(v)
                t.add_row(row)
        else:
            field_names += self.p_positions
            t.field_names = field_names
            for nn, info in self.players_info.items():
                row = [nn]
                for k, v in info.items():
                    row_know = []
                    if k == 'knowledge':
                        for n, s in v.items():
                            row_know.append(s)
                    else:
                        row.append(v)
                    row += row_know
                t.add_row(row)
        return str(t)

    def show_game_records(self, nickname, revealed=False):
        """
        To show previous game records. Could be requested by player.
        If revealed is True, means all the players' details (side, if they have attempted to fail the quest) would
        be revealed.
        """
        t = PrettyTable()
        field_names = ['Q', 'R', 'L', 'M']
        if self.has_lake_lady:
            field_names += ['LL', 'T']

        nicknames = [display_user_label(nickname, n) for n in self.nicknames]
        if revealed:
            nickname_with_star = [n + '*' if n in self.game_param['p_evil'] else n for n in self.nicknames]
            field_names += sorted(nickname_with_star)
        else:
            field_names += sorted(nicknames)

        field_names += ['N_A', 'VR', 'N_F', 'QR']
        t.field_names = field_names

        for quest, records in self.game_records.items():
            for record in records:
                row = [quest, record['round'], display_user_label(nickname, record['leader'])]
                if record['round'] > 1:
                    row = ['', record['round'], record['leader']]
                if revealed:
                    members_with_star = [display_user_label(nickname, n) + '*'
                                         if n in self.game_param['p_evil'] else display_user_label(nickname, n)
                                         for n in record['members']]
                    row.append(', '.join(members_with_star))
                else:

                    row.append(', '.join([display_user_label(nickname, n) for n in record['members']]))

                if self.has_lake_lady:
                    row += [record['lake_lady'], record['lake_lady_target']]
                if record['votes'] == {}:
                    row_vote = ['-'] * self.n_players
                else:
                    row_vote = ['o' if record['votes'][n] == 'approve' else 'x' for n in sorted(record['votes'].keys())]
                row += row_vote + [record['n_approve'], record['vote_result']]
                if record['quest_result'] is not None:
                    if revealed:
                        members = [k for k, v in record['attempts'].items() if v == 'fail']
                        row += [', '.join(members), record['quest_result']]
                    else:
                        row += [record['n_fail'], record['quest_result']]
                else:
                    row += ['N/A', 'N/A']

                t.add_row(row)

        return str(t)

    def show_votes(self, nickname):
        """
        To show votes details in pretty table.
        """
        t = PrettyTable()
        t.field_names = ['Player', 'Vote']
        for k, v in self.game_param['votes'].items():
            if k == nickname:
                k += '(You)'
            t.add_row([k, v])
        return str(t)

    def get_value_for_msg(self, key, nickname):
        """
        To compile the value from 'game_param' to readable/precise content for displaying the game messages.
        This is because all game messages are pre-generated, and all parameters in game messages will be looking
        the value in 'game_param' by their key. Like to get current leader, simply find game_param['leader'] will
        do the trick.
        But some parameters are not straightforward, for instance to get a player's vote, it needs to look at
        'game_param['votes'][nickname] instead, this function is to handle these special cases.
        """
        # game_param does not store nickname, so special handle if nickname is requested
        if key == 'nickname':
            return nickname
        # To convert list to string, mainly target for parameters like 'members', 'p_no_vote' etc
        elif isinstance(self.game_param[key], list):
            return ', '.join(self.game_param[key])
        # To look further in game_param with nickname, mainly target for parameters like 'votes' and 'attempts'
        elif isinstance(self.game_param[key], dict):
            return self.game_param[key][nickname]
        else:
            return self.game_param[key]

    def get_options(self, key, target=None):
        """
        To generate the options list for players to choose their actions.
        Example: while player needs to vote, the options would be shown as
        0. approve
        1. reject
        """
        options = ''
        if target is None:
            options_list = getattr(self, key)
        else:
            options_list = target[key]
        for i in range(len(options_list)):
            options += f'{i}. {options_list[i]}\n'
        return options

    def gen_msg_packs(self):
        """
        To pre-generated the game message 'packs' and allow players to pick the specific pack based on their progress.
        The message pack are store in dict format.
        There are total 5 + 1 stages and each stage contains a list of different message packs.
        Then all lists would be again, stored as dict format, where the stage as the key. The example is shown below:

        {
            'stage1': [
                {
                    'msg': msg1,
                    'condition': condition1,
                    'event': self.function1
                },
                {
                    'msg': msg2,
                    'condition': condition2,
                    'event': self.function2
                },
                ...
            ],
            ...
        }

        The 'stage', 'step' items in self.game_param['progress'][nickname] will determine which message would be picked
        for specific player, where 'stage' tell the system which list to look into, and 'step' is the index of the
        message pack in list.

        There are 4 items (or less) in game message pack, which are:

        'msg': The content of the message or the function to generate the message.

        'condition': The condition (in string format) if this message should be displayed under different circumstance.
        This string then would be evaluated by using eval() to determine if the condition is met.
        Note that there is a little hack here by using f"{parameter=}".split('=')[0] to get the name of the parameter.
        This method would report error if you change the parameter name somewhere else, which makes the debugging
        easier.

        'event': To handle the player's action such as proposal member, vote proposal etc. It also handles the
        validation of player's input.

        'wait': Indicator to tell player the game could only proceed if some other event is completed. With this, the
        messages would be picked up repeatedly and displayed until some other player completes his event.
        """
        msg_packs = {stage: list() for stage in self.stages}

        msg_packs['init'] = list(map(lambda m: {'msg': m},
                                     ['Hi {nickname}, welcome to Avalon.',
                                      self.show_game_info,
                                      self.show_players_info]))

        msg_pack = {
            'msg': 'Please wait other players to complete init stage.'
        }
        msg_packs['init'].append(msg_pack)

        if self.has_lake_lady:
            msg_pack = {
                'msg': 'You are the lady of the lake.',
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " == nickname"
            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': '{lake_lady} is the lady of the lake.',
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " != nickname"
            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': 'Please select your target or type x for not using your power this round. \n' +
                       self.get_options('p_no_lake_lady', self.game_param),
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " == nickname"
            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': 'Please wait if the lady of the lake {lake_lady} wants to use her power.',
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " != nickname",
                'wait': 'done_lake_lady'
            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " == nickname",
                'event': self.use_lake_lady_power
            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': 'You have selected {lake_lady_target} and he is on {sides} side.',
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " == nickname and " +
                             f"{self.game_param['done_lake_lady']=}".split('=')[0] + " and " +
                             f"{self.game_param['lake_lady_target']=}".split('=')[0]

            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': 'You have decided not to use your power this round.',
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " == nickname and " +
                             f"{self.game_param['done_lake_lady']=}".split('=')[0] + " and " +
                             f"not {self.game_param['lake_lady_target']=}".split('=')[0]
            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': 'The lady of the lake {lake_lady} has selected {lake_lady_target} and know his side.',
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " != nickname and " +
                             f"{self.game_param['done_lake_lady']=}".split('=')[0] + " and " +
                             f"{self.game_param['lake_lady_target']=}".split('=')[0]

            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': 'The lady of the lake {lake_lady} has decided not to use your power this round.',
                'condition': f"{self.game_param['lake_lady']=}".split('=')[0] + " != nickname and " +
                             f"{self.game_param['done_lake_lady']=}".split('=')[0] + " and " +
                             f"not {self.game_param['lake_lady_target']=}".split('=')[0]
            }
            msg_packs['lake_lady'].append(msg_pack)

            msg_pack = {
                'msg': 'Please wait other players to complete lake lady stage.'
            }
            msg_packs['lake_lady'].append(msg_pack)

        msg_pack = {
            'msg': 'Quest {quest} Round {round}'
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'Warning! This is voting round 5.\n'
                   'Whoever the current leader proposed to do the quest will be approved without vote!\n',
            'condition': f"{self.game_param['round']=}".split('=')[0] + " == 5",
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'You are the current leader\n',
            'condition': f"{self.game_param['leader']=}".split('=')[0] + " == nickname"
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': '{leader} is the current leader\n',
            'condition': f"{self.game_param['leader']=}".split('=')[0] + " != nickname"
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'Please select {n_members} members to do the quest {quest} (Example: 1 2 3)\n' +
                   self.get_options('nicknames'),
            'condition': f"{self.game_param['leader']=}".split('=')[0] + " == nickname"
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait leader {leader} to select members to do quest {quest}.',
            'condition': f"{self.game_param['leader']=}".split('=')[0] + " != nickname and " +
                         f"not {self.game_param['members']=}".split('=')[0],
            'wait': 'done_proposal'
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'You have selected {members} to do quest {quest}.',
            'condition': f"{self.game_param['leader']=}".split('=')[0] + " == nickname",
            'event': self.propose_quest
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'Leader {leader} has selected {members} to do quest {quest}.',
            'condition': f"{self.game_param['leader']=}".split('=')[0] + " != nickname"
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait other players to complete proposal stage.'
        }
        msg_packs['proposal'].append(msg_pack)

        msg_pack = {
            'msg': 'Please vote if you approve or reject {members} to do quest {quest}.\n' +
                   self.get_options('vote_cards')
        }
        msg_packs['vote'].append(msg_pack)

        msg_pack = {
            'msg': 'You have voted {votes}',
            'event': self.vote_quest
        }
        msg_packs['vote'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait for other player(s) {p_no_vote} to vote.',
            'condition': f"not {self.game_param['done_vote']=}".split('=')[0],
            'wait': 'done_vote'
        }
        msg_packs['vote'].append(msg_pack)

        msg_pack = {
            'msg': self.show_votes
        }
        msg_packs['vote'].append(msg_pack)

        msg_pack = {
            'msg': 'Total {n_approve} approve, the proposal is {vote_result}.'
        }
        msg_packs['vote'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait other players to complete vote stage.'
        }
        msg_packs['vote'].append(msg_pack)

        msg_pack = {
            'msg': 'You are selected to do quest {quest}.',
            'condition': "nickname in " + f"{self.game_param['members']=}".split('=')[0]
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': 'You are on evil side. Please select your attempt.\n' +
                   self.get_options('quest_cards'),
            'condition': "nickname in " + f"{self.game_param['members']=}".split('=')[0] + " and " +
                         "nickname in " + f"{self.game_param['p_evil']=}".split('=')[0]
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': 'You are on good side. You could only attempt to success the quest.\n',
            'condition': "nickname in " + f"{self.game_param['members']=}".split('=')[0] + " and " +
                         "nickname in " + f"{self.game_param['p_good']=}".split('=')[0]
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': 'You attempt to {attempts} quest {quest}.',
            'condition': "nickname in " + f"{self.game_param['members']=}".split('=')[0],
            'event': self.do_quest
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': '{members} are now doing quest {quest}',
            'condition': "nickname not in " + f"{self.game_param['members']=}".split('=')[0]
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait. {p_no_attempt} are now doing quest {quest}',
            'condition': f"not {self.game_param['done_quest']=}".split('=')[0],
            'wait': 'done_quest'
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': 'Total {n_fail} fail, the quest result is {quest_result}.'
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait other players to complete quest stage.'
        }
        msg_packs['quest'].append(msg_pack)

        msg_pack = {
            'msg': self.show_game_records
        }
        msg_packs['record'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait other players to complete record stage.'
        }
        msg_packs['record'].append(msg_pack)

        msg_pack = {
            'msg': 'The {win_3_quests} side have won 3 quests.',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0]
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'Now evil side have their last chance for Assassin to identify who is Merlin!',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good'"
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'You are the assassin.',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " == nickname"
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': '{assassin} is the assassin.',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " != nickname"
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'Please choose your target.\n' + self.get_options('p_good', self.game_param),
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " == nickname"
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'Please wait assassin {assassin} to choose his target.',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " != nickname",
            'wait': 'assassin_target'
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'You have picked {assassin_target}.',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " == nickname",
            'event': self.assassinate
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'Assassin {assassin} has picked {assassin_target}.',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " != nickname"
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'And you did it! {merlin} is Merlin! Evil side win!',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " == nickname and " +
                         f"{self.game_param['assassin_success']=}".split('=')[0]
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'And you missed it! {merlin} is Merlin! Good side win!',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " == nickname and " +
                         f"not {self.game_param['assassin_success']=}".split('=')[0]
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'And Assassin {assassin} did it! {merlin} is Merlin! Evil side win!',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " != nickname and " +
                         f"{self.game_param['assassin_success']=}".split('=')[0]
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'And Assassin {assassin} missed it! {merlin} is Merlin! Good side win!',
            'condition': f"{self.game_param['win_3_quests']=}".split('=')[0] + " == 'good' and " +
                         f"{self.game_param['assassin']=}".split('=')[0] + " != nickname and " +
                         f"not {self.game_param['assassin_success']=}".split('=')[0]
        }
        msg_packs['end'].append(msg_pack)

        msg_pack = {
            'msg': 'End Game. Thanks for playing'
        }
        msg_packs['end'].append(msg_pack)

        return msg_packs

    # This part is the functions for player's action.
    def propose_quest(self, members):
        """
        For leader to propose the members to do quest.
        """
        self.game_param['members'] = members

    def vote_quest(self, nickname, vote):
        """
        For player to vote the proposal from leader.
        If player has voted, he/she will be removed from 'p_no_vote' list.
        """
        self.game_param['votes'][nickname] = vote
        self.game_param['p_no_vote'].remove(nickname)

    def do_quest(self, nickname, attempt=None):
        """
        For player to attempt to fail/success the quest.
        If player has attempted, he/she will be removed from 'p_no_attempt' list.
        """
        self.game_param['attempts'][nickname] = attempt
        self.game_param['p_no_attempt'].remove(nickname)

    def assassinate(self, nickname):
        """
        For assassin to pick his target.
        """
        self.game_param['assassin_target'] = nickname

    def use_lake_lady_power(self, nickname):
        """
        For lady of the lake to pick her target.
        The player that she picked would be next lady of the lake so the name will be removed from 'p_no_lake_lady'.
        If the nickname is herself, means she decided not to use her power.
        """
        if nickname != self.game_param['lake_lady']:
            self.game_param['lake_lady_target'] = nickname
            self.game_param['p_no_lake_lady'].remove(nickname)

    # This part is the function for system
    def get_vote_result(self):
        """
        To calculate the vote result and update the result to self.game_param.
        """
        n_approve = [v for v in self.game_param['votes'].values()].count('approve')
        if n_approve > int(self.n_players / 2):
            res = 'approved'
        else:
            res = 'rejected'
        self.game_param['n_approve'] = n_approve
        self.game_param['vote_result'] = res

    def get_quest_result(self):
        """
        To calculate the quest result and update result to self.game_param.
        Note that the self.need_2_fail_cards is needed in here.
        """
        n_fail = [a for a in self.game_param['attempts'].values()].count('fail')
        res = 'success'

        if n_fail > 0 or (self.need_2_fail_cards and self.game_param['quest'] == 4 and n_fail > 1):
            res = 'fail'

        self.game_param['n_fail'] = n_fail
        self.game_param['quest_result'] = res
        self.game_param['quest_results'].append(res)

    def handle_lake_lady(self):
        """
        To handle the game progress after lady of the lake used her power.

        If a computer player is lady of the lake, randomly pick a target from the pool.
        Note that the nickname of current lady of the lake also would be in the pool, if system pick the lady of the
        lake as target, it indicates the lady of the lake decides not to user her power.

        If lady of the lake uses her power (pick a nickname that is not herself), the system will update her knowledge
        in players_info by revealing the target's side. Then set 'done_lake_lady' to True.

        With 'done_lake_lady' is True, not only the players who are in 'wait' could now continue to proceed the game,
        the system also will not run this function anymore until this quest is completed, where self.move_next_round()
        function is triggered and 'done_lake_lady' will be reset to None.
        """
        if self.game_param['lake_lady'] in self.ai_nicknames:
            target = random.choice(self.game_param['p_no_lake_lady'] + [self.game_param['lake_lady']])
            self.use_lake_lady_power(target)
        if self.game_param['lake_lady_target']:
            target = self.game_param['lake_lady_target']
            reveal_side = self.players_info[target]['side']
            self.players_info[self.game_param['lake_lady']]['knowledge'][target] = reveal_side
            self.game_param['done_lake_lady'] = True

    def handle_proposal(self):
        """
        To handle the game progress after leader selected the members.

        If a computer player is leader, randomly pick the members.

        Copy the 'members' to 'p_no_attempts' for later 'quest' stage, if this proposal is approved.
        Also copy all the nicknames to 'p_no_vote' for later 'vote' stage, unless it is 5th round which no vote is
        required.

        Set the 'done_proposal' is True to indicate the proposal stage is done.
        Similar to the 'handle_lake_lady' function, with 'done_proposal' is True, players can continue to proceed the
        game and the system will not run this function until this round is completed, where self.move_next_round()
        function is triggered and 'done_proposal' will be reset to None.
        """
        if self.game_param['leader'] in self.ai_nicknames and not self.game_param['members']:
            self.propose_quest(random.sample(self.nicknames, self.game_param['n_members']))

        if self.game_param['members']:
            self.game_param['p_no_attempt'] = self.game_param['members'].copy()
            if self.game_param['round'] < 5:
                self.game_param['p_no_vote'] = self.nicknames.copy()
            self.game_param['done_proposal'] = True

    def handle_vote(self):
        """
        To handle the game progress after every player made their vote.

        If found any computer player hasn't voted, randomly vote for them.

        If every player has voted, set 'done_vote' to True.
        With 'done_vote' is True, players could then proceed the game and the system will not run this function again
        until this round is completed, where self.move_next_round() will be triggered and 'done_vote' will be reset to
        None.

        Then the system will calculate the vote result by calling self.get_vote_result().
        If the result is rejected, the game will skip 'quest' stage and straight to 'record' stage. Therefore, the
        system will record the history here for later 'record' stage.
        """
        if any(n in self.game_param['p_no_vote'] for n in self.ai_nicknames):
            for n in self.ai_nicknames:
                vote = random.choice(['approve', 'reject'])
                self.vote_quest(n, vote)

        if len(self.game_param['votes']) == len(self.nicknames):
            self.game_param['done_vote'] = True
            self.get_vote_result()
            if self.game_param['vote_result'] == 'rejected':
                self.record_game_history()

    def handle_quest(self):
        """
        To handle the game progress after players did quest.

        If found any computer player hasn't made attempt, randomly make attempt for them.

        If every player has made their attempt, set 'done_quest' to True.
        With 'done_quest' is True, players could then proceed the game and the system will not run this function again
        until this quest is completed, where self.move_next_round() will be triggered and 'done_quest' will be reset to
        None.

        Then the system will calculate the quest result by calling self.get_quest_result().
        The next stage is 'record' where system is going to display the game record. Therefore, record the game history
        in here.

        The system will also check if either side has won at least 3 quests here, if yes, after 'record' stage the game
        will move the 'end' stage which is the last stage of the game.

        """
        if any(n in self.game_param['p_no_attempt'] for n in self.ai_nicknames):
            for n in self.game_param['p_no_attempt']:
                if n in self.ai_nicknames:
                    attempt = random.choice(['success', 'fail'])
                    if n in self.game_param['p_good']:
                        attempt = 'success'
                    self.do_quest(n, attempt)

        if len(self.game_param['attempts']) == self.game_param['n_members']:
            self.game_param['done_quest'] = True
            self.get_quest_result()
            self.record_game_history()
            if any(self.game_param['quest_results'].count(R := r) > 2 for r in
                   self.game_param['quest_results']):
                if R == 'success':
                    self.game_param['win_3_quests'] = 'good'
                else:
                    self.game_param['win_3_quests'] = 'evil'

    def handle_end(self):
        """
        To handle the game progress if assassin has picked his target.

        If a computer player is assassin, randomly pick a target for him.

        Check if the target is Merlin and store the value in 'assassin_success'. 'assassin_success' is to determine
        which message pack to be picked for players.
        """
        if self.game_param['assassin'] in self.ai_nicknames:
            target = random.choice(self.game_param['p_good'])
            self.assassinate(target)
        if self.game_param['assassin_target'] and \
                self.game_param['assassin_target'] == self.game_param['merlin']:
            self.game_param['assassin_success'] = True
        else:
            self.game_param['assassin_success'] = False

    def server_run(self):
        """
        To handle the game progress after player's action and auto make action for computer players.

        This function is listening the whole game to detect if any player has made any action by checking their
        'progress' parameter.
        If a player made an action, his 'progress' value would be different.

        Then determine what kind of action and handle the follow-up movement for the game.

        If all players are in the last message pack of the same stage, decide what is the next stage should be.
        """
        while True:
            # Check if any player make any action
            if self.game_param['progress'] != self.game_param_copy['progress']:
                # Update the old progress value
                self.game_param_copy['progress'] = copy.deepcopy(self.game_param['progress'])
                # log file
                with open('../log/log', 'a') as log:
                    log.write('server side: \n')
                    pprint.pprint(self.game_param, log)
                    log.write('\n')

                if self.has_lake_lady:
                    if self.game_param['stage'] == 'lake_lady' and not self.game_param['done_lake_lady']:
                        self.handle_lake_lady()

                if self.game_param['stage'] == 'proposal' and not self.game_param['done_proposal']:
                    self.handle_proposal()

                elif self.game_param['stage'] == 'vote' and not self.game_param['done_vote']:
                    self.handle_vote()

                elif self.game_param['stage'] == 'quest' and not self.game_param['done_quest']:
                    self.handle_quest()

                elif self.game_param['stage'] == 'end' and self.game_param['win_3_quests'] == 'good':
                    self.handle_end()

                # determine if all player are in last message pack of the same stage, if yes lead them to next stage
                if all(v['stage'] == self.game_param['stage'] and
                       v['step'] == len(self.msg_packs[self.game_param['stage']]) - 1
                       for k, v in self.game_param['progress'].items()):
                    self.move_next_stage()

                # if is end game break the loop
                if self.end_game:
                    break

    def client_run(self, nickname, input_):
        """
        To handle which message to be displayed for player and handle player's input.

        This function will first pick a msg_pack accordingly based on the player's current progress.

        If the msg_pack contains 'event' item, means the system needs to validate player's input to trigger the event.
        If the input is not valid, error message will return and wait for player's another input.
        Otherwise, process the event with player's input.

        If the msg_pack contains 'msg' item, process the message and display it for players.

        If the msg_pack contains 'wait' item, system will not allow player to proceed to next message pack until the
        wait is resolved. The 'wait' usually target parameter names that start with 'done_something' like 'done_vote'
        or 'done_quest'.

        If msg_pack does not contain 'wait' item or the 'wait' is resolved, allow player to proceed the game by calling
        self.move_next_step() which is to update self.game_param['progress'].

        Then this function will return the game message.

        Note that this function also handle the help request from player, if player's input is starting with '?'.
        """
        # log file
        with open('../log/log', 'a') as log:
            log.write(f'{nickname} turn: \n')
            pprint.pprint(self.game_param, log)
            log.write('\n')

        # Handle player's help request
        if input_ and input_[0] == '?':
            return self.get_help_msg(input_)

        # Get game message pack
        msg_pack = self.get_msg_pack(nickname)
        pack_argv = msg_pack.get('argv', {})

        # Handle 'event' item, process with player's input
        if 'event' in msg_pack.keys():
            error_msg = self.process_event(nickname, msg_pack['event'], input_, pack_argv)
            # if error occur return the error message immediately
            if error_msg:
                return error_msg

        # Handle 'msg' item for displaying proper game message
        msg = None
        if 'msg' in msg_pack.keys():
            msg = self.process_msg(nickname, msg_pack['msg'], pack_argv)

        # Check if player is allowed to proceed their game with next step
        if 'wait' not in msg_pack.keys() or self.game_param[msg_pack['wait']]:
            self.move_next_step(nickname)

        return msg

    def get_msg_pack(self, nickname):
        """
        To get msg_pack from self.msg_packs based on player's progress.
        If 'condition' is found, check if the player's or game info are met the condition.
        If yes, return the msg_pack, otherwise look into next message by adding 1 to player's step.
        """
        while True:
            stage = self.game_param['progress'][nickname]['stage']
            step = self.game_param['progress'][nickname]['step']
            msg_pack = self.msg_packs[stage][step]
            if 'condition' not in msg_pack.keys() or eval(msg_pack['condition']):
                break
            self.game_param['progress'][nickname]['step'] += 1
        return msg_pack

    def process_msg(self, nickname, pack_msg, pack_argv):
        """
        To process the 'msg' item in msg_pack.
        There are 2 types in 'msg' item. One is the function that generates the message content, and another
        one is a pure message content in string format with parameters.

        If 'msg' is a function, extract the required argv name by using inspect lib and compare with self.game_param.
        If there is a match, store the argv name and the value from self.game_param as dict.
        Note that 'nickname' is not in self.game_param so the system manually add 'nickname' to the dict.
        Execute the function and pass the dict as argument(s) to get the message content.

        If 'msg' is pure string, extract all the parameters in the string by using re lib. Pass all the extracted
        parameters to self.get_value_for_msg() to get the corresponding value and store as dict.
        Then format the string with the dict to get the message content.
        """
        # is function
        if inspect.ismethod(pack_msg):
            # Get parameter names from the function and check if they are in self.game_param
            # Get the value from self.game_param with the corresponding parameters
            # Combine the parameter name and value as argv dict
            argv = dict((k, self.game_param[k])
                        for k in [a.name for a in inspect.signature(pack_msg).parameters.values()]
                        if k in self.game_param.keys())
            # Manually add 'nickname' if it is required in the function
            if 'nickname' in [a.name for a in inspect.signature(pack_msg).parameters.values()]:
                argv['nickname'] = nickname
            argv.update(pack_argv)
            # Execute the function with argv dict
            msg = pack_msg(**argv)
        else:
            # Extract the parameter from string and get the value
            # Combine the parameter name and value as argv dict
            argv = dict((k, self.get_value_for_msg(k, nickname))
                        for k in list(map(lambda m: m[1:-1], re.findall(r'{.*?}', pack_msg))))
            # Format the string with argv dict
            msg = pack_msg.format(**argv)
        return msg

    def process_event(self, nickname, pack_event, input_, pack_argv):
        """
        To process 'event' item in msg_pack.

        'event' item only contains function name. Therefore, extract the parameter names from function by using inspect
        lib and compare with self.game_param to get their values. Then store the names, values pair as argv dict.

        Manually add 'nickname' to argv dict if 'nickname' is required in the event function.

        System has kept 3 attributes for handling the input for all event functions which are input format, options and
        target.

        'input_format' is re pattern in string format for input validation.

        'options' is to determine which is the corresponding options list for getting the value. For instance if the
        input is '1' and the options is self.vote_cards (value is ['approve', 'reject']), the corresponding value then
        is self.vote_cards[1], which would be 'reject' in this case.

        'target' is to point the target parameter of the event function for this input.

        Then system will validate the input by using re.match with 'input_format'
        If yes, get the value from the 'options' list based on the input and update the argv dict with 'target'.
        Then execute the event function with argv dict.
        If the input is not valid, return error message and ask the player to key in the input again.
        """
        error_msg = None
        input_format = None
        options = None
        target = None

        # Get parameter names from the function and check if they are in self.game_param
        # Get the value from self.game_param with the corresponding parameters
        # Combine the parameter name and value as argv dict
        argv = dict((a.name, self.game_param[a.name] if a.name in self.game_param.keys() else None)
                    for a in inspect.signature(pack_event).parameters.values())

        # Manually add nickname to argv dict
        if 'nickname' in [a.name for a in inspect.signature(pack_event).parameters.values()]:
            argv['nickname'] = nickname
        argv.update(pack_argv)

        # Get input_format, options and target based on event function name
        if pack_event == self.propose_quest:
            input_format = r'^(?!.*(.\s).*\1)([0-' + f'{self.n_players - 1}' + \
                           r']\s){' + f'{self.game_param["n_members"]}' + r'}$'
            options = self.nicknames
            target = 'members'

        elif pack_event == self.vote_quest:
            input_format = r'^[0-1]\s*$'
            options = self.vote_cards
            target = 'vote'

        elif pack_event == self.do_quest:
            if nickname in self.game_param['p_evil']:
                input_format = r'^[0-1]\s*$'
                options = self.quest_cards
                target = 'attempt'
            else:
                argv['attempt'] = 'success'

        elif pack_event == self.assassinate:
            input_format = r'^[0-' + str(int(len(self.game_param['p_good']) - 1)) + r']\s*$'
            options = self.game_param['p_good']
            target = 'nickname'

        elif pack_event == self.use_lake_lady_power:
            input_format = r'^[0-' + str(int(len(self.game_param['p_no_lake_lady']) - 1)) + r'x]\s*$'
            options = self.game_param['p_no_lake_lady']
            target = 'nickname'

        # Validate input
        if all(input_info for input_info in [input_format, options, target]):
            if re.match(input_format, input_.strip() + ' '):
                # input is valid, get input corresponding value in proper format (string or list)
                if len(input_.strip().split()) == 1:
                    # input == 'x' is specifically for lake lady action, where x means does not use the power
                    # so the value is nickname of the lake lady
                    if input_.strip() == 'x':
                        value = nickname
                    else:
                        value = options[int(input_.strip())]
                else:
                    value = [options[int(i)] for i in input_.strip().split()]
                # update argv dict
                argv[target] = value

                # execute event function
                pack_event(**argv)

            else:
                error_msg = 'Wrong format! Please key in again'
        else:
            pack_event(**argv)

        return error_msg

    def move_next_step(self, nickname):
        """
        To handle player's progress.

        According to self.server_run(), system will only move to next stage while all players are in the last msg_pack
        in the same stage. Therefore, player's stage is not equal to system's stage means he is one stage behind.

        So if player's is not equal to system's stage, update player's stage to system's stage and change the step to 0.

        Otherwise (same stage as system), if the step is not yet reach the last msg_pack of the stage, step + 1 to let
        player could pick the next available msg_pack.

        This also could make sure if not all players are in the last msg_pack in same stage, the last message would be
        repeated for the player who has reached last msg_pack (but others are not) until other players also reach the
        same last msg_pack, then self.server_run() could detect this and move the system stage to next stage by calling
        self.move_next_stage().
        """
        stage = self.game_param['progress'][nickname]['stage']
        step = self.game_param['progress'][nickname]['step']
        if stage != self.game_param['stage']:
            self.game_param['progress'][nickname]['stage'] = self.game_param['stage']
            self.game_param['progress'][nickname]['step'] = 0
        else:
            if step < len(self.msg_packs[stage]) - 1:
                self.game_param['progress'][nickname]['step'] += 1

    def move_next_stage(self):
        """
        To handle which stage to move next based on game progress.

        TODO write document here
        """
        if (self.game_param['stage'] == 'record' and self.game_param['vote_result'] == 'rejected') or \
                (self.game_param['stage'] == 'record' and not self.game_param['win_3_quests']):
            self.move_next_round()
            self.game_param['stage'] = 'proposal'
            if self.has_lake_lady:
                if self.game_param['quest'] > 2 and not self.game_param['done_lake_lady']:
                    self.game_param['stage'] = 'lake_lady'

        elif self.game_param['stage'] == 'vote' and self.game_param['vote_result'] == 'rejected':
            self.game_param['stage'] = 'record'
        elif self.game_param['stage'] == 'proposal' and self.game_param['round'] == 5:
            self.game_param['stage'] = 'quest'
        elif self.has_lake_lady and self.game_param['stage'] == 'init':
            self.game_param['stage'] = 'proposal'
        elif self.game_param['stage'] != self.stages[-1]:
            self.game_param['stage'] = self.stages[self.stages.index(self.game_param['stage']) + 1]
        else:
            self.end_game = True

    def move_next_round(self):
        if self.game_param['quest_result'] is None:
            self.game_param['round'] += 1
        else:
            self.game_param['quest'] += 1
            self.game_param['round'] = 1
            self.game_param['n_members'] = self.quests[self.game_param['quest'] - 1]
            self.game_records[self.game_param['quest']] = []

            if self.has_lake_lady and self.game_param['lake_lady_target']:
                self.game_param['done_lake_lady'] = None
                self.game_param['lake_lady'] = self.game_param['lake_lady_target']
                self.game_param['lake_lady_target'] = None

        if self.game_param['leader'] == self.p_positions[-1]:
            self.game_param['leader'] = self.p_positions[0]
        else:
            self.game_param['leader'] = self.p_positions[self.p_positions.index(self.game_param['leader']) + 1]

        self.game_param['members'] = []
        self.game_param['done_proposal'] = None
        self.game_param['votes'] = {}
        self.game_param['p_no_vote'] = []
        self.game_param['done_vote'] = None
        self.game_param['n_approve'] = None
        self.game_param['vote_result'] = None
        self.game_param['attempts'] = {}
        self.game_param['p_no_attempt'] = []
        self.game_param['done_quest'] = None
        self.game_param['n_fail'] = None
        self.game_param['quest_result'] = None
        self.game_param['new_round'] = True

    def record_game_history(self):
        game_record = dict((k, self.game_param[k]) for k in self.game_record_keys if k in self.game_param)
        self.game_records[self.game_param['quest']].append(game_record)

    def get_help_msg(self, input_):
        if input_.strip() == '?cheat':
            help_msg = pprint.pformat(self.game_param, indent=4)
        elif input_.strip() == '?game':
            help_msg = self.show_game_info()
        elif input_.strip() == '?player':
            help_msg = self.show_players_info(self.game_param['nickname'])
        elif input_.strip() == '?history':
            help_msg = self.show_game_records()
        else:
            help_msg = '?game = print game info\n' \
                       '?player = print player info\n' \
                       '?history = print game history'
        return help_msg
