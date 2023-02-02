import panel as pn#
import pandas as pd
import numpy as np


pn.extension(sizing_mode='stretch_width',notifications=True) 
# sizing_mode='stretch_width'，让panel的宽度和浏览器的宽度一致，notifications=True，让panel的通知显示在浏览器的右下角


"""
key funtions:
1.Log in 
    1.1 a log in page to recorginize user or admin
    1.2 user page to show user's information and waiting game to be started
    1.3 amidn page to show all users' information and start game 

2. Game
    2.1 Admin page
        2.1.1 Game confguration(game settings)
        2.1.2 show table and change table order
        2.1.3 start game
        2.1.4 start mission memeber vote
        2.1.5 show mission memeber vote result
        2.1.6 start mission
        2.1.7 show mission result
        2.1.8 display repert mission memeber vote number
        2.1.9 display vote history
        2.1.10 display timmer
        2.1.11 random select start position and given huzhong meiren 
        
    2.2 User page
        2.2.1 see your role and description
        2.2.2 vote for mission memeber
        2.2.3 vote for mission
        2.2.4 start timmer
        2.2.5 check history vote result
        
"""
