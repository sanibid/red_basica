from .ui.ProfileWidgetUi import Ui_ProfileWidget
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import QgsProject, QgsPointXY
from qgis.gui import *
from ...base.helper_functions import HelperFunctions
from ...base.rasterinterpolator import RasterInterpolator
from .. import pyqtgraph as pg
from ...app.models.Calculation import Calculation
from ..utils.vLayer import vLayer

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class MainView(QDockWidget, Ui_ProfileWidget):
    def __init__(self, iface):
        QDockWidget.__init__(self)
        self.setupUi(self)
        self.location = Qt.BottomDockWidgetArea
        self.h = HelperFunctions(iface)
        #options
        self.opts = {
            'area_fill_margin':1.5,
            'pipe_width': 0.05,
            'device_width': 0.8
        } 
        
        #layout
        self.layout = self.frame_for_plot.layout()
        self.plotWdg = self.set_plot_widget()
        self.layout.addWidget(self.plotWdg)
        
        #mouseover
        self.plotWdg.scene().sigMouseMoved.connect(self.mouseMoved)
        
        self.plotWdg.sigRangeChanged.connect(self.onRangeChanged)
        #layers
        self.layers = {}
        self.rasterLayer = None
        self.virtualLayer = vLayer("nameVirtual", "Point")
        self.area_fill_layer = None
        self.devices_layer = None
        self.pipesBackgroung = None
        self.waterBackground = None
        self.devices = None
        self.pipes = None
        self.labels = None
        
        #Cursor point
        self.show_cursor = self.showCursorCheckBox.isChecked()
        self.current_cursor_position = QgsVertexMarker(iface.mapCanvas())
        self.current_cursor_position.setColor(QColor(Qt.red))
        self.current_cursor_position.setIconSize(5)
        self.current_cursor_position.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.current_cursor_position.setPenWidth(3)
        self.showCursorCheckBox.clicked.connect(self.setCursorVisibility)
        
        #update button
        self.updateButton.clicked.connect(self.updatePlot)
        
        #show virtual layer
        self.showLayerCheckBox.clicked.connect(self.setVirtualLayerVisibility)

        #layers combo
        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        layer_list = []
        for layer in layers:
            if (layer.type() == layer.RasterLayer) or \
                (layer.type() == layer.MeshLayer) or \
                (layer.type() == layer.PluginLayer and layer.LAYER_TYPE == 'selafin_viewer'):
                layer_list.append(layer.name())
        self.layerComboBox.addItems(layer_list)


    def setCursorVisibility(self):
        """ show/hide cursor from map and profile"""
        checked = self.showCursorCheckBox.isChecked()
        self.show_cursor = checked
        if not self.show_cursor:
            #clean widget
            self.current_cursor_position.hide()
            for item in self.plotWdg.allChildItems():
                    if str(type(item)) == "<class 'red_basica.profile.pyqtgraph.graphicsItems.InfiniteLine.InfiniteLine'>":
                        if item.name() == 'cross_vertical':
                            item.hide()
                        elif item.name() == 'cross_horizontal':
                            item.hide()
                    elif str(type(item)) == "<class 'red_basica.profile.pyqtgraph.graphicsItems.TextItem.TextItem'>":
                        if item.textItem.toPlainText()[0] == 'X':
                            item.hide()
                        elif item.textItem.toPlainText()[0] == 'Y':
                            item.hide()

    def setVirtualLayerVisibility(self):
        """ show/hide layer from layer tree """
        checked = self.showLayerCheckBox.isChecked()
        self.virtualLayer.setVisibility(checked)
    
    def clearLayers(self):
        """ remove layers and items from widget """
        
        if self.area_fill_layer:
            self.plotWdg.removeItem(self.area_fill_layer)
        if self.devices_layer:
            self.plotWdg.removeItem(self.devices_layer)
        if self.waterBackground:
            self.plotWdg.removeItem(self.waterBackground)
        if self.pipesBackgroung:
            self.plotWdg.removeItem(self.pipesBackgroung)
        if self.labels:
            for item in self.labels:
                self.plotWdg.removeItem(item['label'])
        
        for k in self.layers.keys():
            self.layers[k].clear()

    def set_plot_widget(self):
        """ creates instance of pg.PlotWidget and sets initial config """
        plotWdg = pg.PlotWidget()
        plotWdg.showGrid(True,True,int(1))
        datavline = pg.InfiniteLine(0, angle=90 ,pen=pg.mkPen('b',  width=1) , name = 'cross_vertical' )
        datahline = pg.InfiniteLine(0, angle=0 , pen=pg.mkPen('b',  width=1) , name = 'cross_horizontal')
        plotWdg.addItem(datavline)
        plotWdg.addItem(datahline)
        #cursor
        xtextitem = pg.TextItem('X : /', color = (0,0,0), border = pg.mkPen(color=(0, 0, 0),  width=1), fill=pg.mkBrush('w'), anchor=(0,1))
        ytextitem = pg.TextItem('Y : / ', color = (0,0,0) , border = pg.mkPen(color=(0, 0, 0),  width=1), fill=pg.mkBrush('w'), anchor=(0,0))
        plotWdg.addItem(xtextitem)
        plotWdg.addItem(ytextitem)

        plotWdg.getViewBox().autoRange(items=[])
        plotWdg.getViewBox().disableAutoRange()
        plotWdg.getViewBox().border = pg.mkPen(color=(0, 0, 0),  width=1)
        return plotWdg
    
    
    def onRangeChanged(self, r):
        axX = self.plotWdg.getAxis('bottom').range
        range = axX[1] - axX[0]
        for item in self.labels:
            if range < 15:
                item['label'].show()
            else:
                if item['extension'] > 25 and range <= 95:
                    item['label'].show()
                if item['extension'] <= 25 and range <= 30:
                    item['label'].show()
                if item['extension'] <= 25 and range > 30:
                    item['label'].hide()
                if  range > 95:
                    item['label'].hide()
        return r


    def mouseMoved(self, pos):
        if self.show_cursor and self.plotWdg.sceneBoundingRect().contains(pos):
            range = self.plotWdg.getViewBox().viewRange()
            mousePoint = self.plotWdg.getViewBox().mapSceneToView(pos)
            x_cursor = mousePoint.x()
            y_cursor = mousePoint.y()
            if x_cursor is not None and y_cursor is not None:
                    for item in self.plotWdg.allChildItems():
                        if str(type(item)) == "<class 'red_basica.profile.pyqtgraph.graphicsItems.InfiniteLine.InfiniteLine'>":
                            if item.name() == "cross_vertical":
                                item.show()
                                item.setPos(x_cursor)
                            elif item.name() == "cross_horizontal":
                                item.show()
                                item.setPos(y_cursor)
                        elif str(type(item)) == "<class 'red_basica.profile.pyqtgraph.graphicsItems.TextItem.TextItem'>":
                            if item.textItem.toPlainText()[0] == "X":
                                item.show()
                                item.setText("X : " + str(round(x_cursor, 3)))
                                item.setPos(x_cursor, range[1][0])
                            elif item.textItem.toPlainText()[0] == "Y":
                                item.show()
                                item.setText("Y : " + str(round(y_cursor, 3)))
                                item.setPos(range[0][0], y_cursor)
            self.updateCursorOnMap(x_cursor)
        
    
    def updateCursorOnMap(self, x_cursor):
        """ Draw cursor position on map """
        features = self.virtualLayer.getFeatures()
        d = (self.distanceDoubleSpinBox.value() / 2)
        points = [ f.geometry().asPoint() for f in features if abs(float(x_cursor) - float(f['x_axis'])) < d]
        if len(points)>0:
            point = points[0]
            self.current_cursor_position.setCenter(point)
            self.current_cursor_position.show()
        else:
            self.current_cursor_position.hide()
        

    def resetDevices(self):
        """ set default inspection devices structure """
        self.devices = {'x':[], 'y':[], 'h':[] }
        return self.devices

    def resetPipes(self):
        """ set default pipes structure """
        self.pipes =  {
            'top': {'x':[], 'y':[]},
            'bottom': {'x':[], 'y':[]},
            'water': {'x':[], 'y':[]}
        }
        return self.pipes
    
    def resetLabels(self):
        self.labels = []
        return self.labels
    
    def addPipe(self, col, extension):
        """ adds a single pipe to pipes -> returns coords """
        x1 = extension
        x2 = extension + col['extension']
        rasterInterpolator = RasterInterpolator(self.rasterLayer, 1, 1)
        initialPointY = QgsPointXY(col['geom_x_initial'], col['geom_y_initial'])
        iPy = rasterInterpolator.interpolate(initialPointY)
        finalPointY = QgsPointXY(col['geom_x_final'], col['geom_y_final'])
        fPy = rasterInterpolator.interpolate(finalPointY)
        y1 = iPy - col['y_initial']
        y2 = fPy - col['y_final']

        displacement = self.opts['device_width'] / 2
        self.pipes['bottom']['x'].extend([x1 + displacement, x2 - displacement])
        self.pipes['bottom']['y'].extend([y1, y2])

        self.pipes['top']['x'].extend([x1 + displacement, x2 - displacement])
        self.pipes['top']['y'].extend([y1 + self.opts['pipe_width'], y2 + self.opts['pipe_width']])

        porc_flow = round(col['water_level'], 0)
        flow_width = (porc_flow * self.opts['pipe_width'])/100
        self.pipes['water']['x'].extend([x1 + displacement, x2 - displacement])
        self.pipes['water']['y'].extend([y1 + flow_width, y2 + flow_width])

        self.addLabel((x1 + (x2-x1)/2) -0.5, y1 + (self.opts['device_width']/2), "<div align='center'><b>{}</b><br>{}m<br>Ø{}<br>{}</div>".format(
                col['col_seg'], col['extension'], col['adopted_diameter'], round(col['slopes_adopted_col'],5)), center=True, extension=col['extension']
            )
        return [[x1,x2], [y1,y2]]

    def drawPipes(self):
        for p in self.pipes.keys():
            layerName = 'pipe-{}'.format(p)
            self.layers[layerName] = self.plotWdg.plot(self.pipes[p]['x'], self.pipes[p]['y'], pen=pg.mkPen('000000',  width=0.8))
        self.pipesBackgroung = pg.FillBetweenItem(self.layers['pipe-bottom'], self.layers['pipe-top'], brush=pg.mkBrush(255, 255, 255, 100))
        self.waterBackground = pg.FillBetweenItem(self.layers['pipe-water'], self.layers['pipe-bottom'], brush=pg.mkBrush(0, 0, 255, 50))
        self.plotWdg.addItem(self.pipesBackgroung)
        self.plotWdg.addItem(self.waterBackground)

    def updatePlot(self):
        self.clearLayers()
        self.virtualLayer.clear()
        profileLayerName = self.layerComboBox.currentText()
        interval = self.distanceDoubleSpinBox.value()
        col_seg_att_name = self.h.readValueFromProject("SEG_NAME_C")
        selectedFeatures = sorted(self.h.GetLayer().selectedFeatures(), key=lambda x: x.attribute(col_seg_att_name))
        features, notInList = Calculation.getTree(col_seg_att_name, selectedFeatures) if len(selectedFeatures)>1 else selectedFeatures
        self.rasterLayer = QgsProject.instance().mapLayersByName(profileLayerName)[0]
        rasterInterpolator = RasterInterpolator(self.rasterLayer, 1, 1)
        xRaster = []
        yRaster = []
        self.resetDevices()
        self.resetPipes()
        self.resetLabels()
        xVal = None
        for f in features:
            col_seg = f.attribute(col_seg_att_name)
            line = f.geometry()
            #overlays
            data = Calculation.getActiveProfileData(col_seg)
            for n in data.keys():
                for col in data[n]:
                    extension = 0 if xVal == None else xExt2
                    xExt2 = col['extension'] if xVal == None else xExt2 + col['extension']
                    #add pipe
                    [[x1,x2], [y1,y2]] = self.addPipe(col, extension)
                    #set xVal if dosnt exist
                    if xVal is None:
                        xVal = x1

                    #add device
                    self.devices['x'].extend([x1, x2])
                    h1 = col['y_initial']
                    h2 = col['y_final']
                    self.devices['h'].extend([h1, h2])
                    self.devices['y'].extend([y1 + h1/2, y2 + h2/2])
                    self.addLabel(x1 - 0.5, y1, "{}<br>CT = {}<br>CF = {}<br>h = {}".format(
                        col['inspection_type_up'], round(col['el_terr_up'], 2), round(col['el_col_up'], 2), col['y_initial']),
                        color="red", extension=col['extension']
                    )
            #Last inspection device item
            if (features[-1].attribute(col_seg_att_name) == col_seg):
                dwSeg = Calculation.getDownstreamSeg(col['downSeg'])
                self.addLabel(x2 - 0.5, y2, "{}<br>CT = {}<br>CF = {}<br>h = {}".format(
                    dwSeg.value('inspection_type_up'), round(dwSeg.value('el_terr_up'),2), round(dwSeg.value('el_col_up'),2), dwSeg.value('y_initial')),
                    color="red", extension=col['extension']
                )

            #ground layer
            for part in line.get():
                line_start = part[0]
                line_end = part[-1]
                pointm = self.virtualLayer.diff(line_end, line_start)
                cosa,cosb = self.virtualLayer.dirCos(pointm)
                lg = self.virtualLayer.length(line_end, line_start)
                i = 0
                rest = lg % interval
                last = False
                while i <= lg:
                    point_x = line_start.x() + (i * cosa)
                    point_y = line_start.y() + (i * cosb)
                    point = QgsPointXY(point_x, point_y)

                    yVal = rasterInterpolator.interpolate(point)
                    yRaster.append(yVal)
                    xRaster.append(xVal)
                    attributes = {
                        'col_seg': col_seg,
                        'x_axis': xVal,
                        'y_axis': yVal,
                        'x': point_x,
                        'y': point_y,
                        'h': '??'
                    }
                    self.virtualLayer.createPoint(point, attributes)
                    if ((i + rest) == lg):
                        i = lg
                        xVal += rest
                        last = True
                    else:
                        i += interval
                        if not last:
                            xVal += interval

        if notInList:
            self.h.ShowError('You have selected one or more sections that do not belong to another:{}'.format(notInList))
        #draw ground area
        self.layers['ground'] = self.plotWdg.plot(xRaster, yRaster, pen=pg.mkPen('CCCCCC',  width=1))
        lower_y_axis = min(self.devices['y'])
        yGroundBase = [ (lower_y_axis - self.opts['area_fill_margin']) for i in yRaster]
        self.layers['ground_base'] = self.plotWdg.plot(xRaster, yGroundBase, pen=pg.mkPen('CCCCCC',  width=1))
        self.area_fill_layer = pg.FillBetweenItem(self.layers['ground'], self.layers['ground_base'], brush=pg.mkBrush(242, 176, 109, 100))
        self.plotWdg.addItem(self.area_fill_layer)
        self.plotWdg.getViewBox().autoRange(items=self.plotWdg.getPlotItem().listDataItems())
        
        # draw pipes
        self.drawPipes()
        
        #draw inspection devices
        self.devices_layer = pg.BarGraphItem(x = self.devices['x'], y = self.devices['y'], height = self.devices['h'], width = self.opts['device_width'], brush ='w')
        self.plotWdg.addItem(self.devices_layer)

        # draw labels
        self.drawLabels()
    
    def drawLabels(self):
        for item in self.labels:
            self.plotWdg.addItem(item['label'],  ignoreBounds = True)

    def addLabel(self, x, y, text, center=False, color='', extension=None):
        label = pg.TextItem('', color=(0,0,0),rotateAxis=(1, 0), anchor=(0,0), angle=0)
        label.setHtml(text)
        label.setPos(x,y)
        label.forgetViewBox()
        if (center):
            it = label.textItem
            option = it.document().defaultTextOption()
            option.setAlignment(QtCore.Qt.AlignCenter)
            it.document().setDefaultTextOption(option)
            it.setTextWidth(it.boundingRect().width())
        if (color == 'red'):
            label.setColor(QColor(255,0,0))
        labelDict = {
            'label': label,
            'extension': extension
        }
        self.labels.append(labelDict)