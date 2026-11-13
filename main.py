import sys
import os
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
        self.resize(500, 420)

        main_layout = QHBoxLayout()

        # Левая часть: Постер
        poster_layout = QVBoxLayout()
        self.poster_label = QLabel("Нет постера")
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setFixedSize(140, 180)
        self.poster_label.setStyleSheet("border: 1px solid gray; background-color: #222; color: #aaa;")

        poster_path = movie_data[2]
        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            if not pixmap.isNull():
                self.poster_label.setPixmap(
                    pixmap.scaled(140, 180, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                )

        poster_layout.addWidget(self.poster_label)
        poster_layout.addStretch()
        main_layout.addLayout(poster_layout)

        # Правая часть: Данные
        layout = QFormLayout()
        layout.addRow("<b>Название:</b>", QLabel(str(movie_data[1])))
        layout.addRow("<b>Год:</b>", QLabel(str(movie_data[3] or "-")))
        layout.addRow("<b>Жанр(ы):</b>", QLabel(str(movie_data[8] or "-")))
        layout.addRow("<b>Страна/ы:</b>", QLabel(str(movie_data[9] or "-")))
        layout.addRow("<b>Режиссёр/ы:</b>", QLabel(str(movie_data[10] or "-")))
        layout.addRow("<b>Категория:</b>", QLabel(str(movie_data[6] or "-")))

        rating_val = f"{movie_data[4]} / 10" if movie_data[4] and movie_data[4] > 0 else "Нет оценки"
        layout.addRow("<b>Оценка:</b>", QLabel(rating_val))
        layout.addRow("<b>Дата добавления:</b>", QLabel(str(movie_data[7])))

        review_label = QTextEdit()
        review_label.setText(movie_data[5] or "Отзыва нет")
        review_label.setReadOnly(True)
        layout.addRow("<b>Личный отзыв:</b>", review_label)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addRow(close_btn)

        main_layout.addLayout(layout)
        self.setLayout(main_layout)


class MovieApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = MovieDatabase()
        self.current_movie_id = None
        self.cover_path = None

        self.setWindowTitle("Каталог фильмов — Фильмотека")
        self.resize(1100, 650)

        self.init_ui()
        self.load_movies()

    def init_ui(self):
        main_layout = QHBoxLayout()

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

        # Виджеты для постера
        self.CoverLabel = QLabel("Постер не выбран")
        self.CoverLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.CoverLabel.setFixedSize(140, 180)
        self.CoverLabel.setStyleSheet("border: 1px solid gray; background-color: #222; color: #aaa;")

        self.poster_btn_layout = QHBoxLayout()
        self.btn_load_movie_poster = QPushButton("Выбрать")
        self.btn_load_movie_poster.clicked.connect(self.load_movie_poster)
        self.btn_clear_poster = QPushButton("Очистить")
        self.btn_clear_poster.clicked.connect(self.clear_poster)
        self.poster_btn_layout.addWidget(self.btn_load_movie_poster)
        self.poster_btn_layout.addWidget(self.btn_clear_poster)

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
        form_layout.addRow("Постер:", self.CoverLabel)
        form_layout.addRow("", self.poster_btn_layout)
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
        form_widget.setFixedWidth(380)

        # Правая панель (Таблица и фильтры)
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Категория:"))
        self.filter_category = QComboBox()
        self.filter_category.addItems(["Все", "В планах", "Смотрели", "Избранные", "Брошенные"])
        self.filter_category.currentTextChanged.connect(self.load_movies)
        controls_layout.addWidget(self.filter_category)

        controls_layout.addSpacing(20)

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

        table_btn_layout = QHBoxLayout()
        self.edit_btn_mode = QPushButton("Редактировать выбранный")
        self.edit_btn_mode.clicked.connect(self.load_to_form_for_edit)

        self.delete_btn = QPushButton("Удалить выбранный")
        self.delete_btn.clicked.connect(self.delete_movie)

        self.import_btn = QPushButton("Импортировать из файла...")
        self.import_btn.clicked.connect(self.import_movies_from_file)

        table_btn_layout.addWidget(self.edit_btn_mode)
        table_btn_layout.addWidget(self.delete_btn)
        table_btn_layout.addWidget(self.import_btn)
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

        selected_category = self.filter_category.currentText()
        if selected_category != "Все":
            movies = [m for m in movies if m[6] == selected_category]

        sort_idx = self.sort_combo.currentIndex()
        if sort_idx == 0:
            movies.sort(key=lambda x: x[1].lower())
        elif sort_idx == 1:
            movies.sort(key=lambda x: x[7], reverse=True)
        elif sort_idx == 2:
            movies.sort(key=lambda x: (x[3] is not None, x[3]), reverse=True)
        elif sort_idx == 3:
            movies.sort(key=lambda x: (x[4] is not None, x[4]), reverse=True)

        self.table.setRowCount(0)
        for row_idx, movie in enumerate(movies):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(movie[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(movie[1]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(movie[3]) if movie[3] else ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(movie[8] or ""))
            self.table.setItem(row_idx, 4, QTableWidgetItem(movie[9] or ""))
            self.table.setItem(row_idx, 5, QTableWidgetItem(movie[10] or ""))
            self.table.setItem(row_idx, 6, QTableWidgetItem(movie[6] or ""))

            rating_display = str(movie[4]) if movie[4] and movie[4] > 0 else "-"
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
        poster = self.cover_path

        if not title or not genre_str:
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля: «Название» и «Жанр(ы)»!")
            return

        year = int(year_str) if year_str.isdigit() else None
        genres = [g.strip() for g in genre_str.split(",") if g.strip()]
        countries = [c.strip() for c in country_str.split(",") if c.strip()]
        directors = [d.strip() for d in director_str.split(",") if d.strip()]

        if self.current_movie_id is None:
            self.db.add_movie(title, poster, year, rating, review, category, genres, countries, directors)
        else:
            self.db.update_movie(self.current_movie_id, title, poster, year, rating, review, category, genres,
                                 countries, directors)
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
            self.year_input.setText(str(movie[3]) if movie[3] else "")
            self.genre_input.setText(movie[8] or "")
            self.country_input.setText(movie[9] or "")
            self.director_input.setText(movie[10] or "")

            cat_index = self.category_combo.findText(movie[6])
            if cat_index >= 0:
                self.category_combo.setCurrentIndex(cat_index)

            rating_val = movie[4] if movie[4] else 0
            self.rating_slider.setValue(rating_val)

            self.review_input.setText(movie[5] or "")

            # Загружаем постер при редактировании
            self.cover_path = movie[2]
            if self.cover_path and os.path.exists(self.cover_path):
                pixmap = QPixmap(self.cover_path)
                if not pixmap.isNull():
                    self.CoverLabel.setPixmap(
                        pixmap.scaled(140, 180, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
                    )
            else:
                self.CoverLabel.clear()
                self.CoverLabel.setText("Постер не выбран")

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

    def import_movies_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл для импорта", "", "Текстовые файлы и таблицы (*.csv *.txt);;Все файлы (*.*)"
        )
        if not file_path:
            return

        added_count = 0
        error_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
        except Exception:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    lines = f.readlines()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл:\n{str(e)}")
                return

        if not lines:
            QMessageBox.warning(self, "Внимание", "Файл пустой!")
            return

        start_idx = 0
        first_line_lower = lines[0].lower()
        if "название" in first_line_lower or "title" in first_line_lower:
            start_idx = 1

        for idx in range(start_idx, len(lines)):
            line = lines[idx].strip()
            if not line:
                continue

            if '/' in line:
                parts = [p.strip() for p in line.split('/')]
            elif ';' in line:
                parts = [p.strip() for p in line.split(';')]
            else:
                parts = [p.strip() for p in line.split(',')]

            parts = [p for p in parts if p != '']

            if len(parts) < 2:
                error_count += 1
                continue

            title = parts[0]
            genre_str = parts[1] if len(parts) > 1 and parts[1] else "Другое"

            year = None
            if len(parts) > 2 and parts[2].isdigit():
                year = int(parts[2])

            country_str = parts[3] if len(parts) > 3 else ""
            director_str = parts[4] if len(parts) > 4 else ""

            category = "В планах"
            if len(parts) > 5 and parts[5] in ["В планах", "Смотрели", "Избранные", "Брошенные"]:
                category = parts[5]

            rating = None
            if len(parts) > 6 and parts[6].isdigit():
                r_val = int(parts[6])
                if 0 <= r_val <= 10:
                    rating = r_val

            review = parts[7] if len(parts) > 7 else ""

            try:
                genres = [g.strip() for g in genre_str.split(",") if g.strip()]
                countries = [c.strip() for c in country_str.split(",") if c.strip()]
                directors = [d.strip() for d in director_str.split(",") if d.strip()]

                self.db.add_movie(title, None, year, rating, review, category, genres, countries, directors)
                added_count += 1
            except Exception:
                error_count += 1

        self.load_movies()
        QMessageBox.information(
            self, "Импорт завершен",
            f"Успешно добавлено фильмов: {added_count}\nПропущено строк с ошибками: {error_count}"
        )

    def load_movie_poster(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите постер", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not path:
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть изображение")
            return

        self.cover_path = os.path.abspath(path)
        self.CoverLabel.setPixmap(
            pixmap.scaled(140, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

    def clear_poster(self):
        self.cover_path = None
        self.CoverLabel.clear()
        self.CoverLabel.setText("Постер не выбран")

    def clear_form(self):
        self.title_input.clear()
        self.genre_input.clear()
        self.year_input.clear()
        self.country_input.clear()
        self.director_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.rating_slider.setValue(0)
        self.review_input.clear()
        self.clear_poster()

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
