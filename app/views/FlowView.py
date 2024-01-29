from qgis.core import QgsProject, QgsWkbTypes, QgsProcessingFeedback, QgsField, edit, QgsFeatureRequest
from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis import processing
from .ui.FlowDialogUi import Ui_Dialog

import time

class FlowView(QDialog, Ui_Dialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        self.type = 'population'
        self.selected_layer = None
        self.manhole_layer = None
        self.voronoi_layer = None
        self.timer = None

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
          self.accept()

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

    def calculate_flow(self):
      self.selected_layer.startEditing()

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

          feature.setAttribute('qi', initial_consumption)
          feature.setAttribute('qf', final_consumption)
          feature.setAttribute('C', return_coeff)
          feature.setAttribute('Qi_pop', initial_flow)
          feature.setAttribute('Qf_pop', final_flow)
          self.selected_layer.updateFeature(feature)

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

          feature.setAttribute('Gr', grow_rate)
          feature.setAttribute('econ_con', economy_conn)
          feature.setAttribute('qi', initial_consumption)
          feature.setAttribute('qf', end_consumption)
          feature.setAttribute('HF_Ini', initial_occupancy_rate)
          feature.setAttribute('HF_Fin', end_occupancy_rate)
          feature.setAttribute('C', return_coeff)
          feature.setAttribute('Qi_con', initial_flow)
          feature.setAttribute('Qf_con', final_flow)
          self.selected_layer.updateFeature(feature)

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
            feature.setAttribute('ProjRate', flow_projection_rate)

          feature.setAttribute('Qi_cat', initial_flow)
          feature.setAttribute('Qf_cat', final_flow)
          self.selected_layer.updateFeature(feature)

      self.selected_layer.updateFields()
      self.selected_layer.commitChanges()

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
      self.timer = time.time()
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
        #TODO delete timer
        end = time.time()
        tiempo = end - self.timer
        print('add_attributes tardó {}'.format(tiempo))
        self.timer = time.time()
        self.create_voronoi(parameters)
        end = time.time()
        tiempo = end - self.timer
        print('create_voronoi tardó {}'.format(tiempo))
        self.timer = time.time()
        self.calculate_flow()
        end = time.time()
        tiempo = end - self.timer
        print('calculate_flow tardó {}'.format(tiempo))
        self.timer = time.time()
        self.iterate_over_voronoi()
        end = time.time()
        tiempo = end - self.timer
        print('iterate_over_voronoi tardó {}'.format(tiempo))

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

      input_layer_attributes = dict(
        population=[
          dict(name='qi', type=QVariant.Int),
          dict(name='qf', type=QVariant.Int),
          dict(name='C', type=QVariant.Double),
          dict(name='Qi_pop', type=QVariant.Double),
          dict(name='Qf_pop', type=QVariant.Double)
        ],
        connections=[
          dict(name='ProjRate', type=QVariant.Double),
          dict(name='Qi_cat', type=QVariant.Double),
          dict(name='Qf_cat', type=QVariant.Double)
        ],
        flow=[
          dict(name='Gr', type=QVariant.Double),
          dict(name='econ_con', type=QVariant.Int),
          dict(name='HF_Ini', type=QVariant.Double),
          dict(name='HF_Fin', type=QVariant.Double),
          dict(name='Qi_con', type=QVariant.Double),
          dict(name='Qf_con', type=QVariant.Double)
        ]
      )

      manhole_layer_attributes = dict(
        population=[
          dict(name='Qi_pop', type=QVariant.Double),
          dict(name='Qf_pop', type=QVariant.Double),
        ], 
        connections=[
          dict(name='Qi_con', type=QVariant.Double),
          dict(name='Qf_con', type=QVariant.Double),
        ],
        flow=[
          dict(name='Qi_cat', type=QVariant.Double),
          dict(name='Qf_cat', type=QVariant.Double),
        ]
      )

      data_provider_input = input_layer.dataProvider()      
      for attr in input_layer_attributes[self.type]:
        index = input_layer.fields().indexFromName(attr['name'])
        if index == -1:
          data_provider_input.addAttributes([QgsField(attr['name'], attr['type'])])
          input_layer.updateFields()

      data_provider_manhole = manhole_layer.dataProvider()      
      for attr in manhole_layer_attributes[self.type]:
        index = manhole_layer.fields().indexFromName(attr['name'])
        if index == -1:
          data_provider_manhole.addAttributes([QgsField(attr['name'], attr['type'])])
          manhole_layer.updateFields()


    def iterate_over_voronoi(self):     
      """ Go over every polygon and acumulate flow from intersected nodes into inspection box"""
      
      for poly in self.voronoi_layer.getFeatures():
        qi_sum = 0
        qf_sum = 0
        for point in self.selected_layer.getFeatures(QgsFeatureRequest().setFilterRect(poly.geometry().boundingBox())):
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
        for box in self.manhole_layer.getFeatures(QgsFeatureRequest().setFilterRect(poly.geometry().boundingBox())):
          if box.geometry().intersects(poly.geometry()):
            inspection_box = box

        if inspection_box is not None:
          self.manhole_layer.startEditing()          
          if self.type == 'population':                        
            inspection_box.setAttribute('Qi_pop', qi_sum)
            inspection_box.setAttribute('Qf_pop', qf_sum)
          elif self.type == 'connections':            
            inspection_box.setAttribute('Qi_con', qi_sum)
            inspection_box.setAttribute('Qf_con', qf_sum)
          else:              
            inspection_box.setAttribute('Qi_cat', qi_sum)
            inspection_box.setAttribute('Qf_cat', qf_sum)
          
          self.manhole_layer.updateFeature(inspection_box)
          self.manhole_layer.commitChanges()

