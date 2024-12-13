'''Reschedule tasks tab layout'''
import dash_bootstrap_components as dbc
from dash import dash_table, html

reschedule_tasks_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H3('Reschedule Tasks', className='text-center my-4'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id='reschedule-tasks-table',
            columns=[
                {'name': 'Task ID', 'id': 'task_id'},
                {'name': 'Task Name', 'id': 'name', 'type': 'text'},
                {'name': 'Complexity', 'id': 'complexity', 'type': 'text'},
                {'name': 'Type', 'id': 'type', 'type': 'text'},
                {'name': 'Priority', 'id': 'priority', 'type': 'text'}
            ],
            data=[],
            row_selectable='multi',
            hidden_columns=['task_id'],
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
            css=[{"selector": ".show-hide", "rule": "display: none"}],
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dbc.Button(
            'Reschedule Selected', id='reschedule-selected',
            color='primary', className='mr-2'), width='auto')
    ])
])
