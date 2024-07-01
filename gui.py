import base64
import secrets
import time
from contextlib import contextmanager

from fastapi.security import HTTPAuthorizationCredentials, HTTPDigest
from fastapi.security.utils import get_authorization_scheme_param
from nicegui import ui, app, nicegui, Client
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, PlainTextResponse
from door_status_thread import DoorStatus
from utils import last_boot
from fastapi import Request, Security


unrestricted_page_routes = {'/login'}


def create_door_image(garage):
    with ui.image(source='static/Open.jpg') as image:
        image_label = ui.label('OPEN').classes('absolute-bottom text-subtitle2 text-center')

    def update_image(door_status):
        if door_status == DoorStatus.OPEN:
            image.source = 'static/Open.jpg'
            image_label.text = 'OPEN'
        elif door_status == DoorStatus.CLOSED:
            image.source = 'static/Closed.jpg'
            image_label.text = 'CLOSED'
        elif door_status == DoorStatus.OPENING:
            image_label.text = 'OPENING'
        elif door_status == DoorStatus.CLOSING:
            image_label.text = 'CLOSING'
        image.update()

    update_image(garage.door_status.door_status)
    garage.door_status.listeners.append(update_image)
    return image


def create_door_status_label(garage):
    label = ui.label(f'Door is {garage.door_status.door_status.name}')

    def update_label(door_status):
        label.text = f'Door is {door_status.name}'
        label.update()

    update_label(garage.door_status.door_status)
    garage.door_status.listeners.append(update_label)
    return label


def create_open_close_button(garage):
    def open_or_close():
        garage.open_or_close(' because website user pressed button')

    button = ui.button('Open/Close', on_click=open_or_close)

    def update_button_text(door_status):
        if door_status == DoorStatus.OPEN:
            button.text = 'Close Garage'
            button.update()
        elif door_status == DoorStatus.CLOSED:
            button.text = 'Open Garage'
            button.update()

    update_button_text(garage.door_status.door_status)
    garage.door_status.listeners.append(update_button_text)
    return button


def create_distance_chart(garage):
    """Creates a distance gauge and adds it as a listener to garage.listeners."""
    chart = ui.chart({
        'title': { 'text': 'Car Distance' },
        'chart': { 'type': 'gauge' },
        'xAxis': {
            'categories': [ 'Dist (cm)' ],
        },
        'yAxis': {
            'min': 0.0,
            'max': garage.max_distance,
            'title': {
                'text': 'Dist (cm)',
            },
        },
        'series': [
            {
                'data': [0.0]
            }
        ],
    }, extras=['solid-gauge']).classes('w-64 h-64')
    chart.last_updated = time.time()

    def update_chart(distance):
        # update about every 1.0 seconds otherwise browser falls behind
        if time.time() - chart.last_updated > 1.0:
            chart.options['series'][0]['data'][0] = distance
            chart.update()
            chart.last_updated = time.time()

    garage.listeners.append(update_chart)
    return chart


