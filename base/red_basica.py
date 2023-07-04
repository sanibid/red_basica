# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from builtins import next
from builtins import str
from builtins import object
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, QVariant
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from PyQt5.QtGui import QIcon, QFont, QColor, QIntValidator
from PyQt5.QtWidgets import QAction, QTableWidgetItem, QFileDialog, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QLineEdit
from qgis.core import QgsProject, QgsProperty

# Initialize Qt resources from file resources.py
from . import resources
import locale
# Import the code for the dialog
from .red_basica_dialog import RedBasicaDialog
from .name_segment_dialog import NameSegmentDialog
from .export_dialog import ExportDialog
from .ui_segment_dock import UiSegmentDock
from .create_pointLayer_importRaster_dialog import CreatePointLayerImportRaster
from .helper_functions import HelperFunctions
from .recobrimento_dialog import CalcularProfundidadeDialog
from .profundidade import CalculaProfundidade
from .pendencias import AnalisaPendencias
import os.path
from osgeo import ogr
import os
from qgis.core import *
from qgis.gui import *
from ..app import App
from ..profile import Profile
from ..app.lib.Store import Store

translate = QCoreApplication.translate

class RedBasica(object):
 
    def __init__(self, iface):
        super().__init__()
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        global h
        h = HelperFunctions(iface)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,           
            '../i18n',
            'RedBasica_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog's (after translation) and keep reference
        self.dlg = RedBasicaDialog()
        self.dlg.SetIface(iface)
        self.dlgNameSegment = NameSegmentDialog()
        self.dlgNameSegment.SetIface(iface)
        self.dlgCreatePointLayerImportRaster = CreatePointLayerImportRaster()
        self.dlgCreatePointLayerImportRaster.SetIface(iface)

        self.dlgExport = ExportDialog()
        self.dlgExport.SetIface(iface)

        self.dlgProfundidade = CalcularProfundidadeDialog()
        self.dlgProfundidade.SetIface(iface)


        # Declare instance attributes
        self.actions = []
        self.menu = translate("AutomaticGeometricAttributes",u'&saniHUB RedBasica')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'saniHUB RedBasica')
        self.toolbar.setObjectName(u'saniHUB RedBasica')

        QgsProject.instance().layersAdded.connect( self.startHandler )
        QgsProject.instance().readProject.connect( self.readProject )

        self.dockPatchs = UiSegmentDock()
        self.dockPatchs.SetIface(iface)
        self.iface.addDockWidget( Qt.RightDockWidgetArea, self.dockPatchs )

        self.dockPatchs.saveFunction = self.saveAttributesDock

        self.dockPatchs.btnSave.clicked.connect( self.saveAttributesDock )

        self.NamingMode = False
        self.SupressNameForm = False
        self.HandlerInitialized = False

        # start events of widget

        self.dockPatchs.btnNamePatch.clicked.connect( self.NameAPatch )

        self.dockPatchs.btnUpdateFlowRateList.clicked.connect( self.UpdateFlowRateList )
             
        #self.dockPatchs.chkSupressPopup.stateChanged.connect( self.SupressCheckChanged )        

        # end events of widget
        
        self.startHandler()

    
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/RedBasica/icons/'
        self.add_action( \
            icon_path  + 'settings.png', \
            text=translate("AutomaticGeometricAttributes", "Adjust settings for automatic geometric watcher"), \
            callback=self.run, \
            parent=self.iface.mainWindow())

        
        self.add_action( \
            icon_path + 'gen-point-layer.png', \
            text=translate("AutomaticGeometricAttributes","Create a point layer based on vector layer and get raster values"), \
            callback=self.createPointLayer, \
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'recobrimento.png',
            text=translate("AutomaticGeometricAttributes","Estimate the depth of the sewers"),
            callback=self.calculateDepth,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'refresh-atributes.png',
            text=translate("AutomaticGeometricAttributes","Update geometric attributes of all features"),
            callback=self.updateAllFeatures,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'validate.png',
            text=translate("AutomaticGeometricAttributes","Select all features that not have sequence"),
            callback=self.selectAllEndFeatures,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'pendencias.png',
            text=translate("AutomaticGeometricAttributes","Verify network´s consistency"),
            callback=self.AnalisarPendencias,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'blocks.png',
            text=translate("AutomaticGeometricAttributes","Add block layer"),
            callback=self.AddBlockLayer,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'arrow_down.png',
            text=translate("AutomaticGeometricAttributes","Add Natural Slope Arrow layer"),
            callback=self.AddNaturalSlopeArrowLayer,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'nodes.png',
            text=translate("AutomaticGeometricAttributes","Add Required Points layer"),
            callback=self.AddRequiredPointsLayer,
            parent=self.iface.mainWindow())

        self.alternateAction = self.add_action(
            icon_path + 'edit.png',
            text=translate("AutomaticGeometricAttributes","Current in Edit-Mode: Alternate to Plot Mode"),
            callback=self.alternateModes,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'export.png',
            text=translate("AutomaticGeometricAttributes","Export data"),
            callback=self.exportDataShow,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'import.png',
            text=translate("AutomaticGeometricAttributes","Import data to vector layer"),
            callback=self.importDataShow,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'import-node.png',
            text=translate("AutomaticGeometricAttributes","Import data to node layer"),
            callback=self.importDataNodeShow,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'calc.png',
            text=translate("AutomaticGeometricAttributes","Abrir con app"),
            callback=self.openCalculationsApp,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path + 'processing.png',
            text="Perfiles",
            callback=self.openProfileWindow,
            parent=self.iface.mainWindow())

    def readProject(self):
        """ Called every time a new project is opened and resets dock panel """      
        self.HandlerInitialized = False
        self.dockPatchs.SetSelectedId(None)            
        lab = QLabel()
        lab.setText(translate("AutomaticGeometricAttributes","No feature selected"))
        self.dockPatchs.saPropFeatures.setWidget(lab)
        self.calcApp.connectLayer()
    
    def AnalisarPendencias(self):
        ap = AnalisaPendencias(self.iface, h)
        return ap.AnalisarPendencias()

    def calculateDepth(self):
        self.dlgProfundidade.show()
        result = self.dlgProfundidade.exec_()
        if result:
            calculap = CalculaProfundidade(self.iface, h)
            cmd = QgsProject.instance().readEntry("AutGeoAtt", "NODE_LAYER")[0]
            lst = QgsProject.instance().mapLayersByName(cmd)
            if lst:
                nos = lst[0]
                calculap.processNetwork(h.GetLayer(), nos, self.dlgProfundidade.qdsbRecobrimento.value(), self.dlgProfundidade.qdsbDiamentro.value()*1.0 / 1000.0, self.dlgProfundidade.qdsbDeclividade.value(), self.dlgProfundidade.qdsbProfundidade.value(), self.dlgProfundidade.cbSelecionados.isChecked())
            else:
                h.ShowError("Não há camadas de nós!")
            

    def alternateModes(self):
        icon_path = ':/plugins/RedBasica/icons/'
        if self.plotMode == False:
            self.plotMode = True
            icon = QIcon(icon_path + 'blueprint.png')
            self.alternateAction.setIcon(icon)
            self.alternateAction.setText(translate("AutomaticGeometricAttributes","Current in Plot-Mode: Alternate to Edit Mode"))

            vecLayer = h.GetLayer()

            if vecLayer:
                qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'default_plot_style.qml')
                vecLayer.loadNamedStyle(qmlFile)

            lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )
            if lst:
                nodeLayer = lst[0]
                if nodeLayer:
                    qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'Default_nodes_plot_style.qml')
                    nodeLayer.loadNamedStyle(qmlFile)
        else:
            self.plotMode = False
            icon = QIcon(icon_path + 'edit.png')
            self.alternateAction.setIcon(icon)
            self.alternateAction.setText(translate("AutomaticGeometricAttributes","Current in Edit-Mode: Alternate to Plot Mode"))

            vecLayer = h.GetLayer()

            if vecLayer:
                qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'default_style.qml')
                vecLayer.loadNamedStyle(qmlFile)

            lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )
            if lst:
                nodeLayer = lst[0]
                if nodeLayer:
                    qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'Default_nodes_style.qml')
                    nodeLayer.loadNamedStyle(qmlFile)

        self.refresh_layers()
        proj = QgsProject.instance()
        proj.writeEntry("AutGeoAtt","PLOT_MODE",self.plotMode)

    def refresh_layers(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

    def SupressCheckChanged(self,state):
        QSettings().setValue( '/qgis/digitizing/disable_enter_attribute_values_dialog', state )

    def UpdateFlowRateList(self):

        self.dockPatchs.tblFlowRateConcentrated.setRowCount(0)
        self.dockPatchs.tblFlowRateConcentrated.setSortingEnabled(False)
        
        lst = QgsProject.instance().mapLayersByName( h.names()["BLOCK_LAYER_NAME"][0] )
        if lst:
            blockLayer = lst[0]
            seg_name_c = h.readValueFromProject("SEG_NAME_C")
            

            lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )
            if lst:
                nodeLayer = lst[0]
                if nodeLayer:
                    mydic = {}
                    for f in h.GetLayer().getFeatures():
                        geom = f.geometry()
                        geom.convertToSingleType()
                        point1 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])
                        if point1:
                            _qeList = point1.attributes()[nodeLayer.fields().lookupField( h.readValueFromProject('QE') )]
                            if _qeList:                                
                                
                                
                  
                                if (len(_qeList) > 0) & (_qeList[0] != ""):
                                    name = f[seg_name_c]
                                    for x in _qeList.split(","):
                                        
                                        if x not in mydic:
                                            mydic[x] = [name]
                                        else:
                                            mydic[x].append(name)                                               

                rowCount = blockLayer.featureCount()

                self.dockPatchs.tblFlowRateConcentrated.setRowCount(rowCount)
                row = 0
                
                
                for f in blockLayer.getFeatures():
                    
                    self.dockPatchs.tblFlowRateConcentrated.setItem(row,0,QTableWidgetItem(f[h.names()["ID_QE"][0]]))
                    self.dockPatchs.tblFlowRateConcentrated.setItem(row,1,QTableWidgetItem(str(f[h.names()["QE_IP"][0]])))
                    self.dockPatchs.tblFlowRateConcentrated.setItem(row,2,QTableWidgetItem(str(f[h.names()["QE_FP"][0]])))

                    if f[h.names()["ID_QE"][0]] in mydic:
                        
                        joinedV = ",".join(mydic[f[h.names()["ID_QE"][0]]])
                        self.dockPatchs.tblFlowRateConcentrated.setItem(row,3,QTableWidgetItem(joinedV))
                    else:
                        self.dockPatchs.tblFlowRateConcentrated.setItem(row,3,QTableWidgetItem(""))

                    row = row + 1

                    
        
        
        self.dockPatchs.tblFlowRateConcentrated.setSortingEnabled(True)
        

    def AddNaturalSlopeArrowLayer(self):
        h.AddNaturalSlopeArrowLayer()
        
    def AddRequiredPointsLayer(self):
        h.AddRequiredPointsLayer()

    def AddBlockLayer(self):
        h.CreateBlockLayer()

    def saveAttributesDock(self):
        selId = self.dockPatchs.GetSelectedId()
        
        if selId != None:
            
            f = next(h.GetLayer().getFeatures( QgsFeatureRequest( selId ) ))
            geom = f.geometry()

            lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )
            nodeLayer = None 

            if lst:
                nodeLayer = lst[0]

            qe = h.readValueFromProject("QE")
            qei = h.readValueFromProject("QEI")
            qef = h.readValueFromProject("QEF")
            cota = h.readValueFromProject("COTA")

            if nodeLayer is not None:
                qe_idx = nodeLayer.fields().lookupField(qe)
                qei_idx = nodeLayer.fields().lookupField(qei)
                qef_idx = nodeLayer.fields().lookupField(qef)
                cota_idx = nodeLayer.fields().lookupField(cota)

                if not nodeLayer.isEditable():
                    nodeLayer.startEditing()
            geom.convertToSingleType()
            
            #self.iface.messageBar().pushMessage("Error", "XI: "+str(geom.asPolyline()[0].x()), level=Qgis.Critical, duration=3)
            #self.iface.messageBar().pushMessage("Error", "XF: "+str(geom.asPolyline()[-1].x()), level=Qgis.Critical, duration=3)
            if nodeLayer is not None:
                point1 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])

                if point1:
                    #QE
                    els = self.dockPatchs.saPropFeatures.findChildren(QLineEdit,h.names()['QE'][0])
                    if els:
                        nodeLayer.changeAttributeValue( point1.id(), qe_idx , els[0].text() )

                    #COTA_I
                    els = self.dockPatchs.saPropFeatures.findChildren(QLineEdit,h.names()['COTA_I'][0])
                    if els:
                        nodeLayer.changeAttributeValue( point1.id(), cota_idx , els[0].text() )

                #COTA_F
                els = self.dockPatchs.saPropFeatures.findChildren(QLineEdit,h.names()['COTA_F'][0])
                if els:
                    point2 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[-1])
                    
                    if point2:
                        nodeLayer.changeAttributeValue( point2.id(), cota_idx , els[0].text() )
                

            h.ShowMessage(translate("AutomaticGeometricAttributes","Values changed successfully"))
            

    def selectAllEndFeatures(self):
        mLayer = h.GetLayer()
        mLayer.selectByIds([])
        if mLayer:

            beg_line_coord_e = h.readValueFromProject("BEG_LINE_COORD_E")
            beg_line_coord_n = h.readValueFromProject("BEG_LINE_COORD_N")
            fin_line_coord_e = h.readValueFromProject("FIN_LINE_COORD_E")
            fin_line_coord_n = h.readValueFromProject("FIN_LINE_COORD_N")
            
            toSel = []
            lstMinFeatures = []
            for ft in mLayer.getFeatures():
                minFeatureObj = {}
                minFeatureObj["BEG_LINE_COORD_E"] = ft[beg_line_coord_e]
                minFeatureObj["BEG_LINE_COORD_N"] = ft[beg_line_coord_n]
                minFeatureObj["FIN_LINE_COORD_E"] = ft[fin_line_coord_e]
                minFeatureObj["FIN_LINE_COORD_N"] = ft[fin_line_coord_n]
                minFeatureObj["SEG_NAME"] = ft[h.readValueFromProject("SEG_NAME")]
                minFeatureObj["SEG_NAME_C"] = ft[h.readValueFromProject("SEG_NAME_C")]
                lstMinFeatures.append(minFeatureObj)
            
            for f in mLayer.getFeatures():
                fnd = h.Get_Feature_On_Index(lstMinFeatures,f,+1,True,[],True)
                if fnd == None:
                    toSel.append(f.id())

            mLayer.selectByIds(toSel)
                

    def updateAllFeatures(self):
        mLayer = h.GetLayer()
        if mLayer:
            if not mLayer.isEditable():
                mLayer.startEditing()
            
            h.UpdateGeoAttributesAllFeatures()

            mLayer.commitChanges()
            h.ShowMessage(translate("AutomaticGeometricAttributes","Operation executed successfully"))

    def select_input_file(self):
        filename, __ = QFileDialog.getOpenFileName(self.dlg,"Select source file","","*.csv")
        self.dlgExport.txtFileName.setText(filename)

    def importDataShow(self):
        self.dlgExport.show()
        
        self.dlgExport.lblInfoMsg.setText(translate("AutomaticGeometricAttributes","Select the vector input file"))
        try:
            self.dlgExport.btnFileDiaolog.clicked.disconnect()
        except TypeError:
            pass 

        try:
            self.dlgExport.buttonBox.accepted.disconnect()
        except TypeError:
            pass 

        
        self.dlgExport.btnFileDiaolog.clicked.connect(self.select_input_file)
        self.dlgExport.buttonBox.accepted.connect(self.importData)
        self.dlgExport.buttonBox.show()
        self.dlgExport.progressBar.hide()
        result = self.dlgExport.exec_()
    
    def importDataNodeShow(self):
        self.dlgExport.show()
        self.dlgExport.lblInfoMsg.setText(translate("AutomaticGeometricAttributes","Select the node input file"))
        try:
            self.dlgExport.btnFileDiaolog.clicked.disconnect()
        except TypeError:
            pass 

        try:
            self.dlgExport.buttonBox.accepted.disconnect()
        except TypeError:
            pass 

        
        self.dlgExport.btnFileDiaolog.clicked.connect(self.select_input_file)
        self.dlgExport.buttonBox.accepted.connect(self.importNodeData)
        self.dlgExport.buttonBox.show()
        self.dlgExport.progressBar.hide()
        result = self.dlgExport.exec_()



    def importNodeData(self):
        if self.dlgExport.txtFileName.text() == "":
            h.ShowError(translate("AutomaticGeometricAttributes","The file must be specified"))
        else:

            _myLayer = h.GetLayer()

            if _myLayer:

                lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )
                if lst:
                    nodeLayer = lst[0]
                    if nodeLayer:
            
                        _file = open(self.dlgExport.txtFileName.text(),'r')
                        main_dic =  {}
                        headers = []
                        keyIndex = 0
                        cur_idx = 0
                        cur_row = 0
                        seg_name_c = h.readValueFromProject("SEG_NAME_C")
                        nodo_name = "id_nodo"
                        
                        self.dlgExport.buttonBox.hide()
                        self.dlgExport.progressBar.setMinimum(0)
                        self.dlgExport.progressBar.setMaximum(h.GetLayer().featureCount())
                        self.dlgExport.progressBar.setValue(0)
                        self.dlgExport.progressBar.show()
                        QCoreApplication.processEvents()

                        for line in _file:
                            values = line.split(";")
                            if cur_row == 0: # header
                                for v in values:
                                    if v == nodo_name:
                                        keyIndex = cur_idx
                                    cur_idx = cur_idx + 1
                                    headers.append(v[:10].replace("\n",""))
                            else:
                                val_dic = {}
                                cur_idx = 0
                                for v in values:
                                    #if cur_idx != keyIndex:
                                    val_dic[headers[cur_idx]] = v
                                    cur_idx = cur_idx + 1                    

                                main_dic[values[keyIndex]] = val_dic
                                        
                            cur_row = cur_row + 1

                        _file.close()

                        if not nodeLayer.isEditable():
                            nodeLayer.startEditing()
                    
                        
                        for _h in headers:
                            _idx = nodeLayer.fields().lookupField( _h )
                            if _idx == -1:
                                
                                self.createDefaultAtt(nodeLayer,_h,QVariant.String)

                        nodeLayer.commitChanges()
                        
                        if not nodeLayer.isEditable():
                            nodeLayer.startEditing()
                        
                        for f in _myLayer.getFeatures():
                            self.dlgExport.progressBar.setValue(self.dlgExport.progressBar.value() + 1)
                            point = None
                            name = f[seg_name_c]
                            name_f = f[seg_name_c] + "-FINAL"
                            if name in main_dic:

                                geom = f.geometry()
                                geom.convertToSingleType()
                                point = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])

                                if point:
                                    for x in main_dic[name]:                        
                                        nodeLayer.changeAttributeValue( point.id(), nodeLayer.fields().lookupField( x ), main_dic[name][x] )


                            if name_f in main_dic:

                                geom = f.geometry()
                                geom.convertToSingleType()                                
                                point = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[-1])

                                if point:
                                    for x in main_dic[name_f]:                        
                                        nodeLayer.changeAttributeValue( point.id(), nodeLayer.fields().lookupField( x ), main_dic[name_f][x] )
                            
                        _myLayer.commitChanges()
                

        self.dlgExport.accept()

            

    def importData(self):
        if self.dlgExport.txtFileName.text() == "":
            h.ShowError(translate("AutomaticGeometricAttributes","The file must be specified"))
        else:            
            _file = open(self.dlgExport.txtFileName.text(),'r')
            main_dic =  {}
            headers = []
            keyIndex = 0
            cur_idx = 0
            cur_row = 0
            seg_name_c = h.readValueFromProject("SEG_NAME_C")

            self.dlgExport.buttonBox.hide()
            self.dlgExport.progressBar.setMinimum(0)
            self.dlgExport.progressBar.setMaximum(h.GetLayer().featureCount())
            self.dlgExport.progressBar.setValue(0)
            self.dlgExport.progressBar.show()
            QCoreApplication.processEvents()
         
            
            for line in _file:
                values = line.split(";")
                if cur_row == 0: # header
                    for v in values:
                        if v == seg_name_c:
                            keyIndex = cur_idx
                        cur_idx = cur_idx + 1
                        headers.append(v[:10].replace("\n",""))
                else:
                    val_dic = {}
                    cur_idx = 0
                    for v in values:
                        if cur_idx != keyIndex:
                            val_dic[headers[cur_idx]] = v
                        cur_idx = cur_idx + 1                    

                    main_dic[values[keyIndex]] = val_dic
                            
                cur_row = cur_row + 1

            _file.close()

            _myLayer = h.GetLayer()
