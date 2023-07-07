from PyQt5.QtWidgets import QDialog, QApplication, QLabel, QVBoxLayout, QPushButton

class GenericWindow(QDialog):
    def __init__(self, message):
        super().__init__()
        self.setWindowTitle("Sanihub")
        
        layout = QVBoxLayout()
        
        self.label = QLabel(message, self)
        layout.addWidget(self.label)
        
        self.button = QPushButton("Aceptar", self)
        self.button.clicked.connect(self.accept)
        layout.addWidget(self.button)
        
        self.setLayout(layout)

    def showWindow(self):
        self.exec_()