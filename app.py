'''Main application file'''
from flask import Flask, request, jsonify
import dash
import dash_bootstrap_components as dbc
from dash import ctx, dcc, html
from dash.dependencies import Input, Output, State
import requests

#layouts
from happiness.ui.add_task_tab import add_task_layout
from happiness.ui.view_tasks_tab import view_tasks_layout
from happiness.ui.workflow_tab import workflow_layout
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
#TODO: URL is hardcoded, should be in a config file
SERVER_URL = 'http://127.0.0.1:8050'

@server.route('/add_task', methods=['POST'])
def add_task():
    '''Add a new task'''
    data = request.json
    task = TaskWrapper.from_dict(data)
    task_name = data['name']
    repository.add_task(task)
    return jsonify({'message': f'Task "{task_name}" added successfully!'})


@server.route('/get_tasks', methods=['GET'])
def get_tasks():
    '''Get all pending tasks'''
    tasks = repository.get_tasks()
    tasks_list = [
        {
            'task_id': task.get_id(),
            'name': task.get_name(),
            'complexity': task.get_complexity(),
            'type': task.get_type(),
            'priority': task.get_priority(),
            'repeatable': task.is_repeatable(),
            'status': task.get_status()
        } for task in tasks
    ]
    return jsonify({'tasks': tasks_list})


@server.route('/recommend_tasks', methods=['GET'])
def recommend_tasks():
    '''Recommend tasks based on user's mood'''
    num_tasks = 3
    tasks = repository.recommend_tasks(num_tasks)
    tasks_list = [
        {
            'task_id': task.get_id(),
            'rec_id': task.get_rec_id(),
            'name': task.get_name(),
            'type': task.get_type(),
            'priority': task.get_priority(),
        } for task in tasks
    ]
    return jsonify({'tasks': tasks_list})

@server.route('/transact_task', methods=['POST'])
def transact_task():
    '''Start, stop or end a task'''
    data = request.json
    task_id = data['task_id']
    rec_id = data['rec_id']
    action = data['action']

    message = 'Invalid request'

    if action == 'start':
        message = repository.start_task(task_id, rec_id)
    elif action == 'stop':
        message = repository.stop_task(task_id, rec_id)
    elif action == 'end':
        rating = data['rating']
        message = repository.finish_task(task_id, rec_id, rating)

    return jsonify({'message': message})


# Dash setup
app = dash.Dash(__name__, server=server,
                url_base_pathname='/', external_stylesheets=[dbc.themes.SUPERHERO])

app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1('Task Manager', className='text-center my-4'), width=12)
        ]),
        dbc.Row([
            dbc.Col(dcc.Tabs(id='tabs', value='add-task', children=[
                dcc.Tab(label='Add Task', value='add-task', children=add_task_layout),
                dcc.Tab(label='View Tasks', value='view-tasks', children=view_tasks_layout),
                dcc.Tab(label='Workflow', value='workflow', children=workflow_layout)
            ]), width=12)
        ])
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
    if n_clicks and n_clicks > 0:
        task = {
            'name': name,
            'complexity': complexity,
            'type': task_type,
            'priority': priority,
            'repeatable': bool(repeatable)
        }
        response = requests.post(f'{SERVER_URL}/add_task', json=task, timeout=5)
        return response.json()['message']

@app.callback(
    Output('tasks-table', 'data'),
    Input('tabs', 'value')
)
def load_tasks(tab):
    '''Load tasks into the table'''
    if tab == 'view-tasks':
        tasks_response = requests.get(f'{SERVER_URL}/get_tasks', timeout=5)
        return tasks_response.json()['tasks']
    return []

@app.callback(
    Output('recommended-tasks-table', 'data'),
    Input('tabs', 'value'),
    Input('regenerate', 'n_clicks')
)
def load_recommended_tasks(tab, n_clicks):
    '''Load recommended tasks into the table'''
    if tab == 'workflow' or (n_clicks and n_clicks > 0):
        tasks_response = requests.get(f'{SERVER_URL}/recommend_tasks', timeout=5)
        return tasks_response.json()['tasks']
    return []

@app.callback(
    Output('rating-modal', 'is_open', allow_duplicate=True),
    Input('end-task', 'n_clicks'),
    State('rating-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_modal(end_clicks, is_open):
    '''Toggle the rating modal visibility'''
    if end_clicks:
        return not is_open
    return is_open

@app.callback(
    Output('workflow-output', 'children', allow_duplicate=True),
    Input('start-task', 'n_clicks'),
    Input('stop-task', 'n_clicks'),
    State('recommended-tasks-table', 'selected_rows'),
    State('recommended-tasks-table', 'data'),
    prevent_initial_call=True
)
def manage_workflow(start_clicks, stop_clicks, selected_rows, tasks):
    '''Manage task workflow'''
    if not selected_rows:
        return 'No task selected'

    selected_task = tasks[selected_rows[0]]
    task_id = selected_task['task_id']
    rec_id = selected_task['rec_id']
    data = {'task_id': task_id, 'rec_id': rec_id}
    action = ctx.triggered_id.split('-')[0]

    if action == 'end':
        return ''

    data['action'] = action
    response = requests.post(f'{SERVER_URL}/transact_task', json=data, timeout=5)
    return response.json()['message']

@app.callback(
    Output('workflow-output', 'children', allow_duplicate=True),
    Output('rating-modal', 'is_open', allow_duplicate=True),
    Input('submit-rating', 'n_clicks'),
    State('recommended-tasks-table', 'selected_rows'),
    State('recommended-tasks-table', 'data'),
    State('rating-slider', 'value'),
    prevent_initial_call=True
)
def submit_rating(n_clicks, selected_rows, tasks, rating):
    '''Submit rating for the task and close modal'''
    if not selected_rows:
        return 'No task selected', False

    selected_task = tasks[selected_rows[0]]
    task_id = selected_task['task_id']
    rec_id = selected_task['rec_id']
    data = {'task_id': task_id, 'rec_id': rec_id, 'action': 'end', 'rating': rating}

    response = requests.post(f'{SERVER_URL}/transact_task', json=data, timeout=5)
    return response.json()['message'], False

@app.callback(
    Output('viewtasks-output', 'children'),
    Input('stop-view-task', 'n_clicks'),
    Input('end-view-task', 'n_clicks'),
    State('tasks-table', 'selected_rows'),
    State('tasks-table', 'data')
)
def manage_view_tasks(view_stop_clicks, view_end_clicks, selected_rows, tasks):
    '''Manage tasks from the View Tasks tab'''
    if not selected_rows:
        return 'No task selected'

    selected_task = tasks[selected_rows[0]]
    task_id = selected_task['task_id']
    rec_id = -1
    data = {'task_id': task_id, 'rec_id': rec_id}
    data['action'] = ctx.triggered_id.split('-')[0]
    data['rating'] = 5 # TODO: get rating from user

    response = requests.post(f'{SERVER_URL}/transact_task', json=data, timeout=5)
    return response.json()['message']

if __name__ == '__main__':
    app.run_server(debug=True)