##            print "inicio"
##            for x in main_dic["001-1"]:
##                print x,main_dic["001-1"][x]
            #print len(main_dic["001-1"])

            if not _myLayer.isEditable():
                _myLayer.startEditing()
            

            for _h in headers:
                if _h != seg_name_c:
                    _idx = _myLayer.fields().lookupField( _h )
                    if _idx == -1:
                        self.createDefaultAtt(_myLayer,_h,QVariant.String)

            _myLayer.commitChanges()
            if not _myLayer.isEditable():
                _myLayer.startEditing()
            
            for f in _myLayer.getFeatures():
                self.dlgExport.progressBar.setValue(self.dlgExport.progressBar.value() + 1)
                if f[seg_name_c] in main_dic:
                    for x in main_dic[f[seg_name_c]]:                        
                        _myLayer.changeAttributeValue( f.id(), _myLayer.fields().lookupField( x ), main_dic[f[seg_name_c]][x] )
                
            _myLayer.commitChanges()
            
        self.dlgExport.accept()
            
        h.ShowMessage(translate("AutomaticGeometricAttributes","Import sucessefull"))
        
    def select_output_file(self):
        filename, __ = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.csv')
        self.dlgExport.txtFileName.setText(filename)
        
    def exportDataShow(self):

        if self.AnalisarPendencias() == False:
            h.ShowError(translate("AutomaticGeometricAttributes","There are errors in the project. Please fix those before exporting."))
            return None
        self.dlgExport.show()
        
        self.dlgExport.lblInfoMsg.setText(translate("AutomaticGeometricAttributes","Select the output file:"))
        try:
            self.dlgExport.btnFileDiaolog.clicked.disconnect()
        except TypeError:
            pass

        try:
            self.dlgExport.buttonBox.accepted.disconnect()
        except TypeError:
            pass 
        
        self.dlgExport.btnFileDiaolog.clicked.connect(self.select_output_file)
        self.dlgExport.buttonBox.accepted.connect(self.exportData)
        self.dlgExport.buttonBox.show()
        self.dlgExport.progressBar.hide()
        result = self.dlgExport.exec_()
        
    def campo_ordem(self, f):
        return f[h.readValueFromProject("SEG_NAME_C")]

    def exportData(self):


        if self.dlgExport.txtFileName.text() == "":
            h.ShowError(translate("AutomaticGeometricAttributes","The file must be specified"))
        else:

            beg_line_coord_e = h.readValueFromProject("BEG_LINE_COORD_E")
            beg_line_coord_n = h.readValueFromProject("BEG_LINE_COORD_N")
            fin_line_coord_e = h.readValueFromProject("FIN_LINE_COORD_E")
            fin_line_coord_n = h.readValueFromProject("FIN_LINE_COORD_N")

            qe = h.readValueFromProject("QE")
            qei = h.readValueFromProject("QEI")
            qef = h.readValueFromProject("QEF")
            cota_i = "COTA_I"
            cota_f = "COTA_F"
            cota = h.readValueFromProject("COTA")
            mylayer = h.GetLayer()

            self.dlgExport.buttonBox.hide()
            self.dlgExport.progressBar.setMinimum(0)
            if self.dlgExport.cbSelecionados.isChecked():
                vetores = mylayer.selectedFeatures()
            else:  
                vetores = mylayer.getFeatures()
            dicionario = [f for f in vetores]

            dicionario.sort(key=self.campo_ordem)
            self.dlgExport.progressBar.setMaximum(len(dicionario))
            self.dlgExport.progressBar.setValue(0)
            self.dlgExport.progressBar.show()
            QCoreApplication.processEvents()
            
            #export data
            filename = self.dlgExport.txtFileName.text()
            output_file = open(filename, 'wb')
           
            

            lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )
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
            fieldnames.append(h.readValueFromProject("SEG_NAME"))
            fieldnames.append(h.readValueFromProject("SEG_NAME_C"))
            fieldnames.append(h.readValueFromProject("EXT_FIELD_NAME"))
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


            fieldnames.append(h.readValueFromProject("AUX_PROF_I"))
            fieldnames.append(h.readValueFromProject("AUX_POS"))
            fieldnames.append(h.readValueFromProject("AUX_PROF_F"))
            fieldnames.append(cota_i)
            fieldnames.append(cota_f)
            fieldnames.append("TRM_(N+1)")
            fieldnames.append("ID_TRM")
            fieldnames.append(beg_line_coord_e)
            fieldnames.append(beg_line_coord_n)
            fieldnames.append(fin_line_coord_e)
            fieldnames.append(fin_line_coord_n)
            fieldnames.append(h.readValueFromProject("AUX_PAV_1"))
            fieldnames.append(h.readValueFromProject("AUX_PAV_2"))
            fieldnames.append(h.readValueFromProject("AUX01"))
            fieldnames.append(h.readValueFromProject("AUX02"))
            fieldnames.append(h.readValueFromProject("AUX03"))
            fieldnames.append(h.names()["NODO_I"][0])
            fieldnames.append(h.names()["NODO_F"][0])


            line = ';'.join(x for x in fieldnames) + '\n'
            unicode_line = line.encode('utf-8')
            output_file.write(unicode_line)

            lstMinFeatures = []
            lstFeatures = []
            for ft in dicionario:
                try:
                    pol = ft.geometry().isEmpty()
                except:
                    h.ShowError(translate("AutomaticGeometricAttributes","O trecho " + ft[h.readValueFromProject("SEG_NAME_C")] + " esta corrompido. nao possui geometria" ))
                    break
                    
                minFeatureObj = {}
                minFeatureObj["BEG_LINE_COORD_E"] = ft[beg_line_coord_e]
                minFeatureObj["BEG_LINE_COORD_N"] = ft[beg_line_coord_n]
                minFeatureObj["FIN_LINE_COORD_E"] = ft[fin_line_coord_e]
                minFeatureObj["FIN_LINE_COORD_N"] = ft[fin_line_coord_n]
                minFeatureObj["SEG_NAME"] = ft[h.readValueFromProject("SEG_NAME")]
                minFeatureObj["SEG_NAME_C"] = ft[h.readValueFromProject("SEG_NAME_C")]
                lstMinFeatures.append(minFeatureObj)
                lstFeatures.append(ft)
           
            for f in dicionario:

                self.dlgExport.progressBar.setValue(self.dlgExport.progressBar.value() + 1)
                
                values = []
                geom = f.geometry()
                isBegin,isEnd,totalEnd = h.Get_Aux_Trm(f.id(),lstFeatures)

                #SEG_NAME_C
                
                name = f.attributes()[mylayer.fields().lookupField( h.readValueFromProject('SEG_NAME_C') )]
                o_name = name

                geom.convertToSingleType()
                vl_id = '{0:.6f}, {1:.6f}'.format(geom.asPolyline()[0].x(), geom.asPolyline()[0].y())
                values.append(str(vl_id))
                values.append(str(str(f[h.readValueFromProject("EXT_FIELD_NAME")])))
                values.append(str(str(f[beg_line_coord_e])))
                values.append(str(str(f[beg_line_coord_n])))
                values.append(str(str(f[fin_line_coord_e])))
                values.append(str(str(f[fin_line_coord_n])))
                values.append(str(f[h.readValueFromProject("SEG_NAME")]))
                values.append(str(name))
                values.append(str(f[h.readValueFromProject("AUX_POS")]))
                values.append(str(f[h.readValueFromProject("AUX_PAV_1")]))
                values.append(str(f[h.readValueFromProject("AUX_PAV_2")]))
                values.append(str(f[h.readValueFromProject("AUX_PROF_I")]))
                values.append(str(f[h.readValueFromProject("AUX_PROF_F")]))
                values.append(str(f[h.readValueFromProject("AUX01")]))
                values.append(str(f[h.readValueFromProject("AUX02")]))
                values.append(str(f[h.readValueFromProject("AUX03")]))

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
                
                fnd = h.Get_Feature_On_Index(lstMinFeatures,f,-1)
                if fnd != None:
                    nameOf = fnd["SEG_NAME_C"]
                    values.append(str(nameOf))
                else:
                    values.append("")
                #TRM_(N-1)_B                
                fnd = h.Get_Feature_On_Index(lstMinFeatures,f,-1,False)
                if fnd != None:
                    nameOf = fnd["SEG_NAME_C"]
                    values.append(str(nameOf))
                    toExclud = fnd["SEG_NAME"]

                    #TRM_(N-1)_C                
                    fnd = h.Get_Feature_On_Index(lstMinFeatures,f,-1,False,[toExclud])
                    if fnd != None:
                        nameOf = fnd["SEG_NAME_C"]
                        values.append(str(nameOf))
                    else:
                        values.append("")
                        
                else:
                    values.append("")
                    values.append("")

                
                #TRM_(N+1)
                
                fnd = h.Get_Feature_On_Index(lstMinFeatures,f,1,False,[],True)

                if fnd != None:
                    nameOf = fnd["SEG_NAME_C"]
                    values.append(str(nameOf))
                else:
                    values.append("")               

                
                if nodeLayer:
                    point1 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])
                    point2 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[-1])

                    if point1:

                        _qeList = point1.attributes()[nodeLayer.fields().lookupField( h.readValueFromProject('QE') )]
                        
                        #QE
                        values.append(str(_qeList))

                        if _qeList:
                            qei,qef = h.GetQEFromBlockLayer(_qeList.split(","))

                            #QEI
                            values.append(str(qei))

                            #QEF
                            values.append(str(qef))
                            
                        else:
                            #QEI
                            values.append("")
                            #QEF
                            values.append("")
                            
                        #COTA_I
                        values.append(str(point1.attributes()[cota_idx]))

                        #NODO_I
                        values.append(str(o_name))
                        
                    else:
                        values.append("")
                        values.append("")
                        values.append("")
                        values.append("")

                    if point2:                  
                        #COTA_F
                        values.append(str(point2.attributes()[cota_idx]))

                        #NODO_F
                        if totalEnd:
                            nodo_name = name + "-FINAL"
                        else:
                            fnd = h.Get_Feature_On_Index(lstMinFeatures,f,+1,True,[],True)
                            if fnd:
                                nodo_name = fnd['SEG_NAME_C'] 
                            

                        values.append(str(nodo_name))
                    else:
                        values.append("")
          
                v2 = []
                v2.append(values[16])
                v2.append(values[17])
                v2.append(values[6])
                v2.append(values[7])
                v2.append(values[1])
                v2.append(values[18])
                v2.append(values[19])
                v2.append(values[20])
                v2.append(values[22])
                v2.append(values[24])
                v2.append(values[23])
                v2.append(values[11])
                v2.append(values[8])
                v2.append(values[12])
                v2.append(values[25])
                v2.append(values[27])
                v2.append(values[21])
                v2.append(values[0])
                v2.append(values[2])
                v2.append(values[3])
                v2.append(values[4])
                v2.append(values[5])
                v2.append(values[9])
                v2.append(values[10])
                v2.append(values[13])
                v2.append(values[14])
                v2.append(values[15])
                v2.append(values[26])
                v2.append(values[28])

                v2.append("")

                line = ';'.join(v2) + '\n'
                unicode_line = line.encode('utf-8')
                output_file.write(unicode_line)
            output_file.close()

            self.dlgExport.accept()
            
            h.ShowMessage(translate("AutomaticGeometricAttributes","Export sucessefull"))

    def showNameDialog(self,nVertices):
        
        #call the dialog to name the patch
        self.dlgNameSegment.txtSegmentName.setText("")
        self.dlgNameSegment.txtInitialCount.setText("")

        self.dlgNameSegment.SetNVertices(nVertices)

        self.dlgNameSegment.txtInitialCount.setValidator( QIntValidator(0, 100) )

        self.dlgNameSegment.txtSegmentName.setFocus()
        # Run the dialog event loop
        try:
            result = self.dlgNameSegment.exec_()
        except Exception as e: 
            logger.Exception('main crashed. Error: $s', e)

        if result:
            return result,self.dlgNameSegment.txtSegmentName.text(),int(self.dlgNameSegment.txtInitialCount.text())
        else:
            return result,"",0

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                translate("AutomaticGeometricAttributes",u'&saniHUB RedBasica'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def handleAddedFeatures(self,fid, geom = None):
        self.updateFeatureAttrs(fid,geom,1)

    def handleDeletedFeatures(self, fids):
        self.UpdatePatches()

    def NameAPatch(self):
        if self.NamingMode == False:
            self.BeginFeature = None
            self.FinalFeature = None
            self.NamingMode = True
            self.dockPatchs.btnNamePatch.setText(translate("AutomaticGeometricAttributes","Cancel"))
            self.dockPatchs.lblMsg.setText(translate("AutomaticGeometricAttributes","Select the begin feature of the patch"))
            h.GetLayer().selectByIds([])
            self.iface.actionSelect().trigger()
            try:
                h.GetLayer().selectionChanged.disconnect( self.SelectedFeatureToName )
            except TypeError:
                pass 
            
            h.GetLayer().selectionChanged.connect( self.SelectedFeatureToName )
        else:
            self.BeginFeature = None
            self.FinalFeature = None
            self.NamingMode = False
            self.dockPatchs.btnNamePatch.setText(translate("AutomaticGeometricAttributes","Name a Patch"))
            self.dockPatchs.lblMsg.setText('')
            try:
                h.GetLayer().selectionChanged.disconnect( self.SelectedFeatureToName )
            except TypeError:
                pass

    def CreateSeparator(self,hLay,vLay,text):
        lab = QLabel()
        lab.setText(text)
        #lab.setAlignment(Qt.AlignCenter)
        f = QFont()            
        #f.setUnderline(True)
        lab.setFont(f)
        lab.setStyleSheet("QLabel { color : gray; font-weight: bold; }");
        hLay.addWidget(lab)
        vLay.addLayout(hLay)

    
    def CreateElementAttributeInLay(self,hLay,vLay,name,displayName,value,readOnly = False, onEnterPressFunction = None, tooltipText = None):
        lab = QLabel()
        lab.setText(translate("AutomaticGeometricAttributes","field_" + displayName,displayName))
        lab.setFixedWidth(100)
        if tooltipText:
            lab.setToolTip(translate("AutomaticGeometricAttributes","tooltip_" + tooltipText))
        le = QLineEdit()
        le.setObjectName(name)
        le.setReadOnly(readOnly)
        if value:
            le.setText(str(value))

        if onEnterPressFunction:
            le.returnPressed.connect(onEnterPressFunction)

        if readOnly == False:
            color = "blue"
        else:
            color = "black"
            
        lab.setStyleSheet("QLabel { color : "+ color +"; padding-left: 10px }");

        teste = QHBoxLayout()
        teste.addWidget(lab)
        teste.addWidget(le)
        hLay.addLayout(teste)
        
        #teste.addLayout(hLay)
        vLay.addLayout(hLay)

    def click_expand_patch(self,btn):
        if self.Group1Expanded:
            self.Group1WHeiht = self.Group1W.height()
            self.Group1W.setFixedHeight(0)
            self.Group1Expanded = False
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-right.png')
            btn.setIcon(icon)
        else:
            self.Group1W.setFixedHeight(self.Group1WHeiht)
            self.Group1Expanded = True
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-down.png')
            btn.setIcon(icon)

        h.saveValueOnProject("Expanded_Group1",str(self.Group1Expanded))
        

    def click_expand_node(self,btn):
        if self.Group2Expanded:
            self.Group2WHeiht = self.Group2W.height()
            self.Group2W.setFixedHeight(0)
            self.Group2Expanded = False
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-right.png')
            btn.setIcon(icon)
        else:
            self.Group2W.setFixedHeight(self.Group2WHeiht)
            self.Group2Expanded = True
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-down.png')
            btn.setIcon(icon)

        h.saveValueOnProject("Expanded_Group2",str(self.Group2Expanded))

    def click_expand_hidraulic(self,btn):
        if self.Group3Expanded:
            self.Group3WHeiht = self.Group3W.height()
            self.Group3W.setFixedHeight(0)
            self.Group3Expanded = False
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-right.png')
            btn.setIcon(icon)
        else:
            self.Group3W.setFixedHeight(self.Group3WHeiht)
            self.Group3Expanded = True
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-down.png')
            btn.setIcon(icon)

        h.saveValueOnProject("Expanded_Group2",str(self.Group2Expanded))

    def InitializeGroupAreas(self):
        self.Group1WHeiht = self.Group1W.height()
        self.Group2WHeiht = self.Group2W.height()
        self.Group3WHeiht = self.Group3W.height()
        
        _v = h.readValueFromProject("Expanded_Group1")        
        if _v == "False":
            self.click_expand_patch(self.btnG1)
            
        _v = h.readValueFromProject("Expanded_Group2")
        if _v == "False":
            self.click_expand_node(self.btnG2)

        _v = h.readValueFromProject("Expanded_Group3")
        if _v == "False":
            self.click_expand_hidraulic(self.btnG3)

    def SelectedFeatureAttrWindows(self,selected,deselected,clearAndSelect):
        if len(selected) == 1:
            self.dockPatchs.SetSelectedId(selected[0])            

            beg_line_coord_e = h.readValueFromProject("BEG_LINE_COORD_E")
            beg_line_coord_n = h.readValueFromProject("BEG_LINE_COORD_N")
            fin_line_coord_e = h.readValueFromProject("FIN_LINE_COORD_E")
            fin_line_coord_n = h.readValueFromProject("FIN_LINE_COORD_N")

            lstMinFeatures = []
            lstFeatures = []
            for ft in h.GetLayer().getFeatures():
                try:
                    pol = ft.geometry().isEmpty()
                except:
                    h.ShowError(translate("AutomaticGeometricAttributes","O trecho " + ft[h.readValueFromProject("SEG_NAME_C")] + " esta corrompido. nao possui geometria" ))
                    break
                    
                minFeatureObj = {}
                minFeatureObj["BEG_LINE_COORD_E"] = ft[beg_line_coord_e]
                minFeatureObj["BEG_LINE_COORD_N"] = ft[beg_line_coord_n]
                minFeatureObj["FIN_LINE_COORD_E"] = ft[fin_line_coord_e]
                minFeatureObj["FIN_LINE_COORD_N"] = ft[fin_line_coord_n]
                minFeatureObj["SEG_NAME"] = ft[h.readValueFromProject("SEG_NAME")]
                minFeatureObj["SEG_NAME_C"] = ft[h.readValueFromProject("SEG_NAME_C")]
                lstMinFeatures.append(minFeatureObj)
                lstFeatures.append(ft)   

            _myLayer = h.GetLayer()

            iterator = h.GetLayer().getFeatures(QgsFeatureRequest().setFilterFid(selected[0]))
            feature = next(iterator)
            geom = feature.geometry()
            geom.convertToSingleType()
            
            wd = QWidget()
            self.dockPatchs.saPropFeatures.setWidget(wd)           

            vLayP = QHBoxLayout(wd)
            hLayP = QVBoxLayout()
            vLayP.setAlignment(Qt.AlignTop)

            wdG1 = QWidget()
            btnG1 = QPushButton()
            btnG1.setText(translate("AutomaticGeometricAttributes","Patch Info"))
            btnG1.clicked.connect(lambda: self.click_expand_patch(btnG1))
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-down.png')
            btnG1.setIcon(icon)

            self.btnG1 = btnG1
            self.Group1W = wdG1
            
            
            self.Group1Expanded = True

##            #ID_TRM
##            vl_id = str(round(geom.vertexAt( 0 )[0],6)) + "," + str(round(geom.vertexAt( 0 )[1],6))
##            self.CreateElementAttributeInLay(hLayP,vLayP, "ID_TRM",translate("AutomaticGeometricAttributes","ID_TRM"),
##                                   vl_id ,True)

            #SEG_NAME_C
            
            name = feature.attributes()[_myLayer.fields().lookupField( h.readValueFromProject('SEG_NAME_C') )]
            o_name = name

            
            self.CreateElementAttributeInLay(hLayP,vLayP,h.readValueFromProject('SEG_NAME_C'),translate("AutomaticGeometricAttributes",h.readValueFromProject("SEG_NAME_C")),
                                  name ,True, None, "SEG_NAME_C")

            
            lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )
            point1 = None
            point2 = None
            
            if lst:
                nodeLayer = lst[0]
                if nodeLayer:
                    point1 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])
                    if point1:
                        _qeList = point1.attributes()[nodeLayer.fields().lookupField( h.readValueFromProject('QE') )]
                #QE
                        self.CreateElementAttributeInLay(hLayP,vLayP,h.names()['QE'][0],translate("AutomaticGeometricAttributes",h.names()['QE'][0]),
                                       _qeList,False,self.saveAttributesDock,"QE")
    
            hLayP.addWidget(btnG1)        
            vLayP.addLayout(hLayP)

            hLayP.addWidget(wdG1)        
            vLayP.addLayout(hLayP)
            
            vLay = QHBoxLayout(wdG1)
            hLay = QVBoxLayout()

            
            #EXT_FIELD_NAME
            self.CreateElementAttributeInLay(hLay,vLay,h.readValueFromProject("EXT_FIELD_NAME"),translate("AutomaticGeometricAttributes",h.readValueFromProject("EXT_FIELD_NAME")),
                                   feature.attributes()[_myLayer.fields().lookupField( h.readValueFromProject("EXT_FIELD_NAME") )],True, None, "EXT_FIELD_NAME")

            #DN - IMPORT
            f_name = 'DN'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, f_name)

            #S - IMPORT
            f_name = 'S'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, f_name)

            #h_col_p1 - IMPORT
            f_name = 'h_col_p1'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, f_name)

            #h_col_p2 - IMPORT
            f_name = 'h_col_p2'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, f_name)


            # ############# SEPARATOR ############
            self.CreateSeparator(hLay,vLay,translate("AutomaticGeometricAttributes","FALL DEVICES"))

            #caida_p2 - IMPORT
            f_name = 'caida_p2'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, f_name)

            #caida_p2_h - IMPORT
            f_name = 'caida_p2_h'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, f_name)

            # ############# SEPARATOR ############
            self.CreateSeparator(hLay,vLay,translate("AutomaticGeometricAttributes","COORDINATES"))
            

            #BEG_LINE_COORD_E
            self.CreateElementAttributeInLay(hLay,vLay,h.readValueFromProject('BEG_LINE_COORD_E'),translate("AutomaticGeometricAttributes",h.readValueFromProject("BEG_LINE_COORD_E")),
                                   feature.attributes()[_myLayer.fields().lookupField( h.readValueFromProject('BEG_LINE_COORD_E') )],True, None,"BEG_LINE_COORD_E")
            #BEG_LINE_COORD_N
            self.CreateElementAttributeInLay(hLay,vLay,h.readValueFromProject('BEG_LINE_COORD_N'),translate("AutomaticGeometricAttributes",h.readValueFromProject("BEG_LINE_COORD_N")),
                                   feature.attributes()[_myLayer.fields().lookupField( h.readValueFromProject('BEG_LINE_COORD_N') )],True, None,"BEG_LINE_COORD_N")
            
            #FIN_LINE_COORD_E
            self.CreateElementAttributeInLay(hLay,vLay,h.readValueFromProject('FIN_LINE_COORD_E'),translate("AutomaticGeometricAttributes",h.readValueFromProject("FIN_LINE_COORD_E")),
                                   feature.attributes()[_myLayer.fields().lookupField( h.readValueFromProject('FIN_LINE_COORD_E') )],True, None,"FIN_LINE_COORD_E")

            #FIN_LINE_COORD_N
            self.CreateElementAttributeInLay(hLay,vLay,h.readValueFromProject('FIN_LINE_COORD_N'),translate("AutomaticGeometricAttributes",h.readValueFromProject("FIN_LINE_COORD_N")),
                                   feature.attributes()[_myLayer.fields().lookupField( h.readValueFromProject('FIN_LINE_COORD_N') )],True, None,"FIN_LINE_COORD_N")

