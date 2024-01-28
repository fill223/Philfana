import json
import os

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from flask_socketio import SocketIO, emit

from datetime import timedelta

from functools import wraps

from db import *

app = Flask(__name__)
app.secret_key = 'secret_key'
app.permanent_session_lifetime = timedelta(minutes=10)
socketio = SocketIO(app)
photo_folder = r'\\path\to\your\folder'

# Decorator to check if the user is authenticated
def login_required(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # User is not authenticated, redirect to login page
            return redirect(url_for('index'))
        return route_function(*args, **kwargs)

    return decorated_function


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user_id from the sessionц
    return redirect(url_for('index'))  # Redirect to the index or any other page after logout


@app.route('/')
def index():
    if 'user_id' in session:
        # User is already authenticated, redirect to spec page or any other page
        return redirect(url_for('spec'))

    conn = connect_db()
    cursor = conn.cursor()
    availability_check = "SELECT * FROM tester WHERE Logged IS NOT NULL LIMIT 25 "
    cursor.execute(availability_check)
    posts = cursor.fetchall()
    conn.close()
    return render_template('index.html', posts=posts)


@app.route('/', methods=['POST'])
def login():
    try:
        data = request.form
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return render_template('index.html', error='Username and password are required')

        conn = connect_db()
        cursor = conn.cursor()

        check_credentials_query = "SELECT * FROM auth "
        cursor.execute(check_credentials_query)
        user_data = cursor.fetchone()

        conn.close()



        if username == user_data['login'] and password == user_data['pass']:
            session['user_id'] = str(user_data['id'])
            return redirect(url_for('spec'))
        else:
            return render_template('login.html', error='Invalid username or password')

    except Exception as e:
        return render_template('index.html', error='Invalid username or password', exception=str(e))


@app.route('/winder')
@login_required
def winder():
    conn = connect_db()
    cursor = conn.cursor()
    select_all_data = "SELECT * FROM bd_name LIMIT 250"
    cursor.execute(select_all_data)
    all_data = cursor.fetchall()
    conn.close()
    return render_template('winder.html', all_data=all_data)


@app.route('/get_photo/<username>')
def get_photo(username):
    # Construct the absolute path to the photo
    photo_path = os.path.join(photo_folder, f'{username}.jpeg')

    # Check if the photo file exists
    if os.path.exists(photo_path):
        # If the file exists, send the photo
        return send_from_directory(photo_folder, f'{username}.jpeg')
    else:
        # If the file doesn't exist, send a default photo
        return send_from_directory('static/fotos', 'noname.jpg')

@app.route('/manage')
@login_required
def manage():
    conn = connect_db()
    cursor = conn.cursor()
    select_all_data = "SELECT * FROM tester LIMIT 100"
    cursor.execute(select_all_data)
    all_data = cursor.fetchall()
    conn.close()
    return render_template('manage.html', all_data=all_data)


@app.route('/spec')
@login_required
def spec():
    conn = connect_db()
    cursor = conn.cursor()
    availability_check = "SELECT * FROM bd_name WHERE Logged IS NOT NULL LIMIT 25 "
    cursor.execute(availability_check)
    posts = cursor.fetchall()
    conn.close()
    return render_template('spec.html', posts=posts)


@app.route('/gpupdate', methods=['POST'])
def gpupdate():
    try:
        data = request.get_json()
        hostname = data.get('hostname')

        conn = connect_db()
        cursor = conn.cursor()

        gpupdate_query = "UPDATE bd_name SET gpupdate= ('yes')"
        cursor.execute(gpupdate_query)

        conn.commit()
        conn.close()

        return {'status': 'success', 'message': f'gpupdate for {hostname} successful'}

    except Exception as e:
        return {'status': 'error', 'message': f'Error performing gpupdate for {hostname}', 'error': str(e)}


@app.route('/apply_changes', methods=['PUT'])
def apply_changes():
    try:
        data = request.get_json()
        changes = data.get('changes')

        if not changes:
            return jsonify({'status': 'error', 'message': 'No changes provided'})

        conn = connect_db()
        cursor = conn.cursor()

        for hostname, actions in changes.items():
            for action, value in actions.items():
                update_query = f"UPDATE bd_name SET {action} = '{value}' WHERE HostName = '{hostname}'"
                cursor.execute(update_query)

        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Changes applied successfully'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Error applying changes', 'error': str(e)})


@socketio.on('update_data_request')
def handle_update_data_request():
    conn = connect_db()
    cursor = conn.cursor()
    availability_check = "SELECT * FROM tester WHERE Logged IS NOT NULL LIMIT 25 "
    cursor.execute(availability_check)
    posts = (cursor.fetchall())  
    serialized_posts = json.dumps(posts, default=str)  
    serialized_posts = serialized_posts.encode('utf-8').decode('unicode-escape')
    emit('update_data', {'posts': serialized_posts}, broadcast=True)
    conn.close()


@socketio.on('update_winder_data_request')
def handle_update_winder_data_request():
    print('Received update_winder_data_request')
    conn = connect_db()
    cursor = conn.cursor()
    select_winder_data = "SELECT HostName, Logged FROM bd_name LIMIT 250"  
    cursor.execute(select_winder_data)
    winder_data = (cursor.fetchall())
    serialized_winder_data = json.dumps(winder_data, default=str)
    serialized_winder_data = serialized_winder_data.encode('utf-8').decode('unicode-escape')
    emit('update_winder_data', {'winder_data': serialized_winder_data}, broadcast=True)
    conn.close()


if __name__ == '__main__':
    socketio.run(app, debug=True)
