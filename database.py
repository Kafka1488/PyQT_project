import sqlite3
from datetime import datetime


class MovieDatabase:
    def __init__(self, db_name="movies.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        default_categories = ["В планах", "Смотрели", "Избранные", "Брошенные"]
        for cat in default_categories:
            self.cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER,
                rating INTEGER,
                review TEXT,
                category_id INTEGER,
                date_added TEXT NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_genres (
                movie_id INTEGER,
                genre_id INTEGER,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
                FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE,
                PRIMARY KEY (movie_id, genre_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_countries (
                movie_id INTEGER,
                country_id INTEGER,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
                FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE CASCADE,
                PRIMARY KEY (movie_id, country_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_directors (
                movie_id INTEGER,
                director_id INTEGER,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
                FOREIGN KEY (director_id) REFERENCES directors(id) ON DELETE CASCADE,
                PRIMARY KEY (movie_id, director_id)
            )
        """)
        self.conn.commit()

    def _get_or_create_id(self, table, name):
        name = name.strip()
        self.cursor.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        self.cursor.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_movie(self, title, year, rating, review, category_name, genres, countries, directors):
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
        cat_row = self.cursor.fetchone()
        cat_id = cat_row[0] if cat_row else None

        self.cursor.execute("""
            INSERT INTO movies (title, year, rating, review, category_id, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, year, rating, review, cat_id, date_added))


        movie_id = self.cursor.lastrowid

        for g in genres:
            if g:
                g_id = self._get_or_create_id("genres", g)
                self.cursor.execute("INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) VALUES (?, ?)", (movie_id, g_id))

        for c in countries:
            if c:
                c_id = self._get_or_create_id("countries", c)
                self.cursor.execute("INSERT OR IGNORE INTO movie_countries (movie_id, country_id) VALUES (?, ?)",
                                    (movie_id, c_id))

        for d in directors:
            if d:
                d_id = self._get_or_create_id("directors", d)
                self.cursor.execute("INSERT OR IGNORE INTO movie_directors (movie_id, director_id) VALUES (?, ?)",
                                    (movie_id, d_id))

        self.conn.commit()


    def update_movie(self, movie_id, title, year, rating, review, category_name, genres, countries, directors):
        self.cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
        cat_row = self.cursor.fetchone()
        cat_id = cat_row[0] if cat_row else None

        self.cursor.execute("""
                UPDATE movies SET title=?, year=?, rating=?, review=?, category_id=?
                WHERE id=?
            """, (title, year, rating, review, cat_id, movie_id))

        self.cursor.execute("DELETE FROM movie_genres WHERE movie_id = ?", (movie_id,))
        self.cursor.execute("DELETE FROM movie_countries WHERE movie_id = ?", (movie_id,))
        self.cursor.execute("DELETE FROM movie_directors WHERE movie_id = ?", (movie_id,))

        for g in genres:
            if g:
                g_id = self._get_or_create_id("genres", g)
                self.cursor.execute("INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) VALUES (?, ?)",
                                    (movie_id, g_id))

        for c in countries:
            if c:
                c_id = self._get_or_create_id("countries", c)
                self.cursor.execute("INSERT OR IGNORE INTO movie_countries (movie_id, country_id) VALUES (?, ?)",
                                    (movie_id, c_id))

        for d in directors:
            if d:
                d_id = self._get_or_create_id("directors", d)
                self.cursor.execute("INSERT OR IGNORE INTO movie_directors (movie_id, director_id) VALUES (?, ?)",
                                    (movie_id, d_id))

        self.conn.commit()


    def delete_movie(self, movie_id):
        self.cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
        self.conn.commit()


    def get_all_movies(self):
        query = """
                SELECT 
                    m.id, m.title, m.year, m.rating, m.review, c.name, m.date_added,
                    GROUP_CONCAT(DISTINCT g.name) AS genres,
                    GROUP_CONCAT(DISTINCT co.name) AS countries,
                    GROUP_CONCAT(DISTINCT d.name) AS directors
                FROM movies m
                LEFT JOIN categories c ON m.category_id = c.id
                LEFT JOIN movie_genres mg ON m.id = mg.movie_id
                LEFT JOIN genres g ON mg.genre_id = g.id
                LEFT JOIN movie_countries mc ON m.id = mc.movie_id
                LEFT JOIN countries co ON mc.country_id = co.id
                LEFT JOIN movie_directors md ON m.id = md.movie_id
                LEFT JOIN directors d ON md.director_id = d.id
                GROUP BY m.id
            """
        self.cursor.execute(query)
        return self.cursor.fetchall()


    def get_movie_by_id(self, movie_id):
        query = """
                SELECT 
                    m.id, m.title, m.year, m.rating, m.review, c.name, m.date_added,
                    GROUP_CONCAT(DISTINCT g.name) AS genres,
                    GROUP_CONCAT(DISTINCT co.name) AS countries,
                    GROUP_CONCAT(DISTINCT d.name) AS directors
                FROM movies m
                LEFT JOIN categories c ON m.category_id = c.id
                LEFT JOIN movie_genres mg ON m.id = mg.movie_id
                LEFT JOIN genres g ON mg.genre_id = g.id
                LEFT JOIN movie_countries mc ON m.id = mc.movie_id
                LEFT JOIN countries co ON mc.country_id = co.id
                LEFT JOIN movie_directors md ON m.id = md.movie_id
                LEFT JOIN directors d ON md.director_id = d.id
                WHERE m.id = ?
                GROUP BY m.id
            """
        self.cursor.execute(query, (movie_id,))
        return self.cursor.fetchone()


    def close(self):
        self.conn.close()