##            #SEG_NAME
##            self.CreateElementAttributeInLay(hLay,vLay,h.readValueFromProject('SEG_NAME'),translate("AutomaticGeometricAttributes",h.readValueFromProject("SEG_NAME")),
##                                   feature.attributes()[_myLayer.fields().lookupField( h.readValueFromProject('SEG_NAME') )],True)


##            #ANGLE
##            p1 = QgsPoint(geom.vertexAt( 0 )[0] ,geom.vertexAt( 0 )[1] )
##            p2 = QgsPoint(geom.asPolyline()[-1][0], geom.asPolyline()[-1][1])
##            az = p1.azimuth(p2)
##            self.CreateElementAttributeInLay(hLay,vLay,"ANGLE","ANGLE",
##                                   az,True)

            isBegin,isEnd,totalEnd = h.Get_Aux_Trm(feature.id(),lstFeatures)           
            

##            #AUX_TRM_I
##            self.CreateElementAttributeInLay(hLay,vLay,h.names()['AUX_TRM_I'][0],translate("AutomaticGeometricAttributes",h.names()['AUX_TRM_I'][0]),
##                                   translate("AutomaticGeometricAttributes",str(isBegin)),True)
##
##            #AUX_TRM_F
##            self.CreateElementAttributeInLay(hLay,vLay,h.names()['AUX_TRM_F'][0],translate("AutomaticGeometricAttributes",h.names()['AUX_TRM_F'][0]),
##                                   translate("AutomaticGeometricAttributes",str(isEnd)),True)

            lst = QgsProject.instance().mapLayersByName( h.readValueFromProject('NODE_LAYER') )


            point1 = None
            point2 = None
            
            if lst:
                nodeLayer = lst[0]
                if nodeLayer:

                    wdG2 = QWidget()
                    btnG2 = QPushButton()
                    btnG2.setText(translate("AutomaticGeometricAttributes","Node Info"))
                    btnG2.clicked.connect(lambda: self.click_expand_node(btnG2))
                    icon_path = ':/plugins/RedBasica/icons/'
                    icon = QIcon(icon_path + 'arrow-down.png')
                    btnG2.setIcon(icon)

                    self.btnG2 = btnG2
                    self.Group2W = wdG2
                    self.Group2Expanded = True

                    hLayP.addWidget(btnG2)        
                    vLayP.addLayout(hLayP)

                    hLayP.addWidget(wdG2)        
                    vLayP.addLayout(hLayP)
                    
                    vLay = QHBoxLayout(wdG2)
                    hLay = QVBoxLayout()
                    geom.convertToSingleType()
                    #self.iface.messageBar().pushMessage("Error", "XI: "+str(geom.asPolyline()[0].x()), level=Qgis.Critical, duration=3)
                    #self.iface.messageBar().pushMessage("Error", "XF: "+str(geom.asPolyline()[-1].x()), level=Qgis.Critical, duration=3)
                    point1 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[0])
                    point2 = h.GetPointFromCoordinates(nodeLayer.getFeatures(),geom.asPolyline()[-1])

                    if point1:
                        self.CreateSeparator(hLay,vLay,translate("AutomaticGeometricAttributes","UPSTREAM NODE"))
                        
                        

                        #NODO_I
                        self.CreateElementAttributeInLay(hLay,vLay,h.names()['NODO_I'][0],translate("AutomaticGeometricAttributes",h.names()['NODO_I'][0]),
                                               o_name,True, None, "NODO_I")

                        #Nodo_tipo - IMPORT
                        f_name = 'Nodo_tipo'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point1.attributes()[fIdx],True, None, "Nodo_tipo")
                        
                        #COTA_I
                        self.CreateElementAttributeInLay(hLay,vLay,h.names()['COTA_I'][0],translate("AutomaticGeometricAttributes",h.names()['COTA_I'][0]),
                                               point1.attributes()[nodeLayer.fields().lookupField( h.readValueFromProject('COTA') )]
                                               ,False,self.saveAttributesDock, "COTA_I")

                        #CF_nodo - IMPORT
                        f_name = 'CF_nodo'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point1.attributes()[fIdx],True, None, "CF_nodo")

                        #h_nodo_NT - IMPORT
                        f_name = 'h_nodo_NT'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point1.attributes()[fIdx],True, None, "h_nodo_NT")

                        #h_nodo_tp - IMPORT
                        f_name = 'h_nodo_tp'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point1.attributes()[fIdx],True, None, "h_nodo_tp")   

                    if point2:
                        self.CreateSeparator(hLay,vLay,translate("AutomaticGeometricAttributes","DOWNSTREAM NODE"))
                        

                        #NODO_F
                        nodo_name = ""
                        if totalEnd:
                            nodo_name = name + "-FINAL"
                        else:
                            fnd = h.Get_Feature_On_Index(lstMinFeatures,feature,+1,True,[],True)
                            if fnd:
                                nodo_name = fnd['SEG_NAME_C']
                        
                        self.CreateElementAttributeInLay(hLay,vLay,h.names()['NODO_F'][0],translate("AutomaticGeometricAttributes",h.names()['NODO_F'][0]),
                                               nodo_name,True, None, "NODO_F")

                        #Nodo_tipo - IMPORT
                        f_name = 'Nodo_tipo'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point2.attributes()[fIdx],True, None, "Nodo_tipo")
                        #Type (CI or PV) and size (CI-60 ...) of the inspection device
                        #COTA_F
                        self.CreateElementAttributeInLay(hLay,vLay,h.names()['COTA_F'][0],translate("AutomaticGeometricAttributes",h.names()['COTA_F'][0]),
                                               point2.attributes()[nodeLayer.fields().lookupField( h.readValueFromProject('COTA') )]
                                               ,False,self.saveAttributesDock, "COTA_F")

                        #CF_nodo - IMPORT
                        f_name = 'CF_nodo'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point2.attributes()[fIdx],True, None, "CF_nodo")

                        #h_nodo_NT - IMPORT
                        f_name = 'h_nodo_NT'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point2.attributes()[fIdx],True, None, "h_nodo_NT")

                        #h_nodo_tp - IMPORT
                        f_name = 'h_nodo_tp'
                        fIdx = nodeLayer.fields().lookupField( f_name )
                        if fIdx > -1:
                            self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                               point2.attributes()[fIdx],True, None, "h_nodo_tp")   
                    else:
                        # fix_print_with_import
                        print('falhou em achar o nó 2')

            wdG3 = QWidget()
            btnG3 = QPushButton()
            btnG3.setText(translate("AutomaticGeometricAttributes","Hydraulic Info"))
            btnG3.clicked.connect(lambda: self.click_expand_hidraulic(btnG3))
            icon_path = ':/plugins/RedBasica/icons/'
            icon = QIcon(icon_path + 'arrow-down.png')
            btnG3.setIcon(icon)

            self.btnG3 = btnG3
            self.Group3W = wdG3
            self.Group3Expanded = True

            hLayP.addWidget(btnG3)        
            vLayP.addLayout(hLayP)

            hLayP.addWidget(wdG3)        
            vLayP.addLayout(hLayP)
            
            vLay = QHBoxLayout(wdG3)
            hLay = QVBoxLayout()

            self.CreateSeparator(hLay,vLay,translate("AutomaticGeometricAttributes","CONTRIBUTION UNITS"))

            if point1:
                _qeList = point1.attributes()[nodeLayer.fields().lookupField( h.readValueFromProject('QE') )]
                #QE
               # self.CreateElementAttributeInLay(hLay,vLay,h.names()['QE'][0],translate("AutomaticGeometricAttributes",h.names()['QE'][0]),
               #                        _qeList,False,self.saveAttributesDock,"QE")

                if _qeList:
                    qei,qef = h.GetQEFromBlockLayer(_qeList.split(","))

                    #QEI
                    self.CreateElementAttributeInLay(hLay,vLay,h.names()['QEI'][0],translate("AutomaticGeometricAttributes",h.names()['QEI'][0]),
                                           qei,True,None,"QEI")

                    #QEF
                    self.CreateElementAttributeInLay(hLay,vLay,h.names()['QEF'][0],translate("AutomaticGeometricAttributes",h.names()['QEF'][0]),
                                           qef,True,None,"QEF")
                    
            self.CreateSeparator(hLay,vLay,translate("AutomaticGeometricAttributes","FLOW RATE"))

            #Qt_i - IMPORT
            f_name = 'Qt_i'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "Qt_i")

            #Qt_f - IMPORT
            f_name = 'Qt_f'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "Qt_f")

            #Q_i - IMPORT
            f_name = 'Q_i'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "Q_i")

            #Q_f - IMPORT
            f_name = 'Q_f'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "Q_f")

            self.CreateSeparator(hLay,vLay,translate("AutomaticGeometricAttributes","HYDRAULIC CONDITIONS"))

            #n - IMPORT
            f_name = 'n'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "n")

            #yn_i - IMPORT
            f_name = 'yn_i'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "yn_i")

            #yn_f - IMPORT
            f_name = 'yn_f'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "yn_f")

            #yrel_i - IMPORT
            f_name = 'yrel_i'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "yrel_i")

            #yrel_f - IMPORT
            f_name = 'yrel_f'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "yrel_f")

            #Trativa_i - IMPORT
            f_name = 'Trativa_i'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "Trativa_i")

            #Trativa_f - IMPORT
            f_name = 'Trativa_f'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "Trativa_f")

            #V_i - IMPORT
            f_name = 'V_i'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "V_i")

            #V_f - IMPORT
            f_name = 'V_f'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "V_f")

            #Vc - IMPORT
            f_name = 'Vc'
            fIdx = _myLayer.fields().lookupField( f_name )
            if fIdx > -1:
                self.CreateElementAttributeInLay(hLay,vLay,f_name,f_name,
                                   feature.attributes()[fIdx],True, None, "Vc")


            
            #self.InitializeGroupAreas()
            
        
        elif len(selected) == 0:
            self.dockPatchs.SetSelectedId(None)
            
            lab = QLabel()
            lab.setText(translate("AutomaticGeometricAttributes","No feature selected"))
            self.dockPatchs.saPropFeatures.setWidget(lab)
        elif len(selected) > 1:
            self.dockPatchs.SetSelectedId(None)
            
            lab = QLabel()
            lab.setText(translate("AutomaticGeometricAttributes","More than one feature are selected"))
            self.dockPatchs.saPropFeatures.setWidget(lab)

    def SelectedFeatureToName(self,selected,deselected,clearAndSelect):
        if len(selected) > 0:
            if self.BeginFeature == None: # first click
                if len(selected) == 1:
                    self.BeginFeature = selected[0]
                    self.dockPatchs.lblMsg.setText(translate("AutomaticGeometricAttributes","Now, select the final feature of the patch"))
                else:
                    h.GetLayer().selectByIds([])
            else: #second click
                
                self.FinalFeature = selected[0]
                self.dockPatchs.lblMsg.setText("")
                self.dockPatchs.btnNamePatch.setText(translate("AutomaticGeometricAttributes","Name a patch"))
                _myLayer = h.GetLayer()
                _myLayer.selectionChanged.disconnect( self.SelectedFeatureToName )

                # adjust all geo atts
                h.UpdateGeoAttributesAllFeatures()
                
                is_ok, fnd_list = h.GetPatchBetween(self.BeginFeature,self.FinalFeature)
                
                if is_ok:
                    #call the dialog to name the patch
                    
                    result,prefixName,initialCount = self.showNameDialog(len(fnd_list)+1)

                    if result:                    
                        count = 1
                        

                        if not _myLayer.isEditable():
                            _myLayer.startEditing()                       
                            
                        for b in fnd_list:
                            
                            _myLayer.changeAttributeValue( b, _myLayer.fields().lookupField( h.readValueFromProject('SEG_NAME' ) ), prefixName )
                            _myLayer.changeAttributeValue( b, _myLayer.fields().lookupField( h.readValueFromProject('SEG_NAME_C' ) ), prefixName + '-' + str(initialCount).zfill(3) )
                            initialCount = initialCount + 1

                        self.UpdatePatches()
                        self.refresh_layers()
                else:
                    h.ShowError(translate("AutomaticGeometricAttributes","Not possible to name the chosen patch, possible cause: disconected patch"))

                self.BeginFeature = None
                self.NamingMode = False
                self.FinalFeature = None
            

    def UpdatePatches(self):
        mydic = {}
