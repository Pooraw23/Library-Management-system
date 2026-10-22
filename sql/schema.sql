-- ====================================================================
-- SMART LIBRARY MANAGEMENT SYSTEM - RELATIONAL SCHEMA
-- Generated from ER Diagram:
-- Entities: Students, Books, Authors, Book_Copies, Reservations
-- Relationships: Written_By (M:N), Contains (1:N), Borrow (M:N), Make (1:N), Reserve (N:1)
-- ====================================================================

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

-- 1. Students Entity (Student_Id, Name, Email)
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    member_id INT GENERATED ALWAYS AS (student_id) STORED,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'member' CHECK (role IN ('admin','librarian','member')),
    department VARCHAR(100),
    joined_on DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. Categories
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

-- 3. Books Entity (Book_Id, Title, category_id, Publisher, Publication_year)
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category_id INT NOT NULL REFERENCES categories(category_id),
    publisher VARCHAR(100),
    publication_year INT,
    isbn VARCHAR(20) UNIQUE NOT NULL
);

-- 4. Authors Entity (Author_Id, Author_Name)
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    author_name VARCHAR(100) NOT NULL
);

-- 5. "Written By" Relationship (Books M:N Authors)
CREATE TABLE book_authors (
    book_id INT REFERENCES books(book_id) ON DELETE CASCADE,
    author_id INT REFERENCES authors(author_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- 6. Book_Copies Entity (Contains 1:N -> Copy_Id, Book_Id, Status)
CREATE TABLE book_copies (
    copy_id SERIAL PRIMARY KEY,
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available','issued','lost'))
);

-- 7. "Borrow" Relationship (Students M:N Book_Copies -> Issue_Date, Due_Date, Return_Date)
CREATE TABLE borrow (
    borrow_id SERIAL PRIMARY KEY,
    issue_id INT GENERATED ALWAYS AS (borrow_id) STORED,
    student_id INT NOT NULL REFERENCES students(student_id),
    member_id INT GENERATED ALWAYS AS (student_id) STORED,
    copy_id INT NOT NULL REFERENCES book_copies(copy_id),
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    return_date DATE,
    CHECK (due_date >= issue_date)
);

-- 8. Reservations Entity (Reservation_Id, Reserved_at, Status)
CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    member_id INT GENERATED ALWAYS AS (student_id) STORED,
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    reserved_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','fulfilled','cancelled'))
);

-- 9. Fines Entity (Incurs 1:1 -> Fine_Id, Fine_Amount, Payment_Status)
CREATE TABLE fines (
    fine_id SERIAL PRIMARY KEY,
    borrow_id INT UNIQUE NOT NULL REFERENCES borrow(borrow_id) ON DELETE CASCADE,
    issue_id INT GENERATED ALWAYS AS (borrow_id) STORED,
    fine_amount NUMERIC(8,2) NOT NULL DEFAULT 0.00 CHECK (fine_amount >= 0),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'Unpaid' CHECK (payment_status IN ('Unpaid', 'Paid', 'Pending')),
    amount NUMERIC(8,2) GENERATED ALWAYS AS (fine_amount) STORED,
    amount_paid NUMERIC(8,2) NOT NULL DEFAULT 0,
    CHECK (amount_paid <= fine_amount)
);

-- Performance Indexes
CREATE INDEX idx_books_category ON books(category_id);
CREATE INDEX idx_book_copies_book ON book_copies(book_id);
CREATE INDEX idx_borrow_student ON borrow(student_id);
CREATE INDEX idx_borrow_copy ON borrow(copy_id);
CREATE INDEX idx_reservations_student ON reservations(student_id);
CREATE INDEX idx_reservations_book ON reservations(book_id);

-- Backward & Application Compatibility Views
CREATE OR REPLACE VIEW members AS SELECT * FROM students;
CREATE OR REPLACE VIEW book_issue AS SELECT * FROM borrow;
