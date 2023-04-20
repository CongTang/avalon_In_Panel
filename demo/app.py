import pprint
import time
import threading
import panel as pn
from panel.viewable import Viewer
from lib.game import Avalon

pn.extension(notifications=True, sizing_mode='stretch_both')
nickname = pn.widgets.StaticText(name='player', value='')
pn.state.location.sync(nickname, {'value': 'nickname'})
if 'nicknames' not in pn.state.cache:
    pn.state.cache['nicknames'] = []
    pn.state.cache['admin'] = None
    pn.state.cache['avalon'] = None
    pn.state.cache['members'] = []
    pn.state.cache['assassin_target'] = None
    pn.state.cache['lake_lady_target'] = None
    pn.state.cache['timer'] = 20

template = pn.template.BootstrapTemplate(title='Welcome to Avalon')
app = pn.Column()


def watch_game(avalon):
    while True:
        avalon.api_server_run()
        if avalon.end_game or not pn.state.cache['avalon']:
            return


class MainPage(Viewer):
    def __init__(self, **params):
        super().__init__(**params)
        self.stop = None
        self.avalon = pn.state.cache['avalon']
        self.nickname = pn.widgets.StaticText(name='Nickname', value=nickname.value)
        self.stage = pn.widgets.StaticText(name='Stage', value=self.avalon.game_param['stage'])
        self.leader = pn.widgets.StaticText(name='Leader', value=self.avalon.game_param['leader'])
        self.lake_lady = pn.widgets.StaticText(name='Lady of Lake',
                                               value=self.avalon.game_param['lake_lady'] if self.avalon.has_lake_lady
                                               else 'N/A')
        self.quest_buttons = [pn.widgets.Button(name=f'Quest {i + 1} ({self.avalon.quests[i]} members)',
                                                button_type='primary' if i < self.avalon.game_param[
                                                    'quest'] else 'default',
                                                disabled=True) for i in range(5)]
        self.round_buttons = [pn.widgets.Button(name=f'Round {i + 1}',
                                                button_type='primary' if i < self.avalon.game_param[
                                                    'round'] else 'default',
                                                disabled=True) for i in range(5)]
        self.nickname_buttons = [pn.widgets.Button(name=n,
                                                   button_type=self.get_nickname_button_type(n),
                                                   disabled=True) for n in self.avalon.p_positions]
        self.timer = pn.indicators.Number(name='Timer', value=pn.state.cache['timer'], visible=False)
        self.lake_lady_btn = pn.widgets.Button(name='Select', visible=False)
        self.speak_btn = pn.widgets.Button(name='Start Speak', visible=False)
        self.propose_btn = pn.widgets.Button(name='Propose', visible=False)
        self.vote_buttons = [pn.widgets.Button(name=card, visible=False) for card in self.avalon.vote_cards]
        self.attempt_buttons = [pn.widgets.Button(name=card, visible=False) for card in self.avalon.quest_cards]
        self.assassinate_btn = pn.widgets.Button(name='Assassinate', visible=False)
        self.new_game_btn = pn.widgets.Button(name='New Game', visible=False)
        self.game_info_btn = pn.widgets.Button(name='Show Game Info', button_type='warning')
        self.player_info_btn = pn.widgets.Button(name='Show Player Info', button_type='warning')
        self.record_btn = pn.widgets.Button(name='Show Records', button_type='warning')
        self.ai_btn = pn.widgets.Button(name='trigger ai move', button_type='danger', visible=False)
        self.debug_btn = pn.widgets.Button(name='debug', button_type='danger')

    def show_buttons(self, target):
        row = pn.Row()
        for btn in getattr(self, target):
            row.append(btn)
        return pn.Column(row)

    def get_nickname_button_type(self, n):
        target = []
        if self.avalon.game_param['stage'] in ['proposal', 'vote', 'quest']:
            if self.avalon.game_param['members']:
                target = self.avalon.game_param['members']
            else:
                target = pn.state.cache['members']
        elif self.avalon.game_param['stage'] == 'lake_lady':
            target = [pn.state.cache['lake_lady_target']]
        elif self.avalon.game_param['stage'] == 'end' and self.avalon.game_param['win_3_quests'] == 'good':
            target = [pn.state.cache['assassin_target']]
        if n in target:
            return 'primary'
        else:
            return 'default'

    def lake_lady_btn_click(self, event):
        if pn.state.cache['lake_lady_target']:
            self.avalon.use_lake_lady_power(nickname.value, pn.state.cache['lake_lady_target'])
            pn.state.notifications.clear()
            pn.state.notifications.success(f"You have picked {pn.state.cache['lake_lady_target']} and he is on "
                                           f"{self.avalon.players_info[pn.state.cache['lake_lady_target']]['side']} "
                                           f"side.",
                                           duration=4000)
            pn.state.cache['lake_lady_target'] = None

        else:
            self.avalon.use_lake_lady_power(nickname.value, None)
            pn.state.notifications.clear()
            pn.state.notifications.success(f'You decided not to use your power.', duration=4000)

    def timer_countdown(self):
        self.stop = False
        t = self.timer.value
        while t >= 0:
            pn.state.cache['timer'] = t
            self.timer.value = t
            time.sleep(1)
            t -= 1
            if self.stop:
                pn.state.cache['timer'] = 20
                break

    def speak_btn_click(self, event):
        if self.speak_btn.name == 'End Speak':
            self.stop = True
            self.avalon.end_speak(nickname.value)
            self.speak_btn.name = 'Start Speak'
            self.speak_btn.disabled = True
            pn.state.cache['timer'] = 20
        else:
            self.speak_btn.name = 'End Speak'
            self.stop = False
            thread = threading.Thread(target=self.timer_countdown)
            thread.start()

    def nickname_btn_click(self, event):
        if self.avalon.game_param['stage'] in ['speak', 'proposal']:
            if event.obj.button_type == 'default':
                if len(pn.state.cache['members']) < self.avalon.game_param['n_members']:
                    event.obj.button_type = 'primary'
                    pn.state.cache['members'].append(event.obj.name)
                else:
                    pn.state.notifications.clear()
                    pn.state.notifications.error(f"You have selected more than {self.avalon.game_param['n_members']}",
                                                 duration=4000)
            else:
                event.obj.button_type = 'default'
                pn.state.cache['members'].remove(event.obj.name)
        elif self.avalon.game_param['stage'] in ['lake_lady', 'end']:
            if event.obj.button_type == 'default':

                for btn in self.nickname_buttons:
                    btn.button_type = 'default'
                event.obj.button_type = 'primary'
                if self.avalon.game_param['stage'] == 'lake_lady':
                    pn.state.cache['lake_lady_target'] = event.obj.name
                else:
                    pn.state.cache['assassin_target'] = event.obj.name

            else:
                event.obj.button_type = 'default'
                if self.avalon.game_param['stage'] == 'lake_lady':
                    pn.state.cache['lake_lady_target'] = None
                else:
                    pn.state.cache['assassin_target'] = None

    def propose_btn_click(self, event):
        if pn.state.cache['members'] and len(pn.state.cache['members']) == self.avalon.game_param['n_members']:
            self.avalon.propose_quest(nickname.value, pn.state.cache['members'])
            pn.state.cache['members'] = []
        else:
            pn.state.notifications.clear()
            pn.state.notifications.error(f"Please select {self.avalon.game_param['n_members']} members!",
                                         duration=4000)

    def vote_btn_click(self, event):
        for btn in self.vote_buttons:
            btn.disabled = True
        self.avalon.vote_quest(nickname.value, event.obj.name)

    def attempt_btn_click(self, event):
        self.avalon.do_quest(nickname.value, event.obj.name)
        for btn in self.attempt_buttons:
            btn.disabled = True

    def assassinate_btn_click(self, event):
        if pn.state.cache['assassin_target']:
            self.avalon.assassinate(nickname.value, pn.state.cache['assassin_target'])
            self.assassinate_btn.disabled = True
        else:
            pn.state.notifications.clear()
            pn.state.notifications.error(f"Please select a target!",
                                         duration=4000)

    def new_game_btn_click(self, event):
        pn.state.cache['avalon'] = None
        app.clear()
        app.append(WaitPage(nickname=nickname.value))
        self.callback.stop()

    def game_info_btn_click(self, event):
        print(self.avalon.show_game_info())

    def player_info_btn_click(self, event):
        print(self.avalon.show_players_info(nickname.value))

    def record_btn_click(self, event):
        print(self.avalon.show_game_records(nickname))

    def auto_callback(self):
        if not pn.state.cache['avalon']:
            app.clear()
            app.append(WaitPage(nickname=nickname.value))
        self.stage.value = self.avalon.game_param['stage']
        self.leader.value = self.avalon.game_param['leader']
        for i in range(5):
            if i < self.avalon.game_param['quest']:
                if i == self.avalon.game_param['quest'] - 1 and self.avalon.game_param['stage'] != 'end':
                    self.quest_buttons[i].button_type = 'primary'
                else:
                    if self.avalon.game_param['quest_results'][i] == 'success':
                        self.quest_buttons[i].button_type = 'success'
                    else:
                        self.quest_buttons[i].button_type = 'danger'
            if i < self.avalon.game_param['round']:
                self.round_buttons[i].button_type = 'primary'
            else:
                self.round_buttons[i].button_type = 'default'
        if nickname.value == pn.state.cache['admin']:
            self.new_game_btn.visible = True

        if self.avalon.game_param['stage'] == 'lake_lady':
            if not pn.state.cache['lake_lady_target']:
                for btn in self.nickname_buttons:
                    btn.button_type = 'default'
            for btn in self.vote_buttons + self.attempt_buttons:
                btn.visible = False
            if nickname.value == self.avalon.game_param['lake_lady']:
                for btn in self.nickname_buttons:
                    if btn.name not in self.avalon.game_param['p_no_lake_lady']:
                        btn.disabled = True
                    else:
                        btn.disabled = False
                self.lake_lady_btn.visible = True

            if self.avalon.game_param['lake_lady'] in self.avalon.ai_nicknames and \
                    nickname.value == pn.state.cache['admin']:
                self.ai_btn.visible = True
            else:
                self.ai_btn.visible = False

        elif self.avalon.game_param['stage'] in ['speak', 'proposal']:
            # previous stage could be either 'vote' or 'quest'
            for btn in self.vote_buttons + self.attempt_buttons + [self.lake_lady_btn]:
                btn.visible = False
            # if new round init nickname buttons
            if all(len(n) == 0 for n in [self.avalon.game_param['members'], pn.state.cache['members']]):
                for btn in self.nickname_buttons:
                    btn.button_type = 'default'
            for btn in self.nickname_buttons:
                if nickname.value == self.avalon.game_param['leader']:
                    btn.disabled = False
                else:
                    btn.button_type = self.get_nickname_button_type(btn.name)
                    btn.disabled = True

            if self.avalon.game_param['stage'] == 'speak':
                self.ai_btn.visible = False
                if nickname.value == self.avalon.game_param['speaker']:
                    self.speak_btn.disabled = False
                    self.speak_btn.visible = True
                else:
                    self.speak_btn.visible = False
                self.timer.visible = True
                self.timer.value = pn.state.cache['timer']

            else:
                self.speak_btn.visible = False
                self.timer.visible = False
                if nickname.value == self.avalon.game_param['leader']:
                    self.propose_btn.visible = True
                if self.avalon.game_param['leader'] in self.avalon.ai_nicknames and \
                        nickname.value == pn.state.cache['admin']:
                    self.ai_btn.visible = True
                else:
                    self.ai_btn.visible = False

        elif self.avalon.game_param['stage'] == 'vote':
            # previous stage is 'proposal'
            for btn in self.nickname_buttons:
                btn.button_type = self.get_nickname_button_type(btn.name)
            self.propose_btn.visible = False
            self.ai_btn.visible = False
            for btn in self.nickname_buttons:
                btn.disabled = True
            for btn in self.vote_buttons:
                btn.visible = True
                if nickname.value not in self.avalon.game_param['votes'].keys():
                    btn.disabled = False

        elif self.avalon.game_param['stage'] == 'quest':
            # previous stage could be either 'proposal' or 'vote'
            self.propose_btn.visible = False
            for btn in self.nickname_buttons:
                btn.disabled = True
                btn.button_type = self.get_nickname_button_type(btn.name)
            for btn in self.vote_buttons:
                btn.visible = False
            if nickname.value in self.avalon.game_param['members']:
                for btn in self.attempt_buttons:
                    btn.visible = True
                    if nickname.value in self.avalon.game_param['attempts'].keys():
                        btn.disabled = True
                    elif nickname.value in self.avalon.game_param['p_good'] and btn.name == 'fail':
                        btn.disabled = True
                    else:
                        btn.disabled = False
            if all(n in self.avalon.ai_nicknames for n in self.avalon.game_param['members']) and \
                    nickname.value == pn.state.cache['admin']:
                self.ai_btn.visible = True
            else:
                self.ai_btn.visible = False

        elif self.avalon.game_param['stage'] == 'end':
            for btn in self.attempt_buttons:
                btn.visible = False
            if self.avalon.game_param['win_3_quests'] == 'good':
                if not pn.state.cache['assassin_target']:
                    for btn in self.nickname_buttons:
                        btn.button_type = 'default'
                if nickname.value == self.avalon.game_param['assassin']:
                    for btn in self.nickname_buttons:
                        if btn.name in self.avalon.game_param['p_evil']:
                            btn.disabled = True
                        else:
                            btn.disabled = False
                    self.assassinate_btn.visible = True
                if self.avalon.game_param['assassin'] in self.avalon.ai_nicknames and \
                        nickname.value == pn.state.cache['admin']:
                    self.ai_btn.visible = True
                else:
                    self.ai_btn.visible = False

    def debug_btn_click(self, event):
        pprint.pprint(self.avalon.game_param)

    def ai_btn_click(self, event):
        self.avalon.trigger_ai_move(nickname.value)

    def __panel__(self):
        self.callback = pn.state.add_periodic_callback(self.auto_callback, 1000, start=True)
        self.lake_lady_btn.on_click(self.lake_lady_btn_click)
        self.speak_btn.on_click(self.speak_btn_click)
        self.propose_btn.on_click(self.propose_btn_click)
        for btn in self.nickname_buttons:
            btn.on_click(self.nickname_btn_click)
        for btn in self.vote_buttons:
            btn.on_click(self.vote_btn_click)
        for btn in self.attempt_buttons:
            btn.on_click(self.attempt_btn_click)
        self.assassinate_btn.on_click(self.assassinate_btn_click)
        self.new_game_btn.on_click(self.new_game_btn_click)
        self.game_info_btn.on_click(self.game_info_btn_click)
        self.player_info_btn.on_click(self.player_info_btn_click)
        self.record_btn.on_click(self.record_btn_click)
        self.ai_btn.on_click(self.ai_btn_click)
        self.debug_btn.on_click(self.debug_btn_click)
        return pn.Column(self.nickname,
                         self.stage,
                         self.leader,
                         self.lake_lady,
                         self.show_buttons('quest_buttons'),
                         self.show_buttons('round_buttons'),
                         self.show_buttons('nickname_buttons'),
                         self.timer,
                         self.lake_lady_btn,
                         self.speak_btn,
                         self.propose_btn,
                         self.show_buttons('vote_buttons'),
                         self.show_buttons('attempt_buttons'),
                         self.assassinate_btn,
                         self.new_game_btn,
                         self.game_info_btn,
                         self.player_info_btn,
                         self.record_btn,
                         self.ai_btn,
                         self.debug_btn)


