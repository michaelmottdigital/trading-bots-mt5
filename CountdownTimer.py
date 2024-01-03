# import the time module 
import time 

def countdown_timer(minutes, seconds):
    t = (minutes * 60) + seconds
    
    while t: 
        mins, secs = divmod(t, 60) 
        status = '{:02d}:{:02d}'.format(mins, secs) 
        print(status, end="\r") 
        time.sleep(1) 
        t -= 1
