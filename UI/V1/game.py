"""
Setup game environment for Avalon with specific requirements.

Change log:

2023-02-14 ~ V0.1
- general code structure
- algorithm to get the number of good/evil side for different player game
- record quest number for different player game
- handle the lady of the lake requirement
- handle characters assignment for each player
- extension to validate initial parameters

2023-03-09 ~ V0.2
- extension to handle knowledge of each characters
- extension to add an indicator for 2 failed cards quest

2023-03-10 ~ V0.3
` extension to handle propose, vote, do quest, check result, assassinate functions
- extension to handle game simulation with random value
- extension to print game/player info and game history

"""

import random
from prettytable import PrettyTable
import json

class Avalon():
    def __init__(self,
                 n_players=5,
                 has_mordred=False,
                 has_oberon=False,
                 has_lake_lady=False):

        self.n_players = n_players
        self.positions = ['player_' + str(i) for i in range(self.n_players)]
        self.has_mordred = has_mordred
        self.has_oberon = has_oberon
        self.has_lake_lady = has_lake_lady
        self.lake_lady = ''
        self.n_good, self.n_evil = self.get_n_of_sides()
        self.validate_setting()
        self.characters = self.get_characters()
        self.quests, self.has_2_failed_cards = self.get_quests()
        self.nicknames = []
        self.quest_results = []
        self.good_players = []
        self.evil_players = []
        self.lake_lady_pool = []
        self.merlin = ''
        self.mordred = ''
        self.percival = ''
        self.oberon = ''
        self.assassin = ''
        self.morgana = ''
        self.proposals = []


    def get_n_of_sides(self):
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

        :return: Return the number of good side & evil side
        """
        good_dic = {
            5:3,
            6:4,
            7:4,
            8:5,
            9:6,
            10:6,
        }

        if self.n_players in good_dic.keys():

            n_good = good_dic[self.n_players]

        else:
            n_good = int(self.n_players/2) + 1

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
        | 2nd Quest |  2  |  3  |  3  |  4  |  4  |  4   |
        +-----------+-----+-----+-----+-----+-----+------+
        | 3rd Quest |  2  |  4  |  3  |  4  |  4  |  4   |
        +-----------+-----+-----+-----+-----+-----+------+
        | 4th Quest |  3  |  3  |  4* |  5* |  5* |  5*  |
        +-----------+-----+-----+-----+-----+-----+------+
        | 5th Quest |  3  |  4  |  4  |  5  |  5  |  5   |
        +-----------+-----+-----+-----+-----+-----+------+

        * Note that the 4th quest (and only the 4th quest) in games of 7 or more
        players require at least two failed cards to be failed quest.

        :return: Return the number of selected players for each quest in list.
                 Return the indicator if the game contains 2 failed cards quest.
        """

        # To indicate this game has 2 failed cards quest
        has_2_failed_cards = True if self.n_players > 6 else False

        # Hardcoding the number of players to be assigned for each quest
        quests = []
        if self.n_players == 5:
            quests = [2, 3, 2, 3, 3]

        elif self.n_players == 6:
            quests = [2, 3, 4, 3, 4]

        elif self.n_players == 7:
            quests = [2, 3, 3, 4, 4]

        elif self.n_players in [8, 9, 10]:
            quests = [3, 4, 4, 5, 5]

        return quests, has_2_failed_cards


    def validate_setting(self):
        """
        To validate the game setting.

        *note: Some validation might be worth to be done at front end

        :return: Return exception message
        """
        if self.n_players not in range(5, 11):
            raise Exception("Have to be 5 to 10 players!")

        # Assassin and Morgana are the must for evil side hence there is a +2 at the end.
        if self.has_mordred + self.has_oberon + 2 > self.n_evil:
            raise Exception("Too many evil characters!")


    def create_player(self, nickname):
        """
        To create a player in the game with the desired nickname.
        Might be worth to think if we need to limit the length of the name.
        All the names would be stored in self.nicknames as list format.
        :param nickname: The unique nickname for new player
        :return:
        """

        # Check if the nickname is unique
        if nickname in self.nicknames:
            raise Exception("Your nickname has been used!")

        # Stop creating new player when the number hit the limit
        if len(self.nicknames) > self.n_players:
            raise Exception("The room is full!")

        self.nicknames.append(nickname)


    def get_characters(self):
        """
        To get a list of characters that would be played in the game based on the game setting.
        The good/evil side is also attached with the characters.
        The number of characters is same as the number of players.
        These characters are stored in list format.
        they would then be randomly assigned to players.
        :return: a list of character names with good/evil side.
        """

        # Define default compulsory characters and their side then add to a good/evil list
        # Note tht percival & morgana are not compulsory in this game.
        # But it would be a lot less fun without it so I treat these characters as a must.
        good_characters = [['merlin', 'good'], ['percival', 'good']]
        evil_characters = [['assassin', 'evil'], ['morgana', 'evil']]

        # Define other special characters based on game setting.
        # And add to corresponding good/evil list (For this case, evil list only)
        if self.has_mordred: evil_characters.append(['mordred', 'evil'])
        if self.has_oberon: evil_characters.append(['oberon', 'evil'])

        # Compare the n of good/evil characters in lists with the n of required good/evil players.
        # If less than the required number,
        # add the normal good/evil characters accordingly to corresponding list.
        while(len(good_characters) < self.n_good):
            good_characters.append(['loyal servant', 'good'])

        while(len(evil_characters) < self.n_evil):
            evil_characters.append(['minion', 'evil'])

        # Combine the good/evil lists
        characters = good_characters + evil_characters

        return characters


    def generate_knowledge(self):
        """
        To generate the knowledge of the character. There are total 4 status which are
        "good", "evil", "unknown" and "either", where "either" status is specifically
        for character card "percival" which happens to know either morgana/merlin but
        without knowing their identity.

        The knowledge will be in dict format as shown below:

        {
            "nickname1": good,
            "nickname2": evil,
            "nickname3:: unknown,
            ...
        }

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
        know who is who. Therefore his knowledge shows 'either' on the players who hold
        *merlin*/*morgana* card, and remains 'unknown' to the rest of the players.

        *oberon* doesn't know who are on evil side, he also doesn't reveal to evil players.
        Only *merlin* know he is from evil side. Therefore if *oberon* involves, evil
        players know (n_evil_players - 1) are evil, and the rest (n_good_players + 1) will
        be 'unknown' as *oberon* is among them. And oberon has no knowledge (all 'unknown').

        All evil players knows each other who are from evil side (except *oberon*).

        All good players (except *merlin* and *percival*) have no knowledge (all 'unknown').

        Note that this function also stores the players' nickname to the corresponding
        special characters and good/evil group.
        :return:
        """

        # Iterate the nicknames to define their character and side
        for nickname in self.nicknames:
            character = self.players_info[nickname]['character']
            side = self.players_info[nickname]['side']
            knowledge = {}

            # Generate knowledge based on character setting
            for key, info in self.players_info.items():
                if side == 'good':
                    # store good player's nickname to a list
                    self.good_players.append(nickname)
                    if character == 'merlin':
                        # store player's nickname who plays as *merlin*
                        self.merlin = nickname
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
                    elif character == 'percival':
                        # Store player's nickname who plays as *percival*
                        self.percival = nickname
                        if info['character'] in ['merlin', 'morgana']:
                            knowledge[key] = 'either'
                        else:
                            knowledge[key] = 'unknown'

                    # all normal good players have no knowledge
                    else:
                        knowledge[key] = 'unknown'

                # evil players
                else:
                    # Store player's nickname who plays as evil's special characters
                    if character == 'mordred': self.mordred = nickname
                    if character == 'morgana': self.morgana = nickname
                    if character == 'assassin': self.assassin = nickname

                    # Store evil player's nickname to a list
                    self.evil_players.append(nickname)

                    if self.has_oberon:
                        # If *oberon* involves, the player who plays as oberon doesn't have any knowledge
                        # so everyone is unknown to him
                        if character == 'oberon':
                            self.oberon = nickname
                            knowledge[key] = 'unknown'

                        # For the rest of evil players, (n_good_players + 1) now are unknown to them as
                        # *oberon* is among them.
                        else:
                            if info['character'] == 'oberon' or info['side'] == 'good':
                                knowledge[key] = 'unknown'

                            # They still know other evil players who is not *oberon*
                            else:
                                knowledge[key] = info['side']

                    # If no *oberon*, evil players know everyone's side
                    else:
                        knowledge[key] = info['side']

            # Store knowledge dict to player_info dict
            self.players_info[nickname]['knowledge'] = knowledge


    def assign_characters(self):
        """
        To assign characters randomly to players, and create player_info dict for reference.

        Reference example for player info:

        {
            'koh': {
                'character': 'merlin',
                'side': 'good',
                'position': 3,
                'lake_lady': false,
                'knowledge': {
                    'nong': 'good',
                    'victor': 'good',
                    ...
                }
            }
        }

        :return:
        """

        # shuffle the nicknames list to make the position of each player randomly each game
        random.shuffle(self.nicknames)

        # shuffle the characters card
        random.shuffle(self.characters)

        # Assign characters to players, this list also determines the position of each player
        self.players_info = {
            nickname: {
                'character': character[0],
                'side': character[1],
                'position': position
            }
            for position, nickname, character in zip([i for i in range(self.n_players)],
                                                     self.nicknames,
                                                     self.characters)
        }


    def build_game(self):
        """
        To build the initial game environment, including assign characters cards to players,
        determine the position, and decide the initial leader, the lady of lake, if applicable.

        :return:
        """

        # Check if enough players are created
        if len(self.nicknames) != self.n_players:
            raise Exception("Need {} players, now only {} players!".format(self.n_players,
                                                                           len(self.nicknames)))

        # Assign characters and determine the position randomly
        # Position is important, as players will rotate to be leader at clockwise direction
        # In this case, the index of current position + 1 would be treated as clockwise direction
        self.assign_characters()
        self.positions = list(self.players_info)

        # Randomly select an initial leader
        self.leader = random.choice(self.positions)


        # Lady of the lake has to be the player who on initial leader's right.
        # Which means the anti-clockwise direction from initial leader.
        # Since the self.position sequence is set for clockwise (next person index is +1)
        # The lady of the lake should be assigned the other direction in self.position (next person is -1)
        # If last player in the self.position is the initial leader, first player then become the lady
        # of the lake.
        # The lady of lake will pick one player to reveal his/her side, she can't pick the player who
        # used to be the lake of the lake.
        # Therefore there is a list (self.lake_lady_pool) to store the available players
        # Whoever is picked by the lady of the lake will be remove from the list.
        if self.has_lake_lady:
            self.lake_lady_pool = self.nicknames.copy()
            if self.leader == self.positions[0]:
                lake_lady = self.positions[-1]
            else:
                lake_lady = self.positions[self.positions.index(self.leader) - 1]

            self.lake_lady = lake_lady
            # Record to player_info dict
            for nickname in self.nicknames:
                if self.lake_lady == nickname:
                    self.players_info[nickname]['lake_lady'] = True
                else:
                    self.players_info[nickname]['lake_lady'] = False

            self.lake_lady_pool.remove(lake_lady)

        # Generate knowledge for different characters
        self.generate_knowledge()


    def quest_proposal(self, leader, quest_round, voting_round, n_member, members):
        """
        To generate the proposal to select players to do the quote. Different quests require
        different number of players to do the quest (refer to self.quests).
        Leader needs to select the players he trusts to achieve the target.

        The proposal details is store in dict format for players references.

        :param leader: Current leader who get to pick players to do the quest
        :param quest_round: Indicate the quest number (Total 5 per game)
        :param voting_round: Indicate the voting round number (Total 5 per quest)
        :param n_member: Number of players need to be picked for the quest
        :param members: a list of player names who are picked to do the quest.
        :return: proposal: proposal details in dict format
        """

        # Check if the selected players and required number of the players are match
        if n_member != len(members):
            raise Exception ("Need {} members to do the quest!".format(n_member))
        # Generate dict to store the proposal details
        else:
            proposal = {}
            votes = {}
            quest_attempts = {}
            proposal['leader'] = leader
            proposal['quest_round'] = quest_round
            proposal['voting_round'] = voting_round
            proposal['n_member'] = n_member
            proposal['members'] = members
            proposal['votes'] = votes
            proposal['quest_attempts'] = quest_attempts

        return proposal

    def vote_proposal(self, player, is_approved, proposal):
        """
        Votes from each player whether they agree with the leader decision
        :param player: player's nickname who makes this vote
        :param is_approved: vote approve or reject the proposal
        :param proposal: proposal dict to store the vote details
        :return:
        """
        proposal['votes'][player] = is_approved

    def get_voting_result(self, proposal):
        """
        To get the vote result. The proposal needs to get majority of votes in order
        to be approved.
        Regardless the voting result, the player who is next to leader's clockwise
        direction would be next leader.
        :param proposal: proposal dict to store the vote details
        :return: res: voting result (approved or rejected)
        """
        n_approved = 0
        for p, v in proposal['votes'].items():
            if v == True: n_approved += 1

        # Check if majority vote to approve the proposal
        if n_approved > int(self.n_players / 2):
            res = 'approved'
        else:
            res = 'rejected'
        proposal['n_approved'] = n_approved
        proposal['voting_result'] = res

        # Move next player to be leader next round.
        # If current leader is in last postition in the list, the first player in the list
        # will be next leader
        if self.leader == self.positions[-1]:
            self.leader = self.positions[0]
        else:
            self.leader = self.positions[self.positions.index(self.leader) + 1]

        return res


    def do_quest(self, player, is_success, proposal):
        """
        To do quest by using success/fail cards from the players who got picked by leader and
        got approved by majority
        :param player: player's nickname who does the quest
        :param is_success: attempt to succeed or fail the quest
        :param proposal: proposal dict to store the vote details
        :return:
        """

        # record the details
        proposal['quest_attempts'][player] = is_success

    def get_quest_result(self, proposal):
        """
        Get the quest result that has done by players who got picked.
        Unless on 4th quest in 7 players game or more, if 1 player attempted to fail the quest,
        the quest is resulted as fail.
        Both side players need to succeed/fail at least 3 quests to win the game.
        The end game situation will be checked here to see if either side has won.
        :param proposal: proposal dict to store the vote details
        :return: end_game: Indicator to check if is end game. 'None' means no side have won,
                           'good'/'evil mean either good or evil side have won 3 quests.
                 res: quest result
        """
        n_fail = 0

        # Record quest result details
        for p, v in proposal['quest_attempts'].items():
            if v == False: n_fail += 1

        # Get quest result, self.has_2_failed_card is used to indicate if this game contains
        # 2 failed cards on 4th quest.
        if self.has_2_failed_cards and proposal['quest_round'] + 1 == 4:
            if n_fail > 1: res = 'fail'
            else: res = 'success'

        # Otherwise 1 failed card will fail the quest
        else:
            if n_fail > 0: res = 'fail'
            else: res = 'success'

        # Record details
        proposal['n_fail'] = n_fail
        proposal['quest_result'] = res

        # Record quest result
        self.quest_results.append(res)

        # Check if good side have succeeded 3 quests
        if self.quest_results.count('success') > 2:
            end_game = 'good'

        # Check if evil side have failed 3 quests
        elif self.quest_results.count('fail') > 2:
            end_game = 'evil'
        else:
            end_game = None

        return res, end_game


    def assassinate_merlin(self, target):
        """
        Evil side last chance if good side have won 3 quest by identifying *merlin*
        :param target: target (player's nickname) to assassinate
        :return: True if successfully identify *merlin*, False is otherwise
        """

        # Check if target is *merlin*
        if self.players_info[target]['character'] == 'merlin':
            return True
        else:
            return False


    def use_lake_lady_power(self, target):
        """
        To use lake lady power to reveal player's side, and update player's knowledge accordingly.
        Special character's knowledge will be updated more widely if he/she reveals other special
        character's side. For instance:

        1) All good side player will be revealed their side to *merlin* if he revealed *mordred*.
        2) Both *merlin*/*morgana* identity will be known by *percival* if he revealed either one of
        them.
        3) All good side player will be also revealed their side to specific evil player, if he
        revealed *oberon*.

        The lady of the lake's power will be passed to the target, and the new lady of the lake
        will be removed from self.lake_lady_pool.
        :param target:
        :return:
        """
        reveal_side = self.players_info[target]['side']

        self.players_info[self.lake_lady]['knowledge'][target] = reveal_side
        if self.has_mordred and self.lake_lady == self.merlin and target == self.mordred:
            for nickname in self.good_players:
                self.players_info[self.lake_lady]['knowledge'][nickname] = 'good'

        elif self.lake_lady == self.percival and target in [self.merlin, self.morgana]:
            self.players_info[self.lake_lady]['knowledge'][self.merlin] = 'good'
            self.players_info[self.lake_lady]['knowledge'][self.morgana] = 'evil'

        elif self.has_oberon and target == self.oberon and self.players_info[self.lake_lady]['side'] == 'evil':
            for nickname in self.good_players:
                self.players_info[self.lake_lady]['knowledge'][nickname] = 'good'

        self.lake_lady = target
        self.lake_lady_pool.remove(target)


    def show_players_info(self):
        """
        To pretty print player info. Pretty table library is used in here.

        Reference example as shown below:
        +----------+---------------+------+----------+-----------+---------+---------+---------+---------+---------+
        | nickname |   character   | side | position | lake_lady |  name1  |  name2  |  name3  |  name4  |  name5  |
        +----------+---------------+------+----------+-----------+---------+---------+---------+---------+---------+
        |  name1   | loyal servant | good |    0     |   False   | unknown | unknown | unknown | unknown | unknown |
        |  name2   |    assassin   | evil |    1     |   False   | unknown |   evil  | unknown | unknown | unknown |
        ...
        +----------+---------------+------+----------+-----------+---------+---------+---------+---------+---------+
        :return:
        """
        print('Player info')
        # Define pretty table object
        t = PrettyTable()
        # Get the list of header by iterating the player_info keys
        # The reason to do this is because we need to convert nested dictionary to a table
        # You could refer players_info dict structure in function self.assign_characters()
        # This will get ['character', 'side', 'position', ..., 'knowledge']
        field_names = [i for i in list(self.players_info.values())[0]]
        # Insert 'nickname' to be the first header
        field_names.insert(0, 'nickname')
        # Remove the last item 'knowledge' as it needs to be replaces by list of player's nicknames
        field_names = field_names[:-1]
        # Combine player's nickname at the end of list
        # Note that the nickname sequence here is matter, which need to be the same as self.positions
        field_names = field_names + self.positions
        # Assign field names to pretty table object
        t.field_names = field_names

        # Generate table content by iterating players_info items
        for nickname, details in self.players_info.items():
            # define row as the data row to be inserted into table
            # insert player's nickname as the first item
            row = [nickname]
            # Then iterate the details
            for key, value in details.items():
                # define another row for knowledge and insert items under knowledge to here
                row_know = []
                if key == 'knowledge':
                    for k, v in value.items():
                        row_know.append(v)
                # insert other items accordingly to row
                else:
                    row.append(value)

                # combine row and row for knowledge, as data of knowledge need to be at the end of the row
                row = row + row_know

            # add data row to table
            t.add_row(row)

        # print table
        print(t)
        print()

    def show_game_info(self):
        """
        To pretty print game info
        :return:
        """
        print()
        print('#############################################################################')
        print('Game info')
        print('Number of player:', self.n_players)
        print('Number of good side:', self.n_good)
        print('Number of evil side:', self.n_evil)
        print('Members for each quest:', self.quests)
        print('4th quest needs 2 cards to be failed:', self.has_2_failed_cards)
        print('Mordred:', self.has_mordred)
        print('Oberon:', self.has_oberon)
        print('Lady of the lake:', self.has_lake_lady)
        print('leader:', self.leader)
        print('lady of the lake:', self.lake_lady)
        print('#############################################################################')
        print()


    def show_game_history(self, cheat=False):
        """
        To pretty print game history as table, which are recorded as dict format.
        Mainly is to let players refer the voting history to analyse other player's side or
        identity.
        Pretty table library is used here.
        :param cheat: If cheat mode is on, the history will show the identity of each player.
        :return:
        """
        print('Game history')
        t = PrettyTable()
        # header for 'quest round', 'voting round', 'leader' and 'members'
        field_names = ['Q', 'R', 'L', 'M']
        # Then put player's nicknames as the following header
        # if cheat mode on, player's nickname with * indicates this player is evil side
        if cheat:
            nickname_with_star = []
            for nickname in self.nicknames:
                if self.players_info[nickname]['side'] == 'evil':
                    nickname_with_star.append(nickname + '*')
                else:
                    nickname_with_star.append(nickname)
            field_names = field_names + nickname_with_star
        else:
            field_names = field_names + self.nicknames

        # The extented headers will be add after nicknames
        # There are 'voting result', 'number of fail' and 'quest result'
        extended_field_names = ['VR', 'F', 'QR']

        t.field_names = field_names + extended_field_names

        # Generate table content by iterating self.proposals
        for proposal in self.proposals:
            q = '-'
            r = '-'
            l = '-'
            m = '-'
            v = []
            vr = 'N/A'
            f = '-'
            qr = '-'
            for key, value in proposal.items():
                # assign value accordingly
                if key == 'quest_round': q = value + 1
                if key == 'voting_round': r = value + 1
                if key == 'leader': l = value
                if key == 'members':
                    # if cheat mode on, the nickname with * in members field indicates the player
                    # is on evil side
                    # 'members' is in list format, convert it to string by using join function
                    if cheat:
                        m = []
                        for nn in value:
                            if self.players_info[nn]['side'] == 'evil':
                                m.append(nn + '*')
                            else:
                                m.append(nn)
                        m = ', '.join(m)
                    else:
                        m = ', '.join(value)

                # assign voting value, convert true to 1 and false to 0 to save space
                if key == 'votes':
                    for val in value.values():
                        if val: v.append(1)
                        else: v.append(0)
                if key == 'voting_result': vr = value
                # if cheat mode on, 'queat_attempt' field would show the player's nickname
                # who attempted to fail the quest.
                # Otherwise it would be just showing the number of fail card.
                if cheat:
                    if key == 'quest_attempts':
                        temp = []
                        for nn, success in value.items():
                            if not success: temp.append(nn)
                        f = ', '.join(temp)
                else:
                    if key == 'n_fail': f = value
                if key == 'quest_result': qr = value

            # This is to put dummy value to 'voting' to handle null voting value that came
            # from 5th voting round.
            if v == []: v = ['-' for i in range(self.n_players)]

            # Combine the values in correct sequence in data row and insert into table
            row = [q, r, l, m] + v + [vr, f, qr]
            t.add_row(row)

        print(t)
        # print description for short form headers
        print('Q = Quest Number, R = Voting Round, L = Leader, M = Members for doing quest,'
              'VR = Voting Result, F = Fail Cards Number, QR = Quest Result')
        if cheat:
            print('* = evil side player')
        print()


    def simulate_game(self):
        # TODO add a verbose option in this function
        """
        To simulate the game with random value, would be useful for testing purpose.
        Might be worth to enhance with user input value in future.

        :return:
        """

        # Display game and players info

        self.show_game_info()
        self.show_players_info()

        quest_round = 0

        print('Game Start')

        # Iterating the self.quests, which store the n of players to do the quest for each quest
        for n_members in self.quests:

            # Player could start using the lady of the lake's power when quest round 2 is end
            # which also means before quest round 3.
            if self.has_lake_lady and quest_round >= 2: # this is round 3 or more
                # TODO record lake lady action in history
                # Randomly decide if player with lake lady card wants to use the power
                trigger_lake_lady = random.choice([True, False])
                if trigger_lake_lady:
                    print('The lady of the lake {} decided to use her power.'.format(self.lake_lady))
                    # select target from pool
                    target = random.choice(self.lake_lady_pool)
                    print('She picked {} to reveal his/her loyalty.'.format(target))
                    self.use_lake_lady_power(target)
                    print('She gained the knowledge and {} becomes the lady of the lake.\n'.format(target))

                else:
                    print('The lady of the lake {} decided not to use her power.\n'.format(self.lake_lady))

            print('Quest {} starts, need {} members to do the quest.\n'.format(quest_round + 1,
                                                                           n_members))
            # initialise voting round
            voting_round = 0
            voting_res = 'rejected'

            # keep changing leader until the proposal got majority support or more than 4 voting round
            while voting_res != 'approved':
                print('Voting round {}.\n'.format(voting_round + 1))
                print('Current leader is {}.\n'.format(self.leader))
                # leader randomly picks up players to do quest based on the required number
                members = random.sample(self.nicknames, n_members)
                print(', '.join(members), 'are selected by {} to do the quest.\n'.format(self.leader))
                # Generate proposal
                proposal = self.quest_proposal(self.leader,
                                               quest_round,
                                               voting_round,
                                               n_members,
                                               members
                                               )

                # If not the 5th voting round for the quest, players still get to vote
                # Otherwise whoever the leader picks would be approved automatically
                # Therefore 5th voting round WOULD NOT have any voting history
                if voting_round < 4:
                    print('The rest are now voting.')
                    print('--------------------------------------------------------------------------')
                    for nickname in self.nicknames:
                        # Each player votes randomly
                        is_approved = random.choice([True, False])
                        print('{} voted {v}.'.format(nickname, v='approved' if is_approved else 'rejected'))
                        self.vote_proposal(nickname, is_approved, proposal)
                    print('--------------------------------------------------------------------------')

                    # Get voting result
                    voting_res = self.get_voting_result(proposal)
                    print('Total {} voted approved and {} voted rejected.'.format(proposal['n_approved'],
                      self.n_players - proposal['n_approved']))

                else:
                    print('This is 5th round of proposal so no vote is needed.')
                    print('Whoever the leader propose will be approved.')
                    voting_res = 'approved'

                # if voting result is not 'approved' mean this proposal is end
                # Save the proposal in self.proposals list before it is initialised
                if voting_res != 'approved':
                    self.proposals.append(proposal)
                print('The proposal is {}.\n'.format(voting_res))

                voting_round += 1

            # Players who are picked are now doing the quest.
            print(', '.join(members), 'are now doing quest.')
            print('--------------------------------------------------------------------------')
            for member in members:
                # Good players in the group member must attempt to succeed the quest.
                # Evil players in the group randomly attempt to succeed or fail the quest.
                if self.players_info[member]['side'] == 'good':
                    is_success = True
                    print('{} attempted to succeed the quest'.format(member))
                else:
                    is_success = random.choice([True, False])
                    print('{} attempted to {a} but nobody know.'.format(member,
                                                      a='pretend to succeed the quest' if is_success
                                                      else 'fail the quest'))

                self.do_quest(member, is_success, proposal)
            print('--------------------------------------------------------------------------')

            # Get quest result
            quest_result, end_game = self.get_quest_result(proposal)
            print('Quest {} is {r}'.format(quest_round + 1, r= 'success, well done!' if quest_result == 'success'
                                           else 'fail, we have snake among us!'))

            # Revise past quest result
            print('We have now {} successful quest(s) and {} failed quest(s)\n'.
                  format(self.quest_results.count('success'), self.quest_results.count('fail')))

            # As the quest is end, save the proposal in self.proposals list.
            self.proposals.append(proposal)

            # Check if either side have won 3 quests.
            if end_game is not None:
                if end_game == 'good':

                    # If good side have won 3 quests, assassin from evil side could try to
                    # assassinate *merlin*
                    print('Good side have succeed 3 quests.')
                    print('Now the assassin {} is trying to assassinate merlin...'.format(self.assassin))

                    # Assassom randomly picks 1 player from self.good_players list
                    target = random.choice(self.good_players)
                    print('He picked {}!'.format(target))

                    # Check if the target is *merlin* If yes, evil side win
                    # Otherwise good side win
                    if self.assassinate_merlin(target):
                        print('And he successfully identified merlin and kill him!')
                        print('Evil side win! End game!')
                    else:
                        print('And he picked the wrong guy!')
                        print('Good side win! End game!')

                else:
                    print('Evil side have failed 3 quests.')
                    print('Evil side win! End game!\n')

                # break the for loop since the game is end before completed 5 quests
                break

            quest_round += 1

        self.show_players_info()
        self.show_game_history(True)

