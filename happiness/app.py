'''Main application file'''
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import dash
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State
import requests

# Flask setup
server = Flask(__name__)
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(server)

class Task(db.Model):
    '''Task model'''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    complexity = db.Column(db.String(10), nullable=False, default='simple')
    type = db.Column(db.String(20))
    due_date = db.Column(db.String(10))
    priority = db.Column(db.String(10), nullable=False, default='low')
    repeatable = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)
    status = db.Column(db.String(10), nullable=False, default='pending')

with server.app_context():
    db.create_all()

@server.route('/add_task', methods=['POST'])
def add_task():
    '''Add a new task'''
    data = request.json
    task_name = data['name']
    new_task = Task(
        name=task_name,
        complexity=data.get('complexity', 'simple'),
        type=data.get('type'),
        priority=data.get('priority', 'low'),
        repeatable=data.get('repeatable', False)
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': f'Task "{task_name}" added successfully!'})


@server.route('/get_tasks', methods=['GET'])
def get_tasks():
    '''Get all tasks'''
    tasks = Task.query.filter_by(status='pending').all()
    tasks_list = [
        {
            'name': task.name,
            'complexity': task.complexity,
            'type': task.type,
            'priority': task.priority,
            'repeatable': task.repeatable
        } for task in tasks
    ]
    return jsonify({'tasks': tasks_list})

# Dash setup
app = dash.Dash(__name__, server=server, url_base_pathname='/')

app.layout = html.Div([
    html.H1('Task Manager'),
    html.Hr(),  # Separator
    html.H2('Add a New Task'),
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
    html.Div(id='output'),
    html.Hr(),  # Separator
    html.H2('Current Tasks'),
    dash_table.DataTable(
        id='tasks-table',
        columns=[
            {'name': 'Task Name', 'id': 'name'},
            {'name': 'Complexity', 'id': 'complexity'},
            {'name': 'Type', 'id': 'type'},
            {'name': 'Priority', 'id': 'priority'},
            {'name': 'Repeatable', 'id': 'repeatable'}
        ],
        data=[]
    ),
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(
    Output('output', 'children'),
    Output('tasks-table', 'data'),
    Input('submit', 'n_clicks'),
    Input('interval-component', 'n_intervals'),
    State('name', 'value'),
    State('complexity', 'value'),
    State('type', 'value'),
    State('priority', 'value'),
    State('repeatable', 'value')
)
def update_output(n_clicks, n_intervals, name, complexity, task_type, priority, repeatable):
    '''Update the output div - save to db'''
    message = ''
    if n_clicks > 0:
        task = {
            'name': name,
            'complexity': complexity,
            'type': task_type,
            'priority': priority,
            'repeatable': bool(repeatable)
        }
        #TODO: URL is hardcoded, should be in a config file
        response = requests.post('http://127.0.0.1:8050/add_task', json=task, timeout=5)
        message = response.json()['message']

    # Get all tasks
    tasks_response = requests.get('http://127.0.0.1:8050/get_tasks', timeout=5)
    tasks_data = tasks_response.json()
    return message, tasks_data['tasks']


if __name__ == '__main__':
    app.run_server(debug=True)