#        
#        myLayer = h.GetLayer()
#        
#        if myLayer:
#            fields = myLayer.fields()
#            # name of the fields
#            for feature in myLayer.getFeatures():
#                vl = h.GetAttributeValue(myLayer,feature.id(),h.readValueFromProject('SEG_NAME' ))
#                if vl:
#                    if vl not in mydic:
#                        mydic[vl] = [feature.id()]
#                    else:
#                        mydic[vl].append(feature.id())
#
#
#            self.patch_dict = mydic
#            self.FillPatchesTable()


    def FillPatchesTable(self):
        rowCount = len(self.patch_dict)
        self.dockPatchs.tblPatches.setRowCount(rowCount)
        total_length = 0
        

        row = 0
        for k in list(self.patch_dict.keys()):
            self.dockPatchs.tblPatches.setItem(row,0,QTableWidgetItem(k))
            self.dockPatchs.tblPatches.setItem(row,1,QTableWidgetItem(str(len(self.patch_dict[k]))))

            length = h.GetExtensionSegment(self.patch_dict[k])
            total_length = total_length + length
            
            self.dockPatchs.tblPatches.setItem(row,2,QTableWidgetItem('{0:.2f}'.format(length)))
            row = row + 1

        self.dockPatchs.txtTotalLength.setText(str(total_length))


    def createPointLayer(self):

        layers = QgsProject.instance().mapLayers().values()

        self.dlgCreatePointLayerImportRaster.cboRasterLayer.clear()
        icon_path = ':/plugins/RedBasica/icons/empty.png'
        icon = QIcon(icon_path)
        self.dlgCreatePointLayerImportRaster.cboRasterLayer.addItem( icon,translate("AutomaticGeometricAttributes","None") )
        self.dlgCreatePointLayerImportRaster.cboRasterLayer.setItemData(0, QColor(Qt.gray), Qt.TextColorRole)
        for layer in layers:
            if layer.type() == QgsMapLayer.RasterLayer:
                self.dlgCreatePointLayerImportRaster.cboRasterLayer.addItem( layer.name() )

        self.dlgCreatePointLayerImportRaster.txtNodeLayertName.setText(h.readValueFromProject("NODE_LAYER",h.names()["NODE_LAYER"][0]))
        
        self.dlgCreatePointLayerImportRaster.show()

        result = self.dlgCreatePointLayerImportRaster.exec_()
    # See if OK was pressed
        

    def disconnectActualLayer(self, layer):
        try:
            layer.featureAdded.disconnect( self.handleAddedFeatures )
        except TypeError:
            pass 

        try:
            layer.featuresDeleted.disconnect( self.handleDeletedFeatures )
        except TypeError:
            pass 

        try:
            layer.geometryChanged.disconnect( self.updateFeatureAttrs )
        except TypeError:
            pass

        try:
            layer.selectionChanged.disconnect( self.SelectedFeatureAttrWindows )
        except TypeError:
            pass

