from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import requests

# Flask setup
server = Flask(__name__)
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(server)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    complexity = db.Column(db.String(10), nullable=False, default='simple')
    type = db.Column(db.String(20))
    due_date = db.Column(db.String(10))
    priority = db.Column(db.String(10), nullable=False, default='low')
    repeatable = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)

with server.app_context():
    db.create_all()

@server.route('/add_task', methods=['POST'])
def add_task():
    data = request.json
    new_task = Task(
        name=data['name'],
        complexity=data.get('complexity', 'simple'),
        type=data.get('type'),
        priority=data.get('priority', 'low'),
        repeatable=data.get('repeatable', False)
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task added successfully!'})

# Dash setup
app = dash.Dash(__name__, server=server, url_base_pathname='/')

app.layout = html.Div([
    html.H1('Task Manager'),
    html.Div([
        html.Label('Task Name:'),
        dcc.Input(id='name', type='text', placeholder='Task Name', required=True, style={'flex': '1'})
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
    html.Div(id='output')
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
    if n_clicks > 0:
        task = {
            'name': name,
            'complexity': complexity,
            'type': task_type,
            'priority': priority,
            'repeatable': bool(repeatable)
        }
        response = requests.post('http://127.0.0.1:5000/add_task', json=task)
        return response.json()['message']

if __name__ == '__main__':
    app.run_server(debug=True)