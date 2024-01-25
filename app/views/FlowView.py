from qgis.core import QgsProject, QgsWkbTypes, QgsProcessingFeedback, QgsVectorLayer, QgsField, edit
from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import QDialog
import processing
from .ui.FlowDialogUi import Ui_Dialog

class FlowView(QDialog, Ui_Dialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        self.type = 'population'
        self.selected_layer = None
        self.manhole_layer = None
        self.voronoi_layer = None

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

        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.popLayerSelect.currentIndexChanged.connect(lambda index, tab='population': self.updateAttributes(index, tab))
        self.connLayerSelect.currentIndexChanged.connect(lambda index, tab='connection': self.updateAttributes(index, tab))
        self.flowLayer.currentIndexChanged.connect(lambda index, tab='flow': self.updateAttributes(index, tab))

        self.connNoConnectionsEndPlan.currentIndexChanged.connect(lambda index, field='connNoConnectionsEndPlan': self.blockFields(index, field))
        self.flowProjected.currentIndexChanged.connect(lambda index, field='flowProjected': self.blockFields(index, field))

        self.buttonBox.accepted.connect(self.run_flow_process)
    
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

    def calculate_flow(self):
      if self.type == 'population':
        initial_consumption = self.popWaterConsumptionStartVal.value()
        final_consumption =  self.popWaterConsumptionEndVal.value()
        return_coeff = self.popCoefficientReturnVal.value()
        initial_selected = self.popStartPlanVal.currentText()
        final_selected = self.popEndPlanVal.currentText()
        for feature in self.selected_layer.getFeatures():
          initial_population = feature[initial_selected]
          final_population = feature[final_selected]
          initial_flow = initial_consumption * initial_population * return_coeff / 86400
          final_flow = final_consumption * final_population * return_coeff / 86400
          #TODO set to layer the initial_flow and final_flow

      elif self.type == 'connections':
        grow_rate = self.connGrowthRateVal.value()
        economy_conn =  self.connEconomyConnVal.value()
        initial_consumption = self.connStartConsumptionVal.value()
        end_consumption = self.connEndConsumptionVal.value()
        initial_occupancy_rate = self.connOcupancyRateStartVal.value()
        end_occupancy_rate = self.connOcupancyRateEndVal.value()
        return_coeff = self.connReturnCoefficientVal.value()
        no_conn_selected = self.connNoConnections.currentText()
        no_conn_end_selected = self.connNoConnectionsEndPlan.currentText()
        for feature in self.selected_layer.getFeatures():
          no_connections = feature[no_conn_selected]
          initial_flow = initial_consumption * no_connections * economy_conn * initial_occupancy_rate * return_coeff / 86400

          if no_conn_end_selected != "":
            no_end_conn = feature[no_conn_end_selected]
            final_flow = end_consumption * no_end_conn * economy_conn * end_occupancy_rate * return_coeff / 86400
          else:
            final_flow = end_consumption * (no_connections * grow_rate) * economy_conn * end_occupancy_rate * return_coeff / 86400
          #TODO set to layer the initial_flow and final_flow

      else:
        flow_start_selected = self.flowCurrentStartPlan.currentText()
        flow_projected = self.flowProjected.currentText()
        for feature in self.selected_layer.getFeatures():
          initial_flow = feature[flow_start_selected]

          if flow_projected != "":
            final_flow = feature[flow_projected]
          else:
            flow_projection_rate = self.flowProjectionRateVal.value()
            final_flow = initial_flow * flow_projection_rate
          #TODO set to layer the initial_flow and final_flow

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
        input_layer = self.manhole_layer.source()
        #TODO change output layer name
        output_layer = "TEMPORARY_OUTPUT"
        parameters = {
            'BUFFER': buffer,
            'INPUT': input_layer,
            'OUTPUT': output_layer
        }
        self.add_attributes()
        self.create_voronoi(parameters)
        self.calculate_flow()
        self.iterate_over_voronoi()

      else:
          print("Error: No se pudo encontrar la capa seleccionada")

    def create_voronoi(self, parameters):
      feedback = QgsProcessingFeedback()
      result = processing.run("qgis:voronoipolygons", parameters, feedback=feedback)
      self.voronoi_layer = result['OUTPUT']
      QgsProject.instance().addMapLayer(self.voronoi_layer)


    def add_attributes(self):
      """ Adds required fields to both layers if they dont exist"""    

      input_layer = self.selected_layer
      manhole_layer = self.manhole_layer

      input_layer_attributes = [
        dict(name='qi', type=QVariant.Int),
        dict(name='qf', type=QVariant.Int),
        dict(name='C', type=QVariant.Double),
        dict(name='Qi_pop', type=QVariant.Double),
        dict(name='Qf_pop', type=QVariant.Double),
        dict(name='ProjRate', type=QVariant.Double),
        dict(name='Qi_cat', type=QVariant.Double),
        dict(name='Qf_cat', type=QVariant.Double),
        dict(name='Gr', type=QVariant.Double),
        dict(name='econ_con', type=QVariant.Int),
        dict(name='HF_Ini', type=QVariant.Double),
        dict(name='HF_Fin', type=QVariant.Double),
        dict(name='Qi_con', type=QVariant.Double),
        dict(name='Qf_con', type=QVariant.Double),
      ]

      manhole_layer_attributes = [
        dict(name='QConc_I', type=QVariant.Double),
        dict(name='QConc_F', type=QVariant.Double),
      ]

      data_provider_input = input_layer.dataProvider()      
      for attr in input_layer_attributes:
        index = input_layer.fields().indexFromName(attr['name'])
        if index == -1:
          data_provider_input.addAttributes([QgsField(attr['name'], attr['type'])])
          input_layer.updateFields()

      data_provider_manhole = manhole_layer.dataProvider()      
      for attr in manhole_layer_attributes:
        index = manhole_layer.fields().indexFromName(attr['name'])
        if index == -1:
          data_provider_manhole.addAttributes([QgsField(attr['name'], attr['type'])])
          manhole_layer.updateFields()


    def iterate_over_voronoi(self):

      QConc_I_idx = self.manhole_layer.fields().indexOf('QConc_I')
      QConc_F_idx = self.manhole_layer.fields().indexOf('QConc_F')

      for poly in self.voronoi_layer.getFeatures():               
        qi_sum = 0
        qf_sum = 0
        for point in self.selected_layer.getFeatures():          
          if point.geometry().intersects(poly.geometry()):
            if self.type == 'population':
              qi = point['Qi_pop']
              qf = point['Qf_pop']
            elif self.type == 'connections':
              qi = point['Qi_con']
              qf = point['Qf_con']
            else:
              qi = point['Qi_cat']
              qf = point['Qf_cat']

            if type(qi) != QVariant:
              qi_sum = qi_sum + qi
            if type(qf) != QVariant:
              qf_sum = qf_sum + qf        
        
        inspection_box = None
        for box in self.manhole_layer.getFeatures():
          if box.geometry().intersects(poly.geometry()):
            inspection_box = box

        if inspection_box is not None:
          with edit(self.manhole_layer):
            self.manhole_layer.changeAttributeValue(inspection_box.id(), QConc_I_idx, qi_sum)
            self.manhole_layer.changeAttributeValue(inspection_box.id(), QConc_F_idx, qf_sum)
              