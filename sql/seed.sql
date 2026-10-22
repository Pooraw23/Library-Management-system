-- ====================================================================
-- SMART LIBRARY MANAGEMENT SYSTEM - SEED SCRIPT (From ER Diagram)
-- ====================================================================

-- 1. Insert Categories
INSERT INTO categories (category_id, category_name) VALUES
(1, 'Database Systems'),
(2, 'Software Engineering'),
(3, 'Computer Science & Algorithms'),
(4, 'Artificial Intelligence'),
(5, 'Operating Systems'),
(6, 'Mathematics & Discrete Logic');

-- 2. Insert Authors (ER: Author_Id, Author_Name)
INSERT INTO authors (author_id, author_name) VALUES
(1, 'Abraham Silberschatz'),
(2, 'Henry F. Korth'),
(3, 'S. Sudarshan'),
(4, 'Robert C. Martin'),
(5, 'Thomas H. Cormen'),
(6, 'Charles E. Leiserson'),
(7, 'Ronald L. Rivest'),
(8, 'Clifford Stein'),
(9, 'Stuart Russell'),
(10, 'Peter Norvig'),
(11, 'Andrew S. Tanenbaum'),
(12, 'Martin Fowler');

-- 3. Insert Books (ER: Book_Id, Title, category_id, Publisher, Publication_year)
INSERT INTO books (book_id, isbn, title, category_id, publisher, publication_year) VALUES
(1, '978-0078022159', 'Database System Concepts (7th Edition)', 1, 'McGraw-Hill', 2019),
(2, '978-0132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 2, 'Prentice Hall', 2008),
(3, '978-0262033848', 'Introduction to Algorithms (CLRS 3rd Edition)', 3, 'MIT Press', 2009),
(4, '978-0134610993', 'Artificial Intelligence: A Modern Approach (4th Edition)', 4, 'Pearson', 2020),
(5, '978-0133591620', 'Modern Operating Systems (4th Edition)', 5, 'Pearson', 2014),
(6, '978-0134757599', 'Refactoring: Improving the Design of Existing Code', 2, 'Addison-Wesley', 2018);

-- 4. Insert Book Authors (ER: Written By M:N)
INSERT INTO book_authors (book_id, author_id) VALUES
(1, 1), (1, 2), (1, 3),
(2, 4),
(3, 5), (3, 6), (3, 7), (3, 8),
(4, 9), (4, 10),
(5, 11),
(6, 12);

-- 5. Insert Book Copies (ER: Book_Copies -> Copy_Id, Book_Id, Status)
INSERT INTO book_copies (copy_id, book_id, status) VALUES
(1, 1, 'issued'),
(2, 1, 'available'),
(3, 1, 'available'),
(4, 2, 'available'),
(5, 2, 'issued'),
(6, 3, 'issued'),
(7, 3, 'issued'),
(8, 4, 'available'),
(9, 4, 'available'),
(10, 5, 'available'),
(11, 5, 'lost'),
(12, 6, 'available');

-- 6. Insert Students (ER: Students -> Student_Id, Name, Email)
-- Passwords:
-- admin@library.edu -> admin123
-- librarian@library.edu -> librarian123
-- john.doe@student.edu -> member123
-- alice.smith@student.edu -> member123
-- bob.taylor@student.edu -> member123
INSERT INTO students (student_id, name, email, password_hash, role, department, joined_on, is_active) VALUES
(1, 'System Administrator', 'admin@library.edu', 'scrypt:32768:8:1$6mPlyQ14zQwmbezy$1e458c9cae1e42a6aed16b10d8673ad36ad55d3c1e4c0a0fde670dcdcca0d965a5d951ee796ee5d68322fe649ea936cc4ee04e37e97294f534688be16ec7b5ec', 'admin', 'Administration', CURRENT_DATE - INTERVAL '180 days', TRUE),
(2, 'Eleanor Vance', 'librarian@library.edu', 'scrypt:32768:8:1$fpwoua8rWbshcS6S$509269e256446ec7f8f4db8a1d1b02000e8eba06161af509f31ebcfeb745c82f84fd054158785bbd62b869a3dfa883ba65df9852f68662c027f9a9432d86bfac', 'librarian', 'Central Library', CURRENT_DATE - INTERVAL '120 days', TRUE),
(3, 'John Doe', 'john.doe@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Computer Science', CURRENT_DATE - INTERVAL '90 days', TRUE),
(4, 'Alice Smith', 'alice.smith@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Information Technology', CURRENT_DATE - INTERVAL '60 days', TRUE),
(5, 'Bob Taylor', 'bob.taylor@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Electrical Engineering', CURRENT_DATE - INTERVAL '30 days', TRUE);

-- 7. Insert Borrow Records (ER: Borrow relationship -> Issue_Date, Due_Date, Return_Date)
INSERT INTO borrow (borrow_id, student_id, copy_id, issue_date, due_date, return_date) VALUES
(1, 3, 1, CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '9 days', NULL),
(2, 4, 5, CURRENT_DATE - INTERVAL '25 days', CURRENT_DATE - INTERVAL '11 days', NULL),
(3, 5, 6, CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE - INTERVAL '16 days', CURRENT_DATE - INTERVAL '10 days'),
(4, 3, 7, CURRENT_DATE - INTERVAL '2 days', CURRENT_DATE + INTERVAL '12 days', NULL);

-- 8. Insert Reservations (ER: Reservations -> Reservation_Id, Reserved at, Status)
INSERT INTO reservations (reservation_id, student_id, book_id, reserved_at, status) VALUES
(1, 4, 3, NOW() - INTERVAL '1 day', 'pending');

-- 9. Insert Fines (Circulation late penalty) (ER: Fines -> Fine_Id, Fine_Amount, Payment_Status)
INSERT INTO fines (fine_id, borrow_id, fine_amount, payment_status, amount_paid) VALUES
(1, 3, 12.00, 'Unpaid', 5.00);

-- Reset Sequences to Highest IDs
SELECT setval('categories_category_id_seq', (SELECT COALESCE(MAX(category_id), 1) FROM categories));
SELECT setval('authors_author_id_seq', (SELECT COALESCE(MAX(author_id), 1) FROM authors));
SELECT setval('books_book_id_seq', (SELECT COALESCE(MAX(book_id), 1) FROM books));
SELECT setval('book_copies_copy_id_seq', (SELECT COALESCE(MAX(copy_id), 1) FROM book_copies));
SELECT setval('students_student_id_seq', (SELECT COALESCE(MAX(student_id), 1) FROM students));
SELECT setval('borrow_borrow_id_seq', (SELECT COALESCE(MAX(borrow_id), 1) FROM borrow));
SELECT setval('reservations_reservation_id_seq', (SELECT COALESCE(MAX(reservation_id), 1) FROM reservations));
SELECT setval('fines_fine_id_seq', (SELECT COALESCE(MAX(fine_id), 1) FROM fines));
