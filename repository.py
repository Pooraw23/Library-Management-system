import datetime
from decimal import Decimal
from config import Config
import logging

logger = logging.getLogger(__name__)

# Ensure mock datasets are ready
import mock_data
if not Config.USE_DB:
    mock_data.reset_mock_data()

# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------

def to_json_serializable(val):
    """Recursively convert Dates, Datetimes, and Decimals to JSON-friendly primitives."""
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, dict):
        return {k: to_json_serializable(v) for k, v in val.items()}
    if isinstance(val, list):
        return [to_json_serializable(item) for item in val]
    return val

def parse_date(d):
    """Safely parse date input into datetime.date object."""
    if isinstance(d, datetime.date):
        return d
    if isinstance(d, datetime.datetime):
        return d.date()
    if isinstance(d, str):
        return datetime.date.fromisoformat(d.split('T')[0])
    return datetime.date.today()

# -------------------------------------------------------------------------
# PostgreSQL Implementation
# -------------------------------------------------------------------------

class DBRepository:
    @staticmethod
    def get_user_by_email(email):
        import db
        query = """
            SELECT member_id, name, email, password_hash, role, department, joined_on, is_active
            FROM members
            WHERE email = %s;
        """
        row = db.execute_query(query, (email.strip().lower(),), fetch='one')
        return to_json_serializable(row)

    @staticmethod
    def get_user_by_id(member_id):
        import db
        query = """
            SELECT member_id, name, email, password_hash, role, department, joined_on, is_active
            FROM members
            WHERE member_id = %s;
        """
        row = db.execute_query(query, (member_id,), fetch='one')
        return to_json_serializable(row)

    @staticmethod
    def create_member(name, email, password_hash, role='member', department=None):
        import db
        query = """
            INSERT INTO members (name, email, password_hash, role, department, joined_on, is_active)
            VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, TRUE)
            RETURNING member_id, name, email, role, department, joined_on, is_active;
        """
        row = db.execute_query(query, (name.strip(), email.strip().lower(), password_hash, role, department), fetch='one', commit=True)
        return to_json_serializable(row)

    @staticmethod
    def get_members():
        import db
        query = """
            SELECT 
                m.member_id, m.name, m.email, m.role, m.department, m.joined_on, m.is_active,
                COUNT(DISTINCT bi.issue_id) FILTER (WHERE bi.return_date IS NULL) AS active_issues,
                COALESCE(SUM(f.amount - f.amount_paid), 0) AS total_unpaid_fines
            FROM members m
            LEFT JOIN book_issue bi ON m.member_id = bi.member_id
            LEFT JOIN fines f ON bi.issue_id = f.issue_id
            GROUP BY m.member_id
            ORDER BY m.member_id ASC;
        """
        rows = db.execute_query(query, fetch='all')
        return to_json_serializable(rows)

    @staticmethod
    def get_categories():
        import db
        query = """
            SELECT c.category_id, c.category_name, COUNT(b.book_id) AS book_count
            FROM categories c
            LEFT JOIN books b ON c.category_id = b.category_id
            GROUP BY c.category_id
            ORDER BY c.category_name ASC;
        """
        rows = db.execute_query(query, fetch='all')
        return to_json_serializable(rows)

    @staticmethod
    def create_category(category_name):
        import db
        query = """
            INSERT INTO categories (category_name)
            VALUES (%s)
            RETURNING category_id, category_name;
        """
        row = db.execute_query(query, (category_name.strip(),), fetch='one', commit=True)
        return to_json_serializable(row)

    @staticmethod
    def get_authors():
        import db
        query = """
            SELECT a.author_id, a.author_name, COUNT(ba.book_id) AS book_count
            FROM authors a
            LEFT JOIN book_authors ba ON a.author_id = ba.author_id
            GROUP BY a.author_id
            ORDER BY a.author_name ASC;
        """
        rows = db.execute_query(query, fetch='all')
        return to_json_serializable(rows)

    @staticmethod
    def create_author(author_name):
        import db
        query = """
            INSERT INTO authors (author_name)
            VALUES (%s)
            RETURNING author_id, author_name;
        """
        row = db.execute_query(query, (author_name.strip(),), fetch='one', commit=True)
        return to_json_serializable(row)

    @staticmethod
    def get_books(query=None, category_id=None):
        import db
        sql = """
            SELECT 
                b.book_id, b.isbn, b.title, b.publisher, b.publication_year,
                b.category_id, c.category_name,
                COALESCE(
                    json_agg(json_build_object('author_id', a.author_id, 'author_name', a.author_name))
                    FILTER (WHERE a.author_id IS NOT NULL), '[]'
                ) AS authors,
                COUNT(bc.copy_id) AS total_copies,
                COUNT(bc.copy_id) FILTER (WHERE bc.status = 'available') AS available_copies
            FROM books b
            JOIN categories c ON b.category_id = c.category_id
            LEFT JOIN book_authors ba ON b.book_id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.author_id
            LEFT JOIN book_copies bc ON b.book_id = bc.book_id
            WHERE 1=1
        """
        params = []
        if category_id:
            sql += " AND b.category_id = %s"
            params.append(category_id)
        if query:
            sql += """ AND (
                b.title ILIKE %s OR 
                b.isbn ILIKE %s OR 
                c.category_name ILIKE %s OR 
                EXISTS (
                    SELECT 1 FROM book_authors ba2 
                    JOIN authors a2 ON ba2.author_id = a2.author_id 
                    WHERE ba2.book_id = b.book_id AND a2.author_name ILIKE %s
                )
            )"""
            pattern = f"%{query.strip()}%"
            params.extend([pattern, pattern, pattern, pattern])

        sql += " GROUP BY b.book_id, c.category_name ORDER BY b.title ASC;"
        rows = db.execute_query(sql, tuple(params), fetch='all')
        return to_json_serializable(rows)

    @staticmethod
    def get_book_by_id(book_id):
        import db
        sql_book = """
            SELECT 
                b.book_id, b.isbn, b.title, b.publisher, b.publication_year,
                b.category_id, c.category_name,
                COALESCE(
                    json_agg(json_build_object('author_id', a.author_id, 'author_name', a.author_name))
                    FILTER (WHERE a.author_id IS NOT NULL), '[]'
                ) AS authors,
                COUNT(bc.copy_id) AS total_copies,
                COUNT(bc.copy_id) FILTER (WHERE bc.status = 'available') AS available_copies
            FROM books b
            JOIN categories c ON b.category_id = c.category_id
            LEFT JOIN book_authors ba ON b.book_id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.author_id
            LEFT JOIN book_copies bc ON b.book_id = bc.book_id
            WHERE b.book_id = %s
            GROUP BY b.book_id, c.category_name;
        """
        book = db.execute_query(sql_book, (book_id,), fetch='one')
        if not book:
            return None

        sql_copies = """
            SELECT copy_id, book_id, status
            FROM book_copies
            WHERE book_id = %s
            ORDER BY copy_id ASC;
        """
        copies = db.execute_query(sql_copies, (book_id,), fetch='all')
        book['copies'] = copies
        return to_json_serializable(book)

    @staticmethod
    def create_book(isbn, title, category_id, publisher, publication_year, author_ids=None):
        import db
        with db.get_db_cursor() as (cur, conn):
            cur.execute("""
                INSERT INTO books (isbn, title, category_id, publisher, publication_year)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING book_id, isbn, title, category_id, publisher, publication_year;
            """, (isbn.strip(), title.strip(), category_id, publisher, publication_year))
            book = dict(cur.fetchone())
            book_id = book['book_id']

            if author_ids:
                for aid in author_ids:
                    cur.execute("""
                        INSERT INTO book_authors (book_id, author_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (book_id, aid))

            # Automatically create 1 initial available copy
            cur.execute("""
                INSERT INTO book_copies (book_id, status)
                VALUES (%s, 'available');
            """, (book_id,))

            conn.commit()
            return DBRepository.get_book_by_id(book_id)

    @staticmethod
    def update_book(book_id, isbn, title, category_id, publisher, publication_year, author_ids=None):
        import db
        with db.get_db_cursor() as (cur, conn):
            cur.execute("""
                UPDATE books 
                SET isbn = %s, title = %s, category_id = %s, publisher = %s, publication_year = %s
                WHERE book_id = %s;
            """, (isbn.strip(), title.strip(), category_id, publisher, publication_year, book_id))

            if author_ids is not None:
                cur.execute("DELETE FROM book_authors WHERE book_id = %s;", (book_id,))
                for aid in author_ids:
                    cur.execute("""
                        INSERT INTO book_authors (book_id, author_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (book_id, aid))

            conn.commit()
            return DBRepository.get_book_by_id(book_id)

    @staticmethod
    def delete_book(book_id):
        import db
        # Check if copies are currently issued
        active_issues = db.execute_query("""
            SELECT COUNT(*) AS active_count
            FROM book_issue bi
            JOIN book_copies bc ON bi.copy_id = bc.copy_id
            WHERE bc.book_id = %s AND bi.return_date IS NULL;
        """, (book_id,), fetch='one')
        if active_issues and active_issues['active_count'] > 0:
            raise ValueError("Cannot delete book: Copies of this book are currently issued to members.")

        db.execute_query("DELETE FROM books WHERE book_id = %s;", (book_id,), commit=True)
        return True

    @staticmethod
    def get_copies(book_id=None):
        import db
        sql = """
            SELECT bc.copy_id, bc.book_id, bc.status, b.title, b.isbn
            FROM book_copies bc
            JOIN books b ON bc.book_id = b.book_id
        """
        params = []
        if book_id:
            sql += " WHERE bc.book_id = %s"
            params.append(book_id)
        sql += " ORDER BY bc.copy_id ASC;"
        rows = db.execute_query(sql, tuple(params), fetch='all')
        return to_json_serializable(rows)

    @staticmethod
    def create_copy(book_id, accession_code=None, status='available'):
        import db
        query = """
            INSERT INTO book_copies (book_id, status)
            VALUES (%s, %s)
            RETURNING copy_id, book_id, status;
        """
        row = db.execute_query(query, (book_id, status or 'available'), fetch='one', commit=True)
        return to_json_serializable(row)

    @staticmethod
    def issue_book(member_id, copy_id, issue_date=None, due_date=None):
        import db
        with db.get_db_cursor() as (cur, conn):
            # Check copy status
            cur.execute("SELECT copy_id, book_id, status FROM book_copies WHERE copy_id = %s FOR UPDATE;", (copy_id,))
            copy = cur.fetchone()
            if not copy:
                raise ValueError("Book copy not found.")
            if copy['status'] != 'available':
                raise ValueError(f"Book Copy #{copy['copy_id']} is currently '{copy['status']}' and cannot be issued.")

            # Check member active unreturned count <= 3
            cur.execute("SELECT COUNT(*) AS active_count FROM book_issue WHERE member_id = %s AND return_date IS NULL;", (member_id,))
            res = cur.fetchone()
            if res['active_count'] >= 3:
                raise ValueError("Borrowing limit exceeded: Member already has 3 unreturned books.")

            issue_dt = parse_date(issue_date) if issue_date else datetime.date.today()
            due_dt = parse_date(due_date) if due_date else issue_dt + datetime.timedelta(days=14)
            if due_dt < issue_dt:
                raise ValueError("Due date cannot be earlier than issue date.")

            # Insert book_issue
            cur.execute("""
                INSERT INTO book_issue (member_id, copy_id, issue_date, due_date)
                VALUES (%s, %s, %s, %s)
                RETURNING issue_id, member_id, copy_id, issue_date, due_date, return_date;
            """, (member_id, copy_id, issue_dt, due_dt))
            issue = dict(cur.fetchone())

            # Update copy status to issued
            cur.execute("UPDATE book_copies SET status = 'issued' WHERE copy_id = %s;", (copy_id,))

            # If member had a pending reservation for this book, fulfill it
            cur.execute("""
                UPDATE reservations 
                SET status = 'fulfilled' 
                WHERE reservation_id = (
                    SELECT reservation_id FROM reservations 
                    WHERE member_id = %s AND book_id = %s AND status = 'pending' 
                    ORDER BY reserved_at ASC LIMIT 1
                );
            """, (member_id, copy['book_id']))

            conn.commit()
            return to_json_serializable(issue)

    @staticmethod
    def return_book(issue_id, return_date=None):
        import db
        with db.get_db_cursor() as (cur, conn):
            cur.execute("""
                SELECT bi.issue_id, bi.member_id, bi.copy_id, bi.issue_date, bi.due_date, bi.return_date, bc.book_id
                FROM book_issue bi
                JOIN book_copies bc ON bi.copy_id = bc.copy_id
                WHERE bi.issue_id = %s FOR UPDATE;
            """, (issue_id,))
            issue = cur.fetchone()
            if not issue:
                raise ValueError("Issue record not found.")
            if issue['return_date'] is not None:
                raise ValueError("This book has already been returned.")

            ret_dt = parse_date(return_date) if return_date else datetime.date.today()
            due_dt = parse_date(issue['due_date'])

            # Update book_issue
            cur.execute("UPDATE book_issue SET return_date = %s WHERE issue_id = %s;", (ret_dt, issue_id))

            # Update copy status to available
            cur.execute("UPDATE book_copies SET status = 'available' WHERE copy_id = %s;", (issue['copy_id'],))

            fine_created = None
            if ret_dt > due_dt:
                overdue_days = (ret_dt - due_dt).days
                fine_amount = Decimal(overdue_days * 2)
                cur.execute("""
                    INSERT INTO fines (issue_id, fine_amount, payment_status, amount_paid)
                    VALUES (%s, %s, 'Unpaid', 0.00)
                    ON CONFLICT (issue_id) DO UPDATE SET fine_amount = EXCLUDED.fine_amount
                    RETURNING fine_id, issue_id, fine_amount, payment_status, amount, amount_paid;
                """, (issue_id, fine_amount))
                fine_created = dict(cur.fetchone())

            conn.commit()
            return {
                'message': 'Book returned successfully',
                'issue_id': issue_id,
                'return_date': ret_dt.isoformat(),
                'fine': to_json_serializable(fine_created)
            }

    @staticmethod
    def get_issues(member_id=None):
        import db
        today = datetime.date.today()
        sql = """
            SELECT 
                bi.issue_id, bi.member_id, bi.copy_id, bi.issue_date, bi.due_date, bi.return_date,
                m.name AS member_name, m.email AS member_email,
                b.book_id, b.title AS book_title, b.isbn,
                f.fine_id, f.amount AS fine_amount, f.amount_paid AS fine_amount_paid
            FROM book_issue bi
            JOIN members m ON bi.member_id = m.member_id
            JOIN book_copies bc ON bi.copy_id = bc.copy_id
            JOIN books b ON bc.book_id = b.book_id
            LEFT JOIN fines f ON bi.issue_id = f.issue_id
            WHERE 1=1
        """
        params = []
        if member_id:
            sql += " AND bi.member_id = %s"
            params.append(member_id)

        sql += " ORDER BY bi.issue_id DESC;"
        rows = db.execute_query(sql, tuple(params), fetch='all')

        for r in rows:
            ret_d = parse_date(r['return_date']) if r['return_date'] else None
            due_d = parse_date(r['due_date'])
            if ret_d:
                r['is_overdue'] = ret_d > due_d
                r['overdue_days'] = max(0, (ret_d - due_d).days)
            else:
                r['is_overdue'] = today > due_d
                r['overdue_days'] = max(0, (today - due_d).days) if today > due_d else 0

        return to_json_serializable(rows)

    @staticmethod
    def create_reservation(member_id, book_id):
        import db
        with db.get_db_cursor() as (cur, conn):
            # Check available copies for book
            cur.execute("""
                SELECT COUNT(*) AS avail_count 
                FROM book_copies 
                WHERE book_id = %s AND status = 'available';
            """, (book_id,))
            avail = cur.fetchone()['avail_count']
            if avail > 0:
                raise ValueError("Cannot reserve book: Copies are currently available for immediate issue.")

            # Check pending reservation by same member
            cur.execute("""
                SELECT COUNT(*) AS pend_count 
                FROM reservations 
                WHERE member_id = %s AND book_id = %s AND status = 'pending';
            """, (member_id, book_id))
            pend = cur.fetchone()['pend_count']
            if pend > 0:
                raise ValueError("You already have an active pending reservation for this book.")

            cur.execute("""
                INSERT INTO reservations (member_id, book_id, reserved_at, status)
                VALUES (%s, %s, NOW(), 'pending')
                RETURNING reservation_id, member_id, book_id, reserved_at, status;
            """, (member_id, book_id))
            row = dict(cur.fetchone())
            conn.commit()
            return to_json_serializable(row)

    @staticmethod
    def get_reservations(member_id=None):
        import db
        sql = """
            SELECT 
                r.reservation_id, r.member_id, r.book_id, r.reserved_at, r.status,
                m.name AS member_name, m.email AS member_email,
                b.title AS book_title, b.isbn
            FROM reservations r
            JOIN members m ON r.member_id = m.member_id
            JOIN books b ON r.book_id = b.book_id
            WHERE 1=1
        """
        params = []
        if member_id:
            sql += " AND r.member_id = %s"
            params.append(member_id)

        sql += " ORDER BY r.reserved_at DESC;"
        rows = db.execute_query(sql, tuple(params), fetch='all')
        return to_json_serializable(rows)

    @staticmethod
    def cancel_reservation(reservation_id, member_id=None, is_admin=False):
        import db
        sql = "UPDATE reservations SET status = 'cancelled' WHERE reservation_id = %s"
        params = [reservation_id]
        if not is_admin and member_id:
            sql += " AND member_id = %s"
            params.append(member_id)
        sql += " AND status = 'pending' RETURNING reservation_id, status;"
        row = db.execute_query(sql, tuple(params), fetch='one', commit=True)
        if not row:
            raise ValueError("Reservation not found or cannot be cancelled.")
        return to_json_serializable(row)

    @staticmethod
    def get_fines(member_id=None):
        import db
        sql = """
            SELECT 
                f.fine_id, f.issue_id, f.amount, f.amount_paid,
                (f.amount - f.amount_paid) AS remaining_amount,
                CASE 
                    WHEN f.amount_paid >= f.amount THEN 'paid'
                    WHEN f.amount_paid > 0 THEN 'partially_paid'
                    ELSE 'unpaid'
                END AS payment_status,
                bi.issue_date, bi.due_date, bi.return_date,
                m.member_id, m.name AS member_name, m.email AS member_email,
                b.title AS book_title, bc.copy_id
            FROM fines f
            JOIN book_issue bi ON f.issue_id = bi.issue_id
            JOIN members m ON bi.member_id = m.member_id
            JOIN book_copies bc ON bi.copy_id = bc.copy_id
            JOIN books b ON bc.book_id = b.book_id
            WHERE 1=1
        """
        params = []
        if member_id:
            sql += " AND bi.member_id = %s"
            params.append(member_id)

        sql += " ORDER BY f.fine_id DESC;"
        rows = db.execute_query(sql, tuple(params), fetch='all')
        return to_json_serializable(rows)

    @staticmethod
    def pay_fine(fine_id, amount=None):
        import db
        with db.get_db_cursor() as (cur, conn):
            cur.execute("SELECT fine_id, issue_id, amount, amount_paid FROM fines WHERE fine_id = %s FOR UPDATE;", (fine_id,))
            fine = cur.fetchone()
            if not fine:
                raise ValueError("Fine not found.")

            total = Decimal(str(fine['amount']))
            paid = Decimal(str(fine['amount_paid']))
            balance = total - paid

            if balance <= 0:
                raise ValueError("Fine is already fully paid.")

            pay_amount = Decimal(str(amount)) if amount is not None else balance
            if pay_amount <= 0:
                raise ValueError("Payment amount must be greater than zero.")
            if pay_amount > balance:
                pay_amount = balance

            new_paid = paid + pay_amount
            new_status = 'Paid' if new_paid >= total else 'Partial'
            cur.execute("""
                UPDATE fines 
                SET amount_paid = %s, payment_status = %s
                WHERE fine_id = %s
                RETURNING fine_id, issue_id, fine_amount, payment_status, amount, amount_paid;
            """, (new_paid, new_status, fine_id))
            updated = dict(cur.fetchone())
            conn.commit()
            return to_json_serializable(updated)

    @staticmethod
    def get_dashboard_stats(member_id=None):
        import db
        if member_id:
            issues = DBRepository.get_issues(member_id=member_id)
            active_issues = [i for i in issues if not i['return_date']]
            overdue_issues = [i for i in active_issues if i['is_overdue']]
            reservations = DBRepository.get_reservations(member_id=member_id)
            active_reservations = [r for r in reservations if r['status'] == 'pending']
            fines = DBRepository.get_fines(member_id=member_id)
            unpaid_fines_total = sum(float(f['remaining_amount']) for f in fines if f['remaining_amount'] > 0)
            return {
                'active_issues_count': len(active_issues),
                'overdue_count': len(overdue_issues),
                'active_reservations_count': len(active_reservations),
                'unpaid_fines_total': round(unpaid_fines_total, 2)
            }
        else:
            total_books = db.execute_query("SELECT COUNT(*) AS count FROM books;", fetch='one')['count']
            total_copies = db.execute_query("SELECT COUNT(*) AS count FROM book_copies;", fetch='one')['count']
            total_members = db.execute_query("SELECT COUNT(*) AS count FROM members WHERE role = 'member';", fetch='one')['count']
            all_issues = DBRepository.get_issues()
            active_issues = [i for i in all_issues if not i['return_date']]
            overdue_issues = [i for i in active_issues if i['is_overdue']]
            all_res = DBRepository.get_reservations()
            pending_res = [r for r in all_res if r['status'] == 'pending']
            all_fines = DBRepository.get_fines()
            unpaid_fines_sum = sum(float(f['remaining_amount']) for f in all_fines if f['remaining_amount'] > 0)
            return {
                'total_books': total_books,
                'total_copies': total_copies,
                'total_members': total_members,
                'active_issues_count': len(active_issues),
                'overdue_count': len(overdue_issues),
                'pending_reservations_count': len(pending_res),
                'unpaid_fines_total': round(unpaid_fines_sum, 2)
            }


# -------------------------------------------------------------------------
# In-Memory Mock Implementation
# -------------------------------------------------------------------------

class MockRepository:
    @staticmethod
    def get_user_by_email(email):
        clean_email = email.strip().lower()
        for m in mock_data.MEMBERS:
            if m['email'].lower() == clean_email:
                return dict(m)
        return None

    @staticmethod
    def get_user_by_id(member_id):
        for m in mock_data.MEMBERS:
            if m['member_id'] == int(member_id):
                return dict(m)
        return None

    @staticmethod
    def create_member(name, email, password_hash, role='member', department=None):
        clean_email = email.strip().lower()
        if any(m['email'].lower() == clean_email for m in mock_data.MEMBERS):
            raise ValueError("A member with this email already exists.")

        new_id = mock_data.get_next_id('member_id')
        member = {
            'member_id': new_id,
            'name': name.strip(),
            'email': clean_email,
            'password_hash': password_hash,
            'role': role,
            'department': department,
            'joined_on': datetime.date.today().isoformat(),
            'is_active': True
        }
        mock_data.MEMBERS.append(member)
        return dict(member)

    @staticmethod
    def get_members():
        result = []
        for m in mock_data.MEMBERS:
            active_issues = sum(1 for bi in mock_data.BOOK_ISSUE if bi['member_id'] == m['member_id'] and bi['return_date'] is None)
            user_fines = []
            for bi in mock_data.BOOK_ISSUE:
                if bi['member_id'] == m['member_id']:
                    for f in mock_data.FINES:
                        if f['issue_id'] == bi['issue_id']:
                            user_fines.append(f['amount'] - f['amount_paid'])
            total_unpaid = sum(user_fines)
            member_dict = dict(m)
            member_dict['active_issues'] = active_issues
            member_dict['total_unpaid_fines'] = round(total_unpaid, 2)
            result.append(member_dict)
        return result

    @staticmethod
    def get_categories():
        result = []
        for c in mock_data.CATEGORIES:
            b_count = sum(1 for b in mock_data.BOOKS if b['category_id'] == c['category_id'])
            result.append({
                'category_id': c['category_id'],
                'category_name': c['category_name'],
                'book_count': b_count
            })
        result.sort(key=lambda x: x['category_name'])
        return result

    @staticmethod
    def create_category(category_name):
        cname = category_name.strip()
        if any(c['category_name'].lower() == cname.lower() for c in mock_data.CATEGORIES):
            raise ValueError("Category name already exists.")
        new_id = mock_data.get_next_id('category_id')
        cat = {'category_id': new_id, 'category_name': cname}
        mock_data.CATEGORIES.append(cat)
        return dict(cat)

    @staticmethod
    def get_authors():
        result = []
        for a in mock_data.AUTHORS:
            b_count = sum(1 for ba in mock_data.BOOK_AUTHORS if ba['author_id'] == a['author_id'])
            result.append({
                'author_id': a['author_id'],
                'author_name': a['author_name'],
                'book_count': b_count
            })
        result.sort(key=lambda x: x['author_name'])
        return result

    @staticmethod
    def create_author(author_name):
        aname = author_name.strip()
        new_id = mock_data.get_next_id('author_id')
        auth = {'author_id': new_id, 'author_name': aname}
        mock_data.AUTHORS.append(auth)
        return dict(auth)

    @staticmethod
    def _enrich_book(book):
        book_id = book['book_id']
        # Category
        cat = next((c for c in mock_data.CATEGORIES if c['category_id'] == book['category_id']), None)
        category_name = cat['category_name'] if cat else 'Uncategorized'

        # Authors
        author_ids = [ba['author_id'] for ba in mock_data.BOOK_AUTHORS if ba['book_id'] == book_id]
        authors = [dict(a) for a in mock_data.AUTHORS if a['author_id'] in author_ids]

        # Copies
        copies = [dict(bc) for bc in mock_data.BOOK_COPIES if bc['book_id'] == book_id]
        total_copies = len(copies)
        avail_copies = sum(1 for c in copies if c['status'] == 'available')

        enriched = dict(book)
        enriched['category_name'] = category_name
        enriched['authors'] = authors
        enriched['total_copies'] = total_copies
        enriched['available_copies'] = avail_copies
        enriched['copies'] = copies
        return enriched

    @staticmethod
    def get_books(query=None, category_id=None):
        results = []
        q = query.strip().lower() if query else None

        for b in mock_data.BOOKS:
            if category_id and b['category_id'] != int(category_id):
                continue
            enriched = MockRepository._enrich_book(b)
            if q:
                author_names = " ".join([a['author_name'].lower() for a in enriched['authors']])
                if (q not in enriched['title'].lower() and 
                    q not in enriched['isbn'].lower() and 
                    q not in enriched['category_name'].lower() and 
                    q not in author_names):
                    continue
            results.append(enriched)

        results.sort(key=lambda x: x['title'])
        return results

    @staticmethod
    def get_book_by_id(book_id):
        book = next((b for b in mock_data.BOOKS if b['book_id'] == int(book_id)), None)
        if not book:
            return None
        return MockRepository._enrich_book(book)

    @staticmethod
    def create_book(isbn, title, category_id, publisher, publication_year, author_ids=None):
        if any(b['isbn'].lower() == isbn.strip().lower() for b in mock_data.BOOKS):
            raise ValueError(f"A book with ISBN '{isbn}' already exists.")

        new_book_id = mock_data.get_next_id('book_id')
        new_book = {
            'book_id': new_book_id,
            'isbn': isbn.strip(),
            'title': title.strip(),
            'category_id': int(category_id),
            'publisher': publisher.strip() if publisher else None,
            'publication_year': int(publication_year) if publication_year else None
        }
        mock_data.BOOKS.append(new_book)

        if author_ids:
            for aid in author_ids:
                mock_data.BOOK_AUTHORS.append({'book_id': new_book_id, 'author_id': int(aid)})

        # Create 1 default available copy
        new_copy_id = mock_data.get_next_id('copy_id')
        mock_data.BOOK_COPIES.append({
            'copy_id': new_copy_id,
            'book_id': new_book_id,
            'status': 'available'
        })

        return MockRepository.get_book_by_id(new_book_id)

    @staticmethod
    def update_book(book_id, isbn, title, category_id, publisher, publication_year, author_ids=None):
        book = next((b for b in mock_data.BOOKS if b['book_id'] == int(book_id)), None)
        if not book:
            raise ValueError("Book not found.")

        # Check duplicate ISBN on other books
        for b in mock_data.BOOKS:
            if b['book_id'] != int(book_id) and b['isbn'].lower() == isbn.strip().lower():
                raise ValueError(f"Another book with ISBN '{isbn}' already exists.")

        book['isbn'] = isbn.strip()
        book['title'] = title.strip()
        book['category_id'] = int(category_id)
        book['publisher'] = publisher.strip() if publisher else None
        book['publication_year'] = int(publication_year) if publication_year else None

        if author_ids is not None:
            mock_data.BOOK_AUTHORS = [ba for ba in mock_data.BOOK_AUTHORS if ba['book_id'] != int(book_id)]
            for aid in author_ids:
                mock_data.BOOK_AUTHORS.append({'book_id': int(book_id), 'author_id': int(aid)})

        return MockRepository.get_book_by_id(book_id)

    @staticmethod
    def delete_book(book_id):
        bid = int(book_id)
        # Check if copies are currently issued
        active_issues = [
            bi for bi in mock_data.BOOK_ISSUE
            if bi['return_date'] is None and any(bc['copy_id'] == bi['copy_id'] and bc['book_id'] == bid for bc in mock_data.BOOK_COPIES)
        ]
        if active_issues:
            raise ValueError("Cannot delete book: Copies of this book are currently issued to members.")

        mock_data.BOOK_COPIES = [bc for bc in mock_data.BOOK_COPIES if bc['book_id'] != bid]
        mock_data.BOOK_AUTHORS = [ba for ba in mock_data.BOOK_AUTHORS if ba['book_id'] != bid]
        mock_data.RESERVATIONS = [r for r in mock_data.RESERVATIONS if r['book_id'] != bid]
        mock_data.BOOKS = [b for b in mock_data.BOOKS if b['book_id'] != bid]
        return True

    @staticmethod
    def get_copies(book_id=None):
        results = []
        for bc in mock_data.BOOK_COPIES:
            if book_id and bc['book_id'] != int(book_id):
                continue
            book = next((b for b in mock_data.BOOKS if b['book_id'] == bc['book_id']), None)
            copy_dict = dict(bc)
            copy_dict['title'] = book['title'] if book else ''
            copy_dict['isbn'] = book['isbn'] if book else ''
            results.append(copy_dict)
        results.sort(key=lambda x: x['copy_id'])
        return results

    @staticmethod
    def create_copy(book_id, accession_code=None, status='available'):
        new_copy_id = mock_data.get_next_id('copy_id')
        copy = {
            'copy_id': new_copy_id,
            'book_id': int(book_id),
            'status': status or 'available'
        }
        mock_data.BOOK_COPIES.append(copy)
        return dict(copy)

    @staticmethod
    def issue_book(member_id, copy_id, issue_date=None, due_date=None):
        cid = int(copy_id)
        mid = int(member_id)
        copy = next((c for c in mock_data.BOOK_COPIES if c['copy_id'] == cid), None)
        if not copy:
            raise ValueError("Book copy not found.")
        if copy['status'] != 'available':
            raise ValueError(f"Book Copy #{copy['copy_id']} is currently '{copy['status']}' and cannot be issued.")

        # Check member active unreturned count <= 3
        active_count = sum(1 for bi in mock_data.BOOK_ISSUE if bi['member_id'] == mid and bi['return_date'] is None)
        if active_count >= 3:
            raise ValueError("Borrowing limit exceeded: Member already has 3 unreturned books.")

        issue_dt = parse_date(issue_date) if issue_date else datetime.date.today()
        due_dt = parse_date(due_date) if due_date else issue_dt + datetime.timedelta(days=14)
        if due_dt < issue_dt:
            raise ValueError("Due date cannot be earlier than issue date.")

        new_issue_id = mock_data.get_next_id('issue_id')
        issue_record = {
            'issue_id': new_issue_id,
            'member_id': mid,
            'copy_id': cid,
            'issue_date': issue_dt.isoformat(),
            'due_date': due_dt.isoformat(),
            'return_date': None
        }
        mock_data.BOOK_ISSUE.append(issue_record)
        copy['status'] = 'issued'

        # Fulfill pending reservation if any
        for r in mock_data.RESERVATIONS:
            if r['member_id'] == mid and r['book_id'] == copy['book_id'] and r['status'] == 'pending':
                r['status'] = 'fulfilled'
                break

        return dict(issue_record)

    @staticmethod
    def return_book(issue_id, return_date=None):
        iid = int(issue_id)
        issue = next((bi for bi in mock_data.BOOK_ISSUE if bi['issue_id'] == iid), None)
        if not issue:
            raise ValueError("Issue record not found.")
        if issue['return_date'] is not None:
            raise ValueError("This book has already been returned.")

        ret_dt = parse_date(return_date) if return_date else datetime.date.today()
        due_dt = parse_date(issue['due_date'])

        issue['return_date'] = ret_dt.isoformat()
        copy = next((c for c in mock_data.BOOK_COPIES if c['copy_id'] == issue['copy_id']), None)
        if copy:
            copy['status'] = 'available'

        fine_created = None
        if ret_dt > due_dt:
            overdue_days = (ret_dt - due_dt).days
            fine_amount = float(overdue_days * 2)
            fine_id = mock_data.get_next_id('fine_id')
            fine_created = {
                'fine_id': fine_id,
                'issue_id': iid,
                'amount': fine_amount,
                'amount_paid': 0.0
            }
            mock_data.FINES.append(fine_created)

        return {
            'message': 'Book returned successfully',
            'issue_id': iid,
            'return_date': ret_dt.isoformat(),
            'fine': fine_created
        }

    @staticmethod
    def get_issues(member_id=None):
        today = datetime.date.today()
        results = []
        for bi in reversed(mock_data.BOOK_ISSUE):
            if member_id and bi['member_id'] != int(member_id):
                continue
            member = next((m for m in mock_data.MEMBERS if m['member_id'] == bi['member_id']), None)
            copy = next((c for c in mock_data.BOOK_COPIES if c['copy_id'] == bi['copy_id']), None)
            book = next((b for b in mock_data.BOOKS if b['book_id'] == copy['book_id']), None) if copy else None
            fine = next((f for f in mock_data.FINES if f['issue_id'] == bi['issue_id']), None)

            ret_dt = parse_date(bi['return_date']) if bi['return_date'] else None
            due_dt = parse_date(bi['due_date'])
            if ret_dt:
                is_overdue = ret_dt > due_dt
                overdue_days = max(0, (ret_dt - due_dt).days)
            else:
                is_overdue = today > due_dt
                overdue_days = max(0, (today - due_dt).days) if today > due_dt else 0

            item = dict(bi)
            item['member_name'] = member['name'] if member else 'Unknown'
            item['member_email'] = member['email'] if member else 'Unknown'
            item['book_id'] = book['book_id'] if book else None
            item['book_title'] = book['title'] if book else 'Unknown'
            item['isbn'] = book['isbn'] if book else 'Unknown'
            item['copy_id'] = copy['copy_id'] if copy else None
            item['is_overdue'] = is_overdue
            item['overdue_days'] = overdue_days
            item['fine_id'] = fine['fine_id'] if fine else None
            item['fine_amount'] = fine['amount'] if fine else None
            item['fine_amount_paid'] = fine['amount_paid'] if fine else None
            results.append(item)
        return results

    @staticmethod
    def create_reservation(member_id, book_id):
        mid = int(member_id)
        bid = int(book_id)

        avail_count = sum(1 for c in mock_data.BOOK_COPIES if c['book_id'] == bid and c['status'] == 'available')
        if avail_count > 0:
            raise ValueError("Cannot reserve book: Copies are currently available for immediate issue.")

        if any(r['member_id'] == mid and r['book_id'] == bid and r['status'] == 'pending' for r in mock_data.RESERVATIONS):
            raise ValueError("You already have an active pending reservation for this book.")

        new_res_id = mock_data.get_next_id('reservation_id')
        res = {
            'reservation_id': new_res_id,
            'member_id': mid,
            'book_id': bid,
            'reserved_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'pending'
        }
        mock_data.RESERVATIONS.append(res)
        return dict(res)

    @staticmethod
    def get_reservations(member_id=None):
        results = []
        for r in reversed(mock_data.RESERVATIONS):
            if member_id and r['member_id'] != int(member_id):
                continue
            member = next((m for m in mock_data.MEMBERS if m['member_id'] == r['member_id']), None)
            book = next((b for b in mock_data.BOOKS if b['book_id'] == r['book_id']), None)
            item = dict(r)
            item['member_name'] = member['name'] if member else 'Unknown'
            item['member_email'] = member['email'] if member else 'Unknown'
            item['book_title'] = book['title'] if book else 'Unknown'
            item['isbn'] = book['isbn'] if book else 'Unknown'
            results.append(item)
        return results

    @staticmethod
    def cancel_reservation(reservation_id, member_id=None, is_admin=False):
        rid = int(reservation_id)
        res = next((r for r in mock_data.RESERVATIONS if r['reservation_id'] == rid), None)
        if not res or res['status'] != 'pending':
            raise ValueError("Reservation not found or cannot be cancelled.")
        if not is_admin and member_id and res['member_id'] != int(member_id):
            raise ValueError("Unauthorized to cancel this reservation.")

        res['status'] = 'cancelled'
        return dict(res)

    @staticmethod
    def get_fines(member_id=None):
        results = []
        for f in reversed(mock_data.FINES):
            issue = next((bi for bi in mock_data.BOOK_ISSUE if bi['issue_id'] == f['issue_id']), None)
            if not issue:
                continue
            if member_id and issue['member_id'] != int(member_id):
                continue

            member = next((m for m in mock_data.MEMBERS if m['member_id'] == issue['member_id']), None)
            copy = next((c for c in mock_data.BOOK_COPIES if c['copy_id'] == issue['copy_id']), None)
            book = next((b for b in mock_data.BOOKS if b['book_id'] == copy['book_id']), None) if copy else None

            rem = round(f['amount'] - f['amount_paid'], 2)
            if f['amount_paid'] >= f['amount']:
                p_status = 'paid'
            elif f['amount_paid'] > 0:
                p_status = 'partially_paid'
            else:
                p_status = 'unpaid'

            results.append({
                'fine_id': f['fine_id'],
                'issue_id': f['issue_id'],
                'amount': f['amount'],
                'amount_paid': f['amount_paid'],
                'remaining_amount': rem,
                'payment_status': p_status,
                'issue_date': issue['issue_date'],
                'due_date': issue['due_date'],
                'return_date': issue['return_date'],
                'member_id': member['member_id'] if member else None,
                'member_name': member['name'] if member else 'Unknown',
                'member_email': member['email'] if member else 'Unknown',
                'book_title': book['title'] if book else 'Unknown',
                'copy_id': copy['copy_id'] if copy else None
            })
        return results

    @staticmethod
    def pay_fine(fine_id, amount=None):
        fid = int(fine_id)
        fine = next((f for f in mock_data.FINES if f['fine_id'] == fid), None)
        if not fine:
            raise ValueError("Fine not found.")

        rem = fine['amount'] - fine['amount_paid']
        if rem <= 0:
            raise ValueError("Fine is already fully paid.")

        pay_val = float(amount) if amount is not None else rem
        if pay_val <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        if pay_val > rem:
            pay_val = rem

        fine['amount_paid'] = round(fine['amount_paid'] + pay_val, 2)
        fine['payment_status'] = 'Paid' if fine['amount_paid'] >= fine['amount'] else 'Partial'
        return dict(fine)

    @staticmethod
    def get_dashboard_stats(member_id=None):
        if member_id:
            issues = MockRepository.get_issues(member_id=member_id)
            active_issues = [i for i in issues if not i['return_date']]
            overdue_issues = [i for i in active_issues if i['is_overdue']]
            reservations = MockRepository.get_reservations(member_id=member_id)
            active_res = [r for r in reservations if r['status'] == 'pending']
            fines = MockRepository.get_fines(member_id=member_id)
            unpaid_fines_total = sum(f['remaining_amount'] for f in fines if f['remaining_amount'] > 0)
            return {
                'active_issues_count': len(active_issues),
                'overdue_count': len(overdue_issues),
                'active_reservations_count': len(active_res),
                'unpaid_fines_total': round(unpaid_fines_total, 2)
            }
        else:
            total_books = len(mock_data.BOOKS)
            total_copies = len(mock_data.BOOK_COPIES)
            total_members = sum(1 for m in mock_data.MEMBERS if m['role'] == 'member')
            all_issues = MockRepository.get_issues()
            active_issues = [i for i in all_issues if not i['return_date']]
            overdue_issues = [i for i in active_issues if i['is_overdue']]
            all_res = MockRepository.get_reservations()
            pending_res = [r for r in all_res if r['status'] == 'pending']
            all_fines = MockRepository.get_fines()
            unpaid_fines_sum = sum(f['remaining_amount'] for f in all_fines if f['remaining_amount'] > 0)
            return {
                'total_books': total_books,
                'total_copies': total_copies,
                'total_members': total_members,
                'active_issues_count': len(active_issues),
                'overdue_count': len(overdue_issues),
                'pending_reservations_count': len(pending_res),
                'unpaid_fines_total': round(unpaid_fines_sum, 2)
            }


# -------------------------------------------------------------------------
# Dynamic Repository Selector with Teammate Auto-Fallback
# -------------------------------------------------------------------------
# Routes only call functions from this active repository instance!
_use_db_active = False
if Config.USE_DB:
    try:
        import db
        test_conn = db.get_db_connection()
        test_conn.close()
        _use_db_active = True
        print("[DATABASE] Successfully connected to PostgreSQL (library_db).")
    except Exception as e:
        print(f"[NOTICE] PostgreSQL not available on this machine: {e}")
        print("[NOTICE] Seamlessly falling back to In-Memory Mock Data so the website runs with 0 errors!")
        mock_data.reset_mock_data()
        _use_db_active = False

_ActiveRepo = DBRepository if _use_db_active else MockRepository

# Expose uniform interface matching requirements
get_user_by_email = _ActiveRepo.get_user_by_email
get_user_by_id = _ActiveRepo.get_user_by_id
create_member = _ActiveRepo.create_member
get_members = _ActiveRepo.get_members
get_categories = _ActiveRepo.get_categories
create_category = _ActiveRepo.create_category
get_authors = _ActiveRepo.get_authors
create_author = _ActiveRepo.create_author
get_books = _ActiveRepo.get_books
get_book_by_id = _ActiveRepo.get_book_by_id
create_book = _ActiveRepo.create_book
update_book = _ActiveRepo.update_book
delete_book = _ActiveRepo.delete_book
get_copies = _ActiveRepo.get_copies
create_copy = _ActiveRepo.create_copy
issue_book = _ActiveRepo.issue_book
return_book = _ActiveRepo.return_book
get_issues = _ActiveRepo.get_issues
create_reservation = _ActiveRepo.create_reservation
get_reservations = _ActiveRepo.get_reservations
cancel_reservation = _ActiveRepo.cancel_reservation
get_fines = _ActiveRepo.get_fines
pay_fine = _ActiveRepo.pay_fine
get_dashboard_stats = _ActiveRepo.get_dashboard_stats