##        try:
##            layer.beforeCommitChanges.disconnect ( self.SetSupressNameFormTrue )
##        except TypeError:
##            pass
##
##        try:
##            layer.committedGeometriesChanges.disconnect ( self.SetSupressNameFormFalse )
##        except TypeError:
##            pass 

    def createDefaultAttrsInLayer(self,layer):

        if not layer.isEditable():
            layer.startEditing()

        for n in h.names():
            splited = h.names()[n][5].split(";")
            fnd = [x for x in splited if x == "PATCH"]
            if len(fnd) > 0:
                if h.names()[n][6] == "ATTRIBUTE":
                    self.createDefaultAtt(layer,h.readValueFromProject(n,h.names()[n][0]),h.names()[n][1],h.names()[n][2],h.names()[n][3],h.names()[n][4])                 
        
        layer.commitChanges()
                                          
##        self.createDefaultAtt(layer,h.readValueFromProject("BEG_LINE_COORD_E"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("BEG_LINE_COORD_N"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("FIN_LINE_COORD_E"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("FIN_LINE_COORD_N"),h.names()['LABEL_X'][1])      
##        self.createDefaultAtt(layer,h.readValueFromProject("SEG_NAME"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("SEG_NAME_C"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX_POS"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX_PAV_1"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX_PAV_2"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX_PROF_I"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX_PROF_F"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX01"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX02"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.readValueFromProject("AUX03"),h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.names()['LABEL_X'][0],h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.names()['LABEL_Y'][0],h.names()['LABEL_X'][1])
##        self.createDefaultAtt(layer,h.names()['LABEL_VIS'][0],h.names()['LABEL_X'][1])

        

    def createDefaultAtt(self,layer,attName,attType,attTypeName = None,Lenght = None, Precision = None):
        fieldIdx = layer.fields().lookupField(attName)

        if fieldIdx == -1:
            if attTypeName:
                layer.dataProvider().addAttributes([QgsField(attName, attType, attTypeName, Lenght, Precision)])
            else:
                layer.dataProvider().addAttributes([QgsField(attName, attType)])
            
    def startHandler(self, addedLayers = None):
        #self.iface.messageBar().pushMessage("Error", "I'm sorry Dave, I'm afraid I can't do that"+str(addedLayers), level=Qgis.Critical)
        layerName = h.readValueFromProject('LAYER')

        addHandler = True
        
        if addedLayers:
            addHandler = False
            for a in addedLayers:
                if a.name() == layerName:
                    addHandler = True
                    break
        #self.iface.messageBar().pushMessage("Error", "AddHandle"+str(addHandler), level=Qgis.Critical)
        if addHandler:

            Store().setup()
            self.calcApp = App()
            self.profileApp = Profile(self.iface)

            # Start a watcher to update attributes when a feature was added to layer or a geometry was changed
            #self.iface.messageBar().pushMessage("Error", "Layer Name: "+str(layerName), level=Qgis.Critical)
            if layerName:
                lst = QgsProject.instance().mapLayersByName( layerName )
                #self.iface.messageBar().pushMessage("Error", "LST: "+str(lst), level=Qgis.Critical)
                if lst:
                    myLayer = lst[0]
                    #self.iface.messageBar().pushMessage("Error", "My Layer: "+str(myLayer.name()), level=Qgis.Critical)
                    if 1==1:
                        #self.iface.messageBar().pushMessage("Error", "Handler: "+str(self.HandlerInitialized), level=Qgis.Critical)
                        if not self.HandlerInitialized:
                            self.disconnectActualLayer(myLayer)
                            #self.iface.messageBar().pushMessage("Error", "Criara os eventos de:"+str(layerName), level=Qgis.Critical)
                            # create the attrs if not exists
                            self.createDefaultAttrsInLayer(myLayer)
                            
                            myLayer.featureAdded.connect( self.handleAddedFeatures )
                            myLayer.featuresDeleted.connect( self.handleDeletedFeatures )
                            myLayer.geometryChanged.connect( self.updateFeatureAttrs )                    
                            myLayer.selectionChanged.connect( self.SelectedFeatureAttrWindows )

                            qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'default_style.qml')
                            myLayer.loadNamedStyle(qmlFile)

