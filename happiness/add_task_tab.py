from dash import dcc, html

add_task_layout = html.Div([
    html.Br(),
    html.Div([
        html.Label('Task Name:'),
        dcc.Input(id='name', type='text', placeholder='Task Name',
                  required=True, style={'flex': '1'})
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px', 'width': '50%'}),
    html.Div([
        html.Label('Complexity'),
        dcc.Dropdown(
            id='complexity',
            options=[
                {'label': 'Simple', 'value': 'simple'},
                {'label': 'Medium', 'value': 'medium'},
                {'label': 'Hard', 'value': 'hard'}
            ],
            value='simple',
            style={'flex': '1'}
        )
    ],style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px', 'width': '50%'}),
    html.Div([
        html.Label('Type:'),
        #TODO: Add more task types or allow manual
        dcc.Dropdown(
            id='type',
            options=[
                {'label': 'Chores', 'value': 'chores'},
                {'label': 'Learning', 'value': 'learning'},
                {'label': 'Creative', 'value': 'creative'},
                {'label': 'Constructive', 'value': 'constructive'}
            ],
            style={'flex': '1'}
        )
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px', 'width': '50%'}),
    html.Div([
        html.Label('Priority'),
        dcc.Dropdown(
            id='priority',
            options=[
                {'label': 'Low', 'value': 'low'},
                {'label': 'Medium', 'value': 'medium'},
                {'label': 'High', 'value': 'high'}
            ],
            value='low',
            style={'flex': '1'}
        )
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px', 'width': '50%'}),
    html.Div([
        dcc.Checklist(
            id='repeatable',
            options=[{'label': 'Repeatable', 'value': 'repeatable'}],
            style={'flex': '1'}
        )
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px', 'width': '50%'}),
    html.Button('Submit', id='submit', n_clicks=0),
    html.Div(id='output')
])