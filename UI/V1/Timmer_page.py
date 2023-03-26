import panel as pn
import pandas as pd
import numpy as np
from game import Avalon
import param
from panel.viewable import Viewer

class Timmer_page(Viewer):
    """
    Timmer page class
    
    Parameters:
    -----------
        speak_time (int): The timmer value in second,default:60s

    How to use:
    -----------
    To use it. using pn.Column(Timmer_page(speak_time = 120)).show()
    """
    speak_time = param.Integer(default=60, doc = 'The timmer value in second')
    
    def __init__(self,**params):
        """
        init the class, define all the button here
        """
        super().__init__(**params)
        self.timmer = pn.indicators.Gauge(
            name='Timmer', 
            value=self.speak_time, 
            bounds=(0, self.speak_time),
            format = '{value} S'
        )
        
        self.start_button = pn.widgets.Toggle(
            name='Start Timmer',
            value=False,
            button_type = 'success',
            height = 100,
        )
        self.reset_button = pn.widgets.Button(
            name = 'reset_timmer',
            button_type = 'warning',
            height = 100,
        )
        
        
    def timmer_update(self)-> None:
        """
        A funtion for timmer update. Call by cb(pn.state.add_periodic_callback)
        """
        self.timmer.value = self.timmer.value-1
        if self.timmer.value == 0:
            self.start_buttom.value = False
            self.timmer.value = self.speak_time 
            
    def reset_click(self,event)-> None:
        """
        reset button event. when click reset timmer value
        """
        self.start_button.value = False
        self.timmer.value = self.speak_time
    
    def layout(self)-> pn.Column:
        """
        Define a periodic_callback for timmer, click event and layout
        """
        cb = pn.state.add_periodic_callback(self.timmer_update, 1000)
        try:
            cb.stop()
        except:
            print('cb not start')
        
        self.start_button.link(cb, bidirectional=True, value='running')
        
        self.reset_button.on_click(self.reset_click)
        
        return pn.Column(
            pn.Row(
                self.start_button,
                self.reset_button
            ),
            self.timmer
        )          
    
    def __panel__(self)-> pn.Column:
        """
        Panel method. Call this funtion when the class is used in panel layout obj
        """
        return self.layout()


pn.Column(
    Timmer_page(
        speak_time = 60
    )
).servable();