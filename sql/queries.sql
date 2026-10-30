-- ====================================================================
-- SMART LIBRARY MANAGEMENT SYSTEM - COMPLETE SQL QUERIES REFERENCE
-- All PostgreSQL & Psycopg2 Queries from Starting to Final Implementation
-- ====================================================================

-- ####################################################################
-- PART 1: DDL (DATA DEFINITION LANGUAGE) - CREATING SCHEMA & TABLES
-- ####################################################################

-- 1. Create the Database (Run from postgres default connection)
CREATE DATABASE library_db;

-- 2. Drop existing tables if re-initializing
DROP VIEW IF EXISTS book_issue CASCADE;
DROP VIEW IF EXISTS members CASCADE;
DROP TABLE IF EXISTS fines CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS borrow CASCADE;
DROP TABLE IF EXISTS book_copies CASCADE;
DROP TABLE IF EXISTS book_authors CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- 3. Create Students Entity Table
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'member' CHECK (role IN ('admin','librarian','member')),
    department VARCHAR(100),
    joined_on DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. Create Categories Table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

-- 5. Create Books Entity Table
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category_id INT NOT NULL REFERENCES categories(category_id),
    publisher VARCHAR(100),
    publication_year INT,
    isbn VARCHAR(20) UNIQUE NOT NULL
);

-- 6. Create Authors Entity Table
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    author_name VARCHAR(100) NOT NULL
);

