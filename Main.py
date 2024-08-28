import sys
import os
import sqlite3
from datetime import date, datetime, timedelta
from win10toast import ToastNotifier
import hashlib
import pygame

from PyQt5.QtCore import QThread, Qt
from PyQt5.QtWidgets import (QApplication, QDialog, QPushButton, QVBoxLayout, QLineEdit, QComboBox, QMessageBox,
                             QTableWidget, QTableWidgetItem, QMainWindow, QToolBar, QStatusBar, QAction, QHeaderView, QLabel,
                             QDialogButtonBox, QHBoxLayout)

from PyQt5.QtGui import QIntValidator, QIcon, QPixmap, QFont


# Utility function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Utility function to check hashed passwords
def check_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)


# Background thread to check for expiring products
class WorkerThread(QThread):
    def run(self):
        try:
            self.conn = sqlite3.connect("database.db")
            self.c = self.conn.cursor()
            result = self.c.execute("SELECT date FROM products")
            row = result.fetchall()
            result2 = self.c.execute("SELECT name FROM products")
            row2 = result2.fetchall()

            today = date.today()
            exp_window = (today + timedelta(minutes=10))
            namelist = ["".join(i) for i in row2]

            for i, y in enumerate("".join(i) for i in row):
                x = datetime.strptime(y, '%d-%m-%Y')
                if int(y[6:]) > int(exp_window.strftime('%Y')) or int(y[3:5]) < int(exp_window.strftime('%m')):
                    continue
                elif int(y[0:2]) <= int(exp_window.strftime('%d')):
                    notifier = ToastNotifier()
                    notifier.show_toast('Alarm', f"Some Products are Near Expiry: {namelist[i]}", 
                                        icon_path="icon/notification-icon-bell-alarm2.ico", duration=5)
                    

            self.conn.commit()
            self.c.close()
            self.conn.close()
        except Exception as e:
            print("Error with notification:", e)


class InsertDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Add New Product")
        self.setFixedSize(600, 600)
        self.setStyleSheet("""
            QDialog { background-color: darkgreen; color: white; }
            QLabel { font-size: 16px; margin-bottom: 0px; color: white; font-weight: bold }
            QLineEdit, QComboBox { 
                background-color: white; 
                color: black; 
                border-radius: 25px;
                padding: 20px 10px;
            }
            QPushButton { 
                background-color: orange; 
                color: white; 
                border-radius: 25px; 
                padding: 15px 25px; 
            }
            QPushButton:hover { 
                background-color: darkorange; 
            }
        """)


        self.QBtn = QPushButton("Register")
        self.QBtn.clicked.connect(self.add_product)

        layout = QVBoxLayout()
        self.nameinput = QLineEdit()
        
        self.name_label = QLabel("Product Name")
        layout.addWidget(self.name_label)
        
        self.nameinput.setPlaceholderText("Product Name")
        layout.addWidget(self.nameinput)
        
        self.branch_label = QLabel("Category")
        layout.addWidget(self.branch_label)

        self.branchinput = QComboBox()
        self.branchinput.addItems([
            "Beverage", "Soft-Drink", "Cosmetics", "Detergents",
            "Fruits", "Water", "Antiseptic", "Alcoholic-Drink",
            "Medical", "Chocolate", "Tooth-Paste", "Toiletries",
            "Pastries"
        ])
        layout.addWidget(self.branchinput)
        
        self.sem_label = QLabel("Quantity")
        layout.addWidget(self.sem_label)

        self.seminput = QComboBox()
        self.seminput.addItems([str(i) for i in range(1, 13)])
        layout.addWidget(self.seminput)
        
        self.date_label = QLabel("Expiry Date")
        layout.addWidget(self.date_label)

        self.dateinput = QLineEdit()
        self.dateinput.setPlaceholderText("Expiry Date (dd-mm-yy)")
        layout.addWidget(self.dateinput)
        
        self.description_label = QLabel("Description")
        layout.addWidget(self.description_label)

        self.descriptioninput = QLineEdit()
        self.descriptioninput.setPlaceholderText("Description")
        layout.addWidget(self.descriptioninput)

        layout.addWidget(self.QBtn)
        self.setLayout(layout)

    def add_product(self):
        name = ""
        branch = ""
        sem = -1
        date = ""
        description = ""
        
        name = self.nameinput.text()
        branch = self.branchinput.itemText(self.branchinput.currentIndex())
        sem = self.seminput.itemText(self.seminput.currentIndex())
        date = self.dateinput.text()
        description = self.descriptioninput.text()

        try:
            self.conn = sqlite3.connect("database.db")
            self.c = self.conn.cursor()
            self.c.execute("INSERT INTO products (name, branch, sem, date, description) VALUES (?, ?, ?, ?, ?)",
                           (name, branch, sem, date, description))
            self.conn.commit()
            self.c.close()
            self.conn.close()
            QMessageBox.information(self, 'Successful', 'Product is added successfully to the database.')
            self.close()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not add Product to the database: {e}')


class SearchDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Search Product")
        self.setFixedSize(600, 400) 
        self.setStyleSheet("""
            QDialog { background-color: darkgreen; color: white; }
            QLabel { font-size: 16px; margin-bottom: 0px; color: white; font-weight: bold }
            QLineEdit, QComboBox { 
                background-color: white; 
                color: black; 
                border-radius: 25px;
                padding: 20px 10px;
            }
            QPushButton { 
                background-color: orange; 
                color: white; 
                border-radius: 25px; 
                padding: 15px 25px; 
            }
            QPushButton:hover { 
                background-color: darkorange; 
            }
        """)

        self.QBtn = QPushButton("Search")
        self.QBtn.clicked.connect(self.search_product)

        layout = QVBoxLayout()
        self.searchinput = QLineEdit()
        self.searchinput.setValidator(QIntValidator())
        self.searchinput.setPlaceholderText("Roll No.")
        layout.addWidget(self.searchinput)
        layout.addWidget(self.QBtn)
        self.setLayout(layout)

    def search_product(self):
        searchrol = self.searchinput.text()
        try:
            self.conn = sqlite3.connect("database.db")
            self.c = self.conn.cursor()
            result = self.c.execute("SELECT * FROM products WHERE roll=?", (searchrol,))
            row = result.fetchone()
            if row:
                search_result = f"Roll No.: {row[0]}\nName: {row[1]}\nGroup: {row[2]}\nQuantity: {row[3]}\nExpiry Date: {row[4]}"
                QMessageBox.information(self, 'Successful', search_result)
            else:
                QMessageBox.warning(self, 'Error', 'Product not found.')
            self.conn.commit()
            self.c.close()
            self.conn.close()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not find Product from the database: {e}')


class DeleteDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Delete Product")
        self.setFixedSize(600, 400)  
        self.setStyleSheet("""
            QDialog { background-color: darkgreen; color: white; }
            QLabel { font-size: 16px; margin-bottom: 0px; color: white; font-weight: bold }
            QLineEdit, QComboBox { 
                background-color: white; 
                color: black; 
                border-radius: 25px;
                padding: 20px 10px;
            }
            QPushButton { 
                background-color: orange; 
                color: white; 
                border-radius: 25px; 
                padding: 15px 25px; 
            }
            QPushButton:hover { 
                background-color: darkorange; 
            }
        """)


        self.QBtn = QPushButton("Delete")
        self.QBtn.clicked.connect(self.delete_product)

        layout = QVBoxLayout()
        self.deleteinput = QLineEdit()
        self.deleteinput.setValidator(QIntValidator())
        self.deleteinput.setPlaceholderText("Roll No.")
        layout.addWidget(self.deleteinput)
        layout.addWidget(self.QBtn)
        self.setLayout(layout)

    def delete_product(self):
        delrol = self.deleteinput.text()
        try:
            self.conn = sqlite3.connect("database.db")
            self.c = self.conn.cursor()
            self.c.execute("DELETE FROM products WHERE roll=?", (delrol,))
            self.conn.commit()
            self.c.close()
            self.conn.close()
            QMessageBox.information(self, 'Successful', 'Deleted from table successfully')
            self.close()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not delete Product from the database: {e}')
            
    
class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)

        self.setFixedWidth(500)
        self.setFixedHeight(250)

        QBtn = QDialogButtonBox.Ok  
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        
        self.setWindowTitle("About")
        title = QLabel("Product Expiry Alert System")
        font = title.font()
        font.setPointSize(20)
        title.setFont(font)

        labelpic = QLabel()
        pixmap = QPixmap('')
        pixmap = pixmap.scaledToWidth(275)
        labelpic.setPixmap(pixmap)
        labelpic.setFixedHeight(150)

        layout.addWidget(title)

        layout.addWidget(QLabel("v1.0"))
        layout.addWidget(QLabel("Copyright Devintel 2024"))
        layout.addWidget(labelpic)


        layout.addWidget(self.buttonBox)

        self.setLayout(layout)


