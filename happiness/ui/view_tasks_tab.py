'''View tasks tab layout'''
import dash_bootstrap_components as dbc
from dash import dash_table, html

view_tasks_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H3('View Tasks', className='text-center my-4'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id='tasks-table',
            columns=[
                {'name': 'Task ID', 'id': 'task_id'},
                {'name': 'Task Name', 'id': 'name', 'type': 'text'},
                {'name': 'Complexity', 'id': 'complexity', 'type': 'text'},
                {'name': 'Type', 'id': 'type', 'type': 'text'},
                {'name': 'Priority', 'id': 'priority', 'type': 'text'},
                {'name': 'Repeatable', 'id': 'repeatable', 'type': 'text'},
                {'name': 'Status', 'id': 'status', 'type': 'text'}
            ],
            page_current=0,
            page_size=10,
            page_action='native',
            sort_action='native',
            filter_action='native',
            row_selectable='single',
            hidden_columns=['task_id'],
            style_table={'overflowX': 'auto'},
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
            css=[{"selector": ".show-hide", "rule": "display: none"}]
        ), width='auto', className='dbc')
    ]),
    dbc.Row([
        dbc.Col(dbc.Button(
            'Stop Task', id='stop-view-task', color='warning', className='mr-2'), width='auto'),
        dbc.Col(dbc.Button(
            'End Task', id='end-view-task', color='danger'), width='auto')
    ], className='my-4'),
    dbc.Row([
        dbc.Col(html.Div(id='viewtasks-output', className='mt-4'), width=12)
    ])
])
