from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDataWidgetMapper,
    QDialog,
    QMessageBox,
    QErrorMessage,
    QTreeWidgetItem
)
from PyQt5.QtSql import (
    QSqlRelation,
    QSqlRelationalTableModel,
    QSqlTableModel,
    QSqlRelationalDelegate,
)
from PyQt5.QtCore import QDateTime
from PyQt5.QtCore import QLocale

from ..models.Parameter import Parameter
from ..models.Project import Project
from ..models.Criteria import Criteria
from ..models.Pipe import Pipe
from ..models.InspectionDevice import InspectionDevice
from .ui.ParameterDialogUi import Ui_NewParameterDialog
from ..models.delegates.PipesDelegate import PipesDecimalsDelegate
from ..views.GenericWindow import GenericWindow


class ParameterView(QDialog, Ui_NewParameterDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        locale = QLocale(QLocale.English, QLocale.UnitedStates)
        self.setLocale(locale)
        self.error_dialog = QErrorMessage()
        self.parameterId = None
        self.profileIsEditable = False

        # ParameterModel
        self.parameterModel = QSqlRelationalTableModel(self.profileComboBox)
        self.parameterModel.setTable("parameters")

        criteria_idx = self.parameterModel.fieldIndex("project_criteria_id")
        self.parameterModel.setRelation(
            criteria_idx, QSqlRelation("project_criterias", "id", "name")
        )

        if not self.parameterModel.select():
            print(self.parameterModel.lastError().text())

        # Tab1
        self.profileComboBox.setModel(self.parameterModel.relationModel(criteria_idx))
        self.profileComboBox.setModelColumn(
            self.parameterModel.relationModel(criteria_idx).fieldIndex("name")
        )
        self.puntualContributionradioButton.setChecked(
            not self.linearContributionradioButton.isChecked()
        )
        self.sewerContributionRateStartEdit.setReadOnly(True)
        self.sewerContributionRateEndEdit.setReadOnly(True)

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.parameterModel)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)
        self.mapper.addMapping(
            self.beginningPopulationEdit,
            self.parameterModel.fieldIndex("beginning_population"),
        )
        self.mapper.addMapping(
            self.finalPopulationEdit, self.parameterModel.fieldIndex("final_population")
        )
        self.mapper.addMapping(
            self.occupancyRateStartEdit,
            self.parameterModel.fieldIndex("occupancy_rate_start"),
        )
        self.mapper.addMapping(
            self.occupancyRateEndEdit,
            self.parameterModel.fieldIndex("occupancy_rate_end"),
        )
        self.mapper.addMapping(
            self.residencesStartEdit, self.parameterModel.fieldIndex("residences_start")
        )
        self.mapper.addMapping(
            self.residencesEndEdit, self.parameterModel.fieldIndex("residences_end")
        )
        self.mapper.addMapping(
            self.hhConnStartEdit, self.parameterModel.fieldIndex("households_conn_start")
        )
        self.mapper.addMapping(
            self.hhConnEndEdit, self.parameterModel.fieldIndex("households_conn_end")
        )
        self.mapper.addMapping(
            self.connectionsStartEdit,
            self.parameterModel.fieldIndex("connections_start"),
        )
        self.mapper.addMapping(
            self.connectionsEndEdit, self.parameterModel.fieldIndex("connections_end")
        )
        self.mapper.addMapping(
            self.pointFlowsStartEdit,
            self.parameterModel.fieldIndex("point_flows_start"),
        )
        self.mapper.addMapping(
            self.pointFlowsEndEdit, self.parameterModel.fieldIndex("point_flows_end")
        )
        self.mapper.addMapping(
            self.qeReferenceMedEdit, self.parameterModel.fieldIndex("qe_reference_med")
        )
        self.mapper.addMapping(
            self.qeReferenceMaxEdit, self.parameterModel.fieldIndex("qe_reference_max")
        )
        self.mapper.addMapping(
            self.linearContributionradioButton,
            self.parameterModel.fieldIndex("contribution_sewage"),
        )
        self.mapper.addMapping(
            self.sewerContributionRateStartEdit,
            self.parameterModel.fieldIndex("sewer_contribution_rate_start"),
        )
        self.mapper.addMapping(
            self.sewerContributionRateEndEdit,
            self.parameterModel.fieldIndex("sewer_contribution_rate_end"),
        )
        self.mapper.addMapping(self.profileComboBox, criteria_idx)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self.profileComboBox))

        # Tab2
        # Criterias
        self.currentCriteriaIndex = None
        self.currentCriteriaId = 1
        self.mapper_project_criterias = QDataWidgetMapper(self)
        self.criteriaModel = Criteria()
        self.mapper_project_criterias.setModel(self.criteriaModel)

        self.mapper_project_criterias.addMapping(
            self.profileName, self.criteriaModel.fieldIndex("name")
        )
        self.mapper_project_criterias.addMapping(
            self.waterConsumptionPcSpinBox,
            self.criteriaModel.fieldIndex("water_consumption_pc"),
        )
        self.mapper_project_criterias.addMapping(
            self.k1DailySpinBox, self.criteriaModel.fieldIndex("k1_daily")
        )
        self.mapper_project_criterias.addMapping(
            self.k2HourlySpinBox, self.criteriaModel.fieldIndex("k2_hourly")
        )
        self.mapper_project_criterias.addMapping(
            self.coefficientReturnCSpinBox,
            self.criteriaModel.fieldIndex("coefficient_return_c"),
        )
        self.mapper_project_criterias.addMapping(
            self.intakeRateSpinBox, self.criteriaModel.fieldIndex("intake_rate")
        )
        self.mapper_project_criterias.addMapping(
            self.avgTractiveForceSpinBox,
            self.criteriaModel.fieldIndex("avg_tractive_force_min"),
        )
        self.mapper_project_criterias.addMapping(
            self.flowMinQminSpinBox, self.criteriaModel.fieldIndex("flow_min_qmin")
        )
        self.mapper_project_criterias.addMapping(
            self.waterSurfaceMaxSpinBox,
            self.criteriaModel.fieldIndex("water_surface_max"),
        )
        self.mapper_project_criterias.addMapping(
            self.maxWaterLevelSpinBox, self.criteriaModel.fieldIndex("max_water_level")
        )
        self.mapper_project_criterias.addMapping(
            self.minDiameterLineEdit, self.criteriaModel.fieldIndex("min_diameter")
        )
        self.mapper_project_criterias.addMapping(
            self.diameterUp150SpinBox, self.criteriaModel.fieldIndex("diameter_up_150")
        )
        self.mapper_project_criterias.addMapping(
            self.diameterUp200SpinBox, self.criteriaModel.fieldIndex("diameter_up_200")
        )
        self.mapper_project_criterias.addMapping(
            self.diameterUp250SpinBox,
            self.criteriaModel.fieldIndex("from_diameter_250"),
        )
        self.mapper_project_criterias.addMapping(
            self.coverMinStreetSpinBox,
            self.criteriaModel.fieldIndex("cover_min_street"),
        )
        self.mapper_project_criterias.addMapping(
            self.coverMinSidewalksGsSpinBox,
            self.criteriaModel.fieldIndex("cover_min_sidewalks_gs"),
        )
        self.mapper_project_criterias.addMapping(
            self.typePreferredHeadColSpinBox,
            self.criteriaModel.fieldIndex("type_preferred_head_col"),
        )
        self.mapper_project_criterias.addMapping(
            self.simplifiedTLInitialSegComboBox,
            self.criteriaModel.fieldIndex("simplified_tl_seg"),
        )
        self.mapper_project_criterias.addMapping(
            self.maxDropSpinBox, self.criteriaModel.fieldIndex("max_drop")
        )
        self.mapper_project_criterias.addMapping(
            self.bottomIbMhSpinBox, self.criteriaModel.fieldIndex("bottom_ib_mh")
        )
        self.mapper_project_criterias.addMapping(
            self.minStepIbMhSpinBox, self.criteriaModel.fieldIndex("min_step_ib_mh")
        )

        # Pipes
        self.pipeModel = Pipe()
        self.pipeModel.setRelation(
            self.pipeModel.fieldIndex("material_id"),
            QSqlRelation("materials", "id", "name_es"),
        )
        self.pipesTable.setModel(self.pipeModel)
        self.pipesTable.setItemDelegate(QSqlRelationalDelegate(self.pipesTable))
        # Custom delegates to avoid comma issues
        numericFormatDelegate = PipesDecimalsDelegate()

        self.pipesTable.setItemDelegateForColumn(
            self.pipeModel.fieldIndex("manning_suggested"), numericFormatDelegate
        )
        self.pipesTable.setItemDelegateForColumn(
            self.pipeModel.fieldIndex("manning_adopted"), numericFormatDelegate
        )
        # hide and strech columns
        self.pipesTable.setColumnHidden(self.pipeModel.fieldIndex("id"), True)
        self.pipesTable.setColumnHidden(self.pipeModel.fieldIndex("criteria_id"), True)
        self.pipesTable.setColumnHidden(self.pipeModel.fieldIndex("created_at"), True)
        self.pipesTable.setColumnHidden(self.pipeModel.fieldIndex("updated_at"), True)
        self.pipesTable.horizontalHeader().setSectionResizeMode(True)

        # Inspection Devices
        self.deviceModel = InspectionDevice()
        self.devicesTable.setModel(self.deviceModel)
        self.devicesTable.setItemDelegate(QSqlRelationalDelegate(self.devicesTable))
        # hide and strech columns
        self.devicesTable.setColumnHidden(self.deviceModel.fieldIndex("id"), True)
        self.devicesTable.setColumnHidden(
            self.deviceModel.fieldIndex("criteria_id"), True
        )
        if self.deviceModel.language == "es":
            self.devicesTable.setColumnHidden(
                self.deviceModel.fieldIndex("type_en"), True
            )
            self.devicesTable.setColumnHidden(
                self.deviceModel.fieldIndex("type_pt"), True
            )
        elif self.deviceModel.language == "pt":
            self.devicesTable.setColumnHidden(
                self.deviceModel.fieldIndex("type_es"), True
            )
            self.devicesTable.setColumnHidden(
                self.deviceModel.fieldIndex("type_en"), True
            )
        else:
            self.devicesTable.setColumnHidden(
                self.deviceModel.fieldIndex("type_es"), True
            )
            self.devicesTable.setColumnHidden(
                self.deviceModel.fieldIndex("type_pt"), True
            )
        self.devicesTable.setColumnHidden(
            self.deviceModel.fieldIndex("created_at"), True
        )
        self.devicesTable.setColumnHidden(
            self.deviceModel.fieldIndex("updated_at"), True
        )
        self.devicesTable.horizontalHeader().setSectionResizeMode(True)

        # conections
        self.profileComboBox.currentIndexChanged.connect(self.onProfileChange)

        self.finalPopulationEdit.valueChanged.connect(self.calculateResidencesEnd)
        self.occupancyRateEndEdit.valueChanged.connect(self.calculateResidencesEnd)
        self.beginningPopulationEdit.valueChanged.connect(self.calculateResidencesStart)
        self.occupancyRateStartEdit.valueChanged.connect(self.calculateResidencesStart)
        self.hhConnStartEdit.valueChanged.connect(self.calculateConnectionsStart)
        self.hhConnEndEdit.valueChanged.connect(self.calculateConnectionsEnd)

        self.waterConsumptionPcSpinBox.valueChanged.connect(
            self.calculateQeReferenceMaxEdit
        )
        self.occupancyRateEndEdit.valueChanged.connect(self.calculateQeReferenceMaxEdit)
        self.coefficientReturnCSpinBox.valueChanged.connect(
            self.calculateQeReferenceMaxEdit
        )
        self.k1DailySpinBox.valueChanged.connect(self.calculateQeReferenceMaxEdit)
        self.k2HourlySpinBox.valueChanged.connect(self.calculateQeReferenceMaxEdit)
        self.waterConsumptionPcSpinBox.valueChanged.connect(
            self.calculateQeReferenceMedEdit
        )
        self.occupancyRateEndEdit.valueChanged.connect(self.calculateQeReferenceMedEdit)
        self.coefficientReturnCSpinBox.valueChanged.connect(
            self.calculateQeReferenceMedEdit
        )

        self.addPipeButton.clicked.connect(self.addPipeRecord)
        self.deletePipeButton.clicked.connect(self.deletePipeRecord)
        self.addDeviceButton.clicked.connect(self.addDeviceRecord)
        self.deleteDeviceButton.clicked.connect(self.deleteDeviceRecord)
        self.newProfileButton.clicked.connect(self.addProfileRecord)
        self.devicesTable.model().dataChanged.connect(self.updateDeviceTranslations)

        self.occupancyRateStartEdit.valueChanged.connect(self.validate_occupancy)
        self.occupancyRateEndEdit.valueChanged.connect(self.validate_occupancy)
        self.occupancyRateStartEdit.valueChanged.emit(
            self.occupancyRateStartEdit.value()
        )
        self.occupancyRateEndEdit.valueChanged.emit(self.occupancyRateEndEdit.value())
        self.getProfilesButton.clicked.connect(self.getProfiles)
        self.addSelectedProfileButton.clicked.connect(self.addProfileSelected)

    def validate_occupancy(self, *args, **kwargs):
        """validates occupancy rate values and sets background color"""
        sender = self.sender()
        valid = sender.value() > 0
        color = "#ffffff" if valid else "#f6989d"
        sender.setStyleSheet("QDoubleSpinBox { background-color: %s }" % color)

    def is_valid_form(self):
        """validates form to allow submiting"""
        return (
            self.occupancyRateStartEdit.value() > 0
            and self.occupancyRateEndEdit.value() > 0
        )

    def isCurrentProfileEditable(self):
        """Returns True if current profile was created under active project"""
        projectId = Project.getActiveId()
        if projectId:
            record = self.criteriaModel.record(self.currentCriteriaIndex)
            return projectId == record.value("parent_project_id")
        return False

    def calculateResidencesEnd(self):
        """Updates value to residencesEndEdit"""
        finalPop = self.finalPopulationEdit.value()
        rateEnd = self.occupancyRateEndEdit.value()
        self.residencesEndEdit.setValue(finalPop / rateEnd) if (
            rateEnd > 0 and rateEnd < finalPop
        ) else self.residencesEndEdit.setValue(0)

    def calculateQeReferenceMaxEdit(self):
        """Updates value to qeReferenceMaxEdit"""
        waterCons = self.waterConsumptionPcSpinBox.value()
        occRate = self.occupancyRateEndEdit.value()
        coeffRetC = self.coefficientReturnCSpinBox.value()
        k1Dly = self.k1DailySpinBox.value()
        k2Hrly = self.k2HourlySpinBox.value()
        qeReferenceMax = (waterCons * occRate * coeffRetC * k1Dly * k2Hrly) / 86400
        self.qeReferenceMaxEdit.setValue(qeReferenceMax)
        self.qeReferenceMaxEdit.setVisible(False)
        self.qeReferenceMaxVisible.setValue(qeReferenceMax)

    def calculateQeReferenceMedEdit(self):
        """Updates value to qeReferenceMedEdit"""
        waterCons = self.waterConsumptionPcSpinBox.value()
        occRate = self.occupancyRateEndEdit.value()
        coeffRetC = self.coefficientReturnCSpinBox.value()
        self.qeReferenceMedEdit.setValue(waterCons * occRate * coeffRetC)

    def calculateResidencesStart(self):
        """Updates value to residencesStartEdit"""
        begPop = self.beginningPopulationEdit.value()
        rateStart = self.occupancyRateStartEdit.value()
        self.residencesStartEdit.setValue(begPop / rateStart) if (
            rateStart > 0 and rateStart < begPop
        ) else self.residencesStartEdit.setValue(0)

    def calculateConnectionsStart(self):
        """Updates value to connections Start"""
        resStart = self.residencesStartEdit.value()
        hhConn = self.hhConnStartEdit.value()
        self.connectionsStartEdit.setValue(resStart / hhConn) if (
            hhConn > 0
        ) else self.connectionsStartEdit.setValue(0)

    def calculateConnectionsEnd(self):
        """Updates value to connections End"""
        resEnd = self.residencesEndEdit.value()
        hhConn = self.hhConnEndEdit.value()
        self.connectionsEndEdit.setValue(resEnd / hhConn) if (
            hhConn > 0
        ) else self.connectionsEndEdit.setValue(0)

    def onProfileChange(self, i):
        """Handles profileComboBox data change"""
        self.currentCriteriaIndex = i
        self.currentCriteriaId = self.criteriaModel.data(
            self.criteriaModel.index(
                self.currentCriteriaIndex, self.criteriaModel.fieldIndex("id")
            )
        )
        self.profileIsEditable = self.isCurrentProfileEditable()
        self.loadProfile()

    def loadProfile(self):
        """Load selected profile and enables/disables editing"""
        if self.currentCriteriaIndex is not None:
            self.mapper_project_criterias.setCurrentIndex(self.currentCriteriaIndex)
            self.loadPipes(self.currentCriteriaId)
            self.loadDevices(self.currentCriteriaId)
        else:
            self.mapper_project_criterias.toFirst()

        # TODO: loop over widgets
        self.waterConsumptionPcSpinBox.setReadOnly(not self.profileIsEditable)
        self.k1DailySpinBox.setReadOnly(not self.profileIsEditable)
        self.k2HourlySpinBox.setReadOnly(not self.profileIsEditable)
        self.coefficientReturnCSpinBox.setReadOnly(not self.profileIsEditable)
        self.intakeRateSpinBox.setReadOnly(not self.profileIsEditable)
        self.avgTractiveForceSpinBox.setReadOnly(not self.profileIsEditable)
        self.flowMinQminSpinBox.setReadOnly(not self.profileIsEditable)
        self.waterSurfaceMaxSpinBox.setReadOnly(not self.profileIsEditable)
        self.maxWaterLevelSpinBox.setReadOnly(not self.profileIsEditable)
        self.minDiameterLineEdit.setReadOnly(not self.profileIsEditable)
        self.diameterUp150SpinBox.setReadOnly(not self.profileIsEditable)
        self.diameterUp200SpinBox.setReadOnly(not self.profileIsEditable)
        self.diameterUp250SpinBox.setReadOnly(not self.profileIsEditable)
        self.coverMinStreetSpinBox.setReadOnly(not self.profileIsEditable)
        self.coverMinSidewalksGsSpinBox.setReadOnly(not self.profileIsEditable)
        self.typePreferredHeadColSpinBox.setReadOnly(not self.profileIsEditable)
        self.simplifiedTLInitialSegComboBox.setEnabled(self.profileIsEditable)
        self.maxDropSpinBox.setReadOnly(not self.profileIsEditable)
        self.bottomIbMhSpinBox.setReadOnly(not self.profileIsEditable)
        self.minStepIbMhSpinBox.setReadOnly(not self.profileIsEditable)
        self.profileName.setReadOnly(not self.profileIsEditable)
        # tables
        self.pipesTable.setEditTriggers(
            QAbstractItemView.AllEditTriggers
            if self.profileIsEditable
            else QAbstractItemView.NoEditTriggers
        )
        self.devicesTable.setEditTriggers(
            QAbstractItemView.AllEditTriggers
            if self.profileIsEditable
            else QAbstractItemView.NoEditTriggers
        )
        # buttons
        self.addPipeButton.setEnabled(self.profileIsEditable)
        self.deletePipeButton.setEnabled(self.profileIsEditable)
        self.addDeviceButton.setEnabled(self.profileIsEditable)
        self.deleteDeviceButton.setEnabled(self.profileIsEditable)

    def loadPipes(self, criteria_id):
        """Load pipesTable data filtered by current criteria_id"""
        if criteria_id:
            self.pipeModel.setFilter("criteria_id = {}".format(criteria_id))

    def loadDevices(self, criteria_id):
        """Load devicesTable data filtered by current criteria_id"""
        if criteria_id:
            self.deviceModel.setFilter("criteria_id = {}".format(criteria_id))

    def refreshProfileCombo(self):
        """clear and repopulate profileCombo data"""
        self.criteriaModel.select()
        self.profileComboBox.model().select()

    def showEvent(self, event):
        """Load parameter data or creates new record"""
        self.parameterId = Project.getActiveProjectParameter()
        if self.parameterId:
            self.parameterModel.setFilter("parameters.id = {}".format(self.parameterId))
            self.mapper.toFirst()  # IMPORTANT: onProfileChqange is triggered by this unless index is 0
            if self.profileComboBox.currentIndex() == 0:
                self.onProfileChange(0)
        else:
            self.addParameterRecord()
            self.loadProfile()

    def addProfileRecord(self):
        """Creates a new profile (project_criteria)"""
        if (
            QMessageBox.question(
                self,
                "New Profile",
                "Create a new profile based on <b>{}</b>, are you sure?".format(
                    self.profileComboBox.currentText()
                ),
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.No
        ):
            return

        row = self.criteriaModel.rowCount()
        self.mapper_project_criterias.submit()
        self.criteriaModel.insertRow(row)
        self.criteriaModel.setData(
            self.criteriaModel.index(row, self.criteriaModel.fieldIndex("name")),
            "{} #{}".format(self.profileComboBox.currentText(), row),
        )
        self.criteriaModel.setData(
            self.criteriaModel.index(
                row, self.criteriaModel.fieldIndex("parent_project_id")
            ),
            Project.getActiveId(),
        )
        newCriteria = self.mapper_project_criterias.submit()
        if newCriteria:
            newCriteriaId = self.criteriaModel.query().lastInsertId()
            self.copyPipesTo(newCriteriaId)
            self.copyDevicesTo(newCriteriaId)
            self.criteriaModel.select()
            self.mapper_project_criterias.setCurrentIndex(row)
            self.profileComboBox.model().select()
            self.profileComboBox.setCurrentIndex(row)
        else:
            self.error_dialog.showMessage(self.criteriaModel.lastError().text())

    def getProfiles(self):
        file = self.dirInputWidget.documentPath()
        self.availableProfilesWidget.clear()
        if 'sanihub.db'in file:
            values = Criteria.getProfileList(file)
            for value in values:
                item = QTreeWidgetItem()
                id = value[0]
                name = value[1]
                item.setText(0, str(id))
                item.setText(1, name)
                self.availableProfilesWidget.addTopLevelItem(item)

    def addProfileSelected(self):
        selected_items = self.availableProfilesWidget.selectedItems()
        file = self.dirInputWidget.documentPath()
        if (len(selected_items) > 0):
            selected_item = selected_items[0]
            criteria_id = selected_item.text(0)
            criteria, pipes, inspection = Criteria.getProfileData(file, criteria_id)
            newCriteriaId = self.criteriaModel.insertData(criteria)
            if newCriteriaId != False:
                pipe = self.pipeModel.insertPipes(newCriteriaId, pipes)
                ins_dev = self.deviceModel.insertInspectionDevices(newCriteriaId, inspection)
                if pipe != False and ins_dev != False:
                    message = "Se ha agregado exitosamente"
                    self.dirInputWidget.resource = None
                    self.availableProfilesWidget.clear()
                else:
                    message = "Error"
            else:
                message = "Error"

            generic_window = GenericWindow(message)
            generic_window.showWindow()
            self.criteriaModel.select()
            self.profileComboBox.model().select()


    def addParameterRecord(self):
        """Creates new Parameter record"""
        row = self.parameterModel.rowCount()
        self.parameterModel.insertRow(row)
        self.mapper.setCurrentIndex(row)
        self.puntualContributionradioButton.setChecked(True)
        self.profileComboBox.setCurrentIndex(0)
        self.occupancyRateStartEdit.setValue(0)
        self.occupancyRateEndEdit.setValue(0)
        self.pointFlowsStartEdit.setValue(0)
        self.pointFlowsEndEdit.setValue(0)

    def addPipeRecord(self):
        """Creates new Pipe record"""
        row = self.pipeModel.rowCount()
        self.pipeModel.insertRow(row)
        self.pipeModel.setData(
            self.pipeModel.index(row, self.pipeModel.fieldIndex("criteria_id")),
            self.currentCriteriaId,
        )

    def addDeviceRecord(self):
        """Creates new InspectionDevice record"""
        row = self.deviceModel.rowCount()
        self.deviceModel.insertRow(row)
        self.deviceModel.setData(
            self.deviceModel.index(row, self.deviceModel.fieldIndex("criteria_id")),
            self.currentCriteriaId,
        )

    def deletePipeRecord(self):
        """Delete selected Pipes"""
        if (
            QMessageBox.question(
                self,
                "Delete",
                "Delete selected rows, are you sure?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.No
        ):
            return
        selection = self.pipesTable.selectionModel().selectedRows()
        for index in selection:
            row = index.row()
            self.pipeModel.removeRow(row)
        self.pipeModel.submitAll()
        self.pipeModel.select()

    def deleteDeviceRecord(self):
        """Delete selected InspectionDevices"""
        if (
            QMessageBox.question(
                self,
                "Delete",
                "Delete selected rows, are you sure?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.No
        ):
            return
        selection = self.devicesTable.selectionModel().selectedRows()
        for index in selection:
            row = index.row()
            self.deviceModel.removeRow(row)
        self.deviceModel.submitAll()
        self.deviceModel.select()

    def copyPipesTo(self, _to):
        """Copy records from current selected profile to recently created one"""
        # self.pipModel is relational and setValue material_id does not work
        pipes = QSqlTableModel()
        pipes.setTable("pipes")
        pipes.setEditStrategy(QSqlTableModel.OnManualSubmit)
        pipes.setFilter("criteria_id = {}".format(self.currentCriteriaId))
        pipes.select()
        for i in range(pipes.rowCount()):
            rec = pipes.record(i)
            newRec = rec
            newRec.setGenerated("id", False)
            newRec.setValue("criteria_id", _to)
            newRec.setValue("created_at", QDateTime.currentDateTime())
            newRec.setValue("updated_at", QDateTime.currentDateTime())
            pipes.insertRecord(-1, newRec)
        pipes.submitAll()

    def copyDevicesTo(self, _to):
        """Copy records from current selected profile to recently created one"""
        for i in range(self.deviceModel.rowCount()):
            rec = self.deviceModel.record(i)
            newRec = rec
            newRec.setGenerated("id", False)
            newRec.setValue("criteria_id", _to)
            newRec.setValue("created_at", QDateTime.currentDateTime())
            newRec.setValue("updated_at", QDateTime.currentDateTime())
            self.deviceModel.insertRecord(-1, newRec)
        self.deviceModel.submitAll()

    def updateDeviceTranslations(self, index):
        """we are using same text in every language when adding custom inspection device"""
        val = index.data()
        columns = ["type_en", "type_es", "type_pt"]
        colName = self.deviceModel.record(index.row()).fieldName(index.column())
        if colName in columns:
            row = index.row()
            for col in columns:
                currentValue = self.deviceModel.record(row).value(col)
                if colName != col and currentValue != val:
                    self.deviceModel.setData(
                        self.deviceModel.index(row, self.deviceModel.fieldIndex(col)),
                        val,
                    )

    def saveParameters(self):
        """Save current dialog data to database"""
        if self.is_valid_form():
            self.mapper.submit()
            self.mapper_project_criterias.submit()
            self.pipeModel.submitAll()
            self.deviceModel.submitAll()
            if self.profileComboBox.currentText() != self.profileName.text():
                self.refreshProfileCombo()
            if not self.parameterId:
                self.parameterId = Parameter.lastInsertedId()
                Project.setParameterToActive(self.parameterId)
            return True
        return False