# Dialog to register a new user
class RegisterDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Create Account")
        self.setFixedSize(600, 600)

        layout = QVBoxLayout()

        # Fullname label and input field
        self.fullname_label = QLabel("Fullname")
        layout.addWidget(self.fullname_label)

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Full Name")
        layout.addWidget(self.fullname_input)

        # Username label and input field
        self.username_label = QLabel("Username")
        layout.addWidget(self.username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a Username")
        layout.addWidget(self.username_input)

        # Email label and input field
        self.email_label = QLabel("Email")
        layout.addWidget(self.email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        # Password label and input field
        self.password_label = QLabel("Password")
        layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.register_button = QPushButton("Create Account")
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)
        
        # Link to Login
        login_link = QLabel(self)
        login_link.setText('<a href="#" style="color: white; text-decoration: none;">Already have an account? Login</a>')
        login_link.setAlignment(Qt.AlignCenter)
        login_link.setOpenExternalLinks(False)
        login_link.linkActivated.connect(self.switch_to_login)
        layout.addWidget(login_link)
        
        layout.setSpacing(15)  # Increased spacing between login button and the link

        self.setLayout(layout)

    def register_user(self):
        fullname = self.fullname_input.text()
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()

        if not fullname or not username or not email or not password:
            QMessageBox.warning(self, 'Error', 'All fields are required!')
            return

        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (full_name, username, email, password) VALUES (?, ?, ?, ?)",
                      (fullname, username, email, hash_password(password)))
            conn.commit()
            c.close()
            conn.close()
            QMessageBox.information(self, 'Success', 'Account created successfully!')
            self.accept()  # Close the dialog
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, 'Error', 'Username already exists!')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not create account: {e}')
            
    def switch_to_login(self):
        self.close()  # Close the registration dialog
        self.login_dialog = LoginDialog()
        self.login_dialog.exec_()


# Dialog to log in an existing user
class LoginDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Login")
        self.setFixedSize(600, 400)  
        self.setStyleSheet("""
            QDialog { background-color: darkgreen; color: white; }
            QLabel { font-size: 16px; margin-bottom: 0px; color: white; font-weight: bold }
            QLineEdit, QComboBox { 
                background-color: white; 
                color: black; 
                border-radius: 25px;
                padding: 20px 10px;
            }
            QPushButton { 
                background-color: orange; 
                color: white; 
                border-radius: 25px; 
                padding: 15px 25px; 
            }
            QPushButton:hover { 
                background-color: darkorange; 
            }
            QLabel[link=true] { color: black; text-decoration: none; } 
        """)


        layout = QVBoxLayout()

        # Username label and input field
        self.username_label = QLabel("Username")
        layout.addWidget(self.username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        # Password label and input field
        self.password_label = QLabel("Password")
        layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.check_login)
        layout.addWidget(self.login_button)

        # Add a "Create Account" link
        self.create_account_button = QPushButton("Create Account")
        self.create_account_button.setStyleSheet("{ text-align: left; border: none; color: black; text-decoration: none; background-color: none; }")
        self.create_account_button.clicked.connect(self.open_register_dialog)
        layout.addWidget(self.create_account_button)
        
        layout.setSpacing(15)  # Increased spacing between login button and the link

        self.setLayout(layout)

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = c.fetchone()
            conn.close()

            if result and check_password(result[0], password):
                QMessageBox.information(self, 'Success', 'Login successful')
                self.accept()  # Close the dialog and proceed to the dashboard
            else:
                QMessageBox.warning(self, 'Error', 'Invalid username or password')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not verify login: {e}')

    def open_register_dialog(self):
        register_dialog = RegisterDialog(self)
        if register_dialog.exec_() == QDialog.Accepted:
            # If registration was successful, log the user in
            self.username_input.setText(register_dialog.username_input.text())
            self.password_input.setText(register_dialog.password_input.text())
            QMessageBox.information(self, 'Success', 'You can now log in with your new account.')
            # self.check_login()

