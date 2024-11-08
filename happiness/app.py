'''Main application file'''
from flask import Flask, request, jsonify
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import requests

#layouts
from happiness.dash.add_task_tab import add_task_layout
from happiness.dash.view_tasks_tab import view_tasks_layout
from happiness.dash.workflow_tab import workflow_layout
from happiness.tasks.model import db
from happiness.tasks.task import TaskWrapper
from happiness.tasks.taskrepository import TaskRepository

# Flask setup
server = Flask(__name__)
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(server)

with server.app_context():
    db.create_all()

repository = TaskRepository(db.session)

@server.route('/add_task', methods=['POST'])
def add_task():
    '''Add a new task'''
    data = request.json
    task = TaskWrapper(data)
    task_name = data['name']
    repository.add_task(task)
    return jsonify({'message': f'Task "{task_name}" added successfully!'})


@server.route('/get_tasks', methods=['GET'])
def get_tasks():
    '''Get all pending tasks'''
    tasks = repository.get_tasks()
    tasks_list = [
        {
            'name': task.get_name(),
            'complexity': task.get_complexity(),
            'type': task.get_type(),
            'priority': task.get_priority(),
            'repeatable': task.is_repeatable()
        } for task in tasks
    ]
    return jsonify({'tasks': tasks_list})


@server.route('/recommend_tasks', methods=['GET'])
def recommend_tasks():
    '''Recommend tasks based on user's mood'''


# Dash setup
app = dash.Dash(__name__, server=server, url_base_pathname='/')

app.layout = html.Div([
    html.H1('Task Manager'),
    html.Hr(),  # Separator
    dcc.Tabs(id='tabs', value='add-task', children=[ # setting value sets default tab
        dcc.Tab(label='Add Task', value='add-task', children=add_task_layout),
        dcc.Tab(label='View Tasks', value='view-tasks', children=view_tasks_layout),
        dcc.Tab(label='Workflow', value='workflow', children=workflow_layout)
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
