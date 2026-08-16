INSERT INTO roles (id, name) VALUES (1, 'CUSTOMER');
INSERT INTO roles (id, name) VALUES (2, 'CASHIER');
INSERT INTO roles (id, name) VALUES (3, 'ADMIN');

-- Pre-hashed passwords using Werkzeug generate_password_hash:
-- 'Admin@123' -> pbkdf2:sha256:600000$Wk9Q0g4J$d213bc034d69359e19d36bb699a71a357ed9a7bd6eec3b570cb3c2ecbb219808
-- 'Cashier@123' -> pbkdf2:sha256:600000$mR1S8VzK$b30dcfeb812e9b25fbcdbbfa99c0dcb2b1e4c7ae4dbbcddfb760fa0f5ce2e90c
-- 'Customer@123' -> pbkdf2:sha256:600000$87XZgT1u$0ab74744ce0749a5b3a4a9840d2d30fa1dbd09d3b0704439c281cb9f2a9ed212

INSERT INTO users (id, full_name, email, phone, password_hash, role_id) VALUES
(1, 'System Administrator', 'admin@ceyloncineplex.lk', '+94771234567', 'pbkdf2:sha256:1000000$OTrcqcYZ5boOwSOt$456be3821bb08d88ccc0a2fffdb5a8d7859313e067de0f73b3472cd6b80e5693', 3),
(2, 'Kamal Fernando (Cashier)', 'cashier@ceyloncineplex.lk', '+94719876543', 'pbkdf2:sha256:1000000$Q5gWuzsejXtGGbpE$697e14e351a96591f91efc37435cb8be93ae31f6f03936bc5288be957649cfbb', 2),
(3, 'Kasun Perera', 'kasun.perera@gmail.com', '+94703334444', 'pbkdf2:sha256:1000000$Lf6KU8yNx9xgzbqN$9811c0e69f5f60f206bde21d6b57971e220a6dad700ba8ef9a4fd8768bbd1b34', 1),
(4, 'Nimali Jayasinghe', 'nimali.j@yahoo.com', '+94721112222', 'pbkdf2:sha256:1000000$Lf6KU8yNx9xgzbqN$9811c0e69f5f60f206bde21d6b57971e220a6dad700ba8ef9a4fd8768bbd1b34', 1);

INSERT INTO seat_types (id, name, base_price_lkr, color_code, description) VALUES
(1, 'Standard', 850.00, '#6C757D', 'Comfortable standard cinema seating'),
(2, 'Premium', 1200.00, '#D4AF6A', 'Extra legroom premium seating with prime viewing angle'),
(3, 'VIP', 1800.00, '#A51C30', 'Luxury recliner VIP seating with complimentary popcorn & beverage service');

INSERT INTO halls (id, name, hall_type, capacity, rows_count, cols_count) VALUES
(1, 'Hall 01', 'Standard Cinema Hall', 120, 10, 12),
(2, 'Hall 02', 'Premium Dolby Atmos Hall', 80, 8, 10),
(3, 'Hall 03', 'Luxury Recliner VIP Hall', 50, 5, 10);

-- Populate Movies
INSERT INTO movies (id, title, title_sinhala, poster_url, backdrop_url, description, genre, duration_mins, language, country, release_date, age_rating, director, cast, trailer_url, status) VALUES
(1, 'Rani', 'Rani', 
'https://tse4.mm.bing.net/th/id/OIP.DwiAE14Ic8dRABJ57EQMqQAAAA?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
'https://i.ytimg.com/vi/UCLsqrx0I24/maxresdefault.jpg',
'A biographical film depicting the life of Sri Lankan political leader Rohana Wijeweera, exploring his revolutionary journey, personal sacrifices, and dramatic historical events.',
'Biography / Drama / History', 138, 'Sinhala', 'Sri Lanka', '2019-01-18', 'PG-13', 'Anuruddha Jayasinghe', 'Kamal Addararachchi, Sulochana Weerasinghe, Jagath Manuwarna', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'NOW SHOWING'),

(2, 'Valampuri', 'Valampuri', 
'https://tse2.mm.bing.net/th/id/OIP.7GsqcK57-_cwRKj14iupJQHaJQ?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
'https://i.ytimg.com/vi/UCLsqrx0I24/maxresdefault.jpg',
'An epic historical Sinhala film focusing on King Valagamba of Anuradhapura and the preservation of the sacred Tripitaka during times of drought and foreign invasion.',
'Epic / Action / History', 140, 'Sinhala', 'Sri Lanka', '2017-01-20', 'PG', 'Chhatra Weeraman', 'Uddika Premarathna, Dilhani Ekanayake, Roshan Ravindra', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'NOW SHOWING'),

