import panel as pn
import pandas as pd
import numpy as np
from game import Avalon
import param
from panel.viewable import Viewer
# comms 部分可以取消，如果想要在notebook中运行panel的话，最好可以用vscod或者用jupyter， panel对jupyter的支持的最好的
pn.extension('echarts',sizing_mode='stretch_width',comms = 'vscode',notifications=True) 
# 用vscode来进行通信，sizing_mode='stretch_width'，让panel的宽度和浏览器的宽度一致，notifications=True，让panel的通知显示在浏览器的右下角


class Login_page(Viewer):
    """
    Login_page class

    How to use:
    -----------    
    pn.Column(Login_page).show()
    """
  
    def __init__(self,**params):
        super().__init__(**params)
        self.user_infor = pd.DataFrame(columns = ['name','character','side','position','lake_lady','knowledge']).set_index('name')
        self.empty = {'character':None,'side':None,'position':None,'lake_lady':None,'knowledge':None}
        if 'user_infor' not in pn.state.cache:
            pn.state.cache['user_infor']  = self.user_infor
        if 'game_status' not in pn.state.cache:
            pn.state.cache['game_status'] = game_status = 'waiting player'
        # 输出玩家名的控件
        self.user_input = pn.widgets.TextInput(name='Player Name', placeholder='Please type your user name here...')
        #登录按钮和callback
        self.sign_in_button = pn.widgets.Button(name='Join in game', button_type='primary')
    def user_name_check(self):
        """
        Define a user name check funtion
        """
        user_name = self.user_input.value
        logined_name = list(self.user_infor.index)
        if user_name == '':
            return 'invaild name',False
        elif user_name in logined_name and game_status == 'waiting player':
            return 'duplicated name',False
        elif user_name in logined_name and game_status != 'waiting player':
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
            pn.state.cache['user_infor'].loc[self.user_input.value] = self.empty
            print('next page')
            
    def __panel__(self):
        
        self.sign_in_button.on_click(self.signin_click)
        self.sign_in_button.js_on_click(code = """window.open("/Timmer_page","_self")""")
        return pn.Column(
            'Welcome to Avalon Game',
            self.user_input, 
            self.sign_in_button
        )        
pn.Column(
    Login_page()
).servable();