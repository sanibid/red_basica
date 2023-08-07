import os
from datetime import datetime
from PyQt5.QtCore import QObject, QLocale
from qgis.utils import iface
from qgis.core import *
from ..models.Project import Project
from ..models.Calculation import Calculation


class SwmmController(QObject):

    def __init__(self, iface, projectId, flowType):
        super().__init__()
        if flowType in ['q_i', 'q_f']:
            self.flowType = flowType
        else:
            raise Exception('invalid flowType value. Valid values are: q_i, q_f')
        
        if projectId:

            # lang
            locale = QLocale().name()
            self.lang = locale[0:2] if locale[0:2] in ('en', 'es', 'pt') else 'en'
            # file sections
            self.sections = ('TITLE', 'OPTIONS', 'JUNCTIONS', 'OUTFALLS', 'CONDUITS',
                             'XSECTIONS', 'REPORT', 'MAP', 'COORDINATES')
            self.line_tab = '\t'
            # project info
            proj = Project()
            proj.setFilter('id = {}'.format(projectId))
            proj.select()
            self.project = proj.record(0)
            # segments and nodes
            self.segments = Calculation.getSwmmSegments()
            self.nodes = Calculation.getSwmmNodes()
            # qgis settings
            self.iface = iface
            self.setCrs(QgsProject.instance().crs())
        else:
            raise Exception('Missing mandatory parameter projectId')

    def getContent(self, section):
        switcher = {
            'TITLE': self.getTitleSection,
            'OPTIONS': self.getOptionsSection,
            'JUNCTIONS': self.getJunctionsSection,
            'OUTFALLS': self.getOutfallsSection,
            'CONDUITS': self.getConduitsSection,
            'XSECTIONS': self.getXsectionsSection,
            'REPORT': self.getReportSection,
            'MAP': self.getMapSection,
            'COORDINATES': self.getCoordinatesSection,
        }
        func = switcher.get(section, lambda: "Invalid Section")
        return func()

    def writeInp(self, filename):
        self.inpfile = open(filename, 'w')
        for section in self.sections:
            self.writeSection(section)
        self.inpfile.close()

    def writeSection(self, section):
        self.writeSectionLabel(section)
        content = self.getContent(section)
        for line in content:
            self.inpfile.write(line + '\n')
        self.inpfile.write('\n')

    def writeSectionLabel(self, section):
        """ Write a section label to the INP file """
        self.inpfile.write('['+section+'] \n')

    def setCrs(self, crs):
        """ Set CRS """
        self.crstransform = False
        canvascrs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.isValid() and canvascrs.isValid():
            self.crstransform = QgsCoordinateTransform(
                crs, canvascrs, QgsProject.instance())
        if self.crstransform.isShortCircuited():
            self.crstransform = False

    def transformXY(self, x, y):
        """ Transform coordinates where necessary to canvas crs """
        if self.crstransform:
            pnt = self.crstransform.transform(QgsPoint(x, y))
            x = pnt.x()
            y = pnt.y()
        return [x, y]

    def getString(self, value):
        """ prevent NULL values in INP file """
        v = str(value)
        if 'NULL' == v:
            return ''
        return v
    
    def getNumber(self, value):
        """ prevent NULL values and turn it into 0 """
        v = str(value)
        if 'NULL' == v:
            return '0'
        return v

    def getTitleSection(self):
        """ [TITLE] section """
        title = {
                 'pt': 'Sistema de Esgoto',
                 'es': 'Sistema de Alcantarillado',
                 'en': 'Sewerage System'
                }
        lines = (self.project.value('name'), title[self.lang])
        return lines

    def getOptionsSection(self):
        """ [OPTIONS] section """
        date = datetime.strptime(self.project.value('date'), '%Y-%m-%d')
        lines = ('FLOW_UNITS' + '\t \t' + 'LPS',  # Padrão de unidades Litros por segundo
                 'START_DATE' + '\t \t' + \
                 date.strftime('%m/%d/%Y'),  # Data do projeto
                 'START_TIME' + '\t \t' + '00:00:00',
                 'REPORT_START_DATE' + '\t' + date.strftime('%m/%d/%Y'),
                 'REPORT_START_TIME' + '\t' + '00:00:00',
                 # Data do final do projeto
                 'END_DATE' + '\t \t' + \
                 date.replace(year=date.year+1).strftime('%m/%d/%Y'),
                 'END_TIME' + '\t \t' + '12:00:00',
                 'SWEEP_START' + '\t \t' + '01/01',
                 'SWEEP_END' + '\t \t' + '12/31',
                 # Padrão de entrada dos valores dos degraus (distância do tubo ao fundo do PV)
                 'LINK_OFFSETS' + '\t \t' + 'DEPTH'
                 )
        return lines

    def getJunctionsSection(self):
        """ [JUNCTIONS] section """

        h1 = self.line_tab.join(
            (';;',   'Invert', 'Max.', 'Init.', 'Surcharge', 'Ponded'))
        h2 = self.line_tab.join(
            (';;Name', 'Elev.', 'Depth', 'Depth', 'Depth   ',    'Area'))
        h3 = self.line_tab.join(
            (';;----', '------', '-----', '-----', '--------', '-------'))

        lines = [h1, h2, h3]
        for rec in self.nodes:
            if ('FINAL' not in rec['node']):
                data = [
                    self.getString(rec['node']),
                    self.getNumber(round(rec['elev'], 2)),
                    self.getNumber(round(rec['depth'], 2)),
                    '0', '0', '0'
                ]
                line = self.line_tab.join(data)
                lines.append(line)
        return lines

    def getOutfallsSection(self):
        """ OUTFALLS section """
        h1 = self.line_tab.join(
            (';;', 'Invert', 'Outfall', 'Stage/Table', 'Tide'))
        h2 = self.line_tab.join(
            (';;Name', 'Elev.', 'Type', 'Time Series', 'Gate'))
        h3 = self.line_tab.join(
            (';;----', '-----', '-----', '-----------', '-----'))
        lines = [h1, h2, h3]
        for rec in self.nodes:
            if ('FINAL' in rec['node']):
                data = [
                    self.getString(rec['node']),
                    self.getNumber(round(rec['elev'], 2)),
                    'FREE',
                    '',
                    'NO'
                ]
                line = self.line_tab.join(data)
                lines.append(line)
        return lines

    def getConduitsSection(self):
        """ CONDUITS section """

        h1 = self.line_tab.join(
            (';;',    'Inlet', 'Outlet', '     ',   'Manning', 'Inlet',  'Outlet', 'Init.', 'Max.'))
        h2 = self.line_tab.join(
            (';;Name', 'Node ', 'Node ', 'Length',  'N      ', 'Offset', 'Offset', 'Flow',  'Flow'))
        h3 = self.line_tab.join((';;----', '-----', '------', '-------',
                                 '-------', '------', '------', '-----', '------'))

        lines = [h1, h2, h3]
        for rec in self.segments:
            data = [
                self.getString(rec['col_seg']),
                self.getString(rec['inspection_id_up']),
                self.getString(rec['inspection_id_down']),
                self.getNumber(rec['extension']),
                self.getNumber(rec['c_manning']),
                '0',
                self.getNumber(rec['total_slope']),
                self.getNumber(rec[self.flowType]),
                '0'
            ]
            line = self.line_tab.join(data)
            lines.append(line)
        return lines

    def getXsectionsSection(self):
        """ XSECTIONS section """

        h1 = self.line_tab.join(
            (';;Link', 'Shape   ', 'Geom1', 'Geom2', 'Geom3', 'Geom4', 'Barrels'))
        h2 = self.line_tab.join(
            (';;----', '--------', '-----', '------', '------', '------', '-------'))

        lines = [h1, h2]
        for rec in self.segments:
            data = [
                self.getString(rec['col_seg']),
                'CIRCULAR',
                self.getNumber(rec['dn_meters']),
                '0',
                '0',
                '0',
                '1'  # Barrels (should be 0 ?)
            ]
            line = self.line_tab.join(data)
            lines.append(line)
        return lines

    def getReportSection(self):
        """ REPORT section """

        return ('INPUT      NO',
                'CONTROLS   NO',
                'SUBCATCHMENTS ALL',
                'NODES ALL',
                'LINKS ALL'
                )

    def getMapSection(self):
        """ MAP section """

        canvas = self.iface.mapCanvas()
        # DIMENSIONS
        extent = canvas.extent()
        mins = str(extent.xMinimum()) + ' ' + str(extent.yMinimum())
        maxs = str(extent.xMaximum()) + ' ' + str(extent.yMaximum())
        dim_line = 'DIMENSIONS ' + mins + ' ' + maxs
        # UNITS
        mapunits = 'Meter'  # TODO: check this
        units_line = 'UNITS ' + mapunits

        lines = (dim_line, units_line)
        return lines

    def getCoordinatesSection(self):
        """ COORDINATES section """

        h1 = self.line_tab.join((';;Node', 'X-Coord    ', 'Y-Coord    '))
        h2 = self.line_tab.join((';;----', '-----------', '-----------'))

        lines = [h1, h2]
        for rec in self.nodes:
            (x, y) = self.transformXY(rec['x'], rec['y'])
            data = [
                rec['node'],
                self.getString(x),
                self.getString(y)
            ]
            line = self.line_tab.join(data)
            lines.append(line)
        return lines
