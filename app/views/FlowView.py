from qgis.core import QgsProject, QgsWkbTypes
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QDialog
from .ui.FlowDialogUi import Ui_FlowDialog
from ..lib.ProgressThread import ProgressThread
from ..controllers.FlowController import FlowController
from qgis.utils import iface

translate = QCoreApplication.translate

class FlowView(QDialog, Ui_FlowDialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.layers = []
        self.type = 'population'
        self.selected_layer = None
        self.manhole_layer = None

        #Needed for ProgressThread
        self.iface = iface
        self.progressMsg = None
        self.messageLabel = None
        self.refreshTables = None

        self.progressBar.hide()
        self.errorMessage.hide()

        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.popLayerSelect.currentIndexChanged.connect(lambda index, tab='population': self.updateAttributes(index, tab))
        self.connLayerSelect.currentIndexChanged.connect(lambda index, tab='connection': self.updateAttributes(index, tab))
        self.flowLayer.currentIndexChanged.connect(lambda index, tab='flow': self.updateAttributes(index, tab))

        self.connNoConnectionsEndPlan.currentIndexChanged.connect(lambda index, field='connNoConnectionsEndPlan': self.blockFields(index, field))
        self.flowProjected.currentIndexChanged.connect(lambda index, field='flowProjected': self.blockFields(index, field))

        self.buttonBox.accepted.disconnect()

        self.popWaterConsumptionStartVal.valueChanged.connect(self.validate_greather_zero)
        self.popWaterConsumptionEndVal.valueChanged.connect(self.validate_greather_zero)
        self.popCoefficientReturnVal.valueChanged.connect(self.validate_greather_zero)

        self.connEconomyConnVal.valueChanged.connect(self.validate_greather_zero)
        self.connStartConsumptionVal.valueChanged.connect(self.validate_greather_zero)
        self.connEndConsumptionVal.valueChanged.connect(self.validate_greather_zero)
        self.connOcupancyRateStartVal.valueChanged.connect(self.validate_greather_zero)
        self.connOcupancyRateEndVal.valueChanged.connect(self.validate_greather_zero)
        self.connReturnCoefficientVal.valueChanged.connect(self.validate_greather_zero)

        self.buttonBox.accepted.connect(self.perform_validation_and_accept)
    
    def showEvent(self, event):
      self.reload_layer_list()

    def blockFields(self, index, field):
      selected_field = self.connNoConnectionsEndPlan.itemText(index) if field == 'connNoConnectionsEndPlan' else self.flowProjected.itemText(index)
      if selected_field != "":
        if field == 'connNoConnectionsEndPlan':
          self.connGrowthRateVal.setReadOnly(True)
          self.connGrowthRateVal.setStyleSheet("background-color: rgb(238, 238, 236);")
        if field == 'flowProjected':
          self.flowProjectionRateVal.setReadOnly(True)
          self.flowProjectionRateVal.setStyleSheet("background-color: rgb(238, 238, 236);")
      else:
        if field == 'connNoConnectionsEndPlan':
          self.connGrowthRateVal.setReadOnly(False)
          self.connGrowthRateVal.setStyleSheet("")
        if field == 'flowProjected':
          self.flowProjectionRateVal.setReadOnly(False)
          self.flowProjectionRateVal.setStyleSheet("")

    def reload_layer_list(self):

      self.layers = [layer for layer in QgsProject.instance().mapLayers().values()]
      layer_list = []

      self.popLayerSelect.clear()
      self.connLayerSelect.clear()
      self.flowLayer.clear()
      self.manholeLayerSelect.clear()

      self.popLayerSelect.addItem("")
      self.connLayerSelect.addItem("")
      self.flowLayer.addItem("")
      self.manholeLayerSelect.addItem("")

      for layer in self.layers:
          if (layer.type() == layer.VectorLayer):
              if layer.geometryType() == QgsWkbTypes.PointGeometry:
                layer_list.append(layer.name())
      
      self.popLayerSelect.addItems(layer_list)
      self.connLayerSelect.addItems(layer_list)
      self.flowLayer.addItems(layer_list)
      self.manholeLayerSelect.addItems(layer_list)

    def tab_changed(self, index):
        if index == 0:
           self.type = 'population'
        elif index == 1:
           self.type = 'connections'
        else:
           self.type = 'flow'
    
    def perform_validation_and_accept(self):
        if self.validate_form():
          self.run_flow_process()

    def close_dialog(self, success):
      self.progressBar.hide()
      self.accept()

    def validate_form(self):
      self.errorMessage.hide()
      error_message = ""
      self.errorMessage.setText("")
      if self.selected_layer == None:
        error_message += translate("Flow", "Seleccione una capa.\n")
      if self.manholeLayerSelect.currentText() == "":
        error_message += translate("Flow", "Seleccione la capa de caja de inspección.\n")
      
      if self.type == 'population':
        if self.popStartPlanVal.currentText() == "":
          error_message += translate("Flow", "Seleccione el atributo de Población inicio de plan\n")
        if self.popEndPlanVal.currentText() == "":
          error_message += translate("Flow", "Seleccione el atributo de Población fin de plan\n")
        if self.popWaterConsumptionStartVal.value() == 0:
          error_message += translate("Flow", "Dotación de inicio de plan debe ser mayor a 0\n")
        if self.popWaterConsumptionEndVal.value() == 0:
          error_message += translate("Flow", "Dotación de fin de plan debe ser mayor a 0\n")
        if self.popCoefficientReturnVal.value() == 0:
          error_message += translate("Flow", "Coeficiente de retorno debe ser mayor a 0\n")

      elif self.type == 'connections':
        if self.connNoConnections.currentText() == "":
          error_message += translate("Flow", "Seleccione el atributo de cantidad de conexiones inicio de plan\n")
        if self.connNoConnectionsEndPlan.currentText() == "" and self.connGrowthRateVal.value() == 0:
          error_message += translate("Flow", "Seleccione el atributo de cantidad de conexiones de fin de plan o la tasa de crecimiento\n")
        if self.connEconomyConnVal.value() == 0:
          error_message += translate("Flow", "Cantidad de economía por conexión debe ser mayor a 0\n")
        if self.connStartConsumptionVal.value() == 0:
          error_message += translate("Flow", "Dotación de inicio de plan debe ser mayor a 0\n")
        if self.connEndConsumptionVal.value() == 0:
          error_message += translate("Flow", "Dotación de fin de plan debe ser mayor a 0\n")
        if self.connOcupancyRateStartVal.value() == 0:
          error_message += translate("Flow", "Tasa de ocupación inicio de plan debe ser mayor a 0\n")
        if self.connOcupancyRateEndVal.value() == 0:
          error_message += translate("Flow", "Tasa de ocupación final de plan debe ser mayor a 0\n")
        if self.connReturnCoefficientVal.value() == 0:
          error_message += translate("Flow", "Coeficiente de retorno debe ser mayor a 0\n")
      else:
        if self.flowCurrentStartPlan.currentText() == "":
          error_message += translate("Flow", "Seleccione el atributo de caudal actual (inicio de plan)\n")
        if self.flowProjected.currentText() == "" and self.flowProjectionRateVal.value() == 0:
          error_message += translate("Flow", "Seleccione el atributo de caudal proyectado o la tasa de proyección")

      if error_message:
            self.errorMessage.show()
            msg = translate("Flow", "Error de validación:\n")
            self.errorMessage.setText(msg + error_message)
            return False
      else:
          self.errorMessage.hide()
          return True

    def validate_greather_zero(self, *args, **kwargs):
        """validates values and sets background color"""
        sender = self.sender()
        valid = sender.value() > 0
        color = "#ffffff" if valid else "#f6989d"
        sender.setStyleSheet("background-color: %s" % color)

    def updateAttributes(self, index, tab):
        self.set_layer(index)

        if self.selected_layer != None:
          field_names = [field.name() for field in self.selected_layer.fields()]
          
          if tab == 'population':
            self.popStartPlanVal.clear()
            self.popEndPlanVal.clear()
            self.popStartPlanVal.addItems(field_names)
            self.popEndPlanVal.addItems(field_names)

          if tab == 'connection':
            self.connNoConnections.clear()
            self.connNoConnectionsEndPlan.clear()
            self.connNoConnections.addItems(field_names)
            self.connNoConnectionsEndPlan.addItem("")
            self.connNoConnectionsEndPlan.addItems(field_names)

          if tab == 'flow':
            self.flowCurrentStartPlan.clear()
            self.flowProjected.clear()
            self.flowCurrentStartPlan.addItems(field_names)
            self.flowProjected.addItem("")
            self.flowProjected.addItems(field_names)

        else:
          if tab == 'population':
            self.popStartPlanVal.clear()
            self.popEndPlanVal.clear()
          if tab == 'connection':
            self.connNoConnections.clear()
            self.connNoConnectionsEndPlan.clear()
          if tab == 'flow':
            self.flowCurrentStartPlan.clear()
            self.flowProjected.clear()


    def set_layer(self, index):
      if self.type == 'population':
        selected_layer_name = self.popLayerSelect.itemText(index)
      elif self.type == 'connections':
        selected_layer_name = self.connLayerSelect.itemText(index)
      else:
        selected_layer_name = self.flowLayer.itemText(index)

      self.selected_layer = next((layer for layer in self.layers if layer.name() == selected_layer_name), None)
    
    def set_manhole_layer(self):
      manhole_layer_name = self.manholeLayerSelect.currentText()
      self.manhole_layer = next((layer for layer in self.layers if layer.name() == manhole_layer_name), None)

    def get_inputs_values(self):
      return dict(
        population=dict(
          initial_consumption = self.popWaterConsumptionStartVal.value(),
          final_consumption = self.popWaterConsumptionEndVal.value(),
          return_coeff = self.popCoefficientReturnVal.value(),
          initial_selected = self.popStartPlanVal.currentText(),
          final_selected = self.popEndPlanVal.currentText()
        ),
        connections=dict(
          dict(
            grow_rate = self.connGrowthRateVal.value(),
            economy_conn = self.connEconomyConnVal.value(),
            initial_consumption = self.connStartConsumptionVal.value(),
            end_consumption = self.connEndConsumptionVal.value(),
            initial_occupancy_rate = self.connOcupancyRateStartVal.value(),
            end_occupancy_rate = self.connOcupancyRateEndVal.value(),
            return_coeff = self.connReturnCoefficientVal.value(),
            no_conn_selected = self.connNoConnections.currentText(),
            no_conn_end_selected = self.connNoConnectionsEndPlan.currentText()
          )
        ),
        flow=dict(
          dict(
            flow_start_selected = self.flowCurrentStartPlan.currentText(),
            flow_projected = self.flowProjected.currentText()
          )
        )
      )

    def get_only_selected_check(self):
      if self.type == 'population':
        return self.popOnlySelectedVal.isChecked()
      elif self.type == 'connections':
        return self.connOnlySelectedVal.isChecked()
      else:
        return self.flowSelectedVal.isChecked()

    def run_flow_process(self):
      """ Runs the main process"""
      self.set_manhole_layer()
      input_fields = self.get_inputs_values()
      buffer = self.influenceAreaBufferVal.value()

      if self.selected_layer and self.manhole_layer:
        controller = FlowController()
        ProgressThread(
            self,
            controller,
            (lambda : controller.run(
              input_fields=input_fields,
              tab=self.type,
              buffer=buffer,
              selected_layer=self.selected_layer,
              manhole_layer=self.manhole_layer,
              only_selected={'manhole': self.manholeOnlySelectedVal.isChecked(), 'layer': self.get_only_selected_check()}
            )),
            callback=self.close_dialog
        )


