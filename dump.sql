-- users 테이블 데이터 삽입
INSERT INTO users (username, email) VALUES
    ('john_doe', 'john.doe@example.com'),
    ('jane_smith', 'jane.smith@example.com'),
    ('alice_wong', 'alice.wong@example.com'),
    ('bob_lee', 'bob.lee@example.com'),
    ('emma_brown', 'emma.brown@example.com'),
    ('david_kim', 'david.kim@example.com');

-- profiles 테이블 데이터 삽입 (1:1 관계)
INSERT INTO profiles (user_id, bio, phone) VALUES
    (1, 'Software engineer with a passion for AI.', '123-456-7890'),
    (2, 'Data scientist exploring machine learning.', '234-567-8901'),
    (3, 'Web developer and coffee enthusiast.', '345-678-9012'),
    (4, 'Cybersecurity expert.', '456-789-0123'),
    (5, NULL, '567-890-1234'), -- bio는 선택적
    (6, 'Cloud architect.', NULL); -- phone은 선택적

-- posts 테이블 데이터 삽입 (1:N 관계)
INSERT INTO posts (title, content, user_id) VALUES
    ('My First Blog', 'Hello, this is my first post!', 1),
    ('AI Trends 2025', 'Exploring the future of AI.', 1),
    ('Web Dev Tips', 'Best practices for modern web development.', 2),
    ('Data Science Journey', 'My experience with Python and R.', 2),
    ('Cybersecurity Basics', 'How to secure your online presence.', 4),
    ('Cloud Computing', 'Introduction to AWS and Azure.', 6),
    ('Machine Learning Intro', 'Getting started with ML.', 2),
    ('Why I Love Coding', 'A personal story about programming.', 3),
    ('Docker Tutorial', 'Containerization made easy.', 1),
    ('SQL Tips', 'Optimizing your database queries.', 5);

-- students 테이블 데이터 삽입
INSERT INTO students (name) VALUES
    ('Sarah Park'),
    ('Michael Chen'),
    ('Emily Davis'),
    ('James Wilson'),
    ('Lisa Taylor'),
    ('Tom Harris');

-- courses 테이블 데이터 삽입
INSERT INTO courses (title) VALUES
    ('Introduction to Python'),
    ('Advanced Machine Learning'),
    ('Web Development Bootcamp'),
    ('Database Systems'),
    ('Cybersecurity Fundamentals'),
    ('Cloud Computing Essentials');

-- student_courses 테이블 데이터 삽입 (N:N 관계)
INSERT INTO student_courses (student_id, course_id) VALUES
    (1, 1), -- Sarah takes Python
    (1, 3), -- Sarah takes Web Dev
    (2, 2), -- Michael takes ML
    (2, 4), -- Michael takes Database
    (3, 1), -- Emily takes Python
    (3, 5), -- Emily takes Cybersecurity
    (4, 3), -- James takes Web Dev
    (4, 6), -- James takes Cloud
    (5, 2), -- Lisa takes ML
    (5, 4), -- Lisa takes Database
    (6, 1), -- Tom takes Python
    (6, 5); -- Tom takes Cybersecurity