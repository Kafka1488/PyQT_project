import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QTextEdit, QMessageBox, QHeaderView, QFormLayout, QDialog, QSlider, QFileDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from database import MovieDatabase


class MovieCardDialog(QDialog):
    """Окно просмотра подробной карточки фильма"""

    def __init__(self, movie_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Карточка: {movie_data[1]}")
        self.resize(450, 420)

        layout = QFormLayout()

        layout.addRow("<b>Название:</b>", QLabel(str(movie_data[1])))
        layout.addRow("<b>Год:</b>", QLabel(str(movie_data[2] or "-")))
        layout.addRow("<b>Жанр(ы):</b>", QLabel(str(movie_data[7] or "-")))
        layout.addRow("<b>Страна/ы:</b>", QLabel(str(movie_data[8] or "-")))
        layout.addRow("<b>Режиссёр/ы:</b>", QLabel(str(movie_data[9] or "-")))
        layout.addRow("<b>Категория:</b>", QLabel(str(movie_data[5] or "-")))

        rating_val = f"{movie_data[3]} / 10" if movie_data[3] and movie_data[3] > 0 else "Нет оценки"
        layout.addRow("<b>Оценка:</b>", QLabel(rating_val))
        layout.addRow("<b>Дата добавления:</b>", QLabel(str(movie_data[6])))

        review_label = QTextEdit()
        review_label.setText(movie_data[4] or "Отзыва нет")
        review_label.setReadOnly(True)
        layout.addRow("<b>Личный отзыв:</b>", review_label)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addRow(close_btn)

        self.setLayout(layout)


class MovieApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = MovieDatabase()
        self.current_movie_id = None

        self.setWindowTitle("Каталог фильмов — Фильмотека")
        self.resize(1100, 650)

        self.init_ui()
        self.load_movies()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # --- Левая панель: Форма добавления/редактирования ---
        form_widget = QWidget()
        form_layout = QFormLayout()

        self.form_title_label = QLabel("<b>Добавить фильм</b>")
        form_layout.addRow(self.form_title_label)

        self.title_input = QLineEdit()
        self.genre_input = QLineEdit()
        self.genre_input.setPlaceholderText("через запятую: Комедия, Драма")

        self.year_input = QLineEdit()
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("через запятую: США, Франция")

        self.director_input = QLineEdit()
        self.director_input.setPlaceholderText("через запятую")

        self.category_combo = QComboBox()
        self.category_combo.addItems(["В планах", "Смотрели", "Избранные", "Брошенные"])

        # Слайдер для оценки (0 - 10)
        slider_layout = QHBoxLayout()
        self.rating_slider = QSlider(Qt.Orientation.Horizontal)
        self.rating_slider.setRange(0, 10)
        self.rating_slider.setValue(0)
        self.rating_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.rating_slider.setTickInterval(1)

        self.rating_label = QLabel("Нет оценки (0)")
        self.rating_slider.valueChanged.connect(self.update_rating_label)

        slider_layout.addWidget(self.rating_slider)
        slider_layout.addWidget(self.rating_label)

        self.review_input = QTextEdit()
        self.review_input.setMaximumHeight(80)

        form_layout.addRow("Название*:", self.title_input)
        form_layout.addRow("Жанр(ы)*:", self.genre_input)
        form_layout.addRow("Год:", self.year_input)
        form_layout.addRow("Страна/ы:", self.country_input)
        form_layout.addRow("Режиссёр/ы:", self.director_input)
        form_layout.addRow("Категория:", self.category_combo)
        form_layout.addRow("Оценка (0-10):", slider_layout)
        form_layout.addRow("Личный отзыв:", self.review_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Добавить")
        self.save_btn.clicked.connect(self.save_movie)
        self.cancel_btn = QPushButton("Очистить")
        self.cancel_btn.clicked.connect(self.clear_form)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        form_layout.addRow(btn_layout)

        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(360)

        # --- Правая панель: Управление фильтрами, сортировкой и таблица ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        # Панель переключателей (Категории + Сортировка)
        controls_layout = QHBoxLayout()

        # 1. Выбор категории (Смотрели, Избранные, В планах, Брошенные)
        controls_layout.addWidget(QLabel("Категория:"))
        self.filter_category = QComboBox()
        self.filter_category.addItems(["Все", "В планах", "Смотрели", "Избранные", "Брошенные"])
        self.filter_category.currentTextChanged.connect(self.load_movies)
        controls_layout.addWidget(self.filter_category)

        controls_layout.addSpacing(20)

        # 2. Сортировка (по алфавиту, дате, году, оценке и т.д.)
        controls_layout.addWidget(QLabel("Сортировка:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "По алфавиту (название А-Я)",
            "По дате добавления (сначала новые)",
            "По году (сначала новые)",
            "По оценке (сначала высокий балл)"
        ])
        self.sort_combo.currentIndexChanged.connect(self.load_movies)
        controls_layout.addWidget(self.sort_combo)

        controls_layout.addStretch()
        right_layout.addLayout(controls_layout)

        # Таблица фильмов
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Название", "Год", "Жанр(ы)", "Страна/ы", "Режиссёр/ы", "Категория", "Оценка"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnHidden(0, True)
        self.table.cellDoubleClicked.connect(self.open_movie_card)

        right_layout.addWidget(self.table)

        # Кнопки управления таблицей
        table_btn_layout = QHBoxLayout()
        self.edit_btn_mode = QPushButton("Редактировать выбранный")
        self.edit_btn_mode.clicked.connect(self.load_to_form_for_edit)

        self.delete_btn = QPushButton("Удалить выбранный")
        self.delete_btn.clicked.connect(self.delete_movie)

        table_btn_layout.addWidget(self.edit_btn_mode)
        table_btn_layout.addWidget(self.delete_btn)
        table_btn_layout.addStretch()

        right_layout.addLayout(table_btn_layout)
        right_widget.setLayout(right_layout)

        main_layout.addWidget(form_widget)
        main_layout.addWidget(right_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def update_rating_label(self, value):
        if value == 0:
            self.rating_label.setText("Нет оценки (0)")
        else:
            self.rating_label.setText(f"{value} из 10")

    def load_movies(self):
        movies = self.db.get_all_movies()

        # 1. Фильтрация по выбранной категории («Все», «В планах», «Избранные» и т.д.)
        selected_category = self.filter_category.currentText()
        if selected_category != "Все":
            movies = [m for m in movies if m[5] == selected_category]

        # 2. Сортировка (Алфавит, дата добавления, год, оценка)
        sort_idx = self.sort_combo.currentIndex()
        if sort_idx == 0:  # По алфавиту
            movies.sort(key=lambda x: x[1].lower())
        elif sort_idx == 1:  # По дате добавления
            movies.sort(key=lambda x: x[6], reverse=True)
        elif sort_idx == 2:  # По году
            movies.sort(key=lambda x: (x[2] is not None, x[2]), reverse=True)
        elif sort_idx == 3:  # По оценке
            movies.sort(key=lambda x: (x[3] is not None, x[3]), reverse=True)

        # Заполнение таблицы
        self.table.setRowCount(0)
        for row_idx, movie in enumerate(movies):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(movie[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(movie[1]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(movie[2]) if movie[2] else ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(movie[7] or ""))
            self.table.setItem(row_idx, 4, QTableWidgetItem(movie[8] or ""))
            self.table.setItem(row_idx, 5, QTableWidgetItem(movie[9] or ""))
            self.table.setItem(row_idx, 6, QTableWidgetItem(movie[5] or ""))

            rating_display = str(movie[3]) if movie[3] and movie[3] > 0 else "-"
            self.table.setItem(row_idx, 7, QTableWidgetItem(rating_display))

    def save_movie(self):
        title = self.title_input.text().strip()
        genre_str = self.genre_input.text().strip()
        year_str = self.year_input.text().strip()
        country_str = self.country_input.text().strip()
        director_str = self.director_input.text().strip()
        category = self.category_combo.currentText()

        rating = self.rating_slider.value()
        if rating == 0:
            rating = None

        review = self.review_input.toPlainText().strip()

        # Валидация
        if not title or not genre_str:
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля: «Название» и «Жанр(ы)»!")
            return

        year = int(year_str) if year_str.isdigit() else None
        genres = [g.strip() for g in genre_str.split(",") if g.strip()]
        countries = [c.strip() for c in country_str.split(",") if c.strip()]
        directors = [d.strip() for d in director_str.split(",") if d.strip()]

        if self.current_movie_id is None:
            self.db.add_movie(title, year, rating, review, category, genres, countries, directors)
        else:
            self.db.update_movie(self.current_movie_id, title, year, rating, review, category, genres, countries,
                                 directors)
            self.current_movie_id = None
            self.form_title_label.setText("<b>Добавить фильм</b>")
            self.save_btn.setText("Добавить")

        self.clear_form()
        self.load_movies()

    def load_to_form_for_edit(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите фильм в таблице для редактирования!")
            return

        row = selected_rows[0].row()
        movie_id = int(self.table.item(row, 0).text())
        movie = self.db.get_movie_by_id(movie_id)

        if movie:
            self.current_movie_id = movie[0]
            self.title_input.setText(movie[1])
            self.year_input.setText(str(movie[2]) if movie[2] else "")
            self.genre_input.setText(movie[7] or "")
            self.country_input.setText(movie[8] or "")
            self.director_input.setText(movie[9] or "")

            cat_index = self.category_combo.findText(movie[5])
            if cat_index >= 0:
                self.category_combo.setCurrentIndex(cat_index)

            rating_val = movie[3] if movie[3] else 0
            self.rating_slider.setValue(rating_val)

            self.review_input.setText(movie[4] or "")

            self.form_title_label.setText(f"<b>Редактирование (ID: {movie[0]})</b>")
            self.save_btn.setText("Сохранить")

    def open_movie_card(self, row, column):
        movie_id = int(self.table.item(row, 0).text())
        movie = self.db.get_movie_by_id(movie_id)
        if movie:
            card = MovieCardDialog(movie, self)
            card.exec()

    def delete_movie(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите фильм для удаления!")
            return

        reply = QMessageBox.question(
            self, "Подтверждение", "Вы уверены, что хотите удалить выбранный фильм?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                movie_id = int(self.table.item(row.row(), 0).text())
                self.db.delete_movie(movie_id)
            self.clear_form()
            self.load_movies()

    def clear_form(self):
        self.title_input.clear()
        self.genre_input.clear()
        self.year_input.clear()
        self.country_input.clear()
        self.director_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.rating_slider.setValue(0)
        self.review_input.clear()

        self.current_movie_id = None
        self.form_title_label.setText("<b>Добавить фильм</b>")
        self.save_btn.setText("Добавить")

    def closeEvent(self, event):
        self.db.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MovieApp()
    window.show()
    sys.exit(app.exec())
