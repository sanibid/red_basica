from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QCoreApplication
from time import sleep
translate = QCoreApplication.translate

class FlowController(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    info = pyqtSignal(str)
    message = pyqtSignal(str)

    def __init__(self, model=None):
        super().__init__()        

    def run(self):
        """ publish project to saniHUB dashboard """
        success = False       
        self.progress.emit(25)
        sleep(2)
        ok = True
        
        if ok:
            self.progress.emit(50)
            sleep(3)
            self.progress.emit(100)
            success = True       
        else:
            success = False

        self.finished.emit(success)
        return True