class JoinPage(Viewer):
    def __init__(self, **params):
        super().__init__(**params)
        self.welcome_msg = pn.panel("<marquee>Welcome to Avalon Game</marquee>",
                                    style={'font-size': '24pt'})
        self.nickname_input = pn.widgets.TextInput(placeholder='Please type your nickname here...')
        self.join_button = pn.widgets.Button(name='Join game', button_type='primary')

    def join_button_click(self, event):
        error_msg = self.validate_nickname()
        self.notification(error_msg)
        if not error_msg:
            if not pn.state.cache['nicknames']:
                pn.state.cache['admin'] = self.nickname_input.value
            pn.state.cache['nicknames'].append(self.nickname_input.value)
            global nickname
            nickname.value = self.nickname_input.value
            app.clear()
            app.append(WaitPage(nickname=self.nickname_input.value))

    def validate_nickname(self):
        error_msg = None
        if self.nickname_input.value == '':
            error_msg = 'Nickname cannot be blank, please try again.'
        elif self.nickname_input.value in pn.state.cache['nicknames']:
            error_msg = 'This nickname has been used, please try again.'
        return error_msg

    def notification(self, error_msg):
        """
        define raise a notification to show log in success or not
        """
        if error_msg:
            pn.state.notifications.clear()
            pn.state.notifications.error(error_msg, duration=4000)

        else:
            pn.state.notifications.clear()
            pn.state.notifications.success(f'{self.nickname_input.value} joins successfully', duration=4000)

    def __panel__(self):
        self.join_button.on_click(self.join_button_click)
        return pn.Column(self.welcome_msg, self.nickname_input, self.join_button)


