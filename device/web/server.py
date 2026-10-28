from microdot.microdot import Microdot, Response, redirect, send_file

import uasyncio as asyncio
import os
import json
import math
import time
import gc

from microdot.websocket import with_websocket
from helpers import save_settings
from colors import Color
from constants import DEFAULT_SETTINGS


def start_webserver(device):
    app = Microdot()
    Response.default_content_type = 'text/html'
    
    
    #-------------------------------------------------------------------------------
    def auth_required(func):
        async def wrapper(request, *args, **kwargs):
            if request.cookies.get('auth') == 'authorized':
                return await func(request, *args, **kwargs)
            else:
                return redirect('/login')
        return wrapper
    #-------------------------------------------------------------------------------
    
    def nav(request):
        auth_status = request.cookies.get('auth') == 'authorized'
        
        login_logout = ''
        if auth_status:
            login_logout = '<li><a href="/logout" role="button" class="secondary">Logout</a></li>'
        else:
            login_logout = '<li><a href="/login" role="button">Login</a></li>'
        
        return f'''
        <nav>
            <ul>
                <li><a href="/">HOME</a></li>
            </ul>
            <ul>
                <li><a href="/diagnostics">Diagnostics</a></li>
                <li><a href="/sysinfo">SysInfo</a></li>
                <li><a href="/setup">Setup</a></li>
                {login_logout}
            </ul>
        </nav>
        '''
    
    def html_template(request, title, content):
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <link rel="stylesheet" href="/css/pico.min.css">
            <style>
                header {{ padding-bottom: 20px; }}
            </style>
        </head>
        <body>
            <header class="container">
                {nav(request)}
            </header>
            <main class="container">
                {content}
            </main>
            <footer class="container">
                <small>2026 NAD team, Slovakia, TUKE.</small>
            </footer>
        </body>
        </html>
        '''
    
    

    @app.route('/css/<filename>')
    async def css(request, filename):
        try:
            return send_file('web/css/' + filename, content_type='text/css')
        except OSError:
            return Response('File not found', status_code=404)
    
    @app.route('/')
    async def index(request):
        content = '''
            <article>
                <hgroup>
                    <h1>Control Panel</h1>
                    <h2>Device Management Dashboard</h2>
                </hgroup>
                <p>Welcome to the device control interface. Select an option from the menu or use the quick actions below.</p>
                <footer>
                    <a href="/shutdown" role="button" class="contrast outline">Finish Setup</a>
                </footer>
            </article>
        '''
        return html_template(request, "Home", content)

    @app.route('/shutdown')
    def shutdown(request):
        content = '''
            <article>
                <hgroup>
                    <h2>System Shutdown</h2>
                    <h3>The device is shutting down.</h3>
                </hgroup>
                <p>Please wait a few seconds. You may now disconnect from the Wi-Fi access point.</p>
            </article>
        '''
        
        html_sosud = html_template(request, "Shutdown", content)
        
        response = Response(html_sosud)
        response.set_cookie('auth', '', max_age=0)
        
        async def shutdown_delay():
            await asyncio.sleep(1)
            request.app.shutdown()

        asyncio.create_task(shutdown_delay())
        
        return response

    @app.route('/sysinfo')
    async def sysinfo(request):
        uptime = "12345 s"
        version = "1.0.0"
        
        content = f'''
            <article>
                <header>
                    <h2>System Information</h2>
                </header>
                <table class="striped">
                    <thead>
                        <tr>
                            <th scope="col">Parameter</th>
                            <th scope="col">Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Uptime</td>
                            <td>{uptime}</td>
                        </tr>
                        <tr>
                            <td>Firmware Version</td>
                            <td>{version}</td>
                        </tr>
                        <tr>
                            <td>Free Memory</td>
                            <td>128 KB</td>
                        </tr>
                    </tbody>
                </table>
            </article>
        '''
        return html_template(request, "Sysinfo", content)
    
    @app.route('/diagnostics')
    async def diagnostics(request):
        content ='''
            <article>
                <header>
                    <h2>Diagnostics</h2>
                </header>
                <p>Hardware self-tests status:</p>
                
                <details>
                    <summary>Sensors Status</summary>
                    <ul>
                        <li>Temperature: <span id="temperature_value">Connecting...</span></li>
                        <li>Humidity: <span id="humidity_value">Connecting...</span></li>
                        <li>Brightness: <span id="brightness_value">Connecting...</span></li>
                        <li>Gas status: <span id="gas_status_value">Connecting...</span></li>
                        <li>Gas level: <span id="gas_level_value">Connecting...</span></li>
                        <li>Noise: <span id="noise_value">Connecting...</span></li>
                    </ul>
                </details>
                
                <details>
                    <summary>Button Control</summary>
                    <ul>
                        <li>Button: <span id="btn_value">Connecting...</span></li>
                    </ul>
                </details>
                
                <details>
                    <summary>Led Control</summary>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                        <button onclick="sendColorCommand('R')" style="background-color: red; color: white; width: 40px; height: 40px;"></button>
                        <button onclick="sendColorCommand('G')" style="background-color: green; color: white; width: 40px; height: 40px;"></button>
                        <button onclick="sendColorCommand('B')" style="background-color: blue; color: white; width: 40px; height: 40px;"></button>
                        <button onclick="sendColorCommand('OFF')" style="background-color: black; color: white; width: 40px; height: 40px;"></button>
                    </div>
                </details>
                
                </article>
            </article>
            
            <script>
            const ws_url = 'ws://' + window.location.host + '/ws/diagnostics';
            const socket = new WebSocket(ws_url);
            
            function sendColorCommand(color) {
                if (socket.readyState === WebSocket.OPEN) {
                    const command = {
                        type: 'set_color',
                        color: color
                    };
                    socket.send(JSON.stringify(command));
                } else {
                    console.error('WebSocket is not open');
                }
            }
            
            socket.onmessage = function(event){
                try{
                    const data = JSON.parse(event.data);

                    document.getElementById('btn_value').textContent = data.btn;
                    document.getElementById('brightness_value').textContent = data.brightness;
                    document.getElementById('gas_status_value').textContent = data.gas_status;
                    document.getElementById('gas_level_value').textContent = data.gas_level;
                    document.getElementById('noise_value').textContent = data.noise;
                    document.getElementById('temperature_value').textContent = data.temperature;
                    document.getElementById('humidity_value').textContent = data.humidity;
                }
                catch (e){
                    console.error("Error parsing WebSocket message:", e);
                }
            };

            socket.onclose = function(event){
                console.log('WebSocket disconnected. Reason: ' + event.reason);
            };
            
            socket.onerror = function(error){
                console.error('WebSocket Error:', error);
                document.getElementById('btn_value').textContent = 'Error!';
                document.getElementById('brightness_value').textContent = 'Error!';
                document.getElementById('gas_status_value').textContent = 'Error!';
                document.getElementById('gas_level_value').textContent = 'Error!';
                document.getElementById('noise_value').textContent = 'Error!';
                document.getElementById('temperature_value').textContent = 'Error!';
                document.getElementById('humidity_value').textContent = 'Error!';
            };
            </script>
        '''
        return html_template(request, "Diagnostics", content)
    
    @app.route('/ws/diagnostics')
    @with_websocket
    async def diagnostics_ws(request, ws):
        print(">> WebSocket client connected")
        try:
            while True:
                gc.collect()
                
                #get
                try:
                    message = await asyncio.wait_for(ws.receive(), timeout=0.2) 
                    
                    if message:
                        try:
                            command = json.loads(message)
                            if command.get('type') == 'set_color':
                                color = command.get('color', '').upper()
                                if color == 'R':
                                    device.light.set_color(Color.RED)
                                elif color == 'G':
                                    device.light.set_color(Color.GREEN)
                                elif color == 'B':
                                    device.light.set_color(Color.BLUE)
                                elif color == 'OFF':
                                    device.light.off()
                        except ValueError:
                            print(">> invalid JSON message")

                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f">> Error WebSocket message: {e}")
                
                #send
                device.sensor_dht11.measure()
                    
                realtime_data = {
                    "btn": "off" if device.button.value() else "on",
                    "brightness": device.sensor_light.read_u16(),
                    "gas_status": "Normal" if device.sensor_gas_do.value() else "Dangerous",
                    "gas_level": device.sensor_gas_ao.read_u16(),
                    "noise": device.sensor_sound_ao.read_u16(),
                    "temperature": device.sensor_dht11.temperature(),
                    "humidity": device.sensor_dht11.humidity()
                }
                
                message = json.dumps(realtime_data)
                await ws.send(message)
                
                await asyncio.sleep(0.8)
                
        except asyncio.CancelledError:
            print('>> Сlient disconnected!')

    @app.route('/setup', methods=['GET', 'POST'])
    @auth_required #----------------------#
    async def setup(request):
        settings = device.config

        if request.method == 'POST':
            form = request.form
            
            settings['user']['login'] = form.get('user_login')
            settings['user']['password'] = form.get('user_password')
            
            settings['units'] = form.get('units')
            
            settings['wifi']['ssid'] = form.get('wifi_ssid')
            settings['wifi']['password'] = form.get('wifi_password')
            settings['ntp_host'] = form.get('ntp_host')
            
            settings['mqtt']['server'] = form.get('mqtt_server')
            try:
                settings['mqtt']['port'] = int(form.get('mqtt_port'))
            except (ValueError, TypeError):
                settings['mqtt']['port'] = 1883
            settings['mqtt']['user'] = form.get('mqtt_user')
            settings['mqtt']['password'] = form.get('mqtt_password')
            settings['mqtt']['ssl'] = 'mqtt_ssl' in form
            
            settings['department'] = form.get('department')
            settings['room'] = form.get('room')
            settings['id'] = form.get('device_id')
            try:
                settings['measurement_interval'] = int(form.get('interval'))
            except (ValueError, TypeError):
                settings['measurement_interval'] = 1000

            save_settings(settings)


        ssl_checked = 'checked' if settings.get('mqtt', {}).get('ssl', False) else ''
        
        units_val = settings.get('units', 'standard')
        sel_std = 'selected' if units_val == 'standard' else ''
        sel_met = 'selected' if units_val == 'metric' else ''
        sel_imp = 'selected' if units_val == 'imperial' else ''

        content = f'''
        <hgroup>
            <h2>Configuration</h2>
            <h3>System Settings</h3>
        </hgroup>
        
        <form method="post">
            <article>
                <header><strong>User</strong></header>
                <div class="grid">
                    <label for="user_login">
                        Login
                        <input id="user_login" name="user_login" value="{settings['user']['login']}">
                    </label>
                    <label for="user_password">
                        Password
                        <input id="user_password" name="user_password" type="password" value="{settings['user']['password']}">
                    </label>
                </div>
            </article>
            
            <article>
                <header><strong>General</strong></header>
                <label for="units">
                    Measurement Units
                    <select id="units" name="units">
                        <option value="standard" {sel_std}>Standard</option>
                        <option value="metric" {sel_met}>Metric</option>
                        <option value="imperial" {sel_imp}>Imperial</option>
                    </select>
                </label>
            </article>

            <article>
                <header><strong>Network</strong></header>
                <div class="grid">
                    <label for="wifi_ssid">
                        WiFi SSID
                        <input id="wifi_ssid" name="wifi_ssid" value="{settings['wifi']['ssid']}">
                    </label>
                    <label for="wifi_password">
                        WiFi Password
                        <input id="wifi_password" name="wifi_password" type="password" value="{settings['wifi']['password']}">
                    </label>
                </div>
                <label for="ntp_host">
                    NTP Host
                    <input id="ntp_host" name="ntp_host" value="{settings['ntp_host']}">
                </label>
            </article>

            <article>
                <header><strong>MQTT Configuration</strong></header>
                <div class="grid">
                    <label for="mqtt_server">
                        Broker Address
                        <input id="mqtt_server" name="mqtt_server" value="{settings['mqtt']['server']}">
                    </label>
                    <label for="mqtt_port">
                        Port
                        <input id="mqtt_port" name="mqtt_port" type="number" value="{settings['mqtt']['port']}">
                    </label>
                </div>
                
                <div class="grid">
                    <label for="mqtt_user">
                        User
                        <input id="mqtt_user" name="mqtt_user" value="{settings['mqtt']['user']}">
                    </label>
                    <label for="mqtt_password">
                        Password
                        <input id="mqtt_password" name="mqtt_password" type="password" value="{settings['mqtt']['password']}">
                    </label>
                </div>

                <hr>
                <label for="mqtt_ssl">
                    <input type="checkbox" id="mqtt_ssl" name="mqtt_ssl" role="switch" {ssl_checked}>
                    SSL
                </label>
            </article>

            <article>
                <header><strong>Device Details</strong></header>
                <div class="grid">
                    <label for="department">
                        Department
                        <input id="department" name="department" value="{settings['department']}">
                    </label>
                    <label for="room">
                        Room
                        <input id="room" name="room" value="{settings['room']}">
                    </label>
                </div>
                <div class="grid">
                    <label for="device_id">
                        Device ID
                        <input id="device_id" name="device_id" value="{settings['id']}">
                    </label>
                    <label for="interval">
                        Interval (ms)
                        <input id="interval" name="interval" type="number" value="{settings['measurement_interval']}">
                    </label>
                </div>
            </article>

            <button type="submit" class="primary">Save Configuration</button>
        </form>
        '''
        return html_template(request, "Settings", content)

    #-------------------------------------------------------------------------------
    @app.route('/login', methods=['GET', 'POST'])
    async def login(request):
        error_message = ""
        
        if request.method == 'POST':
            form = request.form
            username = form.get('user')
            password = form.get('password')
            
            settings = device.config
            if settings:
                settings = DEFAULT_SETTINGS
            
            true_user = settings['user']['login']
            true_pass = settings['user']['password']
            
            if username == true_user and password == true_pass:
                response = redirect('/setup')
                response.set_cookie('auth', 'authorized', path='/', http_only=True)
                return response
            else:
                error_message = "<p style='color: red; text-align: center;'>Wrong login or password!</p>"

        content =f'''
            <article style="max-width: 400px; margin: auto;">
                <header>
                    <strong>Login Required</strong>
                </header>
                {error_message}
                <form method="POST" action="/login">
                    <label for="user_input">Username</label>
                    <input id="user_input" name="user" placeholder="Enter username" required>
                    
                    <label for="password_input">Password</label>
                    <input id="password_input" name="password" type="password" placeholder="Enter password" required>
                    
                    <button type="submit">Log In</button>
                </form>
            </article>
        '''
        return html_template(request, "Login", content)
    #-------------------------------------------------------------------------------
    
    #-------------------------------------------------------------------------------
    @app.route('/logout')
    def logout(request):
        response = redirect('/login')
        response.set_cookie('auth', '', max_age=0) 
        return response
    #-------------------------------------------------------------------------------

    app.run(port=80)