(3, 'Eda-Re', 'Eda-Re', 
'https://www.divaina.lk/wp-content/uploads/2026/01/Eda-Re-23.jpg',
'https://i.ytimg.com/vi/UCLsqrx0I24/maxresdefault.jpg',
'A gripping Sri Lankan mystery drama following suspenseful events unfolding in a single night.',
'Mystery / Drama', 114, 'Sinhala', 'Sri Lanka', '2026-01-15', 'PG-13', 'Uberto Pasolini', 'Dharmapriya Dias, Gihan De Chickera, Namal Jayasinghe', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'NOW SHOWING'),

(4, 'Dune: Part Two', 'Dune: Part Two', 
'https://i.pinimg.com/736x/03/c0/c2/03c0c2137dd12b0dd65d89c3b2ac2baa.jpg',
'https://filmfare.wwmindia.com/thumb/content/2023/aug/upcominghollywoodmovies21690962006.jpg?width=1200&height=900',
'Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.',
'Sci-Fi / Adventure', 166, 'English', 'USA', '2024-03-01', 'PG-13', 'Denis Villeneuve', 'Timothée Chalamet, Zendaya, Rebecca Ferguson', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'NOW SHOWING'),

(5, 'Sihina Nelum Mal', 'Sihina Nelum Mal', 
'https://films.lk/uploads/films/profiles/small/Sihina-Nelum-Mal-sri-lanka-Sinhala-film-2488.jpg',
'https://ceylontheatres.com/wp-content/uploads/2024/07/thumbnail-4.jpg',
'A high-energy Sri Lankan romantic action drama revolving around friends participating in a competition.',
'Action / Comedy / Drama', 145, 'Sinhala', 'Sri Lanka', '2012-05-17', 'U', 'Udara Palliyaguruge', 'Roshan Ranawana, Pubudu Chathuranga, Mahendra Perera', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'NOW SHOWING'),

(6, 'Oppenheimer', 'Oppenheimer', 
'https://feeds.abplive.com/onecms/images/uploaded-images/2024/04/05/559e36af41c35ae580a1f02991548d4b1712320325269597_1.jpg',
'https://filmfare.wwmindia.com/thumb/content/2023/aug/upcominghollywoodmovies21690962006.jpg?width=1200&height=900',
'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.',
'Biography / Drama', 180, 'English', 'USA', '2023-07-21', 'R', 'Christopher Nolan', 'Cillian Murphy, Emily Blunt, Matt Damon', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'NOW SHOWING'),

(7, 'Mandara', 'Mandara', 
'https://ceylontheatres.com/wp-content/uploads/2024/07/thumbnail-4.jpg',
'https://i.ytimg.com/vi/UCLsqrx0I24/maxresdefault.jpg',
'A gripping historical thriller examining colonial times in Sri Lanka and courage under adversity.',
'Historical / Thriller', 135, 'Sinhala', 'Sri Lanka', '2023-11-10', 'PG-13', 'Sanjiva Pushpakumara', 'Shyam Fernando, Nita Fernando, Dinara Punchihewa', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'NOW SHOWING'),

(8, 'Dharmayuddhaya', 'Dharmayuddhaya', 
'https://elgiva.com/wp-content/uploads/2026/01/Dharmayuddhaya-2-square-hero.jpg',
'https://i.ytimg.com/vi/UCLsqrx0I24/maxresdefault.jpg',
'A gripping Sri Lankan crime drama following a protective father who goes to extreme lengths to protect his family after an unexpected incident.',
'Drama / Thriller', 138, 'Sinhala', 'Sri Lanka', '2017-07-14', 'PG-13', 'Chethan Jayalal', 'Jackson Anthony, Dilhani Ekanayake, Kusum Renu', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'COMING SOON'),

(9, 'Spider-Man: Beyond the Spider-Verse', 'Spider-Man: Beyond the Spider-Verse', 
'https://tse2.mm.bing.net/th/id/OIP.murdodBru-2AHkHPI5u-hwHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
'https://feeds.abplive.com/onecms/images/uploaded-images/2024/04/05/559e36af41c35ae580a1f02991548d4b1712320325269597_1.jpg',
'The epic upcoming Spider-Man movie bringing cinematic multiverse spectacles directly to Sri Lankan audiences.',
'Animation / Action / Sci-Fi', 140, 'English', 'USA', '2026-11-20', 'PG', 'Joaquim Dos Santos', 'Shameik Moore, Hailee Steinfeld, Oscar Isaac', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'COMING SOON'),

(10, 'Adaraneeya Tharuwak', 'Adaraneeya Tharuwak', 
'https://tse4.mm.bing.net/th/id/OIP.8SVWwKrqVSIdZyjt57yXmwAAAA?r=0&rs=1&pid=ImgDetMain&o=7&rm=3',
'https://ceylontheatres.com/wp-content/uploads/2024/07/thumbnail-4.jpg',
'Set during the Kandyan kingdom era, an outcast noblewoman is forced to navigate strict social structures and find her freedom.',
'Period Drama', 130, 'Sinhala', 'Sri Lanka', '2023-06-09', 'PG-13', 'Prasanna Vithanage', 'Dinara Punchihewa, Sajitha Anuththara, Shyam Fernando', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'COMING SOON');

