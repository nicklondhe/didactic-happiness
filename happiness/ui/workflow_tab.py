'''Task workflow tab layout'''
from dash import dash_table, html

workflow_layout = html.Div([
    html.Br(),
    dash_table.DataTable(
        id='recommended-tasks-table',
        columns=[
            {'name': 'Task Name', 'id': 'name'},
            {'name': 'Type', 'id': 'type'},
            {'name': 'Priority', 'id': 'priority'},
            {'name': 'Actions', 'id': 'actions'}
        ],
        data=[]
    ),
    html.Button('Regenerate', id='regenerate', n_clicks=0)
])
