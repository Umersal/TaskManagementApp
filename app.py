#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import mysql.connector
from flask_cors import CORS
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app)


db_host = os.environ.get("HOST")
db_user = os.environ.get("USER")
db_password = os.environ.get("PASSWORD")
db_port = os.environ.get("PORT")
db_base = os.environ.get("DATABASE")


mydb = mysql.connector.connect(
  host=db_host,
  user=db_user,
  password=db_password,
    port = db_port,
    database = db_base
)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/addtask', methods=['GET', 'POST'])
def addTask():
    """
    This function adds the task to the database
    """
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        task = data.get('task_name')
        due_date = data.get('due_date')
        priority = data.get('priority')
        tags = ','.join(data.get('tags')) 
        assigned_to = data.get('assigned_to')
        
        mycursor = mydb.cursor()
        query = """
            INSERT INTO tasks (task, due_date, priority, tags, completed, assigned_to)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (task, due_date, priority, tags, False, assigned_to)  # Assuming "completed" is a boolean (False by default)
        
        mycursor.execute(query, values)
        mydb.commit()
        mycursor.close()
        
        # Return the data that was added as a response
        return jsonify({
            'task': task,
            'due_date': due_date,
            'priority': priority,
            'tags': tags,
            'assigned_to': assigned_to
        })


@app.route('/fetchtasks', methods=['GET'])
def getTasks():
    """
    function to fetch all the tasks from the database
    """
    mycursor = mydb.cursor()
    query = "SELECT * FROM tasks"
    mycursor.execute(query)
    tasks = []
    for task in mycursor.fetchall():
        task_data = {
            'task_id': task[0],
            'task_name': task[1],
            'due_date': task[2],
            'priority': task[3],
            'tags': task[4].split(', '),
            'completed': task[5],
            'assigned_to': task[6]
        }
        tasks.append(task_data)

    # Close the cursor
    mycursor.close()

    return jsonify({'tasks': tasks})

@app.route('/updatetask/<int:task_id>', methods=['PUT'])
def updateTask(task_id):
    """
    function to update the task and store in the database
    """
    if request.method == 'PUT':
        data = request.get_json()
        task_name = data.get('task_name')
        due_date = data.get('due_date')
        priority = data.get('priority')
        tags = ','.join(data.get('tags'))
        print(task_name)
        print(due_date)
        print(priority)
        print(tags)

        mycursor = mydb.cursor()

        # Replace 'id' with the actual name of your primary key column
        query = "UPDATE tasks SET task = %s, due_date = %s, priority = %s, tags = %s WHERE id = %s"
        
        values = (task_name, due_date, priority, tags, task_id)

        mycursor.execute(query, values)
        mydb.commit()
        mycursor.close()

        return jsonify({
            'task_name': task_name,
            'due_date': due_date,
            'priority': priority,
            'tags': tags,
        })
    
@app.route('/reassigntask/<int:task_id>', methods=['PUT'])
def reassignTask(task_id):
    """
    function to reassign the task and store in the database
    """
    if request.method == 'PUT':
        data = request.get_json()
        task_name = data.get('task_name')
        assigned_to = data.get('assigned_to')

        mycursor = mydb.cursor()
        query = """
            UPDATE tasks
            SET assigned_to = %s
            WHERE id = %s
        """
        values = (assigned_to, task_id)

        mycursor.execute(query, values)
        mydb.commit()
        mycursor.close()

        return jsonify({
            'task_name': task_name,
            'assigned_to': assigned_to,
        })
    
@app.route('/distinctlabels', methods=['GET'])
def distinctLabels():
    """
    function to return distinct labels from the database so as to add it as a part of filter
    """
    mycursor = mydb.cursor()
    query = "SELECT DISTINCT tags FROM tasks"
    mycursor.execute(query)
    labels = [tag[0] for tag in mycursor.fetchall()]
    print(labels)
    mycursor.close()
    return jsonify({'labels': labels})

@app.route('/filtertasks/<label>', methods=['GET'])
def filterTasksByLabel(label):
    """
    function that returns the filtered task from the database based on labels
    """
    print(label)
    mycursor = mydb.cursor()
    query = "SELECT * FROM tasks WHERE FIND_IN_SET(%s, tags)"
    mycursor.execute(query, (label,))
    tasks = []
    for task in mycursor.fetchall():
        task_data = {
            'task_id': task[0],
            'task_name': task[1],
            'due_date': task[2],
            'priority': task[3],
            'tags': task[4].split(', '),
            'completed': task[5],
            'assigned_to': task[6]
        }
        tasks.append(task_data)

    # Close the cursor
    mycursor.close()

    return jsonify({'tasks': tasks})  


@app.route('/dueintwodays', methods=['GET'])
def getTasksDueInTwoDays():
    """
    function that returns tasks which are due in next two days so that it can be added as a part of web push notification
    """
    # Calculate the date 2 days from now
    today = datetime.now()
    two_days_from_now = today + timedelta(days=2)

    mycursor_due = mydb.cursor(dictionary=True)
    query = "SELECT * FROM tasks WHERE due_date > %s AND due_date <= %s"
    mycursor_due.execute(query, (today, two_days_from_now))
    tasks = []
    for task in mycursor_due.fetchall():
        task_data = {
            'task_id': task['id'],
            'task_name': task['task'],
            'due_date': task['due_date'].strftime('%Y-%m-%d'),
            'priority': task['priority'],
            'tags': task['tags'].split(', '),
            'completed': task['completed'],
            'assigned_to': task['assigned_to']
        }
        tasks.append(task_data)
    print(tasks)
    mycursor_due.close()

    return jsonify({'tasks': tasks})



if __name__ == '__main__':
    app.run()

