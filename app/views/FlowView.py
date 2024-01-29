from qgis.core import QgsProject, QgsWkbTypes, QgsProcessingFeedback, QgsField, edit, QgsFeatureRequest
from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis import processing
from .ui.FlowDialogUi import Ui_Dialog
from ..lib.ProgressThread import ProgressThread
from ..controllers.FlowController import FlowController
from qgis.utils import iface

import time

class FlowView(QDialog, Ui_Dialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        self.type = 'population'
        self.selected_layer = None
        self.manhole_layer = None
        #self.voronoi_layer = None
        self.timer = None
        #Needed for ProgressThread
        self.iface = iface
        self.progressMsg = None
        self.messageLabel = None
        self.refreshTables = None
        self.progressBar.hide()

        layer_list = []

        self.progressBar.hide()
        self.errorMessage.hide()

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

    def validate_form(self):
      self.errorMessage.hide()
      error_message = ""
      self.errorMessage.setText("")
      if self.selected_layer == None:
        error_message += "Seleccione una capa.\n"
      if self.manholeLayerSelect.currentText() == "":
        error_message += "Seleccione la capa de caja de inspección.\n"
      
      if self.type == 'population':
        if self.popStartPlanVal.currentText() == "":
          error_message += "Seleccione el atributo de Población inicio de plan\n"
        if self.popEndPlanVal.currentText() == "":
          error_message += "Seleccione el atributo de Población fin de plan\n"
        if self.popWaterConsumptionStartVal.value() == 0:
          error_message += "Dotación de inicio de plan debe ser mayor a 0\n"
        if self.popWaterConsumptionEndVal.value() == 0:
          error_message += "Dotación de fin de plan debe ser mayor a 0\n"
        if self.popCoefficientReturnVal.value() == 0:
          error_message += "Coeficiente de retorno debe ser mayor a 0\n"

      elif self.type == 'connections':
        if self.connNoConnections.currentText() == "":
          error_message += "Seleccione el atributo de cantidad de conexiones inicio de plan\n"
        if self.connNoConnectionsEndPlan.currentText() == "" and self.connGrowthRateVal.value() == 0:
          error_message += "Seleccione el atributo de cantidad de conexiones de fin de plan o la tasa de crecimiento\n"
        if self.connEconomyConnVal.value() == 0:
          error_message += "Cantidad de economía por conexión debe ser mayor a 0\n"
        if self.connStartConsumptionVal.value() == 0:
          error_message += "Dotación de inicio de plan debe ser mayor a 0\n"
        if self.connEndConsumptionVal.value() == 0:
          error_message += "Dotación de final de plan debe ser mayor a 0\n"
        if self.connOcupancyRateStartVal.value() == 0:
          error_message += "Tasa de ocupación inicio de plan debe ser mayor a 0\n"
        if self.connOcupancyRateEndVal.value() == 0:
          error_message += "Tasa de ocupación final de plan debe ser mayor a 0\n"
        if self.connReturnCoefficientVal.value() == 0:
          error_message += "Coeficiente de retorno debe ser mayor a 0\n"
      else:
        if self.flowCurrentStartPlan.currentText() == "":
          error_message += "Seleccione el atributo de caudal actual (inicio de plan)\n"
        if self.flowProjected.currentText() == "" and self.flowProjectionRateVal.value() == 0:
          error_message += "Seleccione el atributo de caudal proyectado o la tasa de proyección"

      if error_message:
            self.errorMessage.show()
            self.errorMessage.setText("Error de validación:\n" + error_message)
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

    def run_flow_process(self):
      """ Runs the main process"""     
      self.set_manhole_layer()
      buffer = self.influenceAreaBufferVal.value()
     
      if self.selected_layer and self.manhole_layer:
        controller = FlowController()
        ProgressThread(
            self,
            controller,
            (lambda : controller.run(
              dialog=self,
              tab=self.type,
              buffer=buffer,
              selected_layer=self.selected_layer,
              manhole_layer=self.manhole_layer
            ))
        )
        