def create_temperature_chart(garage):
    """Creates a CPU temperature gauge and uses garage.temperature_monitor.listeners to add the gauge as
    a listener for temp changes. """
    # https://www.highcharts.com/demo/highcharts/gauge-speedometer
    chart = ui.chart({
        'title': {
            'text': 'CPU Temperature'
        },
        'chart': {
            'type': 'gauge',
            'plotBackgroundColor': 'white',
            'plotBackgroundImage': None,
            'plotBorderWidth': 0,
            'plotShadow': False,
            'height': '80%'
        },
        'pane': {
            'startAngle': -90,
            'endAngle': 89.9,
            'background': 'white',
            'center': ['50%', '75%'],
            'size': '110%'
        },
        'yAxis': {
            'min': 0,
            'max': 70,
            'tickPixelInterval': 36,
            'tickPosition': 'inside',
            'tickColor': '#FFFFFF',
            'tickLength': 20,
            'tickWidth': 2,
            'minorTickInterval': None,
            'labels': {
                'distance': 15,
                'style': {
                    'fontSize': '14px'
                }
            },
            'lineWidth': 0,
            'plotBands': [{
                'from': 0,
                'to': 50,
                'color': '#55BF3B', # green
                'thickness': 20
            }, {
                'from': 50,
                'to': 60,
                'color': '#DDDF0D', # yellow
                'thickness': 20
            }, {
                'from': 60,
                'to': 70,
                'color': '#DF5353', # red
                'thickness': 20
            }]
        },
        'series': [{
            'name': 'Temperature',
            'data': [ 0.0 ],
            'tooltip': {
                'valueSuffix': '°C'
            },
            'dataLabels': {
                'format': '{y}°C',
                'borderWidth': 0,
                'color': '#333333',
                'style': {
                    'fontSize': '16px'
                }
            },
            'dial': {
                'radius': '80%',
                'backgroundColor': 'gray',
                'baseWidth': 12,
                'baseLength': '0%',
                'rearLength': '0%'
            },
            'pivot': {
                'backgroundColor': 'gray',
                'radius': 6
            }
        }]
    }).classes('w-64')

    chart.last_updated = time.time()

    def update_chart(temperature):
        if time.time() - chart.last_updated > 1.0:
            chart.options['series'][0]['data'][0] = temperature
            chart.update()
            chart.last_updated = time.time()

    garage.temperature_monitor.listeners.append(update_chart)
    return chart


def create_park_distance_slider(garage):
    ui.label('Park Distance').classes('h-16')
    park_distance_slider = ui.slider(min = 0.0, max=garage.max_distance). \
                           props('label-always'). \
                           bind_value(garage, 'park_distance'). \
                           classes('w-64')
    return park_distance_slider



