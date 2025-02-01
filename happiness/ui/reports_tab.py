'''Reports tab layout'''
from datetime import datetime, timedelta
from dash import html, dcc
import dash_bootstrap_components as dbc


def format_date(dt: datetime):
    '''Format datetime to a string'''
    return dt.strftime('%Y-%m-%d')


def generate_week_options(start_date: datetime):
    '''Generate week options from given start date'''
    options = []
    current_date = datetime.now()

    while start_date <= current_date:
        end_date = start_date + timedelta(days=6)
        week_number = start_date.isocalendar()[1]
        start_str = format_date(start_date)
        end_str = format_date(end_date)
        label = f"Week {week_number} ({start_str} - {end_str})"
        value = start_str
        options.append({'label': label, 'value': value})
        start_date += timedelta(days=7)
        week_number += 1

    return options

# Start from the first Sunday of Dec 2024
week_options = generate_week_options(datetime(2024, 12, 1))
default_week_value = week_options[-2]['value']

reports_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H3('Performance Reports', className='text-center my-4'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='week-selector',
            options=week_options,
            value=default_week_value,
            placeholder='Select a week',
            className='mb-4'
        ), width=6)
    ], className='justify-content-center'),
    dbc.Row([
        dbc.Col(dcc.Graph(id='worklog-report-output'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='worklog-group-output'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='task-completion-report-output'), width=12)
    ]),
])
