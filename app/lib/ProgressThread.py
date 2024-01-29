from PyQt5.QtCore import QThread
from qgis.core import Qgis
from qgis.utils import QgsMessageLog

class ProgressThread(QThread):

    def __init__(self, mainView, controller, run, callback=None):
        super().__init__(mainView)     
        self.bar = mainView.progressBar
        self.info = mainView.progressMsg
        self.message = mainView.messageLabel
        self.iface = mainView.iface
        self.refreshTables = mainView.refreshTables
        self.callback = callback

        #show progress bar
        self.bar.show()
        # info and message are not mandatory
        if self.info is not None:
            self.info.show()
        if self.message is not None:
            self.message.show()
        
        #attach worker
        worker = controller
        self.started.connect(run)        
        worker.moveToThread(self)        
        worker.finished.connect(self.threadFinished)        
        worker.error.connect(self.threadError)
        worker.progress.connect(self.bar.setValue)
        if self.info is not None:
            worker.info.connect(self.info.setText)
        if self.message is not None:
            worker.message.connect(self.message.setText)
        self.worker = worker
        self.start()


    def threadFinished(self, response):               
        # clean up the worker and thread
        self.worker.deleteLater()
        self.quit()
        self.wait()
        self.deleteLater()        

        if self.callback:
            return self.callback(response)

        success = response if type(response) == bool else response['success']             
        if success:
            self.bar.hide()
            if self.info is not None:
                self.info.hide()
            if self.message is not None:
                self.message.hide()
            if self.refreshTables is not None:
                self.refreshTables()

            self.iface.messageBar().pushMessage('the process ended successfully!')
            if type(response) != bool and 'message' in response:
                if (response['message'] == True):
                    self.message.show()
        else:
            self.bar.hide()
            #let msg open to display last error
            self.iface.messageBar().pushMessage('Something went wrong! See the message log for more information.', level=Qgis.Critical, duration=3)

    def threadError(self, e, trace):        
        QgsMessageLog.logMessage('ProgressBar thread raised an exception:\n {}'.format(trace), level=Qgis.Critical)         