-- 7. Create "Written By" Junction Table (Many-to-Many between Books and Authors)
CREATE TABLE book_authors (
    book_id INT REFERENCES books(book_id) ON DELETE CASCADE,
    author_id INT REFERENCES authors(author_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- 8. Create Book_Copies Entity Table (Physical Shelf Copies)
CREATE TABLE book_copies (
    copy_id SERIAL PRIMARY KEY,
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available','issued','lost'))
);

-- 9. Create Borrow Table (Circulation Loans between Students and Copies)
CREATE TABLE borrow (
    borrow_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    copy_id INT NOT NULL REFERENCES book_copies(copy_id),
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    return_date DATE,
    CHECK (due_date >= issue_date)
);

-- 10. Create Reservations Entity Table
CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    reserved_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','fulfilled','cancelled'))
);

-- 11. Create Fines Table (Overdue penalty: ₹2/day)
CREATE TABLE fines (
    fine_id SERIAL PRIMARY KEY,
    borrow_id INT UNIQUE NOT NULL REFERENCES borrow(borrow_id) ON DELETE CASCADE,
    amount NUMERIC(8,2) NOT NULL CHECK (amount >= 0),
    amount_paid NUMERIC(8,2) NOT NULL DEFAULT 0,
    CHECK (amount_paid <= amount)
);

-- 12. Create Performance Indexes
CREATE INDEX idx_books_category ON books(category_id);
CREATE INDEX idx_book_copies_book ON book_copies(book_id);
CREATE INDEX idx_borrow_student ON borrow(student_id);
CREATE INDEX idx_borrow_copy ON borrow(copy_id);
CREATE INDEX idx_reservations_student ON reservations(student_id);
CREATE INDEX idx_reservations_book ON reservations(book_id);

-- 13. Compatibility Views
CREATE OR REPLACE VIEW members AS
SELECT student_id AS member_id, student_id, name, email, password_hash, role, department, joined_on, is_active
FROM students;

CREATE OR REPLACE VIEW book_issue AS
SELECT borrow_id AS issue_id, borrow_id, student_id AS member_id, student_id, copy_id, issue_date, due_date, return_date
FROM borrow;


-- ####################################################################
-- PART 2: DML (DATA MANIPULATION LANGUAGE) - INSERT SEED RECORDS
-- ####################################################################

-- Insert Categories
INSERT INTO categories (category_id, category_name) VALUES
(1, 'Database Systems'),
(2, 'Software Engineering'),
(3, 'Computer Science & Algorithms'),
(4, 'Artificial Intelligence'),
(5, 'Operating Systems');

-- Insert Authors
INSERT INTO authors (author_id, author_name) VALUES
(1, 'Abraham Silberschatz'),
(2, 'Henry F. Korth'),
(3, 'S. Sudarshan'),
(4, 'Robert C. Martin'),
(5, 'Thomas H. Cormen'),
(6, 'Charles E. Leiserson');

-- Insert Books
INSERT INTO books (book_id, isbn, title, category_id, publisher, publication_year) VALUES
(1, '978-0078022159', 'Database System Concepts (7th Edition)', 1, 'McGraw-Hill', 2019),
(2, '978-0132350884', 'Clean Code', 2, 'Prentice Hall', 2008),
(3, '978-0262033848', 'Introduction to Algorithms (CLRS)', 3, 'MIT Press', 2009);

-- Insert Book Authors (M:N Links)
INSERT INTO book_authors (book_id, author_id) VALUES
(1, 1), (1, 2), (1, 3), (2, 4), (3, 5), (3, 6);

-- Insert Copies (ER: Book_Copies -> Copy_Id, Book_Id, Status)
INSERT INTO book_copies (copy_id, book_id, status) VALUES
(1, 1, 'issued'),
(2, 1, 'available'),
(3, 2, 'available'),
(4, 2, 'issued'),
(5, 3, 'issued'),
(6, 3, 'issued');

-- Insert Students & Staff (Passwords: admin123, librarian123, member123)
INSERT INTO students (student_id, name, email, password_hash, role, department) VALUES
(1, 'System Administrator', 'admin@library.edu', 'c', 'admin', 'Administration'),
(2, 'Eleanor Vance', 'librarian@library.edu', 'scrypt:32768:8:1$fpwoua8rWbshcS6S$509269e256446ec7f8f4db8a1d1b02000e8eba06161af509f31ebcfeb745c82f84fd054158785bbd62b869a3dfa883ba65df9852f68662c027f9a9432d86bfac', 'librarian', 'Central Library'),
(3, 'John Doe', 'john.doe@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Computer Science'),
(4, 'Alice Smith', 'alice.smith@student.edu', 'scrypt:32768:8:1$upETmHDvdkUM8cUd$ddb5e2fc9af5c73254ebbec67a979d2d3b581cd0ab2f4931e0b4ede525c824759b02c3bd845db6293872444d420a11a2d6b5995d0751478a2fcab58a7e88aabb', 'member', 'Information Technology');

-- Insert Initial Borrow Loans
INSERT INTO borrow (borrow_id, student_id, copy_id, issue_date, due_date, return_date) VALUES
(1, 3, 1, CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '9 days', NULL),
(2, 4, 4, CURRENT_DATE - INTERVAL '25 days', CURRENT_DATE - INTERVAL '11 days', NULL);

-- Insert Pending Reservation (Alice holding Algorithms because all copies are issued)
INSERT INTO reservations (reservation_id, student_id, book_id, reserved_at, status) VALUES
(1, 4, 3, NOW() - INTERVAL '1 day', 'pending');

-- Insert Sample Fine (Alice: 11 days overdue * ₹2 = ₹22)
INSERT INTO fines (fine_id, borrow_id, amount, amount_paid) VALUES
(1, 2, 22.00, 0.00);


-- ####################################################################
-- PART 3: APPLICATION QUERIES USED IN PYTHON (PSYCOPG2)
-- ####################################################################

-- 1. Authentication: Find user by email
SELECT student_id, name, email, password_hash, role, department, joined_on, is_active
FROM students
WHERE email = %s;

-- 2. Registration: Insert new student member
INSERT INTO students (name, email, password_hash, role, department, joined_on, is_active)
VALUES (%s, %s, %s, 'member', %s, CURRENT_DATE, TRUE)
RETURNING student_id, name, email, role, department;

-- 3. Catalog Search: Books with aggregated authors and copy counts
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
WHERE b.title ILIKE %s OR b.isbn ILIKE %s OR c.category_name ILIKE %s
GROUP BY b.book_id, c.category_name
ORDER BY b.title ASC;

-- 4. Borrowing Transaction - Step 1: Check available copy
SELECT copy_id, book_id, status 
FROM book_copies 
WHERE copy_id = %s FOR UPDATE;

-- 5. Borrowing Transaction - Step 2: Check student active loan limit (Max 3)
SELECT COUNT(*) AS active_count 
FROM borrow 
WHERE student_id = %s AND return_date IS NULL;

-- 6. Borrowing Transaction - Step 3: Insert borrow record
INSERT INTO borrow (student_id, copy_id, issue_date, due_date)
VALUES (%s, %s, %s, %s)
RETURNING borrow_id, student_id, copy_id, issue_date, due_date;

-- 7. Borrowing Transaction - Step 4: Update copy status to 'issued'
UPDATE book_copies 
SET status = 'issued' 
WHERE copy_id = %s;

-- 8. Return Transaction - Step 1: Lock borrow record
SELECT b.borrow_id, b.student_id, b.copy_id, b.issue_date, b.due_date, b.return_date, bc.book_id
FROM borrow b
JOIN book_copies bc ON b.copy_id = bc.copy_id
WHERE b.borrow_id = %s FOR UPDATE;

-- 9. Return Transaction - Step 2: Update return_date
UPDATE borrow 
SET return_date = %s 
WHERE borrow_id = %s;

-- 10. Return Transaction - Step 3: Set copy status back to 'available'
UPDATE book_copies 
SET status = 'available' 
WHERE copy_id = %s;

-- 11. Return Transaction - Step 4: Generate fine if overdue (2 * overdue_days)
INSERT INTO fines (borrow_id, amount, amount_paid)
VALUES (%s, %s, 0.00)
ON CONFLICT (borrow_id) DO UPDATE SET amount = EXCLUDED.amount
RETURNING fine_id, borrow_id, amount, amount_paid;

-- 12. Reservations: Check 0 available copies rule
SELECT COUNT(*) AS avail_count 
FROM book_copies 
WHERE book_id = %s AND status = 'available';

-- 13. Reservations: Place reservation hold
INSERT INTO reservations (student_id, book_id, reserved_at, status)
VALUES (%s, %s, NOW(), 'pending')
RETURNING reservation_id, student_id, book_id, reserved_at, status;

-- 14. Fine Settlement: Record payment
UPDATE fines 
SET amount_paid = amount_paid + %s 
WHERE fine_id = %s
RETURNING fine_id, borrow_id, amount, amount_paid;

-- 15. Dashboard Overview: Active loans with overdue flag
SELECT 
    b.borrow_id, b.student_id, b.copy_id, b.issue_date, b.due_date, b.return_date,
    s.name AS student_name, s.email AS student_email,
    bk.book_id, bk.title AS book_title, bk.isbn,
    f.fine_id, f.amount AS fine_amount, f.amount_paid AS fine_amount_paid,
    (CURRENT_DATE > b.due_date AND b.return_date IS NULL) AS is_overdue,
    GREATEST(0, (CURRENT_DATE - b.due_date)) AS overdue_days
FROM borrow b
JOIN students s ON b.student_id = s.student_id
JOIN book_copies bc ON b.copy_id = bc.copy_id
JOIN books bk ON bc.book_id = bk.book_id
LEFT JOIN fines f ON b.borrow_id = f.borrow_id
WHERE b.return_date IS NULL
ORDER BY b.borrow_id DESC;