##                            myLayer.beforeCommitChanges.connect ( self.SetSupressNameFormTrue )
##                            myLayer.committedFeaturesAdded.connect ( self.SetSupressNameFormFalse )

                            self.UpdatePatches()

                            if not myLayer.isEditable():
                                myLayer.startEditing()

                            palyr = QgsPalLayerSettings()
                            #palyr.readFromLayer(myLayer)
                            #palyr.enabled = True 
                            palyr.fieldName = h.readValueFromProject("SEG_NAME_C") 
                            palyr.placement= QgsPalLayerSettings.OverPoint 
                            #palyr.setDataDefinedProperty(QgsPalLayerSettings.Size,True,True,'8','') 
                            c = QgsPropertyCollection()
                            c.setProperty(QgsPalLayerSettings.Size, QgsProperty.fromValue(8))
                            palyr.setDataDefinedProperties(c)
                            labeling = QgsVectorLayerSimpleLabeling(palyr)
                            #palyr.writeToLayer(myLayer)
                            myLayer.setLabeling(labeling)

                            self.iface.mapCanvas().refresh()
                            
                            self.HandlerInitialized = True

                            _v = h.readValueFromProject("plotMode")
                            if _v:
                                self.plotMode = h.parseBoolString(_v)
                            else:
                                self.plotMode = False

                            #self.initializePrintSettings()
                            print_image_path = os.path.join(os.path.dirname(__file__), 'Print')
                            destFolder = os.path.join(QgsProject.instance().readPath("./"),"Print")

                            #print "copy from",print_image_path,"to",destFolder
                            try:
                                h.copyanything(print_image_path,destFolder)
                            except:
                                pass

                            disableDialog = QSettings().value( '/qgis/digitizing/disable_enter_attribute_values_dialog')

                            _mC = False
                            if disableDialog == 2:
                                _mC = True

                            #self.dockPatchs.chkSupressPopup.setChecked( _mC )   
                            
                            h.ShowMessage(translate("AutomaticGeometricAttributes","The plugin watcher has started successfully"))

    def Fill_Attr_Combos(self):
        lstCbos = []
        lstCbos.append(self.dlg.cboExtension)
        lstCbos.append(self.dlg.cboBeginCoordE)
        lstCbos.append(self.dlg.cboBeginCoordN)
        lstCbos.append(self.dlg.cboEndCoordE)
        lstCbos.append(self.dlg.cboEndCoordN)
        lstCbos.append(self.dlg.cboSegName)
        lstCbos.append(self.dlg.cboSegNameC)
        lstCbos.append(self.dlg.cboAuxPos)
        lstCbos.append(self.dlg.cboAuxPav1)
        lstCbos.append(self.dlg.cboAuxPav2)
        lstCbos.append(self.dlg.cboAuxProf1)
        lstCbos.append(self.dlg.cboAuxProf2)
        lstCbos.append(self.dlg.cboAux1)
        lstCbos.append(self.dlg.cboAux2)
        lstCbos.append(self.dlg.cboAux3)
        
        if self.dlg.cboLayers.currentText():
            for c in lstCbos:
                c.clear()
             
            _mlayer = QgsProject.instance().mapLayersByName( self.dlg.cboLayers.currentText() )[0]

            icon_path = ':/plugins/RedBasica/icons/new.png'
            icon = QIcon(icon_path)

            for c in lstCbos:
                dfName = self.GetDefaultFieldNameFromCbo(c)
                lst = [x for x in _mlayer.fields() if x.name() == dfName]
                
                if lst == None or len(lst) == 0:
                    c.addItem(icon,str(dfName))
                    c.setItemData(1, QColor(Qt.red), Qt.TextColorRole)
                
                for field in _mlayer.fields():
                    c.addItem(field.name())
                    

    def GetDefaultFieldNameFromCbo(self,cbo):
        if cbo.objectName() == 'cboExtension':
            return h.names()['EXT_FIELD_NAME'][0]
        elif cbo.objectName() == 'cboBeginCoordE':
            return h.names()['BEG_LINE_COORD_E'][0]
        elif cbo.objectName() == 'cboBeginCoordN':
            return h.names()['BEG_LINE_COORD_N'][0]
        elif cbo.objectName() == 'cboEndCoordE':
            return h.names()['FIN_LINE_COORD_E'][0]
        elif cbo.objectName() == 'cboEndCoordN':
            return h.names()['FIN_LINE_COORD_N'][0]
        elif cbo.objectName() == 'cboSegName':
            return h.names()['SEG_NAME'][0]
        elif cbo.objectName() == 'cboSegNameC':
            return h.names()['SEG_NAME_C'][0]
        elif cbo.objectName() == 'cboAuxPos':
            return h.names()['AUX_POS'][0]
        elif cbo.objectName() == 'cboAuxPav1':
            return h.names()['AUX_PAV_1'][0]
        elif cbo.objectName() == 'cboAuxPav2':
            return h.names()['AUX_PAV_2'][0]
        elif cbo.objectName() == 'cboAuxProf1':
            return h.names()['AUX_PROF_I'][0]
        elif cbo.objectName() == 'cboAuxProf2':
            return h.names()['AUX_PROF_F'][0]
        elif cbo.objectName() == 'cboAux1':
            return h.names()['AUX01'][0]
        elif cbo.objectName() == 'cboAux2':
            return h.names()['AUX02'][0]
        elif cbo.objectName() == 'cboAux3':
            return h.names()['AUX03'][0]

    def run(self):
        """Run method that performs all the real work"""

        layers = self.iface.mapCanvas().layers()

        self.dlg.cboLayers.clear()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                self.dlg.cboLayers.addItem( layer.name() )

        self.readVariablesSettingsScreen()
        
        self.dlg.cboLayers.currentIndexChanged.connect(self.Fill_Attr_Combos)
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            if self.dlg.rbNewLayer.isChecked(): # create the new layer
                nameLayer = self.dlg.txtLayerName.text()
                oldName = h.readValueFromProject("LAYER")
                if nameLayer == oldName:
                    h.ShowError(translate("AutomaticGeometricAttributes","A camada já existe no projeto atual."))
                else:
                    if h.GetLayer():
                        self.disconnectActualLayer(h.GetLayer())

                    self.HandlerInitialized = False
                    
                    myLayer = h.CreateDefaultPatchLayer(nameLayer,h.names()['NODE_LAYER'][0])


            else:
                oldName = h.readValueFromProject("LAYER")
                if oldName:
                    self.HandlerInitialized = False                      
                nameLayer = self.dlg.cboLayers.currentText()
                myLayer = QgsProject.instance().mapLayersByName( nameLayer )[0]
                self.saveVariablesSettingsScreen()
                self.startHandler()

            h.ShowMessage(translate("AutomaticGeometricAttributes","The plugin settings were aplied"))


    def saveVariablesSettingsScreen(self):        
        proj = QgsProject.instance()
        #patch
        proj.writeEntry("AutGeoAtt","LAYER",self.dlg.cboLayers.currentText())
        proj.writeEntry("AutGeoAtt", "EXT_FIELD_NAME", self.dlg.cboExtension.currentText())
        proj.writeEntry("AutGeoAtt", "BEG_LINE_COORD_E", self.dlg.cboBeginCoordE.currentText())
        proj.writeEntry("AutGeoAtt", "BEG_LINE_COORD_N", self.dlg.cboBeginCoordN.currentText())
        proj.writeEntry("AutGeoAtt", "FIN_LINE_COORD_E", self.dlg.cboEndCoordE.currentText())
        proj.writeEntry("AutGeoAtt", "FIN_LINE_COORD_N", self.dlg.cboEndCoordN.currentText())
        proj.writeEntry("AutGeoAtt", "SEG_NAME", self.dlg.cboSegName.currentText())
        proj.writeEntry("AutGeoAtt", "SEG_NAME_C", self.dlg.cboSegNameC.currentText())
        proj.writeEntry("AutGeoAtt", "AUX_POS", self.dlg.cboAuxPos.currentText())
        proj.writeEntry("AutGeoAtt", "AUX_PAV_1", self.dlg.cboAuxPav1.currentText())
        proj.writeEntry("AutGeoAtt", "AUX_PAV_2", self.dlg.cboAuxPav2.currentText())
        proj.writeEntry("AutGeoAtt", "AUX_PROF_I", self.dlg.cboAuxProf1.currentText())
        proj.writeEntry("AutGeoAtt", "AUX_PROF_F", self.dlg.cboAuxProf2.currentText())
        proj.writeEntry("AutGeoAtt", "AUX01", self.dlg.cboAux1.currentText())
        proj.writeEntry("AutGeoAtt", "AUX02", self.dlg.cboAux2.currentText())
        proj.writeEntry("AutGeoAtt", "AUX03", self.dlg.cboAux3.currentText())
        #nodes
        proj.writeEntry("AutGeoAtt", "NODE_LAYER", self.dlg.txtLayerNodeName.text())
        proj.writeEntry("AutGeoAtt", "COTA", self.dlg.txtCota.text())
        proj.writeEntry("AutGeoAtt", "QE", self.dlg.txtQE.text())


    def readVariablesSettingsScreen(self):
        layerName = h.readValueFromProject('LAYER')
        h.SetItemCombo(self.dlg.cboLayers,layerName)

        self.Fill_Attr_Combos()
        #patch
        h.SetItemCombo(self.dlg.cboExtension,h.readValueFromProject("EXT_FIELD_NAME"))
        h.SetItemCombo(self.dlg.cboBeginCoordE,h.readValueFromProject('BEG_LINE_COORD_E'))
        h.SetItemCombo(self.dlg.cboBeginCoordN,h.readValueFromProject('BEG_LINE_COORD_N'))
        h.SetItemCombo(self.dlg.cboEndCoordE,h.readValueFromProject('FIN_LINE_COORD_E'))
        h.SetItemCombo(self.dlg.cboEndCoordN,h.readValueFromProject('FIN_LINE_COORD_N'))
        h.SetItemCombo(self.dlg.cboSegName,h.readValueFromProject('SEG_NAME'))
        h.SetItemCombo(self.dlg.cboSegNameC,h.readValueFromProject('SEG_NAME_C'))
        h.SetItemCombo(self.dlg.cboAuxPos,h.readValueFromProject('AUX_POS'))
        h.SetItemCombo(self.dlg.cboAuxPav1,h.readValueFromProject('AUX_PAV_1'))
        h.SetItemCombo(self.dlg.cboAuxPav2,h.readValueFromProject('AUX_PAV_2'))
        h.SetItemCombo(self.dlg.cboAuxProf1,h.readValueFromProject('AUX_PROF_I'))
        h.SetItemCombo(self.dlg.cboAuxProf2,h.readValueFromProject('AUX_PROF_F'))
        h.SetItemCombo(self.dlg.cboAux1,h.readValueFromProject('AUX01'))
        
        h.SetItemCombo(self.dlg.cboAux2,h.readValueFromProject('AUX02'))
        h.SetItemCombo(self.dlg.cboAux3,h.readValueFromProject('AUX03'))        
        #nodes
        self.dlg.txtLayerNodeName.setText(h.readValueFromProject('NODE_LAYER',h.names()['NODE_LAYER'][0]))
        self.dlg.txtCota.setText(h.readValueFromProject('COTA',h.names()['COTA'][0]))
        self.dlg.txtQE.setText(h.readValueFromProject('QE',h.names()['QE'][0]))

      
    def updateFeatureAttrs( self, fId, geom=None, added = 0 ):
        
        if self.iface.activeLayer():
            _myLayer = self.iface.activeLayer()
            
            if _myLayer:
                if _myLayer.name() == h.readValueFromProject('LAYER'):
                    f = next(_myLayer.getFeatures( QgsFeatureRequest( fId ) ))
                    if not geom:
                        geom = f.geometry()

                    # verify if the draw contains more than 2 vertices (multiline), in positive case, the line must be splited in multiple segments
                    geom.convertToSingleType()
                    vertices = geom.asPolyline()
                    nVertices = len(vertices)
                    #self.iface.messageBar().pushMessage("Update:", "FId: "+str(fId)+", Verti: "+ str(nVertices) + "Added: "+str(added), duration=30)
                
                    if added == 1: # new feature
                        nameSegment = False
                        if nVertices > 2:
                            result,prefixName,initialCount = self.showNameDialog(nVertices)
                            if result:
                                nameSegment = True

                        if nVertices > 2:
                            self.SupressNameForm = True
                            _myLayer.deleteFeature( fId )

                            i = 1
                            trechos_add = []
                            while i < nVertices:
                                seg = QgsFeature()
                                g = QgsGeometry.fromPolyline([geom.vertexAt( i-1 ),geom.vertexAt( i )])
                                seg.setGeometry(g)

                                fields = _myLayer.fields()
                                seg.setFields(fields)
                                seg.setAttribute(h.names()['LABEL_VIS'][0],"1")
                                seg.setAttribute(h.readValueFromProject("EXT_FIELD_NAME"), float("{0:.2f}".format(g.length()) ))
                                seg.setAttribute(h.readValueFromProject('BEG_LINE_COORD_E'), g.asPolyline()[0].x() )
                                seg.setAttribute(h.readValueFromProject('BEG_LINE_COORD_N'), g.asPolyline()[0].y() )
                                seg.setAttribute(h.readValueFromProject('FIN_LINE_COORD_E'), g.asPolyline()[-1].x() )
                                seg.setAttribute(h.readValueFromProject('FIN_LINE_COORD_N'), g.asPolyline()[-1].y() )
                                if nameSegment:
                                    seg.setAttribute(h.readValueFromProject('SEG_NAME' ),prefixName)
                                    seg.setAttribute(h.readValueFromProject('SEG_NAME_C' ),prefixName + "-" + str(initialCount).zfill(3))

                                    initialCount = initialCount + 1
                                
                                trechos_add.append(seg)
                                i = i + 1
                            
                            _myLayer.featureAdded.disconnect( self.handleAddedFeatures )
                            _myLayer.beginEditCommand("Trecho Multiplo")
                            _myLayer.addFeatures( trechos_add )
                            _myLayer.endEditCommand()
                            _myLayer.featureAdded.connect( self.handleAddedFeatures )

                            #_myLayer.reload()
                     
                            self.SupressNameForm = False
                        else:
                            _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.names()['LABEL_VIS'][0]), "1" )
                            
                            if nameSegment:                       
                                _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.readValueFromProject('SEG_NAME' )), prefixName )
                                _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.readValueFromProject('SEG_NAME_C' )), prefixName + "-" + str(initialCount) )
                        
                        

                    if nVertices == 2:
                        _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.readValueFromProject("EXT_FIELD_NAME") ), float("{0:.2f}".format(geom.length()) ))
                        _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.readValueFromProject('BEG_LINE_COORD_E') ), geom.asPolyline()[0].x() )
                        _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.readValueFromProject('BEG_LINE_COORD_N') ), geom.asPolyline()[0].y() )
                        _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.readValueFromProject('FIN_LINE_COORD_E') ), geom.asPolyline()[-1].x() )
                        _myLayer.changeAttributeValue( fId, _myLayer.fields().lookupField( h.readValueFromProject('FIN_LINE_COORD_N') ), geom.asPolyline()[-1].y() )

                        self.UpdatePatches()
