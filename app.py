from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import Config
import repository
import os

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS with credential support for session cookies
CORS(app, supports_credentials=True)

# -------------------------------------------------------------------------
# Authentication & Authorization Helpers
# -------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required. Please sign in.'}), 401
        current_user = repository.get_user_by_id(user_id)
        if not current_user or not current_user.get('is_active', True):
            session.clear()
            return jsonify({'error': 'Account is inactive or does not exist.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required. Please sign in.'}), 401
            current_user = repository.get_user_by_id(user_id)
            if not current_user or not current_user.get('is_active', True):
                session.clear()
                return jsonify({'error': 'Account is inactive or does not exist.'}), 401
            if current_user.get('role') not in allowed_roles:
                return jsonify({'error': f'Access forbidden: Requires one of {list(allowed_roles)} roles.'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return repository.get_user_by_id(user_id)
    return None

# -------------------------------------------------------------------------
# HTML Frontend Page Routes
# -------------------------------------------------------------------------

@app.route('/')
@app.route('/index.html')
def index_page():
    return render_template('index.html')

@app.route('/login')
@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/register')
@app.route('/register.html')
def register_page():
    return render_template('register.html')

@app.route('/books')
@app.route('/books.html')
def books_page():
    return render_template('books.html')

@app.route('/book')
@app.route('/book.html')
def book_detail_page():
    return render_template('book.html')

@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/admin')
@app.route('/admin.html')
def admin_page():
    return render_template('admin.html')

# -------------------------------------------------------------------------
# Authentication Endpoints
# -------------------------------------------------------------------------

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    department = data.get('department', '').strip() or None
    role = data.get('role', 'member')

    # Security check: standard registrations default to 'member'
    # Only logged-in admin can create staff accounts
    curr_user = get_current_user()
    if role in ('admin', 'librarian'):
        if not curr_user or curr_user.get('role') != 'admin':
            role = 'member'

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required fields.'}), 400

    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Please provide a valid email address.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    try:
        existing = repository.get_user_by_email(email)
        if existing:
            return jsonify({'error': 'An account with this email address already exists.'}), 409

        hashed_password = generate_password_hash(password)
        new_member = repository.create_member(name, email, hashed_password, role=role, department=department)

        # Automatically sign user in upon registration
        session['user_id'] = new_member['member_id']
        session['role'] = new_member['role']

        clean_user = {k: v for k, v in new_member.items() if k != 'password_hash'}
        return jsonify({'message': 'Registration successful.', 'user': clean_user}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = repository.get_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    if not user.get('is_active', True):
        return jsonify({'error': 'Account has been deactivated. Please contact the administrator.'}), 403

    session['user_id'] = user['member_id']
    session['role'] = user['role']

    clean_user = {k: v for k, v in user.items() if k != 'password_hash'}
    return jsonify({
        'message': 'Login successful.',
        'user': clean_user
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully.'}), 200

@app.route('/api/me', methods=['GET'])
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated.'}), 401
    clean_user = {k: v for k, v in user.items() if k != 'password_hash'}
    return jsonify({'user': clean_user}), 200

# -------------------------------------------------------------------------
# Books & Catalog Endpoints
# -------------------------------------------------------------------------

@app.route('/api/books', methods=['GET'])
def api_get_books():
    query = request.args.get('q', '').strip() or None
    category_id = request.args.get('category_id')
    try:
        cat_id = int(category_id) if category_id else None
    except ValueError:
        cat_id = None
    books = repository.get_books(query=query, category_id=cat_id)
    return jsonify(books), 200

@app.route('/api/books/<int:book_id>', methods=['GET'])
def api_get_book(book_id):
    book = repository.get_book_by_id(book_id)
    if not book:
        return jsonify({'error': 'Book not found.'}), 404
    return jsonify(book), 200

@app.route('/api/books', methods=['POST'])
@roles_required('admin', 'librarian')
def api_create_book():
    data = request.get_json() or {}
    isbn = data.get('isbn', '').strip()
    title = data.get('title', '').strip()
    category_id = data.get('category_id')
    publisher = data.get('publisher', '').strip() or None
    publication_year = data.get('publication_year')
    author_ids = data.get('author_ids', [])

    if not isbn or not title or not category_id:
        return jsonify({'error': 'ISBN, title, and category are required.'}), 400

    try:
        book = repository.create_book(
            isbn=isbn,
            title=title,
            category_id=int(category_id),
            publisher=publisher,
            publication_year=int(publication_year) if publication_year else None,
            author_ids=[int(a) for a in author_ids] if author_ids else []
        )
        return jsonify({'message': 'Book added successfully.', 'book': book}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/<int:book_id>', methods=['PUT'])
@roles_required('admin', 'librarian')
def api_update_book(book_id):
    data = request.get_json() or {}
    isbn = data.get('isbn', '').strip()
    title = data.get('title', '').strip()
    category_id = data.get('category_id')
    publisher = data.get('publisher', '').strip() or None
    publication_year = data.get('publication_year')
    author_ids = data.get('author_ids')

    if not isbn or not title or not category_id:
        return jsonify({'error': 'ISBN, title, and category are required.'}), 400

    try:
        book = repository.update_book(
            book_id=book_id,
            isbn=isbn,
            title=title,
            category_id=int(category_id),
            publisher=publisher,
            publication_year=int(publication_year) if publication_year else None,
            author_ids=[int(a) for a in author_ids] if author_ids is not None else None
        )
        return jsonify({'message': 'Book updated successfully.', 'book': book}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
@roles_required('admin', 'librarian')
def api_delete_book(book_id):
    try:
        repository.delete_book(book_id)
        return jsonify({'message': 'Book deleted successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# -------------------------------------------------------------------------
# Categories & Authors Endpoints
# -------------------------------------------------------------------------

@app.route('/api/categories', methods=['GET'])
def api_get_categories():
    categories = repository.get_categories()
    return jsonify(categories), 200

@app.route('/api/categories', methods=['POST'])
@roles_required('admin', 'librarian')
def api_create_category():
    data = request.get_json() or {}
    name = data.get('category_name', '').strip()
    if not name:
        return jsonify({'error': 'Category name is required.'}), 400
    try:
        cat = repository.create_category(name)
        return jsonify({'message': 'Category created.', 'category': cat}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/authors', methods=['GET'])
def api_get_authors():
    authors = repository.get_authors()
    return jsonify(authors), 200

@app.route('/api/authors', methods=['POST'])
@roles_required('admin', 'librarian')
def api_create_author():
    data = request.get_json() or {}
    name = data.get('author_name', '').strip()
    if not name:
        return jsonify({'error': 'Author name is required.'}), 400
    try:
        auth = repository.create_author(name)
        return jsonify({'message': 'Author created.', 'author': auth}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# -------------------------------------------------------------------------
# Book Copies Endpoints
# -------------------------------------------------------------------------

@app.route('/api/copies', methods=['GET'])
def api_get_copies():
    book_id = request.args.get('book_id')
    bid = int(book_id) if book_id else None
    copies = repository.get_copies(bid)
    return jsonify(copies), 200

@app.route('/api/books/<int:book_id>/copies', methods=['POST'])
@roles_required('admin', 'librarian')
def api_create_copy(book_id):
    data = request.get_json() or {}
    status = data.get('status', 'available')
    try:
        copy = repository.create_copy(book_id, status=status)
        return jsonify({'message': 'Book copy added successfully.', 'copy': copy}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# -------------------------------------------------------------------------
# Issue & Return Circulation Endpoints
# -------------------------------------------------------------------------

@app.route('/api/issue', methods=['POST'])
@login_required
def api_issue_book():
    user = get_current_user()
    data = request.get_json() or {}
    copy_id = data.get('copy_id')
    book_id = data.get('book_id')
    issue_date = data.get('issue_date')
    due_date = data.get('due_date')

    # If book_id is provided without copy_id, automatically allocate the first available copy
    if not copy_id and book_id:
        copies = repository.get_copies(book_id=int(book_id))
        avail = [c for c in copies if c['status'] == 'available']
        if not avail:
            return jsonify({'error': 'No available copies for this book right now.'}), 400
        copy_id = avail[0]['copy_id']

    # Admin and librarians can issue to any member; regular members borrow for themselves
    if user['role'] in ('admin', 'librarian'):
        member_id = data.get('member_id') or user['member_id']
    else:
        member_id = user['member_id']

    if not copy_id:
        return jsonify({'error': 'Copy ID or Book ID is required.'}), 400

    try:
        issue = repository.issue_book(
            member_id=int(member_id),
            copy_id=int(copy_id),
            issue_date=issue_date,
            due_date=due_date
        )
        return jsonify({'message': 'Book issued successfully.', 'issue': issue}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/return/<int:issue_id>', methods=['POST'])
@login_required
def api_return_book(issue_id):
    user = get_current_user()
    data = request.get_json() or {}
    return_date = data.get('return_date')

    # If member, ensure they can only return their own borrowed books
    if user['role'] not in ('admin', 'librarian'):
        issues = repository.get_issues(member_id=user['member_id'])
        user_issue_ids = [i['issue_id'] for i in issues]
        if issue_id not in user_issue_ids:
            return jsonify({'error': 'Unauthorized: You can only return books borrowed by your own account.'}), 403

    try:
        result = repository.return_book(issue_id=issue_id, return_date=return_date)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/issues', methods=['GET'])
@login_required
def api_get_issues():
    user = get_current_user()
    if user['role'] in ('admin', 'librarian'):
        member_id = request.args.get('member_id')
        mid = int(member_id) if member_id else None
        issues = repository.get_issues(mid)
    else:
        # Regular members can only view their own issues
        issues = repository.get_issues(user['member_id'])
    return jsonify(issues), 200

# -------------------------------------------------------------------------
# Reservations Endpoints
# -------------------------------------------------------------------------

@app.route('/api/reservations', methods=['POST'])
@login_required
def api_create_reservation():
    user = get_current_user()
    data = request.get_json() or {}
    book_id = data.get('book_id')

    # If admin/librarian reserves on behalf of a member, use provided member_id
    member_id = data.get('member_id') if user['role'] in ('admin', 'librarian') and data.get('member_id') else user['member_id']

    if not book_id:
        return jsonify({'error': 'Book ID is required.'}), 400

    try:
        reservation = repository.create_reservation(member_id=int(member_id), book_id=int(book_id))
        return jsonify({'message': 'Reservation placed successfully.', 'reservation': reservation}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/reservations', methods=['GET'])
@login_required
def api_get_reservations():
    user = get_current_user()
    if user['role'] in ('admin', 'librarian'):
        member_id = request.args.get('member_id')
        mid = int(member_id) if member_id else None
        reservations = repository.get_reservations(mid)
    else:
        reservations = repository.get_reservations(user['member_id'])
    return jsonify(reservations), 200

@app.route('/api/reservations/<int:reservation_id>', methods=['DELETE'])
@login_required
def api_cancel_reservation(reservation_id):
    user = get_current_user()
    is_admin = user['role'] in ('admin', 'librarian')
    try:
        res = repository.cancel_reservation(reservation_id, member_id=user['member_id'], is_admin=is_admin)
        return jsonify({'message': 'Reservation cancelled successfully.', 'reservation': res}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# -------------------------------------------------------------------------
# Fines Endpoints
# -------------------------------------------------------------------------

@app.route('/api/fines', methods=['GET'])
@login_required
def api_get_fines():
    user = get_current_user()
    if user['role'] in ('admin', 'librarian'):
        member_id = request.args.get('member_id')
        mid = int(member_id) if member_id else None
        fines = repository.get_fines(mid)
    else:
        fines = repository.get_fines(user['member_id'])
    return jsonify(fines), 200

@app.route('/api/fines/<int:fine_id>/pay', methods=['POST'])
@roles_required('admin', 'librarian')
def api_pay_fine(fine_id):
    data = request.get_json() or {}
    amount = data.get('amount')
    try:
        updated = repository.pay_fine(fine_id, amount=float(amount) if amount is not None else None)
        return jsonify({'message': 'Fine payment recorded successfully.', 'fine': updated}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# -------------------------------------------------------------------------
# Member & Administrative Overview Endpoints
# -------------------------------------------------------------------------

@app.route('/api/members', methods=['GET'])
@roles_required('admin', 'librarian')
def api_get_members():
    members = repository.get_members()
    clean_members = [{k: v for k, v in m.items() if k != 'password_hash'} for m in members]
    return jsonify(clean_members), 200

@app.route('/api/stats', methods=['GET'])
@login_required
def api_get_stats():
    user = get_current_user()
    if user['role'] in ('admin', 'librarian'):
        stats = repository.get_dashboard_stats()
    else:
        stats = repository.get_dashboard_stats(member_id=user['member_id'])
    return jsonify(stats), 200

# -------------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("\n" + "=" * 60)
    print("  Smart Library Management System is running!")
    print(f"  Local URL : http://localhost:{port}")
    print(f"  Network   : http://127.0.0.1:{port}")
    print(f"  Mode      : {'PostgreSQL Database' if repository._use_db_active else 'In-Memory Mock Data (Offline Ready)'}")
    print("=" * 60)
    print("  Demo Login Credentials:")
    print("   - Admin / Librarian:  admin@library.edu    (Password: admin123)")
    print("   - Student Member:     john.doe@student.edu (Password: member123)")
    print("=" * 60 + "\n")

    # Auto-open browser after 1.2s when server is ready
    import threading, webbrowser, time
    def _open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass
    threading.Thread(target=_open_browser, daemon=True).start()

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
