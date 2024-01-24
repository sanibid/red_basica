from qgis.core import QgsProject, QgsWkbTypes, QgsProcessingFeedback, QgsVectorLayer
from PyQt5.QtWidgets import QDialog
import processing
from .ui.FlowDialogUi import Ui_Dialog

class FlowView(QDialog, Ui_Dialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        layer_list = []
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

        self.popLayerSelect.currentIndexChanged.connect(lambda index, tab='population': self.updateAttributes(index, tab))
        self.connLayerSelect.currentIndexChanged.connect(lambda index, tab='connection': self.updateAttributes(index, tab))
        self.flowLayer.currentIndexChanged.connect(lambda index, tab='flow': self.updateAttributes(index, tab))

        self.connNoConnectionsEndPlan.currentIndexChanged.connect(lambda index, field='connNoConnectionsEndPlan': self.blockFields(index, field))
        self.flowProjected.currentIndexChanged.connect(lambda index, field='flowProjected': self.blockFields(index, field))

        self.buttonBox.accepted.connect(self.create_voronoi)
    
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

    def updateAttributes(self, index, tab):
        selected_layer_name = self.popLayerSelect.itemText(index)
        selected_layer = next((layer for layer in self.layers if layer.name() == selected_layer_name), None)

        if selected_layer != None:
          field_names = [field.name() for field in selected_layer.fields()]
          
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


    def create_voronoi(self):
      selected_layer_name = self.manholeLayerSelect.currentText()
      selected_layer = next((layer for layer in self.layers if layer.name() == selected_layer_name), None)
      buffer = self.influenceAreaBufferVal.value()
      if selected_layer:

        input_layer = selected_layer.source()

        #TODO change output layer name
        output_layer = "TEMPORARY_OUTPUT"
        parameters = {
            'BUFFER': buffer,
            'INPUT': input_layer,
            'OUTPUT': output_layer
        }

        feedback = QgsProcessingFeedback()
        result = processing.run("qgis:voronoipolygons", parameters, feedback=feedback)

        output_layer = result['OUTPUT']
        QgsProject.instance().addMapLayer(output_layer)
      else:
          print("Error: No se pudo encontrar la capa seleccionada")

