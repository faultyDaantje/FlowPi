#made by Daniël van Belzen
#I'm to lazy to do comments ¬_¬

import _thread
import time
from Max6675 import MAX6675
from machine import Pin
from machine import I2C
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

so = Pin(15, Pin.IN)
sck = Pin(13, Pin.OUT)
cs = Pin(14, Pin.OUT)
max = MAX6675(sck, cs , so)

I2C_ADDR     = 0x3F
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

start_btn = Pin(16, Pin.IN, Pin.PULL_DOWN)
stop_btn = Pin(17, Pin.IN, Pin.PULL_DOWN)
door_check = Pin(18, Pin.IN, Pin.PULL_DOWN)

def stopwatch():
    global timer
    timer = timer + 1
    print(timer)
def readTemp():
    global temp
    temp = max.read()
    time.sleep(1)
def currentFase(num):
    global FaseName
    global FaseTime
    global TotalTime
    global EndHeat
    global TargetTemp
    FaseName = "none"
    if num == 1:
        FaseName = "Preheat"
        FaseTime = float(time2) - float(time1)
        TotalTime = int(time2)
        EndHeat = heat2
        TargetTemp = ((float(EndHeat)-float(startheat))/float(FaseTime)*(float(timer)-float(time1))+float(startheat))
        print("target =" + str(TargetTemp))
    if num == 2:
        print("startheat =" + str(startheat))
        FaseName = "soak"
        FaseTime = float(time3) - float(time2)
        TotalTime = int(time3)
        EndHeat = heat3
        TargetTemp = ((float(EndHeat)-float(startheat))/float(FaseTime)*(float(timer)-float(time2))+float(startheat))
        print("target =" + str(TargetTemp))
    if num == 3:
        FaseName = "ReflowRamp"
        FaseTime = float(time4) - float(time3)
        TotalTime = int(time4)
        EndHeat = heat4
        TargetTemp = ((float(EndHeat)-float(startheat))/float(FaseTime)*(float(timer)-float(time3))+float(startheat))
        print("target =" + str(TargetTemp))
    if num == 4:
        FaseName = "Reflow"
        FaseTime = float(time5) - float(time4)
        TotalTime = int(time5)
        EndHeat = heat5
        TargetTemp = ((float(EndHeat)-float(startheat))/float(FaseTime)*(float(timer)-float(time4))+float(startheat))
        print("target =" + str(TargetTemp))
    if num == 5:
        FaseName = "Cooling"
        FaseTime = 0
        TotalTime = 100000
        EndHeat = 0
        TargetTemp = ((float(EndHeat)-float(startheat))/float(FaseTime)*(float(timer)-float(time5))+float(startheat))
        print("target =" + str(TargetTemp))
    TargetTemp = round(TargetTemp, 2)         
            