#                        self.SelectedFeatureAttrWindows([fId],None,None)
                    #_myLayer.commitChanges()
                    #_myLayer.startEditing()
                    #self.iface.actionAddFeature().trigger()
    
    def openCalculationsApp(self):
        self.calcApp.show()
    
    def openProfileWindow(self):
        self.profileApp.run()

    def tooltipsTranslate(self):
        translate("AutomaticGeometricAttributes","tooltip_SEG_NAME_C")
        translate("AutomaticGeometricAttributes","tooltip_EXT_FIELD_NAME")
        translate("AutomaticGeometricAttributes","tooltip_DN")
        translate("AutomaticGeometricAttributes","tooltip_S")
        translate("AutomaticGeometricAttributes","tooltip_h_col_p1")
        translate("AutomaticGeometricAttributes","tooltip_h_col_p2")
        translate("AutomaticGeometricAttributes","tooltip_caida_p2")
        translate("AutomaticGeometricAttributes","tooltip_caida_p2_h")
        translate("AutomaticGeometricAttributes","tooltip_BEG_LINE_COORD_E")
        translate("AutomaticGeometricAttributes","tooltip_BEG_LINE_COORD_N")
        translate("AutomaticGeometricAttributes","tooltip_FIN_LINE_COORD_E")
        translate("AutomaticGeometricAttributes","tooltip_FIN_LINE_COORD_N")
        translate("AutomaticGeometricAttributes","tooltip_NODO_I")
        translate("AutomaticGeometricAttributes","tooltip_Nodo_tipo")
        translate("AutomaticGeometricAttributes","tooltip_COTA_I")
        translate("AutomaticGeometricAttributes","tooltip_CF_nodo")
        translate("AutomaticGeometricAttributes","tooltip_h_nodo_NT")
        translate("AutomaticGeometricAttributes","tooltip_h_nodo_tp")
        translate("AutomaticGeometricAttributes","tooltip_NODO_F")
        translate("AutomaticGeometricAttributes","tooltip_COTA_F")
        translate("AutomaticGeometricAttributes","tooltip_QE")
        translate("AutomaticGeometricAttributes","tooltip_QEI")
        translate("AutomaticGeometricAttributes","tooltip_QEF")
        translate("AutomaticGeometricAttributes","tooltip_Qt_i")
        translate("AutomaticGeometricAttributes","tooltip_Qt_f")
        translate("AutomaticGeometricAttributes","tooltip_Q_i")
        translate("AutomaticGeometricAttributes","tooltip_Q_f")
        translate("AutomaticGeometricAttributes","tooltip_n")
        translate("AutomaticGeometricAttributes","tooltip_yn_i")
        translate("AutomaticGeometricAttributes","tooltip_yn_f")
        translate("AutomaticGeometricAttributes","tooltip_yrel_i")
        translate("AutomaticGeometricAttributes","tooltip_yrel_f")
        translate("AutomaticGeometricAttributes","tooltip_Trativa_i")
        translate("AutomaticGeometricAttributes","tooltip_Trativa_f")
        translate("AutomaticGeometricAttributes","tooltip_V_i")
        translate("AutomaticGeometricAttributes","tooltip_V_f")
        translate("AutomaticGeometricAttributes","tooltip_Vc")
        translate("AutomaticGeometricAttributes","field_SEG_NAME_C")
        translate("AutomaticGeometricAttributes","field_EXT_FIELD_NAME")
        translate("AutomaticGeometricAttributes","field_DN")
        translate("AutomaticGeometricAttributes","field_S")
        translate("AutomaticGeometricAttributes","field_h_col_p1")
        translate("AutomaticGeometricAttributes","field_h_col_p2")
        translate("AutomaticGeometricAttributes","field_caida_p2")
        translate("AutomaticGeometricAttributes","field_caida_p2_h")
        translate("AutomaticGeometricAttributes","field_BEG_LINE_COORD_E")
        translate("AutomaticGeometricAttributes","field_BEG_LINE_COORD_N")
        translate("AutomaticGeometricAttributes","field_FIN_LINE_COORD_E")
        translate("AutomaticGeometricAttributes","field_FIN_LINE_COORD_N")
        translate("AutomaticGeometricAttributes","field_NODO_I")
        translate("AutomaticGeometricAttributes","field_Nodo_tipo")
        translate("AutomaticGeometricAttributes","field_COTA_I")
        translate("AutomaticGeometricAttributes","field_CF_nodo")
        translate("AutomaticGeometricAttributes","field_h_nodo_NT")
        translate("AutomaticGeometricAttributes","field_h_nodo_tp")
        translate("AutomaticGeometricAttributes","field_NODO_F")
        translate("AutomaticGeometricAttributes","field_COTA_F")
        translate("AutomaticGeometricAttributes","field_QE")
        translate("AutomaticGeometricAttributes","field_QEI")
        translate("AutomaticGeometricAttributes","field_QEF")
        translate("AutomaticGeometricAttributes","field_Qt_i")
        translate("AutomaticGeometricAttributes","field_Qt_f")
        translate("AutomaticGeometricAttributes","field_Q_i")
        translate("AutomaticGeometricAttributes","field_Q_f")
        translate("AutomaticGeometricAttributes","field_n")
        translate("AutomaticGeometricAttributes","field_yn_i")
        translate("AutomaticGeometricAttributes","field_yn_f")
        translate("AutomaticGeometricAttributes","field_yrel_i")
        translate("AutomaticGeometricAttributes","field_yrel_f")
        translate("AutomaticGeometricAttributes","field_Trativa_i")
        translate("AutomaticGeometricAttributes","field_Trativa_f")
        translate("AutomaticGeometricAttributes","field_V_i")
        translate("AutomaticGeometricAttributes","field_V_f")
        translate("AutomaticGeometricAttributes","field_Vc")
        translate("AutomaticGeometricAttributes","field_ID_TRM_(N)")
        translate("AutomaticGeometricAttributes","field_ID_UC")
        translate("AutomaticGeometricAttributes","field_L")
        translate("AutomaticGeometricAttributes","field_X_I")
        translate("AutomaticGeometricAttributes","field_Y_I")
        translate("AutomaticGeometricAttributes","field_X_F")
        translate("AutomaticGeometricAttributes","field_Y_F")
        translate("AutomaticGeometricAttributes","field_QE_IP")
        translate("AutomaticGeometricAttributes","field_QE_FP")
        #Calc table       
        translate("CalcTbl", "tooltip_initial_segment")
        translate("CalcTbl", "tooltip_final_segment")
        translate("CalcTbl", "tooltip_collector_number")
        translate("CalcTbl", "tooltip_col_seg")
        translate("CalcTbl", "tooltip_extension")
        translate("CalcTbl", "tooltip_previous_col_seg_id")
        translate("CalcTbl", "tooltip_m1_col_id")
        translate("CalcTbl", "tooltip_m2_col_id")
        translate("CalcTbl", "tooltip_block_others_id")
        translate("CalcTbl", "tooltip_qty_final_qe")
        translate("CalcTbl", "tooltip_qty_initial_qe")
        translate("CalcTbl", "tooltip_intake_in_seg")
        translate("CalcTbl", "tooltip_total_flow_rate_end")
        translate("CalcTbl", "tooltip_total_flow_rate_start")
        translate("CalcTbl", "tooltip_col_pipe_position")
        translate("CalcTbl", "tooltip_aux_prof_i")
        translate("CalcTbl", "tooltip_force_depth_up")
        translate("CalcTbl", "tooltip_aux_depth_adjustment")
        translate("CalcTbl", "tooltip_covering_up")
        translate("CalcTbl", "tooltip_covering_down")
        translate("CalcTbl", "tooltip_depth_up")
        translate("CalcTbl", "tooltip_depth_down")
        translate("CalcTbl", "tooltip_force_depth_down")
        translate("CalcTbl", "tooltip_el_terr_up")
        translate("CalcTbl", "tooltip_el_terr_down")
        translate("CalcTbl", "tooltip_el_col_up")
        translate("CalcTbl", "tooltip_el_col_down")
        translate("CalcTbl", "tooltip_el_top_gen_up")
        translate("CalcTbl", "tooltip_el_top_gen_down")
        translate("CalcTbl", "tooltip_slopes_terr")
        translate("CalcTbl", "tooltip_slopes_min_accepted_col")
        translate("CalcTbl", "tooltip_slopes_adopted_col")
        translate("CalcTbl", "tooltip_suggested_diameter")
        translate("CalcTbl", "tooltip_adopted_diameter")
        translate("CalcTbl", "tooltip_c_manning")
        translate("CalcTbl", "tooltip_prj_flow_rate_qgmax")
        translate("CalcTbl", "tooltip_water_level_y")
        translate("CalcTbl", "tooltip_water_level_pipe_end")
        translate("CalcTbl", "tooltip_tractive_force")
        translate("CalcTbl", "tooltip_critical_velocity")
        translate("CalcTbl", "tooltip_velocity")
        translate("CalcTbl", "tooltip_initial_flow_rate_qi")
        translate("CalcTbl", "tooltip_water_level_y_start")
        translate("CalcTbl", "tooltip_water_level_pipe_start")
        translate("CalcTbl", "tooltip_tractive_force_start")
        translate("CalcTbl", "tooltip_inspection_id_up")
        translate("CalcTbl", "tooltip_inspection_type_up")
        translate("CalcTbl", "tooltip_inspection_id_down")
        translate("CalcTbl", "tooltip_inspection_type_down")
        translate("CalcTbl", "tooltip_downstream_seg_id")
        translate("CalcTbl", "tooltip_observations")
        translate("CalcTbl", "tooltip_slopes_min_modified")