# Main application window
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PRODUCT EXPIRY ALERT SYSTEM")
        self.setWindowIcon(QIcon('icon/notification-icon-bell-alarm2.ico'))
        self.setFixedSize(1320, 740)
        self.setStyleSheet("""
            QMainWindow { background-color: darkgreen; color: white; }
            QToolBar { background-color: lightgreen; color: black; }
            QStatusBar { background-color: lightgreen; color: black; }
            QTableWidget { background-color: white; color: black; border-radius: 5px; }
            QPushButton { background-color: orange; color: white; border-radius: 10px; padding: 5px 20px; }
            QPushButton:hover { background-color: darkorange; }
        """)
        
        # Ensure the users table is created
        self.create_tables()

        self.initUI()

    def create_tables(self):
        try:
            self.conn = sqlite3.connect("database.db")
            self.c = self.conn.cursor()

            # Create the 'students' table if it doesn't exist
            self.c.execute(
                "CREATE TABLE IF NOT EXISTS products (roll INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, branch TEXT, sem TEXT, date TEXT, description TEXT)")

            # Create the 'users' table if it doesn't exist
            self.c.execute(
                "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, username TEXT UNIQUE, email TEXT, password TEXT)")

            # Commit the changes and close the connection
            self.conn.commit()
            self.c.close()
            self.conn.close()
        except Exception as e:
            print(f"An error occurred: {e}")

    def initUI(self):
        self.tableWidget = QTableWidget()
        self.setCentralWidget(self.tableWidget)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
        self.tableWidget.verticalHeader().setStretchLastSection(False)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setHorizontalHeaderLabels(("Product Name", "Group", "Quantity", "Expiry Date", "Remark"))

        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        file_menu = self.menuBar().addMenu("&File")

        help_menu = self.menuBar().addMenu("&About")

        btn_ac_adduser = QAction(QIcon("icon/addicon.png"), "Add New Product", self)
        btn_ac_adduser.triggered.connect(self.insert)
        btn_ac_adduser.setStatusTip("Add New Product")
        toolbar.addAction(btn_ac_adduser)

        btn_ac_refresh = QAction(QIcon("icon/r3.png"), "Refresh", self)
        btn_ac_refresh.triggered.connect(self.loaddata)
        btn_ac_refresh.setStatusTip("Refresh Table")
        toolbar.addAction(btn_ac_refresh)
        
        btn_ac_search = QAction(QIcon("icon/s1.png"), "Search", self)  #search icon
        btn_ac_search.triggered.connect(self.search)
        btn_ac_search.setStatusTip("Search Product")
        toolbar.addAction(btn_ac_search)
        
        btn_ac_delete = QAction(QIcon("icon/d1.png"), "Delete", self)
        btn_ac_delete.triggered.connect(self.delete)
        btn_ac_delete.setStatusTip("Delete Product")
        toolbar.addAction(btn_ac_delete)
        
        adduser_action = QAction(QIcon("icon/add-product.png"),"Insert New Product", self)
        adduser_action.triggered.connect(self.insert)
        file_menu.addAction(adduser_action)

        searchuser_action = QAction(QIcon("icon/s1.png"), "Search Product", self)
        searchuser_action.triggered.connect(self.search)
        file_menu.addAction(searchuser_action)

        deluser_action = QAction(QIcon("icon/d1.png"), "Delete", self)
        deluser_action.triggered.connect(self.delete)
        file_menu.addAction(deluser_action)

        about_action = QAction(QIcon("icon/i1.png"),"Developer", self)  #info icon
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)


        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.loaddata() 

    def loaddata(self):
        self.connection = sqlite3.connect("database.db")
        query = "SELECT * FROM products"
        result = self.connection.execute(query)
        self.tableWidget.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.tableWidget.insertRow(row_number)
            for column_number, data in enumerate(row_data[1:]):  # Exclude the first column (roll)
                self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        self.connection.close()
        
    
    def handlePaintRequest(self, printer):
        document = QTextDocument()
        cursor = QTextCursor(document)
        model = self.table.model()
        table = cursor.insertTable(
            model.rowCount(), model.columnCount())
        for row in range(table.rows()):
            for column in range(table.columns()):
                cursor.insertText(model.item(row, column).text())
                cursor.movePosition(QTextCursor.NextCell)
        document.print_(printer)
        

    def insert(self):
        dlg = InsertDialog(self)
        dlg.exec()
        
    def delete(self):
        dlg = DeleteDialog()
        dlg.exec_()

    def search(self):
        dlg = SearchDialog()
        dlg.exec_()
    
    def delete_all(self):
        confirmation = QMessageBox.question(self, "Confirmation", "Are you sure you want to delete all records?", 
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if confirmation == QMessageBox.Yes:
            try:
                self.conn = sqlite3.connect("database.db")
                self.conn.execute("DELETE FROM products")
                self.conn.commit()
                self.conn.close()
                self.load_data()
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not delete data: {e}')
                
    def about(self):
        dlg = AboutDialog()
        dlg.exec_()



# Main application entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Create the main window
    window = MainWindow()
    
    #  Ensure tables are created before showing the login dialog
    # window.create_tables()
    
    # Show the login dialog first
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        worker = WorkerThread()
        worker.start()
        window.loaddata()
        sys.exit(app.exec())