def create_pages(garage, passwords, shutdown, restart) -> None:
    def menu():
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item('Home', on_click=lambda: ui.open(main_page))
                ui.menu_item('Graphs', on_click=lambda: ui.open(graphs_page))
                ui.menu_item('Wifi', on_click=lambda: ui.open(wifi_page))
                ui.menu_item('Status', on_click=lambda: ui.open(status_page))
                ui.menu_item(f'Logout {app.storage.user["username"]}',
                             on_click=lambda: (app.storage.user.clear(), ui.open('/login')))
                ui.menu_item('Restart', on_click=restart)
                ui.menu_item('Shutdown', on_click=shutdown)
                return menu

    @contextmanager
    def layout(title):
        with ui.row().classes('w-96'):
            # ui.label(f'Hello {app.storage.user["username"]}!').classes('text-2xl')
            with ui.column().classes('w-96 items-center h-screen'):
                ui.label(f'🚗 {title}').classes('sky-100 text-xl')
                yield
            with ui.page_sticky(position='top-left', x_offset=10, y_offset=10):
                menu()

    @ui.page('/')
    def main_page():
        with layout('Garage-Pi'):
            create_door_image(garage)
            create_open_close_button(garage)

    @ui.page('/graphs')
    def graphs_page():
        with layout('Graphs'):
            create_distance_chart(garage)
            create_temperature_chart(garage)
            ui.link('Back', main_page)



    class AuthMiddleware(BaseHTTPMiddleware):
        """This middleware restricts access to all NiceGUI pages.

        It redirects the user to the login page if they are not authenticated.
        """
        def authorize_digest(self, request: Request):
            authorization = request.headers.get("Authorization")
            if authorization:
                scheme, credentials = get_authorization_scheme_param(authorization)
                for expected_username, expected_password in passwords.items():
                    expected_token = base64.standard_b64encode(
                        bytes(f"{expected_username}:{expected_password}", encoding="UTF-8")
                    )
                    correct_token = secrets.compare_digest(
                        bytes(credentials, encoding="UTF-8"),
                        expected_token
                    )
                    if correct_token:
                        app.storage.user.update({'username': expected_username, 'authenticated': True})
                        break

        async def dispatch(self, request: Request, call_next):
            self.authorize_digest(request)
            if not app.storage.user.get('authenticated', False):
                if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                    app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                    return RedirectResponse('/login')
            return await call_next(request)

    app.add_middleware(AuthMiddleware)

    @ui.page('/login')
    def login_page():
        def try_login() -> None:  # local function to avoid passing username and password as arguments
            if passwords.get(username.value) == password.value:
                app.storage.user.update({'username': username.value, 'authenticated': True})
                ui.open('/')
            else:
                ui.notify('Wrong username or password', color='negative')

        if app.storage.user.get('authenticated', False):
            return RedirectResponse('/')
        with ui.card().classes('absolute-center'):
            username = ui.input('Username').on('keydown.enter', try_login)
            password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
            ui.button('Log in', on_click=try_login)

    @ui.page('/wifi')
    def wifi_page():
        if garage.wifi_scanner is not None:
            with layout('Wifi Networks'):
                table = ui.aggrid({
                  'columnDefs': [
                      {'headerName': 'SSID', 'field': 'id'},
                      {'headerName': 'Address', 'field': 'address'},
                      {'headerName': 'Signal', 'field': 'signal'},
                  ],
                  'rowData': []
                })

                def update_table(message):
                    #logging.info(f'updating table with {[cell.ssid for cell in garage.wifi_scanner.cells]}')
                    table.options['rowData'] = [{ 'id': cell.ssid, 'address': cell.address, 'signal': cell.signal }
                                  for cell in garage.wifi_scanner.cells if len(cell.ssid) > 0]
                    table.update()

                ui.button('Scan', on_click=update_table)
        else:
            ui.label('Wifi scanner disabled')

    @ui.page('/status')
    def status_page():
        with layout('Status'):
            table = ui.aggrid({
                'columnDefs': [
                    {'headerName': 'Field', 'field': 'field'},
                    {'headerName': 'Status', 'field': 'status'},
                ],
                'rowData': []
            })

            def update_table():
                # logging.info(f'updating table with {[cell.ssid for cell in garage.wifi_scanner.cells]}')
                table.options['rowData'] = [
                    {
                        'field': 'Car Status',
                        'status': garage.db['car_status'].name
                    },
                    {
                        'field': 'Door Status',
                        'status': garage.door_status.door_status.name
                    },
                    {
                        'field': 'Position',
                        'status': garage.current_distance
                    },
                    {
                        'field': 'Park Distance',
                        'status': garage.park_distance
                    },
                    {
                        'field': 'Max Distance',
                        'status': garage.max_distance
                    },
                    {
                        'field': 'Speed',
                        'status': f'{garage.speed:.2f}'
                    },
                    {
                        'field': 'Temperature',
                        'status': garage.temperature_monitor.temperature
                    },
                    {
                        'field': 'Wifi Seen?',
                        'status': str(len(garage.wifi_scanner.found()) > 0) if garage.wifi_scanner else 'N/A'
                    },
                    {
                        'field': 'Parked?',
                        'status': str(garage.display.parked)
                    },
                    {
                        'field': 'Last boot',
                        'status': str(last_boot())
                    }
                ]
                table.update()

            update_table()
            ui.button('Refresh', on_click=update_table)

    @app.get('/door-status', response_class=PlainTextResponse)
    async def door_status():
        return garage.door_status.door_status.name

    @app.get('/press-button', response_class=PlainTextResponse)
    async def press_button():
        garage.open(' because I received a /press-button web command')
        return "Pressed"

    @app.get('/open', response_class=PlainTextResponse)
    async def open_garage():
        garage.open_garage(' because I received a /open web command')
        return "Opened"

    @app.get('/close', response_class=PlainTextResponse)
    async def close_garage():
        garage.close_garage(' because I received a /close web command')
        return "Closed"

    @app.get('/wifi.json')
    async def wifi_json():
        if garage.wifi_scanner is not None and garage.wifi_scanner.cells is not None:
            return garage.wifi_scanner.cells
        return None
