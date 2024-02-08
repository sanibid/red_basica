# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AutomaticGeometricAttributes
                                 A QGIS plugin
 This plugin fill automaticaly the geometric attributes of a line
                              -------------------
        begin                : 2016-07-20
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Infinisoft
        email                : frogerio@infinisoft.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import print_function
from __future__ import absolute_import
from builtins import next
from qgis.PyQt.QtCore import QCoreApplication, QVariant
# from PyQt4.QtGui import *
# Initialize Qt resources from file resources.py
import os.path
import shutil, errno
from qgis.core import *
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsMessageBar
from .rasterinterpolator import RasterInterpolator, ScipyAvailable

class HelperFunctions:

    def __init__(self, iface):
        self.iface = iface

        global names
        names = dict()
        
        #patch        
        names["LAYER"] = ["Patches",QVariant.String,"String",10,0,"PATCH","LAYER"]
        names["EXT_FIELD_NAME"] = ["L",QVariant.Double,"Real",10,2,"PATCH","ATTRIBUTE"]
        names["BEG_LINE_COORD_E"] = ["X_I",QVariant.Double,"String",10,6,"PATCH","ATTRIBUTE"]
        names["BEG_LINE_COORD_N"] = ["Y_I",QVariant.Double,"String",10,6,"PATCH","ATTRIBUTE"]
        names["FIN_LINE_COORD_E"] = ["X_F",QVariant.Double,"String",10,6,"PATCH","ATTRIBUTE"]
        names["FIN_LINE_COORD_N"] = ["Y_F",QVariant.Double,"String",10,6,"PATCH","ATTRIBUTE"]
        names["SEG_NAME"] = ["ID_COL",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["SEG_NAME_C"] = ["ID_TRM_(N)",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX_POS"] = ["AUX_POS",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX_PAV_1"] = ["AUX_PAV_1",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX_PAV_2"] = ["AUX_PAV_2",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX_PROF_I"] = ["AUX_PROF_I",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX_PROF_F"] = ["AUX_PROF_F",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX01"] = ["AUX01",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX02"] = ["AUX02",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["AUX03"] = ["AUX03",QVariant.String,"String",10,0,"PATCH","ATTRIBUTE"]
        names["COTA_I"] = ["COTA_I",QVariant.Double,"String",10,6,"PATCH","FIELD"]
        names["COTA_F"] = ["COTA_F",QVariant.Double,"String",10,6,"PATCH","FIELD"]

        names["AUX_TRM_I"] = ["AUX_TRM_I",QVariant.Int,"integer",10,0,"PATCH","FIELD"]
        names["AUX_TRM_F"] = ["AUX_TRM_F",QVariant.Int,"integer",10,0,"PATCH","FIELD"]
        
        #node
        names["NODE_LAYER"] = ["Nodes",QVariant.String,"String",10,0,"NODES","LAYER"]
        names["COTA"] = ["CT_(N)",QVariant.Double,"String",10,2,"NODES","ATTRIBUTE"]
        names["QE"] = ["ID_UC",QVariant.String,"String",10,0,"NODES","ATTRIBUTE"]
        names["QEI"] = ["QE_IP",QVariant.Int,"integer",10,0,"NODES","FIELD"]
        names["QEF"] = ["QE_FP",QVariant.Int,"integer",10,0,"NODES","FIELD"]
        names["AUX04"] = ["AUX04",QVariant.String,"String",10,0,"NODES","ATTRIBUTE"]
        names["AUX05"] = ["AUX05",QVariant.String,"String",10,0,"NODES","ATTRIBUTE"]
        names["AUX06"] = ["AUX06",QVariant.String,"String",10,0,"NODES","ATTRIBUTE"]

        names["LABEL_X"] = ["LABEL_X",QVariant.Double,"Real",10,6,"PATCH;NODES","ATTRIBUTE"]
        names["LABEL_Y"] = ["LABEL_Y",QVariant.Double,"Real",10,6,"PATCH;NODES","ATTRIBUTE"]
        names["LABEL_VIS"] = ["LABEL_VIS",QVariant.Int,"integer",10,0,"PATCH;NODES","ATTRIBUTE"]

        names["NODO_I"] = ["NODO_I",QVariant.String,"String",10,0,"PATCH","FIELD"]
        names["NODO_F"] = ["NODO_F",QVariant.String,"String",10,0,"PATCH","FIELD"]

        names["CF_NODO_2"] = ["CF_NODO_2",QVariant.Double,"Real",10,2,"NODES","ATTRIBUTE"]
        names["H_NODO_TP2"] = ["H_NODO_TP2",QVariant.Double,"Real",10,2,"NODES","ATTRIBUTE"]

        #block
        names["BLOCK_LAYER_NAME"] = ["Blocks",QVariant.String,"String",10,0,"BLOCK","LAYER"]
        names["ID_QE"] = ["ID_QE",QVariant.String,"String",10,0,"BLOCK","ATTRIBUTE"]
        names["QE_IP"] = ["QE_IP",QVariant.Int,"integer",10,0,"BLOCK","ATTRIBUTE"]
        names["QE_FP"] = ["QE_FP",QVariant.Int,"integer",10,0,"BLOCK","ATTRIBUTE"]
        names["QConcF"] = ["QConcF",QVariant.Double,"Real",10,4,"BLOCK","ATTRIBUTE"]
        names["QConcI"] = ["QConcI",QVariant.Double,"Real",10,4,"BLOCK","ATTRIBUTE"]



    def copyanything(self, src, dst):
        try:
            shutil.copytree(src, dst)
        except OSError as exc: # python >2.5
            if exc.errno == errno.ENOTDIR:
                shutil.copy(src, dst)
            else: raise

    def names(self):
        return names

    def parseBoolString(self,theString):
        if theString:
            if isinstance(theString, str):
                return theString[0].upper()=='T'

        return False

            
    
    # noinspection PyMethodMayBeStatic
    def tr(self, message, default = None):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        tranlated = QCoreApplication.translate('AutomaticGeometricAttributes', message)
        if default:
            if tranlated == message:
                return default
            
        return tranlated

    def saveValueOnProject(self,valueName,value):
        proj = QgsProject.instance()
        
        proj.writeEntry("AutGeoAtt",valueName,value)
    
    def readValueFromProject(self, valueName,defaultValue = None):
        entry = QgsProject.instance().readEntry("AutGeoAtt", valueName)[0]
        if entry:
            value = entry
        else:
            value = defaultValue
        return value                

    def SetItemCombo(self,combo,value):
        fndIndex = combo.findText(value)
        if not fndIndex:
            combo.setCurrentIndex(0)
        else:
            combo.setCurrentIndex(fndIndex)

    def GetLayer(self):
        layerName = self.readValueFromProject('LAYER')
        
        if layerName:
            lst = QgsProject.instance().mapLayersByName( layerName )
            if lst:
                return lst[0]

        return None

    def GetNodeLayer(self):
        layerName = self.readValueFromProject('NODE_LAYER')
        
        if layerName:
            lst = QgsProject.instance().mapLayersByName( layerName )
            if lst:
                return lst[0]

        return None

    def GetAttributeValue(self,layer,fid,attName):
        # iterator = layer.getFeatures(QgsFeatureRequest().setFilterFid(fid))
        feature = layer.getFeature(fid)
    
        idx = layer.fields().lookupField(attName)
        vl = feature.attributes()[idx]
        return vl

    def GetExtensionSegment(self,lstFid):
        total_length = 0
        myLayer = self.GetLayer()
        if myLayer:
            for _id in lstFid:
                try:
                    total_length = total_length + float(self.GetAttributeValue(myLayer,_id,self.readValueFromProject('EXT_FIELD_NAME')))
                except:
                    pass

        return total_length

    def ShowMessage(self,msg):
        msgTxt=self.tr(msg)
        self.iface.messageBar().pushMessage("saniHUB RedBasica:", msgTxt, duration=3)

    def ShowError(self,msg):
        msgTxt=self.tr(msg)
        self.iface.messageBar().pushMessage("saniHUB RedBasica:", msgTxt,level=Qgis.Critical, duration=5)
        

    def UpdateGeoAttributesAllFeatures(self):
        myLayer = self.GetLayer()
        features = myLayer.getFeatures()

        for f in features:
            geom = f.geometry()
            geom.convertToSingleType()
            myLayer.changeAttributeValue( f.id(), myLayer.fields().lookupField( self.readValueFromProject('EXT_FIELD_NAME') ), round(geom.length(),2) )
            myLayer.changeAttributeValue( f.id(), myLayer.fields().lookupField( self.readValueFromProject('BEG_LINE_COORD_E') ), geom.asPolyline()[0].x() )
            myLayer.changeAttributeValue( f.id(), myLayer.fields().lookupField( self.readValueFromProject('BEG_LINE_COORD_N') ), geom.asPolyline()[0].y() )
            myLayer.changeAttributeValue( f.id(), myLayer.fields().lookupField( self.readValueFromProject('FIN_LINE_COORD_E') ), geom.asPolyline()[-1].x() )
            myLayer.changeAttributeValue( f.id(), myLayer.fields().lookupField( self.readValueFromProject('FIN_LINE_COORD_N') ), geom.asPolyline()[-1].y() )

    def GetNexts(self,fid,ffid):
        _nexts = []
        hasEndId = False
        myLayer = self.GetLayer()
        features = myLayer.getFeatures()

        # iterator = myLayer.getFeatures(QgsFeatureRequest().setFilterFid(fid))
        main_feature = myLayer.getFeature(fid)
        main_geom = main_feature.geometry()

        #use the geom to compare instead the attributes, more reliable
        main_geom.convertToSingleType()
        finalCoordE = main_geom.asPolyline()[-1].x() #self.GetAttributeValue(myLayer,fid,self.readValueFromProject('FIN_LINE_COORD_E'))
        finalCoordN = main_geom.asPolyline()[-1].y() #self.GetAttributeValue(myLayer,fid,self.readValueFromProject('FIN_LINE_COORD_N'))
        
        for feat in features:
            geom = feat.geometry()
            geom.convertToSingleType()
            iCE =  geom.asPolyline()[0].x() #self.GetAttributeValue(myLayer,feat.id(),self.readValueFromProject('BEG_LINE_COORD_E'))
            iCN = geom.asPolyline()[0].y() #self.GetAttributeValue(myLayer,feat.id(),self.readValueFromProject('BEG_LINE_COORD_N'))
            
            if (iCE == finalCoordE) & (iCN == finalCoordN):
                if feat.id() == ffid:
                    hasEndId = True
                _nexts.append(feat.id())

        return _nexts,hasEndId

    def GetPatchBetween(self,fidB,fidF):
        patch = []
        if fidB == fidF: # begin and end are the same
            patch.append(fidB)
            return True,patch
        else:
            patch.append(fidB)
            nxts,hasEnd = self.GetNexts(fidB,fidF)
            
            if len(nxts) == 0:
                return False,[] # not possible to find the patch, then first feature dont have anyone linked
            if len(nxts) == 1:
                if hasEnd:
                     patch.append(nxts[0])
                     return True,patch
                else:
                    hasEnd, ptch = self.GetPatchBetween(nxts[0],fidF)
                    if hasEnd:
                        
                        for p in ptch:
                            patch.append(p)
                        return True,patch
                    else:
                        return False,[] # not possible to find the patch, possibly broken or wrong selection
            if len(nxts) > 1:
                for x in nxts:
                    if x == fidF:
                        patch.append(x)
                        return True,patch
                    else:
                        hasEnd,ptch = self.GetPatchBetween(x,fidF)
                        if hasEnd:
                            
                            for p in ptch:
                                patch.append(p)
                            return True,patch

                return False,[] # not possible to find the patch, possibly broken or wrong selection

    # Generate list of QgsPoints from input geometry ( can be point, line, or polygon )
    def extractPoints( self,geom ):
        multi_geom = QgsGeometry()
        temp_geom = []
        if geom.type() == 0: # it's a point
            if geom.isMultipart():
                temp_geom = geom.asMultiPoint()
            else:
                temp_geom.append(geom.asPoint())
        elif geom.type() == 1: # it's a line
            if geom.isMultipart():
                multi_geom = geom.asMultiPolyline() #multi_geog is a multiline
                for i in multi_geom: #i is a line
                    temp_geom.extend( i )
            else:
                temp_geom = geom.asPolyline()
        elif geom.type() == 2: # it's a polygon
            if geom.isMultipart():
                multi_geom = geom.asMultiPolygon() #multi_geom is a multipolygon
                for i in multi_geom: #i is a polygon
                    for j in i: #j is a line
                        temp_geom.extend( j )
            else:
                multi_geom = geom.asPolygon() #multi_geom is a polygon
                for i in multi_geom: #i is a line
                    temp_geom.extend( i )
                    

        if temp_geom == None:
            self.ShowError('Cannot extract point for the geom')

        
        return temp_geom

    def indexInArray(self,array,value):
        try:
            return array.index(value)
        except:
            return -1

            
    def Get_Feature_On_Index(self,lstFeatures,actualFeature,index,sameName = True,excludeNames = [],everyName = False):

        beg_line_coord_e = self.readValueFromProject("BEG_LINE_COORD_E")
        beg_line_coord_n = self.readValueFromProject("BEG_LINE_COORD_N")
        fin_line_coord_e = self.readValueFromProject("FIN_LINE_COORD_E")
        fin_line_coord_n = self.readValueFromProject("FIN_LINE_COORD_N")
        seg_name = self.readValueFromProject("SEG_NAME")

        if index == 0:
            return actualFeature
        feat = actualFeature

        if index < 0:
            fi = [fte for fte in lstFeatures if (fte["FIN_LINE_COORD_E"] == actualFeature[beg_line_coord_e]) & (fte["FIN_LINE_COORD_N"] == actualFeature[beg_line_coord_n])]
            if len(fi) > 0:
                for f in fi:
                    name1 = f["SEG_NAME"]
                    name2 = feat[seg_name]
                    nameEqual = name1 == name2
                    if everyName or ((sameName == True) & (nameEqual == True)) or ((sameName == False) & (nameEqual == False) & (self.indexInArray(excludeNames,name1) == -1)):
                        return f
        elif index > 0:
            fi = [fte for fte in lstFeatures if (fte["BEG_LINE_COORD_E"] == actualFeature[fin_line_coord_e]) & (fte["BEG_LINE_COORD_N"] == actualFeature[fin_line_coord_n])]
            if len(fi) > 0:
                for f in fi:
                    name1 = f["SEG_NAME"]
                    name2 = feat[seg_name]
                    nameEqual = name1 == name2
                    if everyName or ((sameName == True) & (nameEqual == True)) or ((sameName == False) & (nameEqual == False) & (self.indexInArray(excludeNames,name1) == -1)):
                        return f
 #       for f in lstFeatures:
 #           if index < 0:                                   
 #               if (f["FIN_LINE_COORD_E"] == actualFeature[beg_line_coord_e]) & \
 #               (f["FIN_LINE_COORD_N"] == actualFeature[beg_line_coord_n]):
 #                   name1 = f["SEG_NAME"]
 #                   name2 = feat[seg_name]
 #                   nameEqual = name1 == name2
 #                   if everyName or ((sameName == True) & (nameEqual == True)) or ((sameName == False) & (nameEqual == False) & (self.indexInArray(excludeNames,name1) == -1)):
 #                       return f
 #           elif index > 0:
 #               if (f["BEG_LINE_COORD_E"] == actualFeature[fin_line_coord_e]) & \
 #               (f["BEG_LINE_COORD_N"] == actualFeature[fin_line_coord_n]):
 #                   name1 = f["SEG_NAME"]
 #                   name2 = feat[seg_name]
 #                   nameEqual = name1 == name2
 #                   if everyName or ((sameName == True) & (nameEqual == True)) or ((sameName == False) & (nameEqual == False) & (self.indexInArray(excludeNames,name1) == -1)):
 #                       return f
            
    def hasBefore(self,lstFeatures,feature):
        geom = feature.geometry()
        geom.convertToSingleType()
        for f in lstFeatures:
            fg = f.geometry()
            fg.convertToSingleType()
            if (fg.asPolyline()[-1].x() ==  geom.asPolyline()[0].x()) & (fg.asPolyline()[-1].y() ==  geom.asPolyline()[0].y()):
                return True
        return False

    def hasAfter(self,lstFeatures,feature):
        geom = feature.geometry()
        geom.convertToSingleType()
        for f in lstFeatures:
            fg = f.geometry()
            fg.convertToSingleType()
            if (fg.asPolyline()[0].x() ==  geom.asPolyline()[-1].x()) & (fg.asPolyline()[0].y() ==  geom.asPolyline()[-1].y()):
                return [f]
        return []

    def Get_Aux_Trm(self,fid,lstFeatures):
        layer = self.GetLayer()
        isBegin = False
        isEnd = False
        segNameAtt = self.readValueFromProject('SEG_NAME')
        if layer:
            
            isBegin = True
            isEnd = True
            totalEnd = False
            # iterator = layer.getFeatures(QgsFeatureRequest().setFilterFid(fid))
            feature = layer.getFeature(fid)
            
            isBegin = not self.hasBefore(lstFeatures,feature)

            hasAfter = self.hasAfter(lstFeatures,feature)

            if hasAfter:
                if len(hasAfter) > 0:
                    name1 = self.GetAttributeValue(layer,hasAfter[0].id(),segNameAtt)
                    name2 = self.GetAttributeValue(layer,fid,segNameAtt)
  
                    if name1 == name2:
                        isEnd = False
                else:
                    totalEnd = True
            else:
                totalEnd = True
                

        return isBegin,isEnd,totalEnd


    def GetQEFromBlockLayer(self,ids):
        qei = 0
        qef = 0
        qconcf = 0
        qconci = 0
        lst = QgsProject.instance().mapLayersByName( names["BLOCK_LAYER_NAME"][0] )
        if lst:
            retLayer = lst[0]
            for f in retLayer.getFeatures():
                for _id in ids:
                    if f[names["ID_QE"][0]] == _id:
                        _qi = 0
                        if f[names["QE_IP"][0]]:
                            _qi = f[names["QE_IP"][0]]
                        _qe = 0
                        if f[names["QE_FP"][0]]:
                            _qe = f[names["QE_FP"][0]]
                        _qconcf = 0
                        if (f.fields().indexFromName(names["QConcF"][0]) == -1):
                            retLayer.startEditing()
                            new_field = QgsField(names["QConcF"][0], QVariant.Double, 'real', 10, 4)
                            retLayer.addAttribute(new_field)
                            retLayer.updateFields()
                            retLayer.commitChanges()
                        else:
                            _qconcf = f[names["QConcF"][0]] if f[names["QConcF"][0]] != None else 0

                        _qconci = 0
                        if (f.fields().indexFromName(names["QConcI"][0]) == -1):
                            retLayer.startEditing()
                            new_field = QgsField(names["QConcI"][0], QVariant.Double, 'real', 10, 4)
                            retLayer.addAttribute(new_field)
                            retLayer.updateFields()
                            retLayer.commitChanges()
                        else:
                            _qconci = f[names["QConcI"][0]] if f[names["QConcI"][0]] != None else 0

                        qei = qei + _qi
                        qef = qef + _qe
                        qconcf = qconcf + _qconcf
                        qconci = qconci + _qconci

        return qei, qef, qconcf, qconci

    def getQcFlow(self, point1):
        qconci = 0
        qconcf = 0
        nodeLayer = self.GetNodeLayer()
        _qeList = point1.attributes()[nodeLayer.fields().lookupField( self.readValueFromProject('QE') )]
        if _qeList:
            qei,qef, qconcf, qconci = self.GetQEFromBlockLayer(_qeList.split(","))
        q_fields = ['Qi_pop', 'Qf_pop','Qi_con', 'Qf_con','Qi_cat', 'Qf_cat']
        q_dict = dict()
        for f_name in q_fields:
            fIdx = nodeLayer.fields().lookupField(f_name)
            if fIdx > -1:
                q_dict[f_name] = point1.attributes()[fIdx] if point1.attributes()[fIdx] != None else 0

        q_dict['Qc_i'] = sum([val for key, val in q_dict.items() if key.startswith('Qi')], qconci)
        q_dict['Qc_f'] = sum([val for key, val in q_dict.items() if key.startswith('Qf')], qconcf)

        return q_dict

    def CreateLayer(self,name,fields,lType,crs,destName = None):
        path_absolute = QgsProject.instance().readPath("./")+"/layers"
        
        if not os.path.exists(path_absolute):
           os.makedirs(path_absolute)
        if destName != None:
            name_to_save = path_absolute + "/" + destName + ".shp"
        else:
            name_to_save = path_absolute + "/" + name + ".shp"

        layer_node=QgsVectorFileWriter(name_to_save,"UTF-8",fields,lType,crs,"ESRI Shapefile")
        del layer_node

        retLayer = QgsVectorLayer(name_to_save, name, "ogr")

        return retLayer

    def CreateBlockLayer(self):
        destName = names["BLOCK_LAYER_NAME"][0]
        vecLayer = self.GetLayer()

        if vecLayer:
        
            lst = QgsProject.instance().mapLayersByName( destName )
            if lst:
                retLayer = lst[0]
                self.ShowError(self.tr("A camada já existe no projeto atual."))
            else:
                new = True                
   
                fields = QgsFields()
        ##                fields.append(QgsField(names["ID_QE"],QVariant.String,'String',10,0))
        ##                fields.append(QgsField(names["QE_IP"],QVariant.Int,'integer',2,0))
        ##                fields.append(QgsField(names["QE_FP"],QVariant.Int,'integer',2,0))
                for n in names:
                    splited = names[n][5].split(";")
                    fnd = [x for x in splited if x == "BLOCK"]
                    if len(fnd) > 0:
                        if names[n][6] == "ATTRIBUTE":
                            fields.append(QgsField(names[n][0],names[n][1],names[n][2],names[n][3],names[n][4]))
                if vecLayer:
                    retLayer = self.CreateLayer(destName,fields, QgsWkbTypes.Point,vecLayer.crs())
                else:
                    retLayer = self.CreateLayer(destName,fields, QgsWkbTypes.Point,self.iface.mapCanvas().mapSettings().destinationCrs())

                qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'Blocks_Style.qml')
                retLayer.loadNamedStyle(qmlFile)                
                
                retLayer.updateExtents()

                # add layer to the legend   
                QgsProject.instance().addMapLayer(retLayer)

                retLayer.commitChanges()

        

    def CreateNodeLayerFromVectorLayer(self,vecLayer,destName, progressBar = None):
        features = vecLayer.getFeatures()
        new = False
        lst = QgsProject.instance().mapLayersByName( destName )
        if lst:
            retLayer = lst[0]
        else:
            new = True

            fields = QgsFields()

            for n in names:
                splited = names[n][5].split(";")
                fnd = [x for x in splited if x == "NODES"]
                if len(fnd) > 0:
                    if names[n][6] == "ATTRIBUTE":
                        name = self.readValueFromProject(n,names[n][0])
                        # fix_print_with_import
                        print("campo",n,"achou",name)
                        fields.append(QgsField(name,names[n][1],names[n][2],names[n][3],names[n][4]))

            retLayer = self.CreateLayer(destName,fields, QgsWkbTypes.Point,vecLayer.crs())

            qmlFile = os.path.join(os.path.dirname(__file__),'resources', 'styles', 'Default_nodes_style.qml')
            retLayer.loadNamedStyle(qmlFile)      
            
        added = []

        proj = QgsProject.instance()
        proj.writeEntry("AutGeoAtt", "NODE_LAYER",destName)

        if not retLayer.isEditable():
            retLayer.startEditing()
        
        
        provider = retLayer.dataProvider()          
            

        #remove junk points
        if not new:
           
            existingF = retLayer.getFeatures()

            if progressBar != None:
                progressBar.setMaximum(retLayer.featureCount() + progressBar.maximum())
            
            for f in existingF:
                if progressBar != None:
                    progressBar.setValue(progressBar.value() + 1)
                    QCoreApplication.processEvents()
                lstFnd = []
                thePoint = f.geometry().asPoint()
                for x in vecLayer.getFeatures():
                    geomPoint = x.geometry()
                    geomPoint.convertToSingleType()
                    if ((geomPoint.asPolyline()[0] == thePoint) or (geomPoint.asPolyline()[-1] == thePoint)):
                        lstFnd.append(geomPoint)
                        break
                ##lstFnd = [x for x in vecLayer.getFeatures() if ((x.geometry().asPolyline()[0] == thePoint) 
                ##          or (x.geometry().asPolyline()[-1] == thePoint)) ]
                if (lstFnd == None) or (len(lstFnd) == 0):
                    # fix_print_with_import
                    print("remove",f.id())
                    retLayer.deleteFeature(f.id())
                else:
                    added.append(thePoint)
            
        
        for f in features:
            if progressBar != None:
                progressBar.setValue(progressBar.value() + 1)
                QCoreApplication.processEvents()
                
            points = self.extractPoints(f.geometry())
            for p in points:
                el = [x for x in added if (x[0] == p[0]) & (x[1] == p[1])]
                if not el:
                    added.append(p)
                    
                    fet = QgsFeature()
                    fields = retLayer.fields()
                    fet.setFields(fields)

                    g = QgsGeometry.fromPointXY(QgsPointXY(p[0],p[1]))
                    fet.setGeometry(g)

                    fet.setAttributes(["","","","","1"])
                    fet[names["LABEL_VIS"][0]] = 1
                                      
                    _id = provider.addFeatures([fet])


        retLayer.updateExtents()

        # add layer to the legend
        

        QgsProject.instance().addMapLayer(retLayer)

        retLayer.commitChanges()

        return QgsProject.instance().mapLayersByName( destName )[0]


    def GetRasterValueToVector(self,rasterLayer,band,interpol,destLayer,destField,progressBar = None):
        
        rasterInterpolator = RasterInterpolator(rasterLayer, interpol, band)
        features = destLayer.getFeatures()
        fieldIdx = destLayer.fields().lookupField(destField)

        if not destLayer.isEditable():
            # fix_print_with_import
            print("Editing")
            destLayer.startEditing()
            
        for f in features:
            if progressBar != None:
                progressBar.setValue(progressBar.value() + 1)
                QCoreApplication.processEvents()
            
            if not f[self.readValueFromProject("COTA")]:
                thePoint = f.geometry().asPoint()
                value = rasterInterpolator.interpolate(thePoint)
                if fieldIdx == -1:
                    self.ShowError("Something wrong happened in here")
                    break

                updateMap = {}
             
                updateMap[f.id()] = { fieldIdx: value }
            #f.setAttributes([f[self.readValueFromProject("QE")],f[self.readValueFromProject("QEI")],f[self.readValueFromProject("QEF")],value])
                destLayer.dataProvider().changeAttributeValues(updateMap)

        destLayer.commitChanges()

    def GetPointFromCoordinates(self,lstFeaturesPoints,ponto):
        
        toRet = None
        for f in lstFeaturesPoints:
            thePoint = f.geometry().asPoint()
  
            if thePoint == ponto:
                toRet = f
                break
        return toRet

    def GetPointValueToLine(self,pointLayer,destLayer,pointField,destFirstPointField,destFinalPointField):
        features = destLayer.getFeatures()
        pFeatures = pointLayer.getFeatures()
        fieldIdxI = destLayer.fields().lookupField(destFirstPointField)
        fieldIdxF = destLayer.fields().lookupField(destFinalPointField)
        fieldIdxO = pointLayer.fields().lookupField(pointField)

        if not destLayer.isEditable():
            destLayer.startEditing()

        if fieldIdxI == -1:
            destLayer.dataPovider().addAttributes([QgsField(destFirstPointField, QVariant.String)])
            fieldIdxI = destLayer.fields().lookupField(destFirstPointField)

        if fieldIdxF == -1:
            destLayer.dataPovider().addAttributes([QgsField(destFinalPointField, QVariant.String)])
            fieldIdxF = destLayer.fields().lookupField(destFinalPointField)

        for f in features:
            geom = f.geometry()
            geom.convertToSingleType()
            
            point1 = self.GetPointFromCoordinates(pointLayer.getFeatures(),geom.asPolyline()[0])
            point2 = self.GetPointFromCoordinates(pointLayer.getFeatures(),geom.asPolyline()[-1])

            if point1:
                destLayer.changeAttributeValue(f.id(), fieldIdxI, point1.attributes()[fieldIdxO])
            if point2:
                destLayer.changeAttributeValue(f.id(), fieldIdxF, point2.attributes()[fieldIdxO])

        destLayer.commitChanges()
        self.ShowMessage(self.tr("Operation executed successfully"))

    def AddNaturalSlopeArrowLayer(self):
        destName = "pre1"
        
        lst = QgsProject.instance().mapLayersByName( destName )
        if lst:
            retLayer = lst[0]
            self.ShowError(self.tr("A camada já existe no projeto atual."))
        else:
            qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'NaturalSlopeArrow_Style.qml')

            fields = QgsFields()
            fields.append(QgsField("ID",QVariant.String,'String',20,0))
            
            retLayer = self.CreateLayer(destName,fields, QgsWkbTypes.LineString, self.iface.mapCanvas().mapSettings().destinationCrs())

            retLayer.loadNamedStyle(qmlFile)  

            QgsProject.instance().addMapLayer(retLayer)


            retLayer.commitChanges()

            retLayer.updateExtents()
        

        return QgsProject.instance().mapLayersByName( destName )[0]

    def AddRequiredPointsLayer(self):
        destName = "pre2"
        lst = QgsProject.instance().mapLayersByName( destName )
        if lst:
            retLayer = lst[0]
            self.ShowError(self.tr("A camada já existe no projeto atual."))
        else:        
            qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'RequiredPoints_Style.qml')
            
            fields = QgsFields()
            fields.append(QgsField("ID",QVariant.String,'String',20,0))

            retLayer = self.CreateLayer(destName,fields, QgsWkbTypes.Point,self.iface.mapCanvas().mapSettings().destinationCrs())

            retLayer.loadNamedStyle(qmlFile)  

            QgsProject.instance().addMapLayer(retLayer)


            retLayer.commitChanges()

            retLayer.updateExtents()
        

        return QgsProject.instance().mapLayersByName( destName )[0]

    def CreateDefaultPatchLayer(self,destName,nodeLayerName = "Nodes"):


        qmlFile = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'default_style.qml')

        fields = QgsFields()

        for n in names:
            splited = names[n][5].split(";")
            fnd = [x for x in splited if x == "PATCH"]
            if len(fnd) > 0:
                if names[n][6] == "ATTRIBUTE":
                    fields.append(QgsField(names[n][0],names[n][1],names[n][2],names[n][3],names[n][4]))
        
        retLayer = self.CreateLayer(destName,fields, QgsWkbTypes.LineString,self.iface.mapCanvas().mapSettings().destinationCrs())
        

        provider = retLayer.dataProvider()    


        #save project variables
        proj = QgsProject.instance()
        proj.writeEntry("AutGeoAtt", "LAYER",destName)
        proj.writeEntry("AutGeoAtt", "NODE_LAYER",nodeLayerName)
        proj.writeEntry("AutGeoAtt", "EXT_FIELD_NAME", names["EXT_FIELD_NAME"][0])
        proj.writeEntry("AutGeoAtt", "BEG_LINE_COORD_E", names["BEG_LINE_COORD_E"][0])
        proj.writeEntry("AutGeoAtt", "BEG_LINE_COORD_N", names["BEG_LINE_COORD_N"][0])
        proj.writeEntry("AutGeoAtt", "FIN_LINE_COORD_E", names["FIN_LINE_COORD_E"][0])
        proj.writeEntry("AutGeoAtt", "FIN_LINE_COORD_N", names["FIN_LINE_COORD_N"][0])
        proj.writeEntry("AutGeoAtt", "SEG_NAME", names["SEG_NAME"][0])
        proj.writeEntry("AutGeoAtt", "SEG_NAME_C", names["SEG_NAME_C"][0])
        proj.writeEntry("AutGeoAtt", "AUX_PAV_1", names["AUX_PAV_1"][0])
        proj.writeEntry("AutGeoAtt", "AUX_PAV_2", names["AUX_PAV_2"][0])
        proj.writeEntry("AutGeoAtt", "AUX_POS", names["AUX_POS"][0])
        proj.writeEntry("AutGeoAtt", "AUX_PROF_I", names["AUX_PROF_I"][0])
        proj.writeEntry("AutGeoAtt", "AUX_PROF_F", names["AUX_PROF_F"][0])
        proj.writeEntry("AutGeoAtt", "AUX01", names["AUX01"][0])
        proj.writeEntry("AutGeoAtt", "AUX02", names["AUX02"][0])
        proj.writeEntry("AutGeoAtt", "AUX03", names["AUX03"][0])

        proj.writeEntry("AutGeoAtt", "COTA", names["COTA"][0])
        proj.writeEntry("AutGeoAtt", "QE", names["QE"][0])
        proj.writeEntry("AutGeoAtt", "QEI", names["QEI"][0])
        proj.writeEntry("AutGeoAtt", "QEF", names["QEF"][0])

        


        # add layer to the legend
        QgsProject.instance().addMapLayer(retLayer)


        retLayer.commitChanges()

        retLayer.updateExtents()

        

        return QgsProject.instance().mapLayersByName( destName )[0]


    def selectByColSeg(self, colsegs):
        """ gets a list of colsegs and selects matching features on layer"""
        
        layer = self.GetLayer()
        layer.removeSelection()
        col = self.readValueFromProject("SEG_NAME_C")
        fids = []
        for colseg in colsegs:                       
            features = layer.getFeatures(QgsFeatureRequest(QgsExpression("\"{}\" = '{}'".format(col, colseg))))
            for f in features:
                fids.append(f.id())
        if len(fids) > 0:
            layer.select(fids)
        self.iface.mapCanvas().setSelectionColor( QColor("yellow") )


        