def core0():
    import network
    import socket
    import re
    
    global heat1
    global heat2
    global heat3
    global heat4
    global heat5
    global time1
    global time2
    global time3
    global time4
    global time5
    global startbool
    global response
    global writer
    global ipaddress
    startbool = False
    ipaddress = 'connecting...'
    from secrets import secrets

    from machine import Pin
    import uasyncio as asyncio
    
    DataBase=open("DataBase.csv","r")
    dataset = DataBase.read().split(",")
    DataBase.close()


    heat1 = dataset[0]
    heat2 = dataset[1]
    heat3 = dataset[2]
    heat4 = dataset[3]
    heat5 = dataset[4]

    time1 = dataset[5]
    time2 = dataset[6]
    time3 = dataset[7]
    time4 = dataset[8]
    time5 = dataset[9]

    global relay
    
    
    relay = Pin(2, Pin.OUT)
    onboard = Pin("LED", Pin.OUT, value=0)

    expression = re.compile("\D+")

    ssid = secrets['ssid']
    password = secrets['pw']
    
    # Function to load in html page    
    def get_html(html_name):
        with open(html_name, 'r') as file:
            html = file.read()
        return html
    def get_css(css_name):
        with open(css_name, 'r') as file:
            cssstring = file.read()
        return cssstring
            
    wlan = network.WLAN(network.STA_IF)
    main_html = get_html('index.html')
    def replace_html():
        main_html = get_html('index.html')
        
        main_html = main_html.replace('val1', heat1)
        main_html = main_html.replace('val2', heat2)
        main_html = main_html.replace('val3', heat3)
        main_html = main_html.replace('val4', heat4)
        main_html = main_html.replace('val5', heat5)
        main_html = main_html.replace('val6', time1)
        main_html = main_html.replace('val7', time2)
        main_html = main_html.replace('val8', time3)
        main_html = main_html.replace('val9', time4)
        main_html = main_html.replace('val0', time5)
        
        return main_html

    response = main_html

    about_html = get_html('about.html')
    cssresponse = get_css('style.css')
    def connect_to_network():
        wlan.active(True)
        wlan.config(pm = 0xa11140)  # Disable power-save mode
        wlan.connect(ssid, password)

        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)

        if wlan.status() != 3:
            raise RuntimeError('network connection failed')
        else:
            global ipaddress
            print('connected')
            status = wlan.ifconfig()
            ipaddress = status[0]
            print('ip = ' + status[0])
        currenthtml = get_html('index.html')
    async def serve_client(reader, writer):
        print("Client connected")
        request_line = await reader.readline()
        print("Request:", request_line)


        # We are not interested in HTTP request headers, skip them
        while await reader.readline() != b"\r\n":
            pass

        request = str(request_line)
        findGet = request.find('GET')
        heat = request.find('Heat')
        times = request.find('Time')
        print(request)
        print('get = ' + str(findGet))
        start = request.find('/?start=')
        stop = request.find('/?stop=')
        print( 'relay on = ' + str(start))
        print( 'relay off = ' + str(stop))
        submit = request.find('submit')
        if findGet != -1:
            css = request.find('/style.css')
            about = request.find('/about.html')
            if css != -1:
                print("css requested")
                writer.write('HTTP/1.0 200 OK\r\nContent-type: text/css\r\n\r\n')
                writer.write(cssresponse)
        if heat != -1 and times != -1:    
            request_list = expression.split(request_line)
            print("matches:", request_list)
            heat1 = int(request_list[1])
            heat2 = int(request_list[2])
            heat3 = int(request_list[3])
            heat4 = int(request_list[4])
            heat5 = int(request_list[5])
            time1 = int(request_list[6])
            time2 = int(request_list[7])
            time3 = int(request_list[8])
            time4 = int(request_list[9])
            time5 = int(request_list[10])
            DataBase=open("DataBase.csv","w")
            DataBase.write(str(heat1) +",")
            DataBase.write(str(heat2)+",")
            DataBase.write(str(heat3)+",")
            DataBase.write(str(heat4)+",")
            DataBase.write(str(heat5)+",")
            DataBase.write(str(time1) +",")
            DataBase.write(str(time2)+",")
            DataBase.write(str(time3)+",")
            DataBase.write(str(time4)+",")
            DataBase.write(str(time5))
            DataBase.close()
            print("uploaded to db!")
            replace_html()
        if submit != -1:
            machine.reset()
        if about != -1:
            writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            writer.write(about_html)
        else:
            response = replace_html()
            writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            writer.write(response)    
        

        if start == 6:
            global startbool
            print("start")
            startbool = False
            startbool = True
            print(startbool)
            
        
        if stop == 6:
            global startbool
            print("stop")
            startbool = False
        
        

        await writer.drain()
        await writer.wait_closed()
        print("Client disconnected")
        
        
    async def main():
        print('Connecting to Network...')
        connect_to_network()

        print('Setting up webserver...')
        asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
        while True:
            onboard.on()
            print("heartbeat")
            await asyncio.sleep(0.25)
            onboard.off()
            await asyncio.sleep(5)
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()




def core1():
    i2c = I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
    lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
    lcd.move_to(5,0)
    lcd.putstr("FlowPI")
    lcd.move_to(2,1)
    lcd.putstr("By Daniel vB")
    lcd.clear()
    time.sleep(1)
    global startbool
    print(startbool)
    global timer
    timer = 0
    global temp
    temp = 20
    global startheat
    readTemp()
    startheat = temp
    fasecount = 1
    currentFase(fasecount)
    lcd.putstr(ipaddress)
 
    
    while True:
        if start_btn.value() == True:
            print("start")
            startbool = False
            startbool = True
            print(startbool)
            
        
        if stop_btn.value() == True:
            print("stop")
            startbool = False
        if door_check.value() == False and startbool == True:
            lcd.clear()
            lcd.move_to(0,0)
            lcd.putstr("Abborted")
            lcd.move_to(0,1)
            lcd.putstr("pls close door")
            startbool = False
            time.sleep(1)
        if startbool == True:
            stopwatch()
            readTemp()
            print(temp)
            lcd.clear()
            lcd.move_to(0,0)
            lcd.putstr(FaseName)
            lcd.putstr("  " + str(timer))
            lcd.move_to(0,1)
            lcd.putstr(str(temp))
            lcd.putstr('/')
            lcd.putstr(str(TargetTemp))
            lcd.putstr('C')
            
            

            if timer < TotalTime:
                currentFase(fasecount)
                print(FaseName)
                if temp - 1 > TargetTemp:
                    relay.value(0)
                elif temp + 1 < TargetTemp:
                    relay.value(1)
                    
            else:
                fasecount = fasecount + 1
                print("total =" + str(TotalTime))
                print(fasecount)
                currentFase(fasecount)
                startheat = temp
        else:
            lcd.clear()
            lcd.move_to(0,0)
            lcd.putstr(ipaddress)
            time.sleep(1)
            
                   


        

        
second_thread = _thread.start_new_thread(core1, ())

core0()