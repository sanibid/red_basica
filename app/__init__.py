import sys
import os
from PyQt5.QtCore import QLocale
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from PyQt5.QtWebKitWidgets import *
from PyQt5.QtWidgets import QMainWindow
from .models.Project import Project
from .views.MainView import MainView
from .views.ProjectDialogView import ProjectView
from .views.NewProjectView import NewProjectView
from .views.ParameterView import ParameterView
from .views.EditValuesView import EditValuesView
from .views.IterationsView import IterationsView
from .views.LoginView import LoginView
from .views.ExportLayersView import ExportLayersView
from .views.FlowView import FlowView

class App(QMainWindow):

    def __init__(self):
        super(App, self).__init__()
        self.projectModel = Project()
        self.newProjectDialog = NewProjectView()
        self.projectDialog = ProjectView()
        self.parametersDialog = ParameterView()
        self.editValuesDialog = EditValuesView()
        self.iterationsDialog = IterationsView()
        self.loginDialog = LoginView()
        self.exportDialog = ExportLayersView()
        self.flowDialog = FlowView()

        self.dialogs = {
            'newProject': self.newProjectDialog,
            'project': self.projectDialog,
            'parameters': self.parametersDialog,
            'editValues': self.editValuesDialog,
            'iterations': self.iterationsDialog,
            'login': self.loginDialog,
            'export': self.exportDialog,
            'flow': self.flowDialog
        }

        self.MainView = MainView(self.dialogs)
        self.MainView.setLocale(QLocale(QLocale.English, QLocale.UnitedKingdom))


    if __name__ == '__main__':
        app = App()
        sys.exit(app.exec_())

    def show(self):
        self.MainView.show()
        if not self.projectModel.getActiveProject():
            self.insert_new_project()
        if self.projectModel.getActiveProject():
            self.MainView.setWindowTitle('saniHUB [' + self.projectModel.getNameActiveProject() + ']')

    def runFlow(self):
        self.flowDialog.show()


    def insert_new_project(self):
        self.MainView.openNewProjectDialog()


    def connectLayer(self):
        self.MainView.addLayerConnection()