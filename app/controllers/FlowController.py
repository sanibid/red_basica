from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication
from qgis.core import QgsProject, QgsProcessingFeedback, QgsField, QgsFeatureRequest, QgsProcessingFeatureSourceDefinition
from PyQt5.QtCore import QVariant
translate = QCoreApplication.translate
from qgis import processing
import time

class FlowController(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(int)
    info = pyqtSignal(str)
    message = pyqtSignal(str)
    voronoi_layer = None
    timer = None

    def __init__(self, model=None):
        super().__init__()        

    def run(self, input_fields, tab, buffer, selected_layer, manhole_layer, only_selected):
        """  """
        self.timer = time.time()
        self.progress.emit(10)
        
        #Step 1
        self.add_attributes(tab, selected_layer, manhole_layer)
        self.progress.emit(25)
        step_1 = time.time() - self.timer
        print("add_attributes: ", step_1)
        
        #Step 2
        self.timer = time.time()

        if only_selected['manhole']:
          input_source = QgsProcessingFeatureSourceDefinition(manhole_layer.source(), selectedFeaturesOnly=only_selected['manhole'], featureLimit=-1,geometryCheck = QgsFeatureRequest.GeometryAbortOnInvalid)
        else:
          input_source = manhole_layer.source()

        voronoi_parameters = {
            'BUFFER': buffer,
            'INPUT': input_source,
            'OUTPUT': "TEMPORARY_OUTPUT"
        }

        self.create_voronoi_layer(voronoi_parameters)
        self.progress.emit(50)
        step_2 = time.time() - self.timer
        print("create_voronoi_layer: ", step_2)

        #Step 3
        self.timer = time.time()
        self.calculate_flow(input_fields, tab, selected_layer, only_selected=only_selected['layer'])
        self.progress.emit(75)
        step_3 = time.time() - self.timer
        print("calculate_flow: ", step_3)

        #Step 4
        self.timer = time.time()
        self.iterate_over_voronoi(tab=tab, selected_layer=selected_layer, manhole_layer=manhole_layer, only_selected=only_selected['layer'])
        self.progress.emit(100)
        step_4 = time.time() - self.timer
        print("iterate_over_voronoi: ", step_4)

        self.finished.emit(True)
        return True
        
        
    def create_voronoi_layer(self, parameters):
      feedback = QgsProcessingFeedback()
      result = processing.run("qgis:voronoipolygons", parameters, feedback=feedback)
      self.voronoi_layer = result['OUTPUT']
      QgsProject.instance().addMapLayer(self.voronoi_layer)


    def add_attributes(self, tab, selected_layer, manhole_layer):
      """ Adds required fields to both layers if they dont exist"""    
      
      selected_layer_attributes = dict(
        population=[
          dict(name='qi', type=QVariant.Int),
          dict(name='qf', type=QVariant.Int),
          dict(name='C', type=QVariant.Double),
          dict(name='Qi_pop', type=QVariant.Double),
          dict(name='Qf_pop', type=QVariant.Double)
        ],
        connections=[
          dict(name='Gr', type=QVariant.Double),
          dict(name='econ_con', type=QVariant.Int),
          dict(name='HF_Ini', type=QVariant.Double),
          dict(name='HF_Fin', type=QVariant.Double),
          dict(name='Qi_con', type=QVariant.Double),
          dict(name='Qf_con', type=QVariant.Double)
        ],
        flow=[
          dict(name='ProjRate', type=QVariant.Double),
          dict(name='Qi_cat', type=QVariant.Double),
          dict(name='Qf_cat', type=QVariant.Double)
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

      data_provider_input = selected_layer.dataProvider()      
      for attr in selected_layer_attributes[tab]:
        index = selected_layer.fields().indexFromName(attr['name'])
        if index == -1:
          data_provider_input.addAttributes([QgsField(attr['name'], attr['type'])])
          selected_layer.updateFields()

      data_provider_manhole = manhole_layer.dataProvider()      
      for attr in manhole_layer_attributes[tab]:
        index = manhole_layer.fields().indexFromName(attr['name'])
        if index == -1:
          data_provider_manhole.addAttributes([QgsField(attr['name'], attr['type'])])
          manhole_layer.updateFields()


    def iterate_over_voronoi(self, tab, selected_layer, manhole_layer, only_selected):
      """ Go over every polygon and acumulate flow from intersected nodes into inspection box"""

      for poly in self.voronoi_layer.getFeatures():
        qi_sum = 0
        qf_sum = 0
        features = selected_layer.selectedFeatures() if only_selected else selected_layer.getFeatures(QgsFeatureRequest().setFilterRect(poly.geometry().boundingBox()))
        for point in features:
          if point.geometry().intersects(poly.geometry()):
            if tab == 'population':
              qi = point['Qi_pop']
              qf = point['Qf_pop']
            elif tab == 'connections':
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
        for box in manhole_layer.getFeatures(QgsFeatureRequest().setFilterRect(poly.geometry().boundingBox())):
          if box.geometry().intersects(poly.geometry()):
            inspection_box = box

        if inspection_box is not None:
          manhole_layer.startEditing()          
          if tab == 'population':                        
            inspection_box.setAttribute('Qi_pop', qi_sum)
            inspection_box.setAttribute('Qf_pop', qf_sum)
          elif tab == 'connections':            
            inspection_box.setAttribute('Qi_con', qi_sum)
            inspection_box.setAttribute('Qf_con', qf_sum)
          else:              
            inspection_box.setAttribute('Qi_cat', qi_sum)
            inspection_box.setAttribute('Qf_cat', qf_sum)
          
          manhole_layer.updateFeature(inspection_box)
          manhole_layer.commitChanges()

    def calculate_flow(self, inputs, tab, selected_layer, only_selected):
      selected_layer.startEditing()

      if tab == 'population':
        initial_consumption = inputs[tab]['initial_consumption']
        final_consumption =  inputs[tab]['final_consumption']
        return_coeff = inputs[tab]['return_coeff']
        initial_selected = inputs[tab]['initial_selected']
        final_selected = inputs[tab]['final_selected']
        features = selected_layer.selectedFeatures() if only_selected else selected_layer.getFeatures()
        for feature in features:
          initial_population = feature[initial_selected]
          final_population = feature[final_selected]
          initial_flow = initial_consumption * initial_population * return_coeff / 86400
          final_flow = final_consumption * final_population * return_coeff / 86400

          feature.setAttribute('qi', initial_consumption)
          feature.setAttribute('qf', final_consumption)
          feature.setAttribute('C', return_coeff)
          feature.setAttribute('Qi_pop', initial_flow)
          feature.setAttribute('Qf_pop', final_flow)
          selected_layer.updateFeature(feature)

      elif tab == 'connections':
        grow_rate = inputs[tab]['grow_rate']
        economy_conn =  inputs[tab]['economy_conn']
        initial_consumption = inputs[tab]['initial_consumption']
        end_consumption = inputs[tab]['end_consumption']
        initial_occupancy_rate = inputs[tab]['initial_occupancy_rate']
        end_occupancy_rate = inputs[tab]['end_occupancy_rate']
        return_coeff = inputs[tab]['return_coeff']
        no_conn_selected = inputs[tab]['no_conn_selected']
        no_conn_end_selected = inputs[tab]['no_conn_end_selected']
        for feature in selected_layer.getFeatures():
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
          selected_layer.updateFeature(feature)

      else:
        flow_start_selected = inputs[tab]['flow_start_selected']
        flow_projected = inputs[tab]['flow_projected']
        for feature in selected_layer.getFeatures():
          initial_flow = feature[flow_start_selected]

          if flow_projected != "":
            final_flow = feature[flow_projected]
          else:
            flow_projection_rate = inputs[tab]['flow_projection_rate']
            final_flow = initial_flow * flow_projection_rate
            feature.setAttribute('ProjRate', flow_projection_rate)

          feature.setAttribute('Qi_cat', initial_flow)
          feature.setAttribute('Qf_cat', final_flow)
          selected_layer.updateFeature(feature)

      selected_layer.commitChanges()