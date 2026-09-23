import sys
import re
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import QThread, pyqtSignal
from ui_mainwindow import Ui_MainWindow


class DatabaseThread(QThread):
    finished = pyqtSignal()

    def __init__(self, name, height, weight, bmi):
        super().__init__()
        self.name = name
        self.height = height
        self.weight = weight
        self.bmi = bmi

    def run(self):
        conn = sqlite3.connect('bmi_database.db')
        cursor = conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("INSERT INTO records (date, name, height, weight, bmi) VALUES (?, ?, ?, ?, ?)",
                       (date, self.name, self.height, self.weight, self.bmi))
        conn.commit()
        conn.close()
        self.finished.emit()


class BMIApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.TableHistory.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.BtnCalculate.clicked.connect(self.calculate_bmi)
        self.create_database()
        self.load_history()

    def create_database(self):
        conn = sqlite3.connect('bmi_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                name TEXT,
                height REAL,
                weight REAL,
                bmi REAL
            )
        ''')
        conn.commit()
        conn.close()

    def load_history(self):
        conn = sqlite3.connect('bmi_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT date, name, height, weight, bmi FROM records ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        self.TableHistory.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.TableHistory.setItem(i, j, QTableWidgetItem(str(val)))

    def calculate_bmi(self):
        name = self.LineEditName.text().strip()
        height_text = self.LineEditHeight.text().strip()
        weight_text = self.LineEditWeight.text().replace('٫', '.').replace('،', '.').replace('/', '.').strip()

        name_regex = r"^[A-Z][a-z]+$"
        height_regex = r"^[0-9]+$"
        weight_regex = r"^[0-9]+(\.[0-9]+)?$"

        if not re.match(name_regex, name):
            QMessageBox.warning(self, "خطا", "نام باید فقط شامل حروف لاتین باشد و حرف اول آن بزرگ باشد! (مثلاً Ali)")
            return

        if not re.match(height_regex, height_text):
            QMessageBox.warning(self, "خطا", "قد باید یک عدد صحیح باشد! (مثلاً 175)")
            return

        if not re.match(weight_regex, weight_text):
            QMessageBox.warning(self, "خطا", "وزن باید یک عدد اعشاری باشد! (مثلاً 70.5)")
            return

        height = float(height_text) / 100
        weight = float(weight_text)

        bmi = weight / (height ** 2)
        bmi = round(bmi, 2)

        self.thread = DatabaseThread(name, height_text, weight_text, bmi)
        self.thread.finished.connect(lambda: self.show_success(bmi))
        self.thread.start()

    def show_success(self, bmi):
        self.LblBMI.setText(f"BMI: {bmi}")
        QMessageBox.information(self, "موفق", f"اطلاعات با موفقیت ذخیره شد!\nBMI شما: {bmi}")
        self.load_history()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BMIApp()
    window.show()
    sys.exit(app.exec_())
