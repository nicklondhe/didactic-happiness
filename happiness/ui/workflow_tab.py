'''Task workflow tab layout'''
import dash_bootstrap_components as dbc
from dash import dash_table, html, dcc

workflow_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H3('Workflow', className='text-center my-4'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id='recommended-tasks-table',
            columns=[
                {'name': 'Task ID', 'id': 'task_id'},
                {'name': 'Recommendation ID', 'id': 'rec_id'},
                {'name': 'Name', 'id': 'name'},
                {'name': 'Type', 'id': 'type'},
                {'name': 'Priority', 'id': 'priority'}
            ],
            data=[],
            row_selectable='single',
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
            hidden_columns=['task_id', 'rec_id'],
            css=[{"selector": ".show-hide", "rule": "display: none"}],
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dbc.Button(
            'Regenerate', id='regenerate', color='primary', className='mr-2'), width='auto'),
        dbc.Col(dbc.Button(
            'Start Task', id='start-task', color='success', className='mr-2'), width='auto'),
        dbc.Col(dbc.Button(
            'Stop Task', id='stop-task', color='warning', className='mr-2'), width='auto'),
        dbc.Col(dbc.Button(
            'End Task', id='end-task', color='danger'), width='auto')
    ], className='my-4'),
    dbc.Row([
        dbc.Col(html.Div(id='workflow-output', className='mt-4'), width=12)
    ]),
    dbc.Modal([
        dbc.ModalHeader("Rate Task Recommendation"),
        dbc.ModalBody([
            dcc.Slider(
                id='rating-slider',
                min=1,
                max=5,
                step=1,
                marks={i: str(i) for i in range(1, 6)},
                value=3
            )
        ]),
        dbc.ModalFooter(
            dbc.Button("Submit", id="submit-rating", className="ml-auto")
        )
    ], id="rating-modal", is_open=False)
])
