-- Create database
CREATE DATABASE IF NOT EXISTS movie_booking;

-- Use database
USE movie_booking;

-- Movies table
CREATE TABLE IF NOT EXISTS movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    movie_name VARCHAR(100) NOT NULL
);

-- Shows table (NEW: each show = movie + screen + time)
CREATE TABLE IF NOT EXISTS shows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT,
    screen VARCHAR(20),
    show_time VARCHAR(20),
    FOREIGN KEY (movie_id) REFERENCES movies(id)
);

-- Bookings table (linked to specific show)
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    show_id INT,
    seats VARCHAR(50),
    payment_method VARCHAR(50),
    FOREIGN KEY (show_id) REFERENCES shows(id)
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    rating VARCHAR(20),
    comments TEXT
);

-- Insert movies
INSERT INTO movies (movie_name) VALUES
('Avatar'),
('Avengers'),
('Inception');

-- Insert shows (VERY IMPORTANT)
INSERT INTO shows (movie_id, screen, show_time) VALUES
-- Avengers (movie_id = 2)
(2, 'Screen 1', '10:00 AM'),
(2, 'Screen 2', '2:00 PM'),
(2, 'Screen 1', '7:00 PM'),

-- Avatar (movie_id = 1)
(1, 'Screen 1', '11:00 AM'),
(1, 'Screen 3', '3:00 PM'),
(1, 'Screen 1', '8:00 PM'),

-- Inception (movie_id = 3)
(3, 'Screen 2', '9:00 AM'),
(3, 'Screen 3', '1:00 PM'),
(3, 'Screen 2', '6:00 PM');