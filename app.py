'''Main application file'''
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import dash
import dash_bootstrap_components as dbc
from dash import ctx, dcc, html
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
from loguru import logger
import pandas as pd
import plotly.express as px
import requests
import tzlocal

#layouts
from happiness.ui.add_task_tab import add_task_layout
from happiness.ui.reports_tab import reports_layout
from happiness.ui.reschedule_tasks import reschedule_tasks_layout
from happiness.ui.view_tasks_tab import view_tasks_layout
from happiness.ui.workflow_tab import workflow_layout
from happiness.tasks.model import db
from happiness.tasks.task import TaskWrapper
from happiness.tasks.taskrepository import TaskRepository

# Flask setup
server = Flask(__name__)
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
server.config['SQLALCHEMY_ECHO'] = True
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
    logger.info(f'add_task invoked with {data}')
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
    logger.info(f'Returning get_tasks with {len(tasks)} tasks')
    return jsonify({'tasks': tasks_list})


@server.route('/get_resched_tasks', methods=['GET'])
def get_reschedulable_tasks():
    '''Get tasks that can be rescheduled'''
    tasks = repository.get_reschedulable_tasks()
    tasks_list = [
        {
            'task_id': task.get_id(),
            'name': task.get_name(),
            'complexity': task.get_complexity(),
            'type': task.get_type(),
            'priority': task.get_priority(),
        } for task in tasks
    ]
    logger.info(f'Returning get_resched_tasks with {len(tasks)} tasks')
    return jsonify({'tasks': tasks_list})


@server.route('/recommend_tasks', methods=['GET'])
def recommend_tasks():
    '''Recommend tasks based on user's mood'''
    num_tasks = 5 #TODO: this is a bad place to control rec size
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
    logger.debug(f'Recommended tasks: {tasks_list}')
    return jsonify({'tasks': tasks_list})


@server.route('/transact_task', methods=['POST'])
def transact_task():
    '''Start, stop or end a task'''
    data = request.json
    logger.info(f'transact_task called with {data}')
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


@server.route('/reschedule_tasks', methods=['POST'])
def reschedule_tasks():
    '''Reschedule selected tasks'''
    data = request.json
    logger.info(f'reschedule_tasks called with {data}')
    task_ids = data['tasks']

    message = repository.reschedule_tasks(task_ids=[int(task_id) for task_id in task_ids])
    return jsonify({'message': message})


@server.route('/start_day', methods=['POST'])
def start_day():
    '''Start day'''
    repository.start_day()
    message = repository.auto_reschedule()
    return jsonify({'message': message})


@server.route('/end_day', methods=['POST'])
def end_day():
    '''End day'''
    repository.end_day()
    return jsonify({})


# Dash setup
app = dash.Dash(__name__, server=server,
                url_base_pathname='/', external_stylesheets=[dbc.themes.MINTY])
load_figure_template('minty')

