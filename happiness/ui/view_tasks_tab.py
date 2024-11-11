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
            style_table={'overflowX': 'auto'},
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
        ), width='auto', className='dbc')
    ])
])
