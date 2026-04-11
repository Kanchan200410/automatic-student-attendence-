-- =========================
-- DATABASE
-- =========================
CREATE DATABASE IF NOT EXISTS student_db;
USE student_db;

-- =========================
-- STUDENTS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll VARCHAR(50) UNIQUE,
    age INT,
    section VARCHAR(20),
    year VARCHAR(10),
    branch VARCHAR(50),
    phone VARCHAR(15),
    email VARCHAR(100),
    image LONGBLOB,
    image_path VARCHAR(255)
);

-- =========================
-- FACE DATA
-- =========================
CREATE TABLE IF NOT EXISTS face_data (
    face_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    encoding BLOB,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =========================
-- CLASSES
-- =========================
CREATE TABLE IF NOT EXISTS classes (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(100),
    subject VARCHAR(100),
    teacher_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- DEVICES (CAMERA)
-- =========================
CREATE TABLE IF NOT EXISTS devices (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100),
    location VARCHAR(100),
    ip_address VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- ATTENDANCE
-- =========================
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    class_id INT,
    device_id INT,
    date DATE,
    check_in DATETIME,
    status ENUM('Present', 'Absent', 'Late') DEFAULT 'Present',
    confidence FLOAT,
    teacher_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, class_id, date),

    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE SET NULL,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE SET NULL
);

-- =========================
-- USERS (LOGIN SYSTEM)
-- =========================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    role ENUM('admin', 'student', 'teacher', 'hod') NOT NULL
);

-- =========================
-- SAMPLE USERS
-- =========================
INSERT INTO users (username, password, role) VALUES
('admin1', 'admin123', 'admin'),
('teacher1', 'teach123', 'teacher'),
('student1', 'stud123', 'student'),
('hod1', 'hod123', 'hod');