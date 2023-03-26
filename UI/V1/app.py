import panel as pn#
import pandas as pd
import numpy as np
from game import Avalon
import param
# comms 部分可以取消，如果想要在notebook中运行panel的话，最好可以用vscod或者用jupyter， panel对jupyter的支持的最好的
pn.extension('echarts','notifications',sizing_mode='stretch_both',notifications=True) 
# 用vscode来进行通信，sizing_mode='stretch_width'，让panel的宽度和浏览器的宽度一致，notifications=True，让panel的通知显示在浏览器的右下角
from panel.viewable import Viewer

from Timmer_page import Timmer_page


# game init

user_infor = pd.DataFrame(columns = ['name','character','side','position','lake_lady','knowledge']).set_index('name')
empty = {'character':None,'side':None,'position':None,'lake_lady':None,'knowledge':None,'admin':None}

this_user = ''

player = pn.widgets.StaticText(name='player', value='')

if 'user_infor' not in pn.state.cache:    
    pn.state.cache['user_infor'] = user_infor
    pn.state.cache['game_status'] = game_status = 'waiting player'



template = pn.template.BootstrapTemplate(title='Avalon Game')

app = pn.Column()

template.main.append(app)



class waiting_page(Viewer):
    
    
    # waiting page
    def __init__(self,**params):
        super().__init__(**params)
        self.game_stage_ui = pn.pane.Str(f"""The current game stage is:{pn.state.cache['game_status']}""")
        self.waiting_info = pn.pane.Str(f'waiting player to join the game')
        self.players = pn.widgets.CheckButtonGroup(
            name='Players',
            value=[], 
            options=list(pn.state.cache['user_infor'].index),
            button_type = 'success',
            disabled = True

        )

    def update(self):
        #print('runed')
        self.players.options = list(pn.state.cache['user_infor'].index)

    

    def __panel__(self):
        players_cb = pn.state.add_periodic_callback(self.update, 5000,start  =True,timeout = 120000)# time out 1minute need to set larage when gam lunched
        return  pn.Column(
            self.game_stage_ui,
            self.players,
            self.waiting_info
        )

class Login_page(Viewer):
    """
    Login_page class

    How to use:
    -----------    
    pn.Column(Login_page).show()
    """
  
    def __init__(self,**params):
        super().__init__(**params)
        # 输出玩家名的控件
        self.user_input = pn.widgets.TextInput(
            name='Player Name', 
            placeholder='Please type your user name here...',

        )
        #登录按钮和callback
        self.sign_in_button = pn.widgets.Button(
            name='Join in game',
            button_type='primary',

        )
        self.welcom_str = pn.panel(
            """
            <marquee>Welcome to Avalon Game</marquee>    
            """,
            style={'font-size': '24pt'}
            )

    def user_name_check(self):
        """
        Define a user name check funtion
        """
        user_name = self.user_input.value
        existing_name = list(pn.state.cache['user_infor'] .index)
        if user_name == '':
            return 'name can not be blank, or not please try again',False
        elif user_name in existing_name and pn.state.cache['game_status'] == 'waiting player':
            return 'duplicated name',False
        elif user_name in existing_name and pn.state.cache['game_status'] != 'waiting player':
            return 'relogin',True
        else:
            return '',True
    def Notification(self,txt,sign):
        """
        define raise a notificaion to show log in success or not
        """
        if sign:
            pn.state.notifications.clear()
            pn.state.notifications.success(f'{self.user_input.value} Login Success', duration=4000)  
        else:
            pn.state.notifications.clear()
            pn.state.notifications.error(txt, duration=4000)
            raise f'log in failed cause{txt}'

    def signin_click(self,event):
        """
        sign in event
        add user name into user_infor, then jump to next page
        """
        
        login_status = self.user_name_check()
        self.Notification(login_status[0],login_status[1])
        if login_status[1]:
            pn.state.cache['user_infor'].loc[self.user_input.value] = empty
            global player
            player.value = self.user_input.value
            print(f'{player.value} login to the game now')
            print('=====================')
            print(pn.state.cache['user_infor'])
            print('=====================')
            app.clear()
            app.append(
                pn.Column(
                    waiting_page()
                )
            )
            print('next page')
            
    def __panel__(self):
        
        self.sign_in_button.on_click(self.signin_click)
        #elf.sign_in_button.js_on_click(code = """window.open("/Timmer_page","_self")""")
        return pn.Column(
            self.welcom_str,
            self.user_input, 
            self.sign_in_button
        ) 
      
    # Not IN Used !!!!!!!!!!!!, used dynamic URL solution instead, see the line below
## remove user when user log out
def user_logout(sessionContext):
    #if pn.state.cache['game_status'] == 'waiting player':
    #    pn.state.cache['user_infor']= pn.state.cache['user_infor'].drop(player.value)
    #    print(f"user {player.value} disconnected")
    #    print(f"""reminding user:{pn.state.cache['user_infor']}""")
    #else:
    print(f"user {player.value} disconnected")
    print('but game already started. he will be able to reconnected.')
pn.state.on_session_destroyed(user_logout)
# sync the user name into player widgets. replcament of the logout function
pn.state.location.sync(player, {'value': 'player'})

if not player.value:
    app.clear()
    app.append(Login_page)
elif player.value and player.value in pn.state.cache['user_infor'].index:
    app.clear()
    app.append(
        pn.Column(
            waiting_page()
        )
    )    
else:
    print(f"{pn.state.cache['user_infor'].index}")
    app.clear()
    app.append('player name not registrat in to the game, reply gothough login page')

template.servable();
