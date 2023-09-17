from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import queue
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/dbname'
db = SQLAlchemy(app)

# Initialize user queue and task priority queue
user_queue = queue.Queue(maxsize=10)
task_priority_queue = queue.PriorityQueue(maxsize=10)

# Create a lock to safely access shared resources
lock = threading.Lock()

def add_user_or_complete(user_id):
    '''
        Put user_id in user_queue
    '''
    user_queue.put(user_id, block=True)

def assign_task_to_user(user_id):
    '''
        Function to assign tasks to users
    '''
    try:
        task_id, task_description, _ = task_priority_queue.get(block=True)
        task = Task.query.get(task_id)
        task.assigned_to = user_id
        task.status = 'Assigned'
        with lock:
            db.session.commit()
        return task_id, task_description
    except queue.Empty:
        return None, None

def task_listener():
    '''
        Listener thread to assign tasks to users
    '''
    while True:
        user_id = user_queue.get()
        task_id, task_description = assign_task_to_user(user_id)
        if task_id is not None:
            print(f'Task {task_id}: "{task_description}" assigned to User {user_id}')
        add_user_or_complete(user_id)
        user_queue.task_done()

def check_login(request):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            user.logged_in = True
            with lock:
                db.session.commit()
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'message': 'Login failed'}), 401

def user_logout(request):
    if request.method == 'POST':
        username = request.form['username']

        user = User.query.filter_by(username=username).first()
        if user:
            user.logged_in = False
            with lock:
                db.session.commit()
            return jsonify({'message': 'Logout successful'}), 200
        else:
            return jsonify({'message': 'User not found'}), 404


# The task listener thread
listener_thread = threading.Thread(target=task_listener)
listener_thread.daemon = True
listener_thread.start()

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    logged_in = db.Column(db.Boolean, default=False)

class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    task_description = db.Column(db.String(200), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    status = db.Column(db.String(20), default='Pending')

@app.route('/login', methods=['POST'])
def login():
    '''
        When user logs in
    '''
    input_json = request.get_json()
    if not input_json or 'user' not in input_json:
        return jsonify({'error': 'Invalid input JSON'}), 400
    response = check_login(input_json)
    if response.status_code == 200:
        user_id = input_json['user_id']
        add_user_or_complete(user_id)
        return jsonify({'message': 'Logged in successfully'})

@app.route('/logout', methods=['POST'])
def logout():
    '''
        When user logs out.
    '''
    input_json = request.get_json()
    if not input_json or 'user' not in input_json:
        return jsonify({'error': 'Invalid input JSON'}), 400
    user_id = input_json['user_id']

    response = user_logout(input_json)

    if response.status_code == 200:
        #Deleting user id from queue
        new_user_queue = queue.Queue(maxsize=10)
        while not user_queue.empty():
            user_id = user_queue.get()
            if user_id != user_id:
                new_user_queue.put(user_id)
        # Replace the original queue with the new queue for updated queue with no old user_id
        user_queue = new_user_queue

        return jsonify({'message': 'Logged out successfully'})
    else:
        return response

@app.route('/createtasks', methods=['GET'])
def create_tasks():
    '''
        Run this first time, add task for task_priority_queue and runs the listener thread
    '''
    input_json = request.get_json()
    if not input_json or 'tasks' not in input_json:
        return jsonify({'error': 'Invalid input JSON'}), 400
    tasks = input_json['tasks']
    task_priority_queue.put(tasks, block=True)
    task_listener()
    return jsonify({'tasks': tasks})


@app.route('/assign_task', methods=['POST'])
def assign_task():
    '''
        Assigns task is to add task to the task_priority_queue.
    '''
    input_json = request.get_json()
    if not input_json or 'tasks' not in input_json:
        return jsonify({'error': 'Invalid input JSON'}), 400
    task_id = input_json['tasks']
    priority = input_json['priority']
    task_priority_queue.put((task_id, priority))
    return jsonify({'message': 'Task added to the queue'})


if __name__ == '__main__':
    app.run(debug=True)
