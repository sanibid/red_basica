from qgis.utils import iface, QgsMessageLog
from qgis.core import Qgis, QgsProject, QgsFeatureRequest, QgsExpression, QgsField, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint, QgsCoordinateTransform, QgsVectorFileWriter
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QCoreApplication, QVariant
from PyQt5.QtSql import QSqlRelation, QSqlRelationalTableModel, QSqlTableModel, QSqlQuery
from PyQt5.QtGui import QColor
from ...base.helper_functions import HelperFunctions
from ...base.pendencias import AnalisaPendencias
import json
from datetime import datetime
import time
import traceback
from ..models.Project import Project
from ..models.Parameter import Parameter
from ..models.Criteria import Criteria
from ..models.Pipe import Pipe
from ..models.InspectionDevice import InspectionDevice
from ..models.Calculation import Calculation
from ..models.Contribution import Contribution
from ..models.WaterLevelAdj import WaterLevelAdj
from ..models.Country import Country

translate = QCoreApplication.translate


class DataController(QObject):
    
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(int)
    info = pyqtSignal(str)
    message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.iface = iface
        self.h = HelperFunctions(iface)

    def campo_ordem(self, f):
        return f[self.h.readValueFromProject("SEG_NAME_C")]

    def runVerifications(self, only_selected_features=False):
        """ run each test in pendencias.py before importing data """
        success = True
        fixSegments = False
        info = None
        self.info.emit(translate("Data", "Running verifications before import"))
        try:
            pendencias = AnalisaPendencias(self.iface, self.h)
            cmd = QgsProject.instance().readEntry("AutGeoAtt", "NODE_LAYER")[0]
            lst = QgsProject.instance().mapLayersByName(cmd)
            if lst:
                nodes = lst[0]
                layer = self.h.GetLayer()
                features = [f for f in (
                    layer.selectedFeatures() if only_selected_features else layer.getFeatures()
                    ) 
                ]

                if success:                    
                    self.progress.emit(2)
                    testVertices = pendencias.AnalisaDoisVertices(features)
                    if testVertices is not None:
                        layer.removeSelection()
                        layer.select(testVertices)
                        info = translate("Data", "Selected patch(es) does not have both vertices")
                        success = False    

                if success:                   
                    self.progress.emit(3)
                    testNames = pendencias.AnalisaFaltaDeNomes(features)
                    if testNames is not None:
                        layer.removeSelection()
                        layer.select(testNames)
                        info = translate("Data", "Selected patch(es) does not have name(s)")
                        success = False
                
                if success:                   
                    self.progress.emit(4)
                    testInvalidNames = pendencias.checkInvalidNames(features)
                    if testInvalidNames is not None:
                        layer.removeSelection()
                        layer.select(testInvalidNames)
                        info = translate("Data", "Selected patch(es) have invalid name(s)")
                        success = False

                if success:                    
                    self.progress.emit(6)
                    testRepeatedNames = pendencias.AnalisaNomeRepetido(features)
                    if testRepeatedNames is not None:
                        layer.removeSelection()
                        layer.select(testRepeatedNames)
                        info = translate("Data", "Selected patch(es) have repeated names")
                        success = False
                
                if success:
                    self.progress.emit(8)                    
                    testExtension = pendencias.AnalisaExtensaoZero(features)
                    if testExtension is not None:
                        layer.removeSelection()
                        layer.select(testExtension)
                        success = False
                        info = translate("Data", "Selected patch(es)  have 0 (zero) extension")
                
                if success:
                    self.progress.emit(10)                    
                    testTwoNodes = pendencias.AnalisaDoisNos(features, nodes)
                    if testTwoNodes is not None:
                        layer.removeSelection()
                        layer.select(testTwoNodes)
                        info = translate("Data", "Selected patch(es) does not have nodes in one or two vertices")
                        success = False 
                
                if success:
                    self.progress.emit(15)
                    self.info.emit(translate("Data", "Checking segments continuity"))
                    testContinuity = pendencias.checkDiscontinuousSegments(features)
                    if testContinuity is not None:                        
                        layer.removeSelection()
                        layer.select(testContinuity)                                           
                        info = translate("Data", "Continuity error detected")
                        success = False                                                
                        fixSegments = True
                    else:
                        info = translate("Data", "Ready to import data")
                
                if not success:
                    self.iface.mapCanvas().setSelectionColor( QColor("red") )
                
            else:
                info = self.h.tr("Node layer not found")
                success = False                

        except Exception as e:
            success = False
            info = translate("Data", "Unexpected error")
            self.error.emit(e, traceback.format_exc())
            
        self.info.emit(info)
        self.finished.emit({
            'success':success, 
            'fix': fixSegments, 
            'info': info, 
            'only_selected_features': only_selected_features
            }
        )

    def getJsonData(self, only_selected_features=False):
        start_time = time.time()
        # data_dir = os.path.join(os.path.dirname(__file__), 'data')

        beg_line_coord_e = self.h.readValueFromProject("BEG_LINE_COORD_E")
        beg_line_coord_n = self.h.readValueFromProject("BEG_LINE_COORD_N")
        fin_line_coord_e = self.h.readValueFromProject("FIN_LINE_COORD_E")
        fin_line_coord_n = self.h.readValueFromProject("FIN_LINE_COORD_N")

        qe = self.h.readValueFromProject("QE")
        qei = self.h.readValueFromProject("QEI")
        qef = self.h.readValueFromProject("QEF")
        cota_i = "COTA_I"
        cota_f = "COTA_F"
        cota = self.h.readValueFromProject("COTA")
        mylayer = self.h.GetLayer()

        #to do: handle loading
        # we are not going to have selected features checkbox  
        vetores = mylayer.selectedFeatures() if only_selected_features else mylayer.getFeatures()
        dicionario = [f for f in vetores]

        dicionario.sort(key=self.campo_ordem)
        
        #export data

        lst = QgsProject.instance().mapLayersByName( self.h.readValueFromProject('NODE_LAYER') )
        if lst:
            nodeLayer = lst[0]

        if nodeLayer:
            qe_idx = nodeLayer.fields().lookupField(qe)
            qei_idx = nodeLayer.fields().lookupField(qei)
            qef_idx = nodeLayer.fields().lookupField(qef)
            cota_idx = nodeLayer.fields().lookupField(cota)
        
        fieldnames = []
        fieldnames.append("AUX_TRM_I")
        fieldnames.append("AUX_TRM_F")
        fieldnames.append(self.h.readValueFromProject("SEG_NAME"))
        fieldnames.append(self.h.readValueFromProject("SEG_NAME_C"))
        fieldnames.append(self.h.readValueFromProject("EXT_FIELD_NAME"))
        fieldnames.append("TRM_(N-1)_A")
        fieldnames.append("TRM_(N-1)_B")
        fieldnames.append("TRM_(N-1)_C")
        if isinstance(qe, basestring):
            fieldnames.append(qe)
        else:
            fieldnames.append("QE")

        if isinstance(qef, basestring):
            fieldnames.append(qef)
        else:
            fieldnames.append("QEF")
            
        if isinstance(qei, basestring):
            fieldnames.append(qei)
        else:
            fieldnames.append("QEI")

        fieldnames.append("QConcF")
        fieldnames.append("QConcI")
        fieldnames.append("Qc_f")
        fieldnames.append("Qc_i")        

        fieldnames.append(self.h.readValueFromProject("AUX_PROF_I"))
        fieldnames.append(self.h.readValueFromProject("AUX_POS"))
        fieldnames.append(self.h.readValueFromProject("AUX_PROF_F"))
        fieldnames.append(cota_i)
        fieldnames.append(cota_f)
        fieldnames.append("TRM_(N+1)")
        fieldnames.append("ID_TRM")
        fieldnames.append(beg_line_coord_e)
        fieldnames.append(beg_line_coord_n)
        fieldnames.append(fin_line_coord_e)
        fieldnames.append(fin_line_coord_n)
        fieldnames.append(self.h.readValueFromProject("AUX_PAV_1"))
        fieldnames.append(self.h.readValueFromProject("AUX_PAV_2"))
        fieldnames.append(self.h.readValueFromProject("AUX01"))
        fieldnames.append(self.h.readValueFromProject("AUX02"))
        fieldnames.append(self.h.readValueFromProject("AUX03"))
        fieldnames.append(self.h.names()["NODO_I"][0])
        fieldnames.append(self.h.names()["NODO_F"][0])


        #line = ';'.join(x for x in fieldnames) + '\n'
        #unicode_line = line.encode('utf-8')
        #output_file.write(unicode_line)

        lstMinFeatures = []
        lstFeatures = []
        for ft in dicionario:
            try:
                pol = ft.geometry().isEmpty()
            except:
                self.h.ShowError(translate("Data", "O trecho {} esta corrompido. nao possui geometria".format(ft[self.h.readValueFromProject("SEG_NAME_C")])))
                break
                
            minFeatureObj = {}
            minFeatureObj["BEG_LINE_COORD_E"] = ft[beg_line_coord_e]
            minFeatureObj["BEG_LINE_COORD_N"] = ft[beg_line_coord_n]
            minFeatureObj["FIN_LINE_COORD_E"] = ft[fin_line_coord_e]
            minFeatureObj["FIN_LINE_COORD_N"] = ft[fin_line_coord_n]
            minFeatureObj["SEG_NAME"] = ft[self.h.readValueFromProject("SEG_NAME")]
            minFeatureObj["SEG_NAME_C"] = ft[self.h.readValueFromProject("SEG_NAME_C")]
            lstMinFeatures.append(minFeatureObj)
            lstFeatures.append(ft)
        
        rows = []
        for f in dicionario:
            #self.dlgExport.progressBar.setValue(self.dlgExport.progressBar.value() + 1)
            values = []
            geom = f.geometry()
            isBegin,isEnd,totalEnd = self.h.Get_Aux_Trm(f.id(),lstFeatures)

            #SEG_NAME_C
            name = f.attributes()[mylayer.fields().lookupField( self.h.readValueFromProject('SEG_NAME_C') )]
            o_name = name
            geom.convertToSingleType()
            vl_id = '{0:.6f}, {1:.6f}'.format(geom.asPolyline()[0].x(), geom.asPolyline()[0].y())
            values.append(str(vl_id))
            values.append(str(str(f[self.h.readValueFromProject("EXT_FIELD_NAME")])))
            values.append(str(str(f[beg_line_coord_e])))
            values.append(str(str(f[beg_line_coord_n])))
            values.append(str(str(f[fin_line_coord_e])))
            values.append(str(str(f[fin_line_coord_n])))
            values.append(str(f[self.h.readValueFromProject("SEG_NAME")]))
            values.append(str(name))
            values.append(str(f[self.h.readValueFromProject("AUX_POS")]))
            values.append(str(f[self.h.readValueFromProject("AUX_PAV_1")]))
            values.append(str(f[self.h.readValueFromProject("AUX_PAV_2")]))
            values.append(str(f[self.h.readValueFromProject("AUX_PROF_I")]))
            values.append(str(f[self.h.readValueFromProject("AUX_PROF_F")]))
            values.append(str(f[self.h.readValueFromProject("AUX01")]))
            values.append(str(f[self.h.readValueFromProject("AUX02")]))
            values.append(str(f[self.h.readValueFromProject("AUX03")]))
            #AUX_TRM_I
            _isBegin = 0
            if isBegin == True:
                _isBegin = 1
            values.append(str(_isBegin))
            #AUX_TRM_F
            _isEnd = 0
            if isEnd == True:
                _isEnd = 1
            values.append(str(_isEnd))
            #TRM_(N-1)_A
            fnd = self.h.Get_Feature_On_Index(lstMinFeatures,f,-1)
            if fnd != None:
                nameOf = fnd["SEG_NAME_C"]
                values.append(str(nameOf))
            else:
                values.append("")
            #TRM_(N-1)_B                
            fnd = self.h.Get_Feature_On_Index(lstMinFeatures,f,-1,False)
            if fnd != None:
                nameOf = fnd["SEG_NAME_C"]
                values.append(str(nameOf))
                toExclud = fnd["SEG_NAME"]
                #TRM_(N-1)_C                
                fnd = self.h.Get_Feature_On_Index(lstMinFeatures,f,-1,False,[toExclud])
                if fnd != None:
                    nameOf = fnd["SEG_NAME_C"]
                    values.append(str(nameOf))
                else:
                    values.append("")
            else:
                values.append("")
                values.append("")
            #TRM_(N+1)
            fnd = self.h.Get_Feature_On_Index(lstMinFeatures,f,1,False,[],True)
            if fnd != None:
                nameOf = fnd["SEG_NAME_C"]
                values.append(str(nameOf))
            else:
                values.append("")               
            if nodeLayer:
                point1 = self.h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])
                point2 = self.h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[-1])
                if point1:
                    _qeList = point1.attributes()[nodeLayer.fields().lookupField( self.h.readValueFromProject('QE') )]
                    q_dict = self.h.getQcFlow(point1)
                    #QE
                    values.append(str(_qeList))
                    if _qeList:
                        qei, qef, qconf, qconci = self.h.GetQEFromBlockLayer(_qeList.split(","))
                        #QEI
                        values.append(str(qei))
                        #QEF
                        values.append(str(qef))
                        #QCONF
                        values.append(str(qconf))
                        #QCONCI
                        values.append(str(qconci))
                    else:
                        #QEI
                        values.append("")
                        #QEF
                        values.append("")
                        #QCONF
                        values.append(None)
                        #QCONCI
                        values.append(None)
                    
                    #Qc_f
                    if q_dict.get("Qc_f") is not None:
                        values.append(q_dict.get("Qc_f"))
                    else:
                        values.append(0)
                    #Qc_i
                    if q_dict.get("Qc_i") is not None:
                        values.append(q_dict.get("Qc_i"))
                    else:
                        values.append(0)                   

                    #COTA_I
                    values.append(str(point1.attributes()[cota_idx]))
                    #NODO_I
                    values.append(str(o_name))
                else:
                    values.append("")
                    values.append("")
                    values.append("")
                    values.append("")
                    #TODO: Para mi aca falta hacer append("") 4 veces
                if point2:                  
                    #COTA_F
                    values.append(str(point2.attributes()[cota_idx]))
                    #NODO_F
                    if totalEnd:
                        nodo_name = name + "-FINAL"
                    else:
                        fnd = self.h.Get_Feature_On_Index(lstMinFeatures,f,+1,True,[],True)
                        if fnd:
                            nodo_name = fnd['SEG_NAME_C'] 
                    values.append(str(nodo_name))
                else:
                    values.append("")
            v2 = []
            v2.append(values[16]) #AUX_TRM_I
            v2.append(values[17]) #AUX_TRM_F
            v2.append(values[6]) #ID_COL
            v2.append(values[7]) #ID_TRM_(N)
            v2.append(values[1]) #L
            v2.append(values[18]) #TRM_(N-1)_A
            v2.append(values[19]) #TRM_(N-1)_B
            v2.append(values[20]) #TRM_(N-1)_C
            v2.append(values[22]) #ID_UC
            v2.append(values[24]) #QE_FP
            v2.append(values[23]) #QE_IP
            v2.append(values[25]) #QConcF
            v2.append(values[26]) #QConcI
            v2.append(values[27]) #Qc_i
            v2.append(values[28]) #Qc_f
            v2.append(values[11]) #AUX_PROF_I
            v2.append(values[8]) #AUX_POS
            v2.append(values[12]) #AUX_PROF_F
            v2.append(values[29]) #COTA_I
            v2.append(values[31]) #COTA_F
            v2.append(values[21]) #TRM_(N+1)
            v2.append(values[0]) #ID_TRM
            v2.append(values[2]) #X_I
            v2.append(values[3]) #Y_I
            v2.append(values[4]) #X_F
            v2.append(values[5]) #Y_F
            v2.append(values[9]) #AUX_PAV_1
            v2.append(values[10]) #AUX_PAV_2
            v2.append(values[13]) #AUX01
            v2.append(values[14]) #AUX02
            v2.append(values[15]) #AUX03
            v2.append(values[30]) #NODO_I
            v2.append(values[32]) #NODO_F
            v2.append("")

            rows.append(v2)

        listRows = {}
        toCheck = []
        for row in rows:
            zipRow = zip(fieldnames,row)
            colSeg = row[3]
            initialSeg = row[0]
            finalSeg = row[1]
            previousCol = row [5]
            col1 = row [6]
            col2 = row [7]
            if initialSeg == '0' and finalSeg == '0' and not previousCol and (col1 or col2):
                toCheck.append(colSeg)         
            listRows[colSeg] = dict(zipRow)
        listRows = self.checkingData(toCheck, listRows)
        print("Total time execution to process: --- %s seconds ---" % (time.time() - start_time))
        return listRows

    def writeToSegmentLayer(self, segments, override, layername):
        """ This will merge data from calculations to Segmets Layer """

        self.info.emit(translate("Data", "Writing data into Layer"))                      
        success = False
        try:
            if override:
                _myLayer = self.h.GetLayer()
            else:
                input_layer = self.h.GetLayer()
                base_path = QgsProject.instance().readPath("./")+"/layers"
                path = "{}/{}.shp".format(base_path, layername)
                writer = QgsVectorFileWriter.writeAsVectorFormat(input_layer, path, 'utf-8', driverName='ESRI Shapefile')                
                _myLayer = iface.addVectorLayer(path, '', 'ogr')
                del(writer)
   
            seg_name_c = self.h.readValueFromProject("SEG_NAME_C")
            first = list(segments.keys())[0]
            headers = list(map(lambda x : x[:10], segments[first].keys())) #attr can have only 10 chars                       
            
            if not _myLayer.isEditable():
                _myLayer.startEditing()
            
            for _h in headers:
                if _h != seg_name_c:
                    _idx = _myLayer.fields().lookupField( _h )
                    if _idx == -1:                        
                        _myLayer.dataProvider().addAttributes([QgsField(_h, QVariant.String)])

            _myLayer.commitChanges()
            if not _myLayer.isEditable():
                _myLayer.startEditing()
            
            progress_step = 50 / _myLayer.featureCount()
            current_progress = 0
            for f in _myLayer.getFeatures():
                current_progress = current_progress + progress_step
                self.progress.emit(current_progress)                
                if f[seg_name_c] in segments:
                    for x in segments[f[seg_name_c]]:                        
                        _myLayer.changeAttributeValue( f.id(), _myLayer.fields().lookupField( x[:10] ), segments[f[seg_name_c]][x] )
            _myLayer.commitChanges()
            success = True
        except Exception as e:
            success = False
            msg = translate("Data", "Unexpected error")
            self.info.emit(msg)
            self.error.emit(e, traceback.format_exc())        
                    
        return success

    def writeToNodeLayer(self, nodes, override, layername):        
        """ This will merge or create new layer with data from calculations """
              
        self.info.emit(translate("Data", "Writing data into Nodes Layer"))
        success = False        

        try:
            _myLayer = self.h.GetLayer()
            if override:                        
                nodeLayer = self.h.GetNodeLayer()
            else:
                input_layer = self.h.GetNodeLayer()
                base_path = QgsProject.instance().readPath("./")+"/layers"
                path = "{}/{}.shp".format(base_path, layername)
                writer = QgsVectorFileWriter.writeAsVectorFormat(input_layer, path, 'utf-8', driverName='ESRI Shapefile')                
                nodeLayer = iface.addVectorLayer(path, '', 'ogr')
                del(writer)
            if _myLayer and nodeLayer:                
                
                if nodeLayer:                                                             
                    seg_name_c = self.h.readValueFromProject("SEG_NAME_C")
                    first = list(nodes.keys())[0]                    
                    headers = list(map(lambda x : x[:10], nodes[first].keys())) # limit of 10 chars issue
                    
                    if not nodeLayer.isEditable():
                        nodeLayer.startEditing()
                                    
                    for _h in headers:
                        _idx = nodeLayer.fields().lookupField( _h )
                        if _idx == -1:                                                        
                            nodeLayer.dataProvider().addAttributes([QgsField(_h, QVariant.String)])
                    nodeLayer.commitChanges()
                    
                    if not nodeLayer.isEditable():
                        nodeLayer.startEditing()
                    
                    progress_step = 50 / _myLayer.featureCount()
                    current_progress = 50
                    for f in _myLayer.getFeatures():
                        current_progress = current_progress + progress_step
                        self.progress.emit(current_progress)
                        point = None
                        name = f[seg_name_c]
                        name_f = f[seg_name_c] + "-FINAL"
                        if name in nodes:
                            geom = f.geometry()
                            geom.convertToSingleType()
                            point = self.h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])
                            if point:
                                for x in nodes[name]:                                                           
                                    nodeLayer.changeAttributeValue( point.id(), nodeLayer.fields().lookupField( x[:10] ), nodes[name][x] )

                        if name_f in nodes:
                            geom = f.geometry()
                            geom.convertToSingleType()                                
                            point = self.h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[-1])

                            if point:
                                for x in nodes[name_f]:                                                            
                                    nodeLayer.changeAttributeValue( point.id(), nodeLayer.fields().lookupField( x[:10] ), nodes[name_f][x] )
                        
                    nodeLayer.commitChanges()
                    success = True
            
        except Exception as e:
            success = False
            msg = translate("Data", "Unexpected error")
            self.info.emit(msg)
            self.error.emit(e, traceback.format_exc())        
                    
        return success 

    def writeToLayers(self, data, override=True, nodes_layername=None, segments_layername=None):
        success = self.writeToSegmentLayer(data['segments'], override=override, layername=segments_layername)
        if success:
            success = self.writeToNodeLayer(data['nodes'], override=override, layername=nodes_layername)
        self.finished.emit({'success': success})
        return success

    def updateSegmentsLayer(self, colseg, data):
        layer = self.h.GetLayer()
        layer.removeSelection()
        fields = layer.fields()
        col = self.h.readValueFromProject("SEG_NAME_C")
        features = layer.getFeatures(QgsFeatureRequest(QgsExpression("\"{}\" = '{}'".format(col, colseg))))
        layer.startEditing()
        for feature in features:            
            for key in data:
                idx = fields.indexFromName(key)
                if idx != -1:
                    msg = translate("Data", "Field {} antes:{} despues:{}".format(key, feature.attributes()[idx], data[key]))
                    layer.changeAttributeValue(feature.id(), idx, data[key])
                    print(msg)
        layer.commitChanges()
        return True
    
    
    def checkingData(self, toCheck, list):        
        for colSeg in toCheck:
            col1 = list[colSeg]['TRM_(N-1)_B']
            col2 = list[colSeg]['TRM_(N-1)_C']
            col1LastNumber = col2LastNumber = 0
            if col1:
                col1LastNumber = int(col1.split('-')[1]) if col1.count('-') == 1 else int(col1.split('--')[1])
            if col2:
                col2LastNumber = int(col2.split('-')[1]) if col2.count('-') == 1 else int(col2.split('--')[1])
            d = {col1: col1LastNumber, col2:col2LastNumber}
            parentCol = max(d, key=d.get)
            list[parentCol]['AUX_TRM_F'] = "0"
            prntColSegLen = len(parentCol.split('-')[1]) if parentCol.count('-') == 1 else len(parentCol.split('--')[1])
            prntColSegLastNr = int(parentCol.split('-')[1]) if parentCol.count('-') == 1 else int(parentCol.split('--')[1])
            colSegLen = len(colSeg.split('-')[1]) if colSeg.count('-') == 1 else len(colSeg.split('--')[1])
            colSegLastNr = int(colSeg.split('-')[1]) if colSeg.count('-') == 1 else int(colSeg.split('--')[1])
            colSegCol = list[colSeg]['ID_COL'] 
            final = 0
            i = 0
            while final == 0:
                prntColSegLastNr = prntColSegLastNr + 1
                colSegIndex = colSegCol + '-' + str(colSegLastNr).zfill(colSegLen)
                lpCol = list[parentCol]['ID_COL']
                lpColN = list[parentCol]['ID_COL'] + '-' + str(prntColSegLastNr).zfill(prntColSegLen)
                if i == 0:
                    replaceCol = list[min(d, key=d.get)]['ID_TRM_(N)'] if col2 else ""                    
                    list[colSegIndex].update({
                        'TRM_(N-1)_A': list[parentCol]['ID_TRM_(N)'],
                        'TRM_(N-1)_B': replaceCol,
                        'TRM_(N-1)_C': ""
                    })   
                else:
                    list[colSegIndex].update({
                        'TRM_(N-1)_A': list[list[colSegIndex]['TRM_(N-1)_A']]['ID_TRM_(N)']
                    })
                final = int(list[colSegIndex]['AUX_TRM_F'])

                data = {
                        'ID_COL': lpCol,
                        'ID_TRM_(N)': lpColN,
                        'NODO_I': lpColN
                    }
                list[colSegIndex].update(data)
                self.updateSegmentsLayer(colSegIndex, data)
                colSegLastNr += 1
                i += 1

        for colSeg in list:
            if (list[colSeg]['AUX_TRM_F'] == "0" and list[list[colSeg]['TRM_(N+1)']]['ID_TRM_(N)'] != list[colSeg]['TRM_(N+1)']):
                newColSeg = list[list[colSeg]['TRM_(N+1)']]['ID_TRM_(N)']
                list[colSeg].update({'TRM_(N+1)': newColSeg, 'NODO_F': newColSeg})
            if (list[colSeg]['AUX_TRM_F'] == "1" and list[colSeg]['TRM_(N+1)'] != "" and list[list[colSeg]['TRM_(N+1)']]['ID_TRM_(N)'] != list[colSeg]['TRM_(N+1)']):
                list[colSeg].update({'TRM_(N+1)': list[list[colSeg]['TRM_(N+1)']]['ID_TRM_(N)']})
            if (list[colSeg]['AUX_TRM_F'] == "1"):
                if ('-FINAL' in list[colSeg]['NODO_F']):
                    if (list[list[colSeg]['NODO_F'].replace('-FINAL','')]['ID_TRM_(N)'] != list[colSeg]['NODO_F'].replace('-FINAL','')):
                        list[colSeg].update({'NODO_F': list[list[colSeg]['NODO_F'].replace('-FINAL','')]['ID_TRM_(N)'] + '-FINAL'})
                if ('-FINAL' not in list[colSeg]['NODO_F']):
                    if (list[list[colSeg]['NODO_F']]['ID_TRM_(N)'] != list[colSeg]['NODO_F']):
                        list[colSeg].update({'NODO_F': list[list[colSeg]['NODO_F']]['ID_TRM_(N)']})

            if (list[colSeg]['TRM_(N-1)_B'] != ""):
                if (list[list[colSeg]['TRM_(N-1)_B']]['ID_TRM_(N)'] != list[colSeg]['TRM_(N-1)_B']):
                    list[colSeg].update({'TRM_(N-1)_B': list[list[colSeg]['TRM_(N-1)_B']]['ID_TRM_(N)']})
            
            if (list[colSeg]['TRM_(N-1)_C'] != ""):
                if (list[list[colSeg]['TRM_(N-1)_C']]['ID_TRM_(N)'] != list[colSeg]['TRM_(N-1)_C']):
                    list[colSeg].update({'TRM_(N-1)_C': list[list[colSeg]['TRM_(N-1)_C']]['ID_TRM_(N)']})
                        
        if toCheck:
            layer = self.h.GetLayer()
            features = [f for f in layer.getFeatures()]
            checks = AnalisaPendencias(self.iface, self.h)
            testRepeatedNames = checks.AnalisaNomeRepetido(features)
            if testRepeatedNames is not None:
                layer.removeSelection()
                layer.select(testRepeatedNames)
                self.info.emit(translate("Data", "Selected patch(es)  have repeated names" ))
                return False
        
        sort_column = self.h.readValueFromProject("SEG_NAME_C")
        sorted_list =  {k: v for k, v in sorted(list.items(), key=lambda item: item[1][sort_column])} #sort by key
        
        return sorted_list.values()

   
    def getFullProject(self, user, password, id=None, wgs84=False):
        """ Returns full project in JSON format """

        projectId = Project.getActiveId() if id is None else id
               
        if projectId is not None:
            try:
                # 1) init models
                projectModel = Project()
                parameterModel = Parameter()
                criteriaModel = Criteria()
                pipesModel = Pipe()
                devicesModel = InspectionDevice()
                calculationModel = Calculation()
                contributionModel = Contribution()
                wlaModel = WaterLevelAdj()

                # 2) Project            
                projectModel.setFilter('id = {}'.format(projectId))
                projectModel.select()
                project = projectModel.record(0)
                
                # 3) Parameters
                parameterModel.setFilter('id = {}'.format(project.value('parameter_id')))                            
                parameterModel.select()
                parameters = parameterModel.record(0)

                # 4) Criteria
                criteriaModel.setFilter('id = {}'.format(parameters.value('project_criteria_id')))
                criteriaModel.select()
                criterias = criteriaModel.record(0)                
                
                pipesModel.setFilter('criteria_id = {}'.format(criterias.value('id')))
                pipesModel.select()
                pipes = [self._record_to_dict(pipesModel.record(x)) for x in range(pipesModel.rowCount())]
                
                devicesModel.setFilter('criteria_id = {}'.format(criterias.value('id')))
                devicesModel.select()
                devices = [self._record_to_dict(devicesModel.record(x)) for x in range(devicesModel.rowCount())]
                
                criterias = self._record_to_dict(criterias)
                criterias['pipes'] = pipes
                criterias['devices'] = devices
                # and finally add criterias to parameters
                parameters = self._record_to_dict(parameters)
                parameters['criteria'] = criterias


                # 5) Calculations, Contributions and Wla
                calculationModel.setFilter('project_id = {}'.format(projectId))
                calculationModel.select()
                while calculationModel.canFetchMore():
                    calculationModel.fetchMore()
                calculations = []
                for i in range(calculationModel.rowCount()):
                    rec = calculationModel.record(i)
                    calc_id = rec.value('id')
                    
                    contributionModel.setFilter('calculation_id = {}'.format(calc_id))                
                    contributionModel.select()
                                        
                    wlaModel.setFilter('calculation_id = {}'.format(calc_id))
                    wlaModel.select()

                    item = self._record_to_dict(rec)
                    item['contribution'] = self._record_to_dict(contributionModel.record(0))
                    item['wl_adj'] = self._record_to_dict(wlaModel.record(0))
                    
                    if wgs84 is True:
                        geom_init = QgsGeometry(QgsPoint(item['x_initial'],item['y_initial']))
                        geom_final = QgsGeometry(QgsPoint(item['x_final'],item['y_final']))
                        sourceCrs = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
                        destCrs = QgsCoordinateReferenceSystem(4326)
                        tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                        geom_init.transform(tr)
                        geom_final.transform(tr)
                        item['x_initial'] = geom_init.asPoint().x()
                        item['y_initial'] = geom_init.asPoint().y()
                        item['x_final'] = geom_final.asPoint().x()
                        item['y_final'] = geom_final.asPoint().y()

                    calculations.append(item)


                obj = {
                    'user': {
                        'name': user,
                        'pass': password
                    },
                    'name': project.value('name'),
                    'country_id': project.value('country_id'),
                    'city': project.value('city'),
                    'microsystem': project.value('microsystem'),
                    'author': project.value('author'),
                    'date': project.value('date'),
                    'username': user,
                    'srid': project.value('srid'),
                    'created_at': project.value('created_at'),
                    'updated_at': project.value('updated_at'),
                    'parameter': parameters,                    
                    'calculations': calculations
                } 
                return obj

            except Exception as e:
                trace = traceback.format_exc()
                QgsMessageLog.logMessage('DataController raised an exception:\n {}'.format(trace), level=Qgis.Critical)                         
                return False                    

        else:
            return False


    def _record_to_dict(self, record):
        exclude_fields = ('id','parameter_id', 'criteria_id', 'project_id','calculation_id', 'project_criteria_id', 'created_at', 'updated_at')
        _dict = {}
        for i in range(record.count()):
            if record.fieldName(i) not in exclude_fields:
                _type = type(record.value(i))
                value = record.value(i)
                if _type not in (int, str, float): # qvariant serialize issue
                    value = str(value)
                if value not in ("", "NULL"):
                    _dict[record.fieldName(i)] = value
        return _dict