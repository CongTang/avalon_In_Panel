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
    #speak_time = param.Integer(default=60, doc = 'The timmer value in second')
    
    def __init__(self,**params):
        """
        init the class, define all the button here
        """
        super().__init__(**params)
        
        self.start_button = pn.widgets.Toggle(
            name='Start Timmer',
            value=False,
            button_type = 'success',
            height = 125,
            width = 125
        )
        self.reset_button = pn.widgets.Button(
            name = 'reset_timmer',
            button_type = 'warning',
            height = 125,
            width = 125
        )
        self.audio = pn.pane.Audio(
            'ES_Sci Fi Alarm 12 - SFX Producer.mp3', 
            name='Audio'
        )
        
        self.time_silder = pn.widgets.IntSlider(
            name = 'Time Slider', 
            start = 0, 
            end = 60, 
            step = 5, 
            value = 60,
            width = 400,
            height = 50
            
        )
        self.timmer = pn.indicators.Gauge(
            name='Timmer', 
            value=self.time_silder.value, 
            bounds=(0, self.time_silder.value),
            format = '{value} S'
        )
      
    def timmer_update(self)-> None:
        """
        A funtion for timmer update. Call by cb(pn.state.add_periodic_callback)
        """
        self.timmer.value = self.timmer.value-1

        if self.timmer.value == 0:
            self.audio.paused = False
            
            #code below is not work??!!
            #self.start_buttom.value = False
            #self.timmer.value = self.speak_time 
            #print('triggered')         
            
    def reset_click(self,event)-> None:
        """
        reset button event. when click reset timmer value
        """
        self.start_button.value = False
        self.timmer.value = self.time_silder.value
    
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
                pn.Column(
                    self.start_button,
                    self.reset_button  
                ),
                self.timmer),
            self.time_silder,
            self.audio
            
        )          
    
    def __panel__(self)-> pn.Column:
        """
        Panel method. Call this funtion when the class is used in panel layout obj
        """
        return self.layout()

if __name__ == "__main__": 
    pn.Column(
        Timmer_page()
    ).show();