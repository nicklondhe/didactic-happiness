'''Main application file'''
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import dash
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State
import requests

#layouts
from add_task_tab import add_task_layout
from view_tasks_tab import view_tasks_layout

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
    dcc.Tabs(id='tabs', value='add-task', children=[ # setting value sets default tab
        dcc.Tab(label='Add Task', value='add-task', children=add_task_layout),
        dcc.Tab(label='View Tasks', value='view-tasks', children=view_tasks_layout)
    ])
])

@app.callback(
    Output('output', 'children'),
    Input('submit', 'n_clicks'),
    State('name', 'value'),
    State('complexity', 'value'),
    State('type', 'value'),
    State('priority', 'value'),
    State('repeatable', 'value')
)
def update_output(n_clicks, name, complexity, task_type, priority, repeatable):
    '''Update the output div - save to db'''
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
        return response.json()['message']

@app.callback(
    Output('tasks-table', 'data'),
    Input('tabs', 'value')
)
def load_tasks(tab):
    '''Load tasks into the table'''
    if tab == 'view-tasks':
        tasks_response = requests.get('http://127.0.0.1:8050/get_tasks', timeout=5)
        return tasks_response.json()['tasks']
    return []


if __name__ == '__main__':
    app.run_server(debug=True)
