-- ====================================================================
-- SMART LIBRARY MANAGEMENT SYSTEM - COMPLETE POSTGRESQL DATABASE
-- Compatible with ER Diagram (Students, Books, Authors, Copies, Borrow, Reservations)
-- ====================================================================

-- 1. DROP EXISTING OBJECTS
DROP VIEW IF EXISTS borrow CASCADE;
DROP VIEW IF EXISTS students CASCADE;
DROP TABLE IF EXISTS fines CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS book_issue CASCADE;
DROP TABLE IF EXISTS book_copies CASCADE;
DROP TABLE IF EXISTS book_authors CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS members CASCADE;

-- 2. CREATE BASE TABLES

-- Members / Students Table (ER: Students -> Student_Id, Name, Email)
CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    student_id INT GENERATED ALWAYS AS (member_id) STORED,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin','librarian','member')),
    department VARCHAR(100),
    joined_on DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Categories Table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

-- Books Table (ER: Books -> Book_Id, Title, category_id, Publisher, Publication_year)
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    category_id INT NOT NULL REFERENCES categories(category_id),
    publisher VARCHAR(100),
    publication_year INT
);

-- Authors Table (ER: Authors -> Author_Id, Author_Name)
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    author_name VARCHAR(100) NOT NULL
);

-- Book Authors Table (ER: Written By M:N)
CREATE TABLE book_authors (
    book_id INT REFERENCES books(book_id) ON DELETE CASCADE,
    author_id INT REFERENCES authors(author_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- Book Copies Table (ER: Contains 1:N -> Copy_Id, Book_Id, Status)
CREATE TABLE book_copies (
    copy_id SERIAL PRIMARY KEY,
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available','issued','lost'))
);

-- Book Issue / Borrow Table (ER: Borrow -> Issue_Date, Due_Date, Return_Date)
CREATE TABLE book_issue (
    issue_id SERIAL PRIMARY KEY,
    borrow_id INT GENERATED ALWAYS AS (issue_id) STORED,
    member_id INT NOT NULL REFERENCES members(member_id),
    student_id INT GENERATED ALWAYS AS (member_id) STORED,
    copy_id INT NOT NULL REFERENCES book_copies(copy_id),
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    return_date DATE,
    CHECK (due_date >= issue_date)
);

-- Reservations Table (ER: Reservations -> Reservation_Id, Reserved_at, Status)
CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(member_id),
    student_id INT GENERATED ALWAYS AS (member_id) STORED,
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    reserved_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','fulfilled','cancelled'))
);

-- Fines Table (Circulation penalty: ₹2/day) (ER: Fines -> Fine_Id, Fine_Amount, Payment_Status)
CREATE TABLE fines (
    fine_id SERIAL PRIMARY KEY,
    issue_id INT UNIQUE NOT NULL REFERENCES book_issue(issue_id) ON DELETE CASCADE,
    borrow_id INT GENERATED ALWAYS AS (issue_id) STORED,
    fine_amount NUMERIC(8,2) NOT NULL DEFAULT 0.00 CHECK (fine_amount >= 0),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'Unpaid' CHECK (payment_status IN ('Unpaid', 'Paid', 'Pending', 'Partial', 'unpaid', 'paid', 'pending', 'partial')),
    amount NUMERIC(8,2) GENERATED ALWAYS AS (fine_amount) STORED,
    amount_paid NUMERIC(8,2) NOT NULL DEFAULT 0.00,
    CHECK (amount_paid <= fine_amount)
);

-- Performance Indexes
CREATE INDEX idx_books_category ON books(category_id);
CREATE INDEX idx_book_copies_book ON book_copies(book_id);
CREATE INDEX idx_book_issue_member ON book_issue(member_id);
CREATE INDEX idx_book_issue_copy ON book_issue(copy_id);
CREATE INDEX idx_reservations_member ON reservations(member_id);
CREATE INDEX idx_reservations_book ON reservations(book_id);

-- 3. VIEWS FOR DIRECT ER DIAGRAM COMPLIANCE
CREATE OR REPLACE VIEW students AS 
SELECT student_id, member_id, name, email, password_hash, role, department, joined_on, is_active 
FROM members;

CREATE OR REPLACE VIEW borrow AS 
SELECT borrow_id, issue_id, student_id, member_id, copy_id, issue_date, due_date, return_date 
FROM book_issue;

-- 4. INSERT SAMPLE SEED DATA

-- Categories
INSERT INTO categories (category_id, category_name) VALUES
(1, 'Database Systems'),
(2, 'Software Engineering'),
(3, 'Computer Science & Algorithms'),
(4, 'Artificial Intelligence'),
(5, 'Operating Systems'),
(6, 'Mathematics & Discrete Logic');

-- Authors
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

-- Books
INSERT INTO books (book_id, isbn, title, category_id, publisher, publication_year) VALUES
(1, '978-0078022159', 'Database System Concepts (7th Edition)', 1, 'McGraw-Hill', 2019),
(2, '978-0132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 2, 'Prentice Hall', 2008),
(3, '978-0262033848', 'Introduction to Algorithms (CLRS 3rd Edition)', 3, 'MIT Press', 2009),
(4, '978-0134610993', 'Artificial Intelligence: A Modern Approach (4th Edition)', 4, 'Pearson', 2020),
(5, '978-0133591620', 'Modern Operating Systems (4th Edition)', 5, 'Pearson', 2014),
(6, '978-0134757599', 'Refactoring: Improving the Design of Existing Code', 2, 'Addison-Wesley', 2018);

-- Book Authors
INSERT INTO book_authors (book_id, author_id) VALUES
(1, 1), (1, 2), (1, 3),
(2, 4),
(3, 5), (3, 6), (3, 7), (3, 8),
(4, 9), (4, 10),
(5, 11),
(6, 12);

-- Book Copies (ER: Book_Copies -> Copy_Id, Book_Id, Status)
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

-- Students / Members (Passwords: admin123, librarian123, member123)
INSERT INTO members (member_id, name, email, password_hash, role, department, joined_on, is_active) VALUES
(1, 'System Administrator', 'admin@library.edu', 'scrypt:32768:8:1$6mPlyQ14zQwmbezy$1e458c9cae1e42a6aed16b10d8673ad36ad55d3c1e4c0a0fde670dcdcca0d965a5d951ee796ee5d68322fe649ea936cc4ee04e37e97294f534688be16ec7b5ec', 'admin', 'Administration', CURRENT_DATE - INTERVAL '180 days', TRUE),
(2, 'Eleanor Vance', 'librarian@library.edu', 'scrypt:32768:8:1$fpwoua8rWbshcS6S$509269e256446ec7f8f4db8a1d1b02000e8eba06161af509f31ebcfeb745c82f84fd054158785bbd62b869a3dfa883ba65df9852f68662c027f9a9432d86bfac', 'librarian', 'Central Library', CURRENT_DATE - INTERVAL '120 days', TRUE),
(3, 'John Doe', 'john.doe@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Computer Science', CURRENT_DATE - INTERVAL '90 days', TRUE),
(4, 'Alice Smith', 'alice.smith@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Information Technology', CURRENT_DATE - INTERVAL '60 days', TRUE),
(5, 'Bob Taylor', 'bob.taylor@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Electrical Engineering', CURRENT_DATE - INTERVAL '30 days', TRUE);

-- Borrow Loans / Book Issues
INSERT INTO book_issue (issue_id, member_id, copy_id, issue_date, due_date, return_date) VALUES
(1, 3, 1, CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '9 days', NULL),
(2, 4, 5, CURRENT_DATE - INTERVAL '25 days', CURRENT_DATE - INTERVAL '11 days', NULL),
(3, 5, 6, CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE - INTERVAL '16 days', CURRENT_DATE - INTERVAL '10 days'),
(4, 3, 7, CURRENT_DATE - INTERVAL '2 days', CURRENT_DATE + INTERVAL '12 days', NULL);

-- Reservations
INSERT INTO reservations (reservation_id, member_id, book_id, reserved_at, status) VALUES
(1, 4, 3, NOW() - INTERVAL '1 day', 'pending');

-- Fines (Issue 3: returned 6 days late * ₹2 = ₹12, ₹5 paid -> Status: Unpaid)
INSERT INTO fines (fine_id, issue_id, fine_amount, payment_status, amount_paid) VALUES
(1, 3, 12.00, 'Unpaid', 5.00);

-- Reset Sequences to Highest IDs
SELECT setval('categories_category_id_seq', (SELECT COALESCE(MAX(category_id), 1) FROM categories));
SELECT setval('authors_author_id_seq', (SELECT COALESCE(MAX(author_id), 1) FROM authors));
SELECT setval('books_book_id_seq', (SELECT COALESCE(MAX(book_id), 1) FROM books));
SELECT setval('book_copies_copy_id_seq', (SELECT COALESCE(MAX(copy_id), 1) FROM book_copies));
SELECT setval('members_member_id_seq', (SELECT COALESCE(MAX(member_id), 1) FROM members));
SELECT setval('book_issue_issue_id_seq', (SELECT COALESCE(MAX(issue_id), 1) FROM book_issue));
SELECT setval('reservations_reservation_id_seq', (SELECT COALESCE(MAX(reservation_id), 1) FROM reservations));
SELECT setval('fines_fine_id_seq', (SELECT COALESCE(MAX(fine_id), 1) FROM fines));
