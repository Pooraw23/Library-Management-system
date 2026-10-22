import unittest
import json
from app import app
import repository
from werkzeug.security import check_password_hash

class TestLibraryApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_01_seed_passwords(self):
        """Verify that seed users can be authenticated with their designated passwords."""
        admin = repository.get_user_by_email('admin@library.edu')
        self.assertIsNotNone(admin)
        self.assertTrue(check_password_hash(admin['password_hash'], 'admin123'))

        librarian = repository.get_user_by_email('librarian@library.edu')
        self.assertIsNotNone(librarian)
        self.assertTrue(check_password_hash(librarian['password_hash'], 'librarian123'))

        member = repository.get_user_by_email('john.doe@student.edu')
        self.assertIsNotNone(member)
        self.assertTrue(check_password_hash(member['password_hash'], 'member123'))

    def test_02_books_and_search(self):
        """Verify book catalog querying and filtering."""
        books = repository.get_books()
        self.assertGreaterEqual(len(books), 6)

        # Search for algorithms
        filtered = repository.get_books(query='Algorithms')
        self.assertGreaterEqual(len(filtered), 1)
        self.assertIn('Algorithms', filtered[0]['title'])

    def test_03_login_and_me_endpoints(self):
        """Verify REST login and /api/me endpoints."""
        res = self.client.post('/api/auth/login', json={
            'email': 'admin@library.edu',
            'password': 'admin123'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['user']['role'], 'admin')

        # Check /api/me with active session
        me_res = self.client.get('/api/me')
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.get_json()['user']['email'], 'admin@library.edu')

    def test_04_business_rule_issue_limit(self):
        """Test business rule: maximum 3 unreturned books per member."""
        member = repository.get_user_by_email('john.doe@student.edu')
        # John Doe initially has 2 active issues
        # Find 2 available copies to test limit
        copies = repository.get_copies()
        avail = [c for c in copies if c['status'] == 'available']
        self.assertGreaterEqual(len(avail), 2)

        # Issue 3rd book (should succeed)
        issue_res = repository.issue_book(member['member_id'], avail[0]['copy_id'])
        self.assertIsNotNone(issue_res['issue_id'])

        # Attempt to issue 4th book (should fail with limit error)
        with self.assertRaises(ValueError) as ctx:
            repository.issue_book(member['member_id'], avail[1]['copy_id'])
        self.assertIn("Borrowing limit exceeded", str(ctx.exception))

    def test_05_business_rule_reservation(self):
        """Test business rule: reservation only allowed when 0 copies available."""
        # Book 1 has available copies (should fail reservation)
        member = repository.get_user_by_email('bob.taylor@student.edu')
        with self.assertRaises(ValueError) as ctx:
            repository.create_reservation(member['member_id'], 1)
        self.assertIn("Copies are currently available", str(ctx.exception))

        # Book 3 (Introduction to Algorithms) has 0 copies available -> should succeed for Bob
        res = repository.create_reservation(member['member_id'], 3)
        self.assertIsNotNone(res['reservation_id'])
        self.assertEqual(res['status'], 'pending')

    def test_06_return_and_fine_calculation(self):
        """Test return book and fine calculation: $2 * overdue days."""
        # Issue 2 is Alice Smith with due date 11 days ago
        issues = repository.get_issues()
        alice_issue = next(i for i in issues if i['issue_id'] == 2)
        self.assertTrue(alice_issue['is_overdue'])
        self.assertGreater(alice_issue['overdue_days'], 0)

        # Process return today
        result = repository.return_book(2)
        self.assertIsNotNone(result['fine'])
        self.assertEqual(result['fine']['amount'], alice_issue['overdue_days'] * 2.0)

    def test_07_fine_payment(self):
        """Test fine payment recording."""
        fines = repository.get_fines()
        self.assertGreaterEqual(len(fines), 1)
        fine = fines[0]
        rem = fine['remaining_amount']
        if rem > 0:
            updated = repository.pay_fine(fine['fine_id'], amount=min(rem, 2.0))
            self.assertGreater(updated['amount_paid'], fine['amount_paid'])

if __name__ == '__main__':
    unittest.main()
