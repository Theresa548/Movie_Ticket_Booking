-- Movies table
CREATE TABLE movies (
    id SERIAL PRIMARY KEY,
    movie_name VARCHAR(100) NOT NULL
);

-- Shows table
CREATE TABLE shows (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER REFERENCES movies(id) ON DELETE CASCADE,
    screen VARCHAR(20),
    show_time VARCHAR(20)
);

-- Bookings table
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    show_id INTEGER REFERENCES shows(id) ON DELETE CASCADE,
    seats VARCHAR(50),
    payment_method VARCHAR(50)
);

-- Feedback table
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    rating INTEGER,
    comments TEXT
);

-- Insert movies
INSERT INTO movies (movie_name) VALUES
('Avatar'),
('Avengers'),
('Inception');

-- Insert shows

-- Avengers (movie_id = 2)
INSERT INTO shows (movie_id, screen, show_time) VALUES
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