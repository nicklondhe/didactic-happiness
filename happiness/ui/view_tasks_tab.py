'''View tasks tab layout'''
from dash import dash_table, html

view_tasks_layout = html.Div([
    html.Br(),
    dash_table.DataTable(
        id='tasks-table',
        columns=[
            {'name': 'Task Name', 'id': 'name'},
            {'name': 'Complexity', 'id': 'complexity'},
            {'name': 'Type', 'id': 'type'},
            {'name': 'Priority', 'id': 'priority'},
            {'name': 'Repeatable', 'id': 'repeatable'},
            {'name': 'Status', 'id': 'status'}
        ],
        data=[]
    )
])