app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1('Task Manager', className='text-center my-4'), width=12)
        ]),
        dbc.Row([
            dbc.Col(dcc.Tabs(id='tabs', value='workflow', children=[
                dcc.Tab(label='Workflow', value='workflow', children=workflow_layout),
                dcc.Tab(label='Add Task', value='add-task', children=add_task_layout),
                dcc.Tab(label='Reschedule Tasks', value='resched-tasks',
                        children=reschedule_tasks_layout),
                dcc.Tab(label='View Tasks', value='view-tasks', children=view_tasks_layout),
                dcc.Tab(label='Performance Reports', value='reports', children=reports_layout)
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
    Output('reschedule-tasks-table', 'data'),
    Input('tabs', 'value')
)
def load_resched_tasks(tab):
    '''Load tasks into the table'''
    if tab == 'resched-tasks':
        tasks_response = requests.get(f'{SERVER_URL}/get_resched_tasks', timeout=5)
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

    if (start_clicks is None) and (stop_clicks is None):
        return 'Invalid action'

    selected_task = tasks[selected_rows[0]]
    task_id = selected_task['task_id']
    rec_id = selected_task['rec_id']
    data = {'task_id': task_id, 'rec_id': rec_id}
    action = ctx.triggered_id.split('-')[0]

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
    if not selected_rows or not n_clicks:
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

    if (view_stop_clicks is None) and (view_end_clicks is None):
        return 'Invalid action'

    selected_task = tasks[selected_rows[0]]
    task_id = selected_task['task_id']
    rec_id = -1
    data = {'task_id': task_id, 'rec_id': rec_id}
    data['action'] = ctx.triggered_id.split('-')[0]
    data['rating'] = 5 # TODO: get rating from user

    response = requests.post(f'{SERVER_URL}/transact_task', json=data, timeout=5)
    return response.json()['message']

@app.callback(
    Output('resched-output', 'children'),
    Input('reschedule-selected', 'n_clicks'),
    State('reschedule-tasks-table', 'selected_rows'),
    State('reschedule-tasks-table', 'data')
)
def manage_reschedule_tasks(regen_clicks, selected_rows, tasks):
    '''Reschedule selected tasks'''
    if not selected_rows:
        return 'No task selected'

    if regen_clicks is None:
        return 'Invalid action'

    task_ids = [tasks[idx]['task_id'] for idx in selected_rows]
    data = {'tasks' : task_ids}
    response = requests.post(f'{SERVER_URL}/reschedule_tasks', json=data, timeout=5)
    return response.json()['message']

@app.callback(
    Output('tasks-table-row', 'style'),
    Output('task-buttons-row', 'style'),
    Output('start-day', 'children'),
    Output('reschedule-toast', 'is_open'),
    Output('reschedule-toast', 'children'),
    Input('start-day', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_day(n_clicks):
    '''Toggle the day start/end and show/hide buttons'''
    if n_clicks % 2 == 1:
        response = requests.post(f'{SERVER_URL}/start_day', timeout=5)
        rescheduled_tasks = response.json().get('message', '')
        toast_message = 'No tasks were rescheduled.' if not rescheduled_tasks else rescheduled_tasks
        return {'display': 'flex'}, {'display': 'flex'}, 'End Day', True, toast_message
    else:
        requests.post(f'{SERVER_URL}/end_day', timeout=5)
        return {'display': 'none'}, {'display': 'none'}, 'Start Day', False, ''

@app.callback(
    Output('worklog-report-output', 'figure'),
    Input('week-selector', 'value')
)
def update_worklog_summary_chart(selected_week):
    '''Plot worklog summary absed on selected week'''
    if selected_week is None:
        return {}

    start_date =  datetime.strptime(selected_week, '%Y-%m-%d').replace(
        tzinfo=tzlocal.get_localzone())
    end_date = start_date + timedelta(days=7)
    summary = repository.get_worklog_summary(start_date, end_date)
    data = [(date, task_type, hours) for (date, task_type), hours in summary.items()]
    df = pd.DataFrame(data, columns=['date', 'type', 'hours_worked'])
    fig = px.bar(df, x='date', y='hours_worked', 
                 color='type', barmode='stack', title='Hours worked per day')
    return fig

@app.callback(
    Output('task-completion-report-output', 'figure'),
    Input('week-selector', 'value')
)
def update_task_completion_heatmap(selected_week):
    '''Plot task compeltions as a heatmap'''
    if selected_week is None:
        return {}

    start_date =  datetime.strptime(selected_week, '%Y-%m-%d').replace(
        tzinfo=tzlocal.get_localzone())
    end_date = start_date + timedelta(days=7)
    data_list = repository.get_task_completion_summary(start_date, end_date)
    df = pd.DataFrame(data_list)

    # Count occurrences
    heatmap_df = df.value_counts().reset_index()
    heatmap_df.columns = ["day_of_week", "hour_of_day", "task_count"]

    # Map weekday numbers to labels
    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    heatmap_df["day_of_week"] = heatmap_df["day_of_week"].map(lambda x: weekday_labels[x])

    # Create all possible (day_of_week, hour_of_day) combinations
    all_combinations = pd.MultiIndex.from_product(
        [weekday_labels, range(24)], names=["day_of_week", "hour_of_day"]
    )

    # Reindex the DataFrame to include all combinations, filling missing values with 0
    heatmap_df = heatmap_df.set_index(["day_of_week", "hour_of_day"]).reindex(
        all_combinations, fill_value=0).reset_index()

    # Plot using Plotly Express
    fig = px.density_heatmap(
        heatmap_df,
        x="hour_of_day",
        y="day_of_week",
        z="task_count",
        title="Completed Tasks Heatmap",
        labels={"hour_of_day": "Hour of Day",
                "day_of_week": "Day of Week",
                "task_count": "Completed Tasks"},
        category_orders={
            "hour_of_day": list(range(24)),
            "day_of_week": weekday_labels[-1:] + weekday_labels[0:6]
        }
    )
    fig.update_xaxes(side="top")
    return fig

@app.callback(
    Output('worklog-group-output', 'figure'),
    Input('week-selector', 'value')
)
def update_worklog_grouped_output(selected_week):
    '''Plot worklog split by priority and complexity'''
    if selected_week is None:
        return {}

    start_date =  datetime.strptime(selected_week, '%Y-%m-%d').replace(
        tzinfo=tzlocal.get_localzone())
    end_date = start_date + timedelta(days=7)

    # get data
    data = repository.get_worklog_splits(start_date, end_date)

    # Convert query result to DataFrame
    df = pd.DataFrame(data, columns=["priority", "complexity", "total_time"])

    # Convert total_time from seconds to hours
    df["total_time"] = df["total_time"] / 3600  # Convert to hours

    # Plot sunburst chart
    fig = px.sunburst(
        df,
        path=["priority", "complexity"],  # Sunburst levels: Priority → Complexity
        values="total_time",
        title="Time Spent on Tasks by Priority and Complexity",
        labels={"priority": "Priority", "complexity": "Complexity", "total_time": "Hours Spent"},
        color="total_time",
        template="minty"
        #color_continuous_scale="blues"
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
