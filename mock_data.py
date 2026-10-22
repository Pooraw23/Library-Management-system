from datetime import date, datetime, timedelta

# In-memory storage tables
MEMBERS = []
CATEGORIES = []
BOOKS = []
AUTHORS = []
BOOK_AUTHORS = []
BOOK_COPIES = []
BOOK_ISSUE = []
RESERVATIONS = []
FINES = []

_COUNTERS = {
    'member_id': 0,
    'category_id': 0,
    'book_id': 0,
    'author_id': 0,
    'copy_id': 0,
    'issue_id': 0,
    'reservation_id': 0,
    'fine_id': 0
}

def get_next_id(entity: str) -> int:
    """Return an auto-incrementing ID for the specified entity."""
    _COUNTERS[entity] += 1
    return _COUNTERS[entity]

def reset_mock_data():
    """Initializes in-memory mock datasets with rich, realistic data."""
    global MEMBERS, CATEGORIES, BOOKS, AUTHORS, BOOK_AUTHORS, BOOK_COPIES, BOOK_ISSUE, RESERVATIONS, FINES, _COUNTERS
    
    today = date.today()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Categories
    CATEGORIES = [
        {'category_id': 1, 'category_name': 'Database Systems'},
        {'category_id': 2, 'category_name': 'Software Engineering'},
        {'category_id': 3, 'category_name': 'Computer Science & Algorithms'},
        {'category_id': 4, 'category_name': 'Artificial Intelligence'},
        {'category_id': 5, 'category_name': 'Operating Systems'},
        {'category_id': 6, 'category_name': 'Mathematics & Discrete Logic'}
    ]

    # Authors
    AUTHORS = [
        {'author_id': 1, 'author_name': 'Abraham Silberschatz'},
        {'author_id': 2, 'author_name': 'Henry F. Korth'},
        {'author_id': 3, 'author_name': 'S. Sudarshan'},
        {'author_id': 4, 'author_name': 'Robert C. Martin'},
        {'author_id': 5, 'author_name': 'Thomas H. Cormen'},
        {'author_id': 6, 'author_name': 'Charles E. Leiserson'},
        {'author_id': 7, 'author_name': 'Ronald L. Rivest'},
        {'author_id': 8, 'author_name': 'Clifford Stein'},
        {'author_id': 9, 'author_name': 'Stuart Russell'},
        {'author_id': 10, 'author_name': 'Peter Norvig'},
        {'author_id': 11, 'author_name': 'Andrew S. Tanenbaum'},
        {'author_id': 12, 'author_name': 'Martin Fowler'}
    ]

    # Books
    BOOKS = [
        {
            'book_id': 1,
            'isbn': '978-0078022159',
            'title': 'Database System Concepts (7th Edition)',
            'category_id': 1,
            'publisher': 'McGraw-Hill',
            'publication_year': 2019
        },
        {
            'book_id': 2,
            'isbn': '978-0132350884',
            'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
            'category_id': 2,
            'publisher': 'Prentice Hall',
            'publication_year': 2008
        },
        {
            'book_id': 3,
            'isbn': '978-0262033848',
            'title': 'Introduction to Algorithms (CLRS 3rd Edition)',
            'category_id': 3,
            'publisher': 'MIT Press',
            'publication_year': 2009
        },
        {
            'book_id': 4,
            'isbn': '978-0134610993',
            'title': 'Artificial Intelligence: A Modern Approach (4th Edition)',
            'category_id': 4,
            'publisher': 'Pearson',
            'publication_year': 2020
        },
        {
            'book_id': 5,
            'isbn': '978-0133591620',
            'title': 'Modern Operating Systems (4th Edition)',
            'category_id': 5,
            'publisher': 'Pearson',
            'publication_year': 2014
        },
        {
            'book_id': 6,
            'isbn': '978-0134757599',
            'title': 'Refactoring: Improving the Design of Existing Code',
            'category_id': 2,
            'publisher': 'Addison-Wesley',
            'publication_year': 2018
        }
    ]

    # Book Authors relationships
    BOOK_AUTHORS = [
        {'book_id': 1, 'author_id': 1},
        {'book_id': 1, 'author_id': 2},
        {'book_id': 1, 'author_id': 3},
        {'book_id': 2, 'author_id': 4},
        {'book_id': 3, 'author_id': 5},
        {'book_id': 3, 'author_id': 6},
        {'book_id': 3, 'author_id': 7},
        {'book_id': 3, 'author_id': 8},
        {'book_id': 4, 'author_id': 9},
        {'book_id': 4, 'author_id': 10},
        {'book_id': 5, 'author_id': 11},
        {'book_id': 6, 'author_id': 12}
    ]

    # Book Copies (ER: Book_Copies -> Copy_Id, Book_Id, Status)
    # Notice Book 3 has both copies issued so reservations can be tested
    BOOK_COPIES = [
        {'copy_id': 1, 'book_id': 1, 'status': 'issued'},
        {'copy_id': 2, 'book_id': 1, 'status': 'available'},
        {'copy_id': 3, 'book_id': 1, 'status': 'available'},
        {'copy_id': 4, 'book_id': 2, 'status': 'available'},
        {'copy_id': 5, 'book_id': 2, 'status': 'issued'},
        {'copy_id': 6, 'book_id': 3, 'status': 'issued'},
        {'copy_id': 7, 'book_id': 3, 'status': 'issued'},
        {'copy_id': 8, 'book_id': 4, 'status': 'available'},
        {'copy_id': 9, 'book_id': 4, 'status': 'available'},
        {'copy_id': 10, 'book_id': 5, 'status': 'available'},
        {'copy_id': 11, 'book_id': 5, 'status': 'lost'},
        {'copy_id': 12, 'book_id': 6, 'status': 'available'}
    ]

    # Members / Students (Passwords: admin123, librarian123, member123)
    MEMBERS = [
        {
            'member_id': 1,
            'student_id': 1,
            'name': 'System Administrator',
            'email': 'admin@library.edu',
            'password_hash': 'scrypt:32768:8:1$6mPlyQ14zQwmbezy$1e458c9cae1e42a6aed16b10d8673ad36ad55d3c1e4c0a0fde670dcdcca0d965a5d951ee796ee5d68322fe649ea936cc4ee04e37e97294f534688be16ec7b5ec',
            'role': 'admin',
            'department': 'Administration',
            'joined_on': (today - timedelta(days=180)).isoformat(),
            'is_active': True
        },
        {
            'member_id': 2,
            'student_id': 2,
            'name': 'Eleanor Vance',
            'email': 'librarian@library.edu',
            'password_hash': 'scrypt:32768:8:1$fpwoua8rWbshcS6S$509269e256446ec7f8f4db8a1d1b02000e8eba06161af509f31ebcfeb745c82f84fd054158785bbd62b869a3dfa883ba65df9852f68662c027f9a9432d86bfac',
            'role': 'librarian',
            'department': 'Central Library',
            'joined_on': (today - timedelta(days=120)).isoformat(),
            'is_active': True
        },
        {
            'member_id': 3,
            'student_id': 3,
            'name': 'John Doe',
            'email': 'john.doe@student.edu',
            'password_hash': 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb',
            'role': 'member',
            'department': 'Computer Science',
            'joined_on': (today - timedelta(days=90)).isoformat(),
            'is_active': True
        },
        {
            'member_id': 4,
            'student_id': 4,
            'name': 'Alice Smith',
            'email': 'alice.smith@student.edu',
            'password_hash': 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb',
            'role': 'member',
            'department': 'Information Technology',
            'joined_on': (today - timedelta(days=60)).isoformat(),
            'is_active': True
        },
        {
            'member_id': 5,
            'student_id': 5,
            'name': 'Bob Taylor',
            'email': 'bob.taylor@student.edu',
            'password_hash': 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb',
            'role': 'member',
            'department': 'Electrical Engineering',
            'joined_on': (today - timedelta(days=30)).isoformat(),
            'is_active': True
        }
    ]

    # Book Issues / Borrow Records
    # Issue 1: John Doe, DBC-101 (issued 5 days ago, due in 9 days)
    # Issue 2: Alice Smith, CC-202 (issued 25 days ago, due 11 days ago -> OVERDUE)
    # Issue 3: Bob Taylor, ALGO-301 (issued 30 days ago, due 16 days ago, returned 10 days ago -> 6 days late, has fine)
    # Issue 4: John Doe, ALGO-302 (issued 2 days ago, due in 12 days)
    BOOK_ISSUE = [
        {
            'issue_id': 1,
            'borrow_id': 1,
            'member_id': 3,
            'student_id': 3,
            'copy_id': 1,
            'issue_date': (today - timedelta(days=5)).isoformat(),
            'due_date': (today + timedelta(days=9)).isoformat(),
            'return_date': None
        },
        {
            'issue_id': 2,
            'borrow_id': 2,
            'member_id': 4,
            'student_id': 4,
            'copy_id': 5,
            'issue_date': (today - timedelta(days=25)).isoformat(),
            'due_date': (today - timedelta(days=11)).isoformat(),
            'return_date': None
        },
        {
            'issue_id': 3,
            'borrow_id': 3,
            'member_id': 5,
            'student_id': 5,
            'copy_id': 6,
            'issue_date': (today - timedelta(days=30)).isoformat(),
            'due_date': (today - timedelta(days=16)).isoformat(),
            'return_date': (today - timedelta(days=10)).isoformat()
        },
        {
            'issue_id': 4,
            'borrow_id': 4,
            'member_id': 3,
            'student_id': 3,
            'copy_id': 7,
            'issue_date': (today - timedelta(days=2)).isoformat(),
            'due_date': (today + timedelta(days=12)).isoformat(),
            'return_date': None
        }
    ]

    # Reservations
    # Alice Smith reserved Book 3 (Introduction to Algorithms)
    RESERVATIONS = [
        {
            'reservation_id': 1,
            'member_id': 4,
            'book_id': 3,
            'reserved_at': now_str,
            'status': 'pending'
        }
    ]

    # Fines (ER: Fines -> Fine_Id, Fine_Amount, Payment_Status)
    # Fine for Issue 3: 6 days overdue * ₹2/day = ₹12.00, ₹5.00 paid -> Unpaid
    FINES = [
        {
            'fine_id': 1,
            'issue_id': 3,
            'borrow_id': 3,
            'fine_amount': 12.00,
            'payment_status': 'Unpaid',
            'amount': 12.00,
            'amount_paid': 5.00
        }
    ]

    _COUNTERS = {
        'member_id': 5,
        'category_id': 6,
        'book_id': 6,
        'author_id': 12,
        'copy_id': 12,
        'issue_id': 4,
        'reservation_id': 1,
        'fine_id': 1
    }

# Initialize upon module load
reset_mock_data()
