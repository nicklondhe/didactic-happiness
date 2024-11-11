'''Add a new task layout'''
import dash_bootstrap_components as dbc
from dash import html

add_task_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H3('Add a New Task', className='text-center my-4'), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(dbc.Label('Task Name'), width=4),
                dbc.Col(dbc.Input(
                    type='text', id='name', placeholder='Enter task name', required=True), width=8)
            ], className='mb-3'),
            dbc.Row([
                dbc.Col(dbc.Label('Complexity'), width=4),
                dbc.Col(dbc.Select(
                    id='complexity',
                    options=[
                        {'label': 'Simple', 'value': 'simple'},
                        {'label': 'Medium', 'value': 'medium'},
                        {'label': 'Hard', 'value': 'hard'}
                    ],
                    placeholder='Select task complexity'
                ), width=8)
            ], className='mb-3'),
            dbc.Row([
                dbc.Col(dbc.Label('Type'), width=4),
                dbc.Col(dbc.Select(
                    id='type',
                    options=[
                        {'label': 'Chores', 'value': 'chores'},
                        {'label': 'Learning', 'value': 'learning'},
                        {'label': 'Creative', 'value': 'creative'},
                        {'label': 'Constructive', 'value': 'constructive'}
                    ],
                    placeholder='Select task type'
                ), width=8)
            ], className='mb-3'),
            dbc.Row([
                dbc.Col(dbc.Label('Priority'), width=4),
                dbc.Col(dbc.Select(
                    id='priority',
                    options=[
                        {'label': 'Low', 'value': 'low'},
                        {'label': 'Medium', 'value': 'medium'},
                        {'label': 'High', 'value': 'high'}
                    ],
                    placeholder='Select task priority'
                ), width=8)
            ], className='mb-3'),
            dbc.Row([
                dbc.Col(dbc.Label('Repeatable'), width=4),
                dbc.Col(dbc.Checkbox(id='repeatable'), width=8)
            ], className='mb-3'),
            dbc.Button('Submit', id='submit', color='primary', className='mt-3')
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='output', className='mt-4'), width=12)
    ])
])
