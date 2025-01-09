from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import json
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')  # Đọc secret key từ biến môi trường hoặc sử dụng giá trị mặc định

# Load data from JSON files
def load_data():
    try:
        with open("D:\\1\\bài dư thi\\library_data.json", "r") as f:
            library = json.load(f)
    except FileNotFoundError:
        library = []
    except json.JSONDecodeError:
        library = []

    try:
        with open("D:\\1\\bài dư thi\\transaction_log.json", "r") as f:
            transaction_log = json.load(f)
    except FileNotFoundError:
        transaction_log = []
    except json.JSONDecodeError:
        transaction_log = []

    return library, transaction_log

# Save data to JSON files
def save_data(library, transaction_log):
    with open("D:\\1\\bài dư thi\\library_data.json", "w") as f:
        json.dump(library, f, indent=4)
    with open("D:\\1\\bài dư thi\\transaction_log.json", "w") as f:
        json.dump(transaction_log, f, indent=4)

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('admin'))
        elif username == 'hocsinh' and password == 'hocsinh':
            session['user'] = 'student'
            return redirect(url_for('student'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/admin')
def admin():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/student')
def student():
    if 'user' not in session or session['user'] != 'student':
        return redirect(url_for('login'))
    return render_template('student.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/api/books', methods=['GET'])
def get_books():
    library, _ = load_data()
    return jsonify(library)

@app.route('/api/books', methods=['POST'])
def add_book():
    library, transaction_log = load_data()
    new_book = request.json
    library.append(new_book)
    save_data(library, transaction_log)
    return jsonify({'message': 'Book added successfully'}), 201

@app.route('/api/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    library, transaction_log = load_data()
    library = [book for book in library if book['book_id'] != book_id]
    save_data(library, transaction_log)
    return jsonify({'message': 'Book deleted successfully'}), 200

@app.route('/api/import_books', methods=['POST'])
def import_books():
    file = request.files['file']
    df = pd.read_excel(file)
    
    # Clear the current library data
    library = []
    transaction_log = []
    
    for _, row in df.iterrows():
        if pd.notna(row.get('title')) and pd.notna(row.get('author')) and pd.notna(row.get('year')) and pd.notna(row.get('book_id')):
            book = {
                "title": str(row['title']),
                "author": str(row['author']),
                "year": str(row['year']),
                "book_id": str(row['book_id']),
                "borrowed": False
            }
            library.append(book)
    
    save_data(library, transaction_log)
    return jsonify({'message': 'Books imported successfully, existing data replaced'}), 201

@app.route('/api/borrow_book', methods=['POST'])
def borrow_book():
    library, transaction_log = load_data()
    data = request.json
    book_index = data.get('book_index')
    borrower_name = data.get('borrower_name')
    borrower_class = data.get('borrower_class')
    borrow_date = data.get('borrow_date')
    borrow_period = data.get('borrow_period')

    if book_index is not None and 0 <= book_index < len(library):
        if not library[book_index]['borrowed']:
            library[book_index]['borrowed'] = True
            transaction = {
                'book_id': library[book_index]['book_id'],
                'borrower_name': borrower_name,
                'borrower_class': borrower_class,
                'borrow_date': borrow_date,
                'borrow_period': borrow_period,
                'action': 'borrow'
            }
            transaction_log.append(transaction)
            save_data(library, transaction_log)
            return jsonify({'message': 'Book borrowed successfully'}), 200
        else:
            return jsonify({'message': 'Book is already borrowed'}), 400
    else:
        return jsonify({'message': 'Invalid book index'}), 400

@app.route('/api/return_book', methods=['POST'])
def return_book():
    library, transaction_log = load_data()
    data = request.json
    returner_name = data.get('returner_name')
    book_id = data.get('book_id')

    book = next((book for book in library if book['book_id'] == book_id), None)
    if book is not None:
        if book['borrowed']:
            book['borrowed'] = False
            transaction = {
                'book_id': book['book_id'],
                'returner_name': returner_name,
                'action': 'return',
                'return_date': str(datetime.now().date())
            }
            transaction_log.append(transaction)
            save_data(library, transaction_log)
            return jsonify({'message': 'Book returned successfully'}), 200
        else:
            return jsonify({'message': 'Book is not borrowed'}), 400
    else:
        return jsonify({'message': 'Invalid book ID'}), 400

@app.route('/api/transaction_log', methods=['GET'])
def get_transaction_log():
    _, transaction_log = load_data()
    return jsonify(transaction_log)

if __name__ == '__main__':
    app.run(debug=True)