class WaitPage(Viewer):
    def __init__(self, **params):
        super().__init__(**params)

        self.is_admin = True if params['nickname'] == pn.state.cache['admin'] else False
        self.n_ai_slider = pn.widgets.IntSlider(name='Number of AI players', start=0, end=9, value=0)
        self.players_cbg = pn.widgets.CheckButtonGroup(name='Players',
                                                       value=[],
                                                       options=pn.state.cache['nicknames'],
                                                       button_type='success',
                                                       disabled=False if self.is_admin else True)
        self.start_game_btn = pn.widgets.Button(name='start game', button_type='success', align='start')
        self.remove_player_btn = pn.widgets.Button(name='remove player', button_type='danger', align='end')
        self.has_percival_cbox = pn.widgets.Checkbox(name='has_percival', value=False)
        self.has_morgana_cbox = pn.widgets.Checkbox(name='has_morgana', value=False)
        self.has_mordred_cbox = pn.widgets.Checkbox(name='has_mordred', value=False)
        self.has_oberon_cbox = pn.widgets.Checkbox(name='has_oberon', value=False)
        self.has_lake_lady_cbox = pn.widgets.Checkbox(name='has_lake_lady', value=False)

    def start_game_btn_click(self, event):
        try:
            avalon = Avalon(pn.state.cache['nicknames'],
                            has_percival=self.has_percival_cbox.value,
                            has_morgana=self.has_morgana_cbox.value,
                            has_mordred=self.has_mordred_cbox.value,
                            has_oberon=self.has_oberon_cbox.value,
                            has_lake_lady=self.has_lake_lady_cbox.value,
                            n_ai=self.n_ai_slider.value,
                            platform='api')
            pn.state.cache['avalon'] = avalon
            thread = threading.Thread(target=watch_game, args=(pn.state.cache['avalon'],))
            thread.start()
            # avalon.game_param['leader'] = nickname.value
            app.clear()
            app.append(MainPage)
        except Exception as e:
            pn.state.notifications.clear()
            pn.state.notifications.error(f'{e}', duration=8000)

    def __panel__(self):
        self.start_game_btn.on_click(self.start_game_btn_click)
        if self.is_admin:
            page = pn.Column(self.n_ai_slider,
                             self.players_cbg,
                             pn.Row(self.start_game_btn,
                                    self.remove_player_btn),
                             pn.Row(self.has_percival_cbox,
                                    self.has_morgana_cbox,
                                    self.has_mordred_cbox,
                                    self.has_oberon_cbox,
                                    self.has_lake_lady_cbox)
                             )
        else:
            page = pn.Column(self.players_cbg)

        return page


pn.state.location.sync(nickname, {'value': 'nickname'})
app.clear()

if nickname.value in pn.state.cache['nicknames']:
    if pn.state.cache['avalon']:
        app.append(MainPage)
    else:
        app.append(WaitPage(nickname=nickname.value))
else:
    app.append(JoinPage)

template.main.append(app)
template.servable()
