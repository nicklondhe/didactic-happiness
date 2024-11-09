'''Task workflow tab layout'''
from dash import dash_table, html

workflow_layout = html.Div([
    html.Br(),
    html.Div([
        html.Button('Regenerate', id='regenerate', n_clicks=0),
        html.Div(id='workflow-output')
    ]),
    dash_table.DataTable(
        id='recommended-tasks-table',
        columns=[
            {'name': 'Task Name', 'id': 'name'},
            {'name': 'Type', 'id': 'type'},
            {'name': 'Priority', 'id': 'priority'}
        ],
        data=[],
        row_selectable='single',
        selected_rows=[],
        hidden_columns=['task_id', 'rec_id']
    ),
    html.Div([
        html.Button('Start Task', id='start-task', n_clicks=0),
        html.Button('Stop Task', id='stop-task', n_clicks=0),
        html.Button('End Task', id='end-task', n_clicks=0),
    ])
])
