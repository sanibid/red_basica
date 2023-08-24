from PyQt5.QtWidgets import (
    QMainWindow,
    QAbstractItemView,
    QMessageBox,
    QFileDialog,
    QActionGroup
)
from PyQt5.QtCore import Qt, QCoreApplication, QItemSelectionModel, QItemSelection
from PyQt5 import QtGui, QtWidgets
from qgis.utils import iface, Qgis
from .ui.MainWindowUi import Ui_MainWindow
from ..controllers.CalculationController import CalculationController
from ..controllers.DataController import DataController
from ..controllers.ApiController import ApiController
from ..controllers.XlsController import XlsController
from ..controllers.SwmmController import SwmmController
from ..models.Calculation import Calculation
from ..models.Contribution import Contribution
from ..models.WaterLevelAdj import WaterLevelAdj
from ..models.delegates.CalculationDelegate import (
    CalculationDelegate,
    NumberFormatDelegate,
)
from ..lib.ProgressThread import ProgressThread
from ...base.helper_functions import HelperFunctions

translate = QCoreApplication.translate


class MainView(QMainWindow, Ui_MainWindow):
    def __init__(self, dialogs):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.iface = iface
        self.selected = {}
        self.h = HelperFunctions(iface)

        # Main window
        self._dialogs = dialogs
        self.currentProjectId = self._dialogs["newProject"].model.getActiveId()
        self.calculationController = CalculationController()

        # Hide progress bar
        self.progressBar.hide()
        self.progressMsg.hide()
        self.messageLabel.hide()

        # Models
        self.calcModel = Calculation()
        self.contribModel = Contribution()
        self.wlaModel = WaterLevelAdj()

        action_group = QActionGroup(self)
        action_group.addAction(self.actionBasic)
        action_group.addAction(self.actionDetailed)
        defaultView = self._dialogs["newProject"].model.getDefaultView()
        if (defaultView == True):
            self.actionBasic.setChecked(True)
        else:
            self.actionDetailed.setChecked(True)

        action_group_depth = QActionGroup(self)
        action_group_depth.addAction(self.actionMin_Excav)
        action_group_depth.addAction(self.actionMin_Desnivel)
        actionDepthView = self._dialogs["newProject"].model.getDepthMinView()
        if (actionDepthView == True):
            self.actionMin_Excav.setChecked(True)
        else:
            self.actionMin_Desnivel.setChecked(True)

        # Red Basica Table
        self.calcTable.setModel(self.calcModel)
        self.calcTable.setItemDelegate(CalculationDelegate(self.calcTable))
        self.calcTable.setItemDelegateForColumn(
            self.calcModel.fieldIndex("slopes_min_accepted_col"), NumberFormatDelegate()
        )
        self.calcTable.model().dataChanged.connect(self.onDataChanged)

        # Contributions Table
        self.contribTable.setModel(self.contribModel)
        self.contribTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # WaterLevelAdj Table
        self.wlaTable.setModel(self.wlaModel)
        self.wlaTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Set header titles
        self.set_headers()

        # set filters
        self.set_table_filters()

        # layer features selection
        self.calcTable.verticalHeader().sectionClicked.connect(self.onRowSelected)
        self.addLayerConnection()

        # menu actions
        self.actionProject.triggered.connect(self.checkProjectAction)
        self.actionParameters.triggered.connect(self.openParametersDialog)
        self.actionCalculara_DN.triggered.connect(self.calculateDN)
        self.actionCalcular_DN_Creciente.triggered.connect(self.calculateGrowingDN)
        self.actionMin_Excav.triggered.connect(self.calculateMinExc)
        self.actionMin_Desnivel.triggered.connect(self.calculateMinSlope)
        self.actionAjuste_NA.triggered.connect(self.setIterations)
        self.actionImportFullNetwork.triggered.connect(self.startImport)
        self.actionImportSelectedSegments.triggered.connect(lambda: self.startImport(only_selected_features=True))
        self.actionExportToXls.triggered.connect(self.downloadXls)
        self.actionResetear_Ajuste_NA.triggered.connect(self.resetWaterLevelAdj)
        self.actionReiniciar_DN.triggered.connect(self.clearDiameters)
        self.actionCreateResultsLayer.triggered.connect(self.showCreateLayerDialog)
        self.actionCreateQiSwmmFile.triggered.connect(lambda: self.writeInpFile("q_i"))
        self.actionCreateQfSwmmFile.triggered.connect(lambda: self.writeInpFile("q_f"))
        self.actionPublishProject.triggered.connect(self.showLogin)
        self.actionBasic.triggered.connect(lambda: self.viewSettings(True))
        self.actionDetailed.triggered.connect(lambda: self.viewSettings(False))
        self.actionMin_Excav.triggered.connect(lambda: self.updateDepthMinView(True))
        self.actionMin_Desnivel.triggered.connect(lambda: self.updateDepthMinView(False))

        # triggered actions
        self._dialogs["newProject"].buttonBox.accepted.connect(self.saveNewProject)
        self._dialogs["project"].newProjectButton.clicked.connect(
            self.openNewProjectDialog
        )
        self._dialogs["project"].dialogButtonBox.accepted.connect(self.updateProject)
        self._dialogs["project"].deleteProjectButton.clicked.connect(self.refreshTables)
        self._dialogs["project"].dialogButtonBox.rejected.connect(self.updateMainWindow)
        self._dialogs["parameters"].buttonBox.accepted.connect(self.saveParameters)
        self._dialogs["editValues"].accepted.connect(
            lambda: self.editAction(self._dialogs["editValues"].editValueEdit.value())
        )
        self._dialogs["iterations"].accepted.connect(
            lambda: self.adjustNA(self._dialogs["iterations"].iterationsEdit.value())
        )
        self._dialogs["login"].accepted.connect(
            lambda: self.publish(
                self._dialogs["login"].userText.text(),
                self._dialogs["login"].passText.text(),
            )
        )
        self._dialogs["export"].accepted.connect(self.createResultLayer)

        # Menu / View
        self.viewSettings(defaultView)
        self.refreshMenuStatus()


    def refreshMenuStatus(self):
        """ Enable/Disable menu actions according project values/status """
        enabled = self.currentProjectId is not None
        self.menuImport.setEnabled(enabled)
        self.menuExport.setEnabled(enabled)
        self.menuFunctions.setEnabled(enabled)
        self.actionParameters.setEnabled(enabled)
        depthMinView = self._dialogs["project"].model.getDepthMinView()
        if (depthMinView == True):
            self.actionMin_Excav.setChecked(True)
        else:
            self.actionMin_Desnivel.setChecked(True)

    def set_column_header(self, colName, model, context):
        model.setHeaderData(model.fieldIndex(colName),Qt.Horizontal, translate(context, colName))

    def set_headers(self):
        """ Set table header text and translations """
        
        #calculations
        columns = self.calcModel.getColumns()
        for col in columns:
            self.set_column_header(col, self.calcModel, "CalcTbl")
        hidden = self.calcModel.getHiddenColumns()
        for h in hidden:
            self.calcTable.setColumnHidden(self.calcModel.fieldIndex(h), True)

        # contributions
        columns = self.contribModel.getColumns()
        for col in columns:
            self.set_column_header(col, self.contribModel, "ContTbl")
        hidden = self.contribModel.getHiddenColumns()
        for h in hidden:
            self.contribTable.setColumnHidden(self.contribModel.fieldIndex(h), True)

        # water level adj
        hidden = self.wlaModel.getHiddenColumns()
        for h in hidden:
            self.wlaTable.setColumnHidden(self.wlaModel.fieldIndex(h), True)

    def viewSettings(self, bool):
        """ Toogles table between basic and detailed view """
        self._dialogs["newProject"].model.updateDefaultView(bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("initial_segment"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("final_segment"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("collector_number"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("aux_depth_adjustment"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("covering_up"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("covering_down"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("el_terr_up"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("el_terr_down"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("el_col_up"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("el_col_down"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("el_top_gen_up"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("el_top_gen_down"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("suggested_diameter"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("water_level_y"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("water_level_y_start"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("inspection_id_up"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("inspection_id_down"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("inspection_type_down"), bool)
        self.calcTable.setColumnHidden(self.calcModel.fieldIndex("downstream_seg_id"), bool)

    def updateDepthMinView(self, bool):
        self._dialogs["newProject"].model.updateDepthMinView(bool)

    def updateMainWindow(self):
        """updates main window content"""
        self.changeMainTitle()
        self.currentProjectId = self._dialogs["project"].model.getActiveId()
        self.set_table_filters()
        self.refreshMenuStatus()

    def set_table_filters(self):
        """applies filters to calculations, contributions and wla_adjustments tables"""
        if self.currentProjectId:
            self.calcModel.setFilter("project_id = {}".format(self.currentProjectId))
            self.contribModel.setFilter(
                "calculation_id in (select id from calculations where project_id = {})".format(
                    self.currentProjectId
                )
            )
            self.wlaModel.setFilter(
                "calculation_id in (select id from calculations where project_id = {})".format(
                    self.currentProjectId
                )
            )
        self.refreshTables()

    def newProject(self):
        self.closeProjectDialog()
        self.openNewProjectDialog()

    def saveNewProject(self):
        self.updateMainWindow()
        self.closeProjectDialog()
        self.openParametersDialog()
        self.actionMin_Excav.setChecked(True)
        self.updateDepthMinView(True)

    def updateProject(self):
        self._dialogs["project"].saveRecord()
        self.updateMainWindow()

    def checkProjectAction(self):
        if self._dialogs["project"].model.getActiveProject():
            self.openProjectDialog()
        else:
            self.openNewProjectDialog()

    def openProjectDialog(self):
        self._dialogs["project"].show()

    def closeProjectDialog(self):
        self._dialogs["project"].hide()

    def openNewProjectDialog(self):
        self.closeProjectDialog()
        self._dialogs["newProject"].addRecord()
        self._dialogs["newProject"].show()

    def changeMainTitle(self):
        name = self._dialogs["newProject"].model.getNameActiveProject()
        title = "saniHUB [{}]".format(name) if name is not None else "saniHUB"
        self.setWindowTitle(title)

    def closeNewProjectDialog(self):
        self._dialogs["newProject"].hide()

    def openParametersDialog(self):
        self._dialogs["parameters"].show()

    def closeParametersDialog(self):
        self._dialogs["parameters"].hide()

    def saveParameters(self):
        """action triggered when saving parameters dialog"""
        valid = self._dialogs["parameters"].saveParameters()
        if valid:
            self.closeParametersDialog()
            selected_checkbox = self._dialogs["newProject"].selectedFeaturesOnly.isChecked()
            self._dialogs["newProject"].selectedFeaturesOnly.setChecked(False)
            self.startImport(validate=True, only_selected_features=selected_checkbox)

    def onDataChanged(self, index, index2, roles):
        # this is fired twice and index is the row after database change
        # TODO: find a better way to do this
        val = index.data()
        colName = self.calcModel.record(index.row()).fieldName(index.column())
        if colName == "slopes_min_accepted_col":
            id = self.calcModel.record(index.row()).value("id")
            self.calcModel.updateColById(1, "slopes_min_modified", id)
        if type(val) in [int]:
            row = index.row()
            record = self.calcModel.record(row)
            colSeg = record.value("col_seg")
            controller = CalculationController()
            ProgressThread(
                self,
                controller,
                (lambda: controller.updateVal(self.currentProjectId, colSeg)),
            )

    def onRowSelected(self, logicalIndex):
        """ when user selects row also selects features on map """
        if self.h.GetLayer():
            selectedRows = self.calcTable.selectionModel().selectedRows()
            colsegs = []
            for index in selectedRows:
                row = index.row()
                rec = self.calcModel.record(row)
                colseg = rec.value("col_seg")
                colsegs.append(colseg)
            self.h.selectByColSeg(colsegs)

    def onFeaturesSelected(self):
        """ triggered every time user selects features on the map """
        layer = self.h.GetLayer()
        col = self.h.readValueFromProject("SEG_NAME_C")
        col_index = self.calcModel.fieldIndex("col_seg")
        features = layer.selectedFeatures()
        selection = QItemSelection()
        selection_model = self.calcTable.selectionModel()
        selection_model.clearSelection()
        selected_colsegs = [ f[col] for f in features]
        
        #find matching table rows
        for row in range(self.calcModel.rowCount(self.calcTable.rootIndex())):
            model_index = self.calcModel.index(row, col_index, self.calcTable.rootIndex())
            model_data = model_index.data()
            if(model_data in selected_colsegs):
                selection.select(model_index, model_index)
        
        # Apply the selection, using the row-wise mode.
        mode = QItemSelectionModel.Select | QItemSelectionModel.Rows
        selection_model.select(selection, mode) 

    def addLayerConnection(self):
        """ adds connection to highlight table on feature selecction """
        if self.h.GetLayer():
            self.h.GetLayer().selectionChanged.connect( self.onFeaturesSelected )  

    def refreshTables(self):
        """Refresh table views, its called from ProgressThread instances"""
        self.calcModel.select()
        while self.calcModel.canFetchMore():
            self.calcModel.fetchMore()
        
        self.contribModel.select()
        while self.contribModel.canFetchMore():
            self.contribModel.fetchMore()
        
        self.wlaModel.select()
        while self.wlaModel.canFetchMore():
            self.wlaModel.fetchMore()
        naDiff = None if self.wlaModel.getMaxNaDiffNeeded() == None else str(round(self.wlaModel.getMaxNaDiffNeeded(), 2))
        self.maxNaLabel.setText(naDiff)

    def startImport(self, validate=False, only_selected_features=False):
        checked = validate and self._dialogs["parameters"].is_valid_form()
        if not validate or checked:
            has_records = self.calcModel.rowCount() > 0
            if has_records > 0:
                if (
                    QMessageBox.question(
                        self,
                        "Import Data",
                        translate("CalcTbl", "This action will replace loaded and calculated data, do you want to continue?"),
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    == QMessageBox.No
                ):
                    self.progressBar.hide()
                    self.progressMsg.setText("Data import aborted by user")
                    return
            self.closeParametersDialog()
            checksCtrl = DataController()
            ProgressThread(
                self, 
                checksCtrl, 
                (lambda : checksCtrl.runVerifications(only_selected_features)), 
                callback=self.uploadData
            )
            self.actionMin_Excav.setChecked(True)
            self.updateDepthMinView(True)

    def uploadData(self, verifications):
        projectId = self._dialogs["newProject"].model.getActiveId()
        controller = CalculationController(projectId)
        only_selected_features = verifications["only_selected_features"]

        if verifications["success"]:
            ProgressThread(
                self, 
                controller, 
                (lambda : controller.importData(only_selected_features))
            )
        else:
            if verifications["fix"]:
                if (
                    QMessageBox.question(
                        self,
                        "Fix Segments",
                        "some segments dont have previous segment and are neither beginning nor ending , do you want automatic correction?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    == QMessageBox.No
                ):
                    self.progressBar.hide()
                    self.progressMsg.setText(
                        "Process aborted by user, fix errors and try again later"
                    )
                    return
                ProgressThread(
                    self, 
                    controller, 
                    (lambda : controller.importData(only_selected_features))
                )
            else:
                self.progressBar.hide()
                self.progressMsg.setText(verifications["info"])
                self.iface.messageBar().pushMessage(
                    verifications["info"], level=Qgis.Critical, duration=3
                )

    def calculateDN(self):
        projectId = self._dialogs["newProject"].model.getActiveId()
        controller = CalculationController()
        ProgressThread(self, controller, (lambda: controller.calculateDN(projectId)))

    def calculateGrowingDN(self):
        projectId = self._dialogs["newProject"].model.getActiveId()
        controller = CalculationController()
        ProgressThread(
            self, controller, (lambda: controller.calculateGrowDN(projectId))
        )

    def calculateMinExc(self):
        projectId = self._dialogs["newProject"].model.getActiveId()
        controller = CalculationController()
        ProgressThread(
            self, controller, (lambda: controller.calculateMinExc(projectId))
        )

    def calculateMinSlope(self):
        projectId = self._dialogs["newProject"].model.getActiveId()
        controller = CalculationController()
        ProgressThread(
            self, controller, (lambda: controller.calculateMinSlope(projectId))
        )

    def setIterations(self):
        iterationsDialog = self._dialogs["iterations"]
        iterationsDialog.show()
        iterationsDialog.iterationsEdit.setValue(12)

    def adjustNA(self, iteration):
        projectId = self._dialogs["newProject"].model.getActiveId()
        controller = CalculationController()
        ProgressThread(
            self, controller, (lambda: controller.adjustNA(projectId, iteration))
        )

    def contextMenuEvent(self, pos):
        if self.calcTable.selectionModel().selection().indexes():
            selected = {}
            for i in self.calcTable.selectionModel().selection().indexes():
                if i.column() not in selected:
                    selected[i.column()] = []
                selected[i.column()].append(i.row())
            self.menu = QtWidgets.QMenu()
            self.selected = selected
            editValuesAction = QtWidgets.QAction(translate("CalcTbl", "Edit Values"), self)
            editValuesAction.triggered.connect(
                lambda: self.editValuesAction(self.selected)
            )
            deleteAction = QtWidgets.QAction(translate("CalcTbl", "Delete Values"), self)
            deleteAction.triggered.connect(lambda: self.deleteAction(self.selected))
            self.menu.addAction(editValuesAction)
            self.menu.addAction(deleteAction)
            self.menu.popup(QtGui.QCursor.pos())

    def editValuesAction(self, selected):
        editDialog = self._dialogs["editValues"]
        editDialog.show()
        editDialog.editValueEdit.setValue(0)

    def editAction(self, value):
        selected = self.selected
        column = next(iter(selected))
        calcModel = self.calcModel
        colSegs = []
        oldColNumber = None
        for item in selected.values():
            for row in item:
                index = calcModel.index(row, column)
                colName = calcModel.record(row).fieldName(column)
                id = calcModel.record(row).value("id")
                collectorNumber = calcModel.record(row).value("collector_number")
                if collectorNumber != oldColNumber:
                    colSegs.append(calcModel.record(row).value("col_seg"))
                calcModel.updateColById(value, colName, id)
                if colName == "slopes_min_accepted_col":
                    calcModel.updateColById(1, "slopes_min_modified", id)
                oldColNumber = collectorNumber
        self.calcModel.select()
        controller = CalculationController()
        ProgressThread(
            self,
            controller,
            (lambda: controller.updateValues(self.currentProjectId, colSegs)),
        )

    def deleteAction(self, selected):
        column = next(iter(selected))
        calcModel = self.calcModel
        colSegs = []
        oldColNumber = None
        for item in selected.values():
            for row in item:
                index = calcModel.index(row, column)
                colName = calcModel.record(row).fieldName(column)
                id = calcModel.record(row).value("id")
                collectorNumber = calcModel.record(row).value("collector_number")
                if collectorNumber != oldColNumber:
                    colSegs.append(calcModel.record(row).value("col_seg"))
                calcModel.updateColById(None, colName, id)
                if colName == "slopes_min_accepted_col":
                    calcModel.updateColById(None, "slopes_min_modified", id)
                oldColNumber = collectorNumber
        self.calcModel.select()
        controller = CalculationController()
        ProgressThread(
            self,
            controller,
            (lambda: controller.updateValues(self.currentProjectId, colSegs)),
        )

    def downloadXls(self):
        controller = XlsController()
        output = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "{}.xls".format(self.windowTitle()),
            "Excel 97-2003 (*.xls)",
        )
        if output:
            controller.createFile(output[0])

    def resetWaterLevelAdj(self):
        controller = CalculationController()
        ProgressThread(
            self,
            controller,
            (lambda: controller.resetWaterLevel(self.currentProjectId)),
        )

    def clearDiameters(self):
        controller = CalculationController()
        ProgressThread(
            self, controller, (lambda: controller.clearDiameters(self.currentProjectId))
        )

    def createResultLayer(self):
        """Merge data from calculations to layer"""
        seg_layer = self.h.GetLayer()
        node_layer = self.h.GetNodeLayer()

        override = self._dialogs["export"].overrideRadioButton.isChecked()
        if seg_layer and node_layer:
            data = CalculationController().exportData(self.currentProjectId)
            if data:
                controller = DataController()
                nodes_layername = self._dialogs["export"].nodesEdit.text()
                segments_layername = self._dialogs["export"].segmentsEdit.text()
                ProgressThread(
                    self,
                    controller,
                    (
                        lambda: controller.writeToLayers(
                            data,
                            override=override,
                            nodes_layername=nodes_layername,
                            segments_layername=segments_layername,
                        )
                    ),
                )
            else:
                self.iface.messageBar().pushMessage(
                    "No data to import", level=Qgis.Info, duration=3
                )
        else:
            self.iface.messageBar().pushMessage(
                "Node layer not found", level=Qgis.Critical, duration=3
            )

    def writeInpFile(self, flowType):
        """Write INP file"""

        if flowType in ["q_i", "q_f"]:
            project = self._dialogs["newProject"].model.getNameActiveProject()
            f, __ = QFileDialog.getSaveFileName(
                self,
                "INP file",
                "{}_{}_{}.inp".format(
                    "saniHUB", project, "QI" if flowType == "q_i" else "QF"
                ),
                "EPANET INP file (*.inp)",
            )

            if 0 < len(f):
                writer = SwmmController(self.iface, self.currentProjectId, flowType)
                try:
                    writer.writeInp(f)
                except Exception as e:
                    print("Saving INP file failed: " + str(e))
                    return False
                return True
            return False
        else:
            self.iface.messageBar().pushMessage(
                "Export Error: Invalid flowType value {}".format(flowType),
                level=Qgis.Critical,
                duration=3,
            )
        return False

    def showLogin(self):
        loginDialog = self._dialogs["login"]
        loginDialog.show()
        loginDialog.passText.setText("")

    def publish(self, user, password):
        if user != "" and password != "":
            projectId = self._dialogs["newProject"].model.getActiveId()
            controller = ApiController()
            ProgressThread(
                self,
                controller,
                (lambda: controller.publishProject(projectId, user, password)),
            )
        else:
            self.showLogin()

    def showCreateLayerDialog(self):
        dg = self._dialogs["export"]
        seg_layer = self.h.GetLayer()
        node_layer = self.h.GetNodeLayer()

        dg.nodesEdit.setText("{}_copy".format(node_layer.name()))
        dg.segmentsEdit.setText("{}_copy".format(seg_layer.name()))
        dg.show()
