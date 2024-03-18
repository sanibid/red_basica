import math
from PyQt5.QtCore import Qt, QCoreApplication, QT_TRANSLATE_NOOP, QVariant
from PyQt5.QtSql import QSqlRelationalTableModel, QSqlQuery
from PyQt5.QtGui import QColor, QBrush

translate = QCoreApplication.translate

class Calculation(QSqlRelationalTableModel):
    
    def __init__(self, *args, **kwargs):
        super(Calculation, self).__init__(*args, **kwargs)
        self.setTable("calculations")
        self.select()
        # is important to use QT_TRANSLATE_NOOP and columns needs to be list () and not array []                    
        self.columns = (            
            QT_TRANSLATE_NOOP("CalcTbl", "id"), QT_TRANSLATE_NOOP("CalcTbl", "project_id"),
            QT_TRANSLATE_NOOP("CalcTbl", "layer_name"),QT_TRANSLATE_NOOP("CalcTbl", "initial_segment"),
            QT_TRANSLATE_NOOP("CalcTbl", "final_segment"),QT_TRANSLATE_NOOP("CalcTbl", "collector_number"),
            QT_TRANSLATE_NOOP("CalcTbl", "col_seg"), QT_TRANSLATE_NOOP("CalcTbl", "extension"),
            QT_TRANSLATE_NOOP("CalcTbl", "previous_col_seg_id"), QT_TRANSLATE_NOOP("CalcTbl", "m1_col_id"),
            QT_TRANSLATE_NOOP("CalcTbl", "m2_col_id"), QT_TRANSLATE_NOOP("CalcTbl", "block_others_id"),
            QT_TRANSLATE_NOOP("CalcTbl", "qty_final_qe"), QT_TRANSLATE_NOOP("CalcTbl", "qty_initial_qe"),
            QT_TRANSLATE_NOOP("CalcTbl", "conc_flow_qcf"),QT_TRANSLATE_NOOP("CalcTbl", "conc_flow_qci"),
            QT_TRANSLATE_NOOP("CalcTbl", "intake_in_seg"), QT_TRANSLATE_NOOP("CalcTbl", "total_flow_rate_end"),
            QT_TRANSLATE_NOOP("CalcTbl", "total_flow_rate_start"), QT_TRANSLATE_NOOP("CalcTbl", "col_pipe_position"),
            QT_TRANSLATE_NOOP("CalcTbl", "aux_prof_i"), QT_TRANSLATE_NOOP("CalcTbl", "force_depth_up"),
            QT_TRANSLATE_NOOP("CalcTbl", "aux_depth_adjustment"), QT_TRANSLATE_NOOP("CalcTbl", "covering_up"),
            QT_TRANSLATE_NOOP("CalcTbl", "covering_down"), QT_TRANSLATE_NOOP("CalcTbl", "depth_up"),
            QT_TRANSLATE_NOOP("CalcTbl", "depth_down"), QT_TRANSLATE_NOOP("CalcTbl", "force_depth_down"),
            QT_TRANSLATE_NOOP("CalcTbl", "el_terr_up"), QT_TRANSLATE_NOOP("CalcTbl", "el_terr_down"),
            QT_TRANSLATE_NOOP("CalcTbl", "el_col_up"), QT_TRANSLATE_NOOP("CalcTbl", "el_col_down"),
            QT_TRANSLATE_NOOP("CalcTbl", "el_top_gen_up"), QT_TRANSLATE_NOOP("CalcTbl", "el_top_gen_down"),
            QT_TRANSLATE_NOOP("CalcTbl", "slopes_terr"), QT_TRANSLATE_NOOP("CalcTbl", "slopes_min_accepted_col"),
            QT_TRANSLATE_NOOP("CalcTbl", "slopes_adopted_col"), QT_TRANSLATE_NOOP("CalcTbl", "suggested_diameter"),
            QT_TRANSLATE_NOOP("CalcTbl", "adopted_diameter"), QT_TRANSLATE_NOOP("CalcTbl", "c_manning"),
            QT_TRANSLATE_NOOP("CalcTbl", "rec_des_flow_qfr"),
            QT_TRANSLATE_NOOP("CalcTbl", "prj_flow_rate_qgmax"), QT_TRANSLATE_NOOP("CalcTbl", "water_level_y"),
            QT_TRANSLATE_NOOP("CalcTbl", "water_level_pipe_end"), QT_TRANSLATE_NOOP("CalcTbl", "tractive_force"),
            QT_TRANSLATE_NOOP("CalcTbl", "critical_velocity"), QT_TRANSLATE_NOOP("CalcTbl", "velocity"), QT_TRANSLATE_NOOP("CalcTbl", "initial_rec_des_flow_qfr"),
            QT_TRANSLATE_NOOP("CalcTbl", "initial_flow_rate_qi"), QT_TRANSLATE_NOOP("CalcTbl", "water_level_y_start"),
            QT_TRANSLATE_NOOP("CalcTbl", "water_level_pipe_start"), QT_TRANSLATE_NOOP("CalcTbl", "tractive_force_start"),
            QT_TRANSLATE_NOOP("CalcTbl", "initial_critical_velocity"), QT_TRANSLATE_NOOP("CalcTbl", "initial_velocity"),
            QT_TRANSLATE_NOOP("CalcTbl", "inspection_id_up"), QT_TRANSLATE_NOOP("CalcTbl", "inspection_type_up"),
            QT_TRANSLATE_NOOP("CalcTbl", "inspection_id_down"), QT_TRANSLATE_NOOP("CalcTbl", "inspection_type_down"),
            QT_TRANSLATE_NOOP("CalcTbl", "downstream_seg_id"), QT_TRANSLATE_NOOP("CalcTbl", "observations"),
            QT_TRANSLATE_NOOP("CalcTbl", "slopes_min_modified")
        )
        self.hiddenColumns = [
            "id","project_id","layer_name","created_at","updated_at", 
            "x_initial", "y_initial","x_final","y_final", "slopes_min_modified"
        ]


    def getColumns(self):        
        return self.columns
    
    def getHiddenColumns(self):
        return self.hiddenColumns


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if (orientation == Qt.Vertical and role == Qt.BackgroundRole and self.record(section).value('initial_segment') == 1):
            return QColor(230, 104, 41)
        if (orientation == Qt.Vertical and role == Qt.DisplayRole):
            return self.record(section).value('col_seg')

        if role == Qt.ToolTipRole:
            if orientation == Qt.Horizontal:
                return translate("CalcTbl", "tooltip_" + self.record().fieldName(section))

        return super(Calculation, self).headerData(section, orientation, role)

    def data(self, index, role):
        if role == Qt.ForegroundRole:
            val = index.data()
            if (val == 'DN !!' or type(val) not in [bool, str, QVariant]):
                if val < 0:
                    return QBrush(Qt.red)
            
            if (type(val) == str):
                try:
                    if (float(val) < 0):
                        return QBrush(Qt.red)
                except ValueError:
                    return False
        
        if role == Qt.DisplayRole:
            col = index.column()
            val = QSqlRelationalTableModel.data(self, index, Qt.DisplayRole)
            
            if val in [None, ''] or type(val) == QVariant:
                return ''
            
            if col in [7, 14, 15, 17, 18, 22, 23, 24, 25, 26, 28, 29, 30, 31, 32, 33, 40, 41, 42, 44, 45, 46, 47, 48, 49, 51]:                
                if not isinstance(val, float):
                    val = float(val)
                if (val < -88888):
                    return 'DN !!'
                return '{:.2f}'.format(round(val, 2))

            if col in [39]:
                if not isinstance(val, float):
                    val = float(val)
                return '{:.3f}'.format(round(val, 3))

            if col in [16, 34]:
                if not isinstance(val, float):
                    val = float(val)
                return '{:.4f}'.format(round(val, 4))

            if col in [35, 36]:
                if not isinstance(val, float):
                    val = float(val)
                return '{:.5f}'.format(round(val, 5))

            if col in [43, 50]:
                if not isinstance(val, float):
                    val = float(val)
                if (val < -88888):
                    return 'DN !!'
                return '{:.0f}%'.format(round(val, 0))
        return super(Calculation, self).data(index, role)

    def updateColById(self, value, colName, id):
        value = 'NULL' if value == None else value
        sql = "UPDATE calculations\
                            SET {} = {}\
                            WHERE id = {}".format(colName, value, id)
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            return query.lastError()
        return value

    def clearProjectRows(self, project_id):
        """ remove all rows from given project_id """
        sql = "delete from calculations where project_id={}".format(project_id)
        query = QSqlQuery()
        query.exec("PRAGMA foreign_keys=on;")  
        success =  query.exec(sql)
        if not success:
            err = query.lastError().text()
        return success

    # $RedBasica.$F$11
    def getExtensionSum(self):
        query = QSqlQuery("SELECT sum(extension)\
                        FROM calculations c\
                        LEFT JOIN projects p ON c.project_id = p.id\
                        WHERE p.active")
        if query.first():
            return round(query.value(0),1)

    # $RedBasica.$K$11
    def getQtyFinalQeSum(self):
        query = QSqlQuery("SELECT sum(qty_final_qe)\
                        FROM calculations c\
                        LEFT JOIN projects p ON c.project_id = p.id\
                        AND p.active")
        if query.first():
            return round(query.value(0),5)

    # $RedBasica.$L$11
    def getQtyInitialQeSum(self):
        query = QSqlQuery("SELECT sum(qty_initial_qe)\
                        FROM calculations c\
                        LEFT JOIN projects p ON c.project_id = p.id\
                        AND p.active")
        if query.first():
            return round(query.value(0),5)

    # $A1.$C$14 Previous Segment - Current Collector Pipe (l/s)
    def getTotalFlowEndByColSeg(self, colSeg):
        query = QSqlQuery("SELECT total_flow_rate_end\
                        FROM calculations c\
                        LEFT JOIN projects pr ON c.project_id = pr.id\
                        WHERE pr.active AND col_seg = '{}'".format(colSeg))
        if query.first():
            return 0 if query.value(0) == None else round(query.value(0), 5)
        else:
            return 0

    def getAvgFlowEndByColSeg(self, colSeg):
        query = QSqlQuery("SELECT avg_flow_end\
                        FROM contributions c\
                        LEFT JOIN calculations ca ON ca.id = c.calculation_id\
                        LEFT JOIN projects pr ON ca.project_id = pr.id\
                        WHERE pr.active AND c.col_seg = '{}'".format(colSeg))
        if query.first():
            return 0 if query.value(0) == None else round(query.value(0), 6)
        else:
            return 0

    def getTotalFlowStartByColSeg(self, colSeg):
        query = QSqlQuery("SELECT total_flow_rate_start\
                        FROM calculations c\
                        LEFT JOIN projects pr ON c.project_id = pr.id\
                        WHERE pr.active AND col_seg = '{}'".format(colSeg))
        if query.first():
            return 0 if query.value(0)==None else round(query.value(0), 5)
        else:
            return 0

    def getAvgFlowStartByColSeg(self, colSeg):
        query = QSqlQuery("SELECT avg_flow_start\
                        FROM contributions c\
                        LEFT JOIN calculations ca ON ca.id = c.calculation_id\
                        LEFT JOIN projects pr ON ca.project_id = pr.id\
                        WHERE pr.active AND c.col_seg = '{}'".format(colSeg))
        if query.first():
            return 0 if query.value(0) == None else round(query.value(0), 6)
        else:
            return 0

    def getValueBy(self, column, where=None):
        sql = "SELECT c.{}\
                FROM calculations c\
                LEFT JOIN projects pr ON c.project_id = pr.id\
                WHERE pr.active".format(column)
        if where != None:
            sql = sql + " AND {}".format(where)
        query = QSqlQuery(sql)
        if query.first():
            return query.value(0)
        else:
            return 0
    
    def eh(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        else:
            return ((nman * qls / 1000)/ ((imm ** 0.5) * ((dmm / 1000) ** (8/3))))
    
    def ehlin(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        else:
            return 8 * ((((((nman * qls / 1000) / ((imm**0.5) * ((dmm / 1000) ** (8 / 3))))) ** 3) / 4) ** 0.2)

    def angteta(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        tta = 3
        ttb = math.sin(tta) + (self.ehlin(qls,dmm,imm,nman)) * (tta ** 0.4)
        while (abs(tta-ttb) > 0.00001):
            tta = ttb
            ttb = math.sin(tta) + (self.ehlin(qls,dmm,imm,nman)) * (tta ** 0.4)
        return ttb

    def raiohidr(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        else:
            angteta = self.angteta(qls, dmm, imm, nman)
            if angteta < (2 * 3.14159265358979):
                return dmm / (1000 * 4) * ((1 - (math.sin(angteta) / angteta)))
            else:
                return -9999999999  #"Diâmetro Insuficiente"
    
    def laminaabs(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        else:
            angteta = self.angteta(qls, dmm, imm, nman)
            if angteta < (2 * 3.14159265358979):
                return dmm / (1000 * 2) * ((1 - (math.cos(angteta / 2))))
            else:
                return -8888888888 #DN!!
    
    def laminarel(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        else:
            angteta = self.angteta(qls, dmm, imm, nman)
            if angteta < (2 * 3.14159265358979):
                return 0.5 * ((1 - (math.cos(angteta / 2))))
            else:
                return -8888888888 #DN!!
    
    def areamolh(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        else:
            angteta = self.angteta(qls, dmm, imm, nman)
            if angteta < (2 * 3.14159265358979):
                return ((dmm / 1000) ** 2) / 8 * ((angteta - (math.sin(angteta))))
            else:
                return -8888888888 #DN!!
    
    def perimolh(self, qls, dmm, imm, nman):
        if qls == 0:
            return 0
        else:
            angteta = self.angteta(qls, dmm, imm, nman)
            if angteta < (2 * 3.14159265358979):
                return dmm / 1000 * (angteta / 2)
            else:
                return -8888888888 #DN!!
    
    def tenstrat(self, qls, dmm, imm, nman):
        if self.angteta(qls, dmm, imm, nman) < (2 * 3.14159265358979):
            return (self.raiohidr(qls, dmm, imm, nman) * imm * 1000 * 9.81)
        else:
            return -8888888888 #DN!!
    
    def velocid(self, qls, dmm, imm, nman):
        if nman == 0:
            return 0
        else:
            if self.angteta(qls, dmm, imm, nman) < (2 * 3.14159265358979):
                return (self.raiohidr(qls, dmm, imm, nman) ** 0.6667) * (imm ** 0.5) / nman
            else:
                return -8888888888 #DN!!

    def velocrit(self, qls, dmm, imm, nman):
        if nman == 0:
            return 0
        else:
            if self.angteta(qls, dmm, imm, nman) < (2 * 3.14159265358979):
                return (((self.raiohidr(qls, dmm, imm, nman) * 9.8) ** 0.5) * 6)
            else:
                return -8888888888 #DN!!
    
    def dn1mm(self, qls, imm, nman, tirmx):
        if qls == 0:
            return 0
        else:
            return 1000 * ((nman * qls / 1000) / (self.e2((tirmx/100)) * (imm ** (1 / 2)))) ** (3 / 8)
    

    #Function to estimate the flow section factor E for blades 60 to 90
    def e1(self, tirmax):
        if tirmax == 0:
            return 0
        else:
            return (-0.8224 * (tirmax ** 3)) + (1.3033 * (tirmax ** 2)) - (0.1362 * tirmax)
    

    def e2(self, tirmx):
        if tirmx == 0:
            return 0
        else:
            return (-0.7867 * (tirmx ** 3)) + (1.2133 * (tirmx ** 2)) - (0.0912 * tirmx)
    
    def getCompleteStructure(self, projectId):
        structure = self.getColNumberGroup(projectId)
        m1Cols = self.getM1Cols(projectId)
        m2Cols = self.getM2Cols(projectId)

        for collectorNumber, colSegList in list(structure.items()):
            for m1 in m1Cols:
                if m1 in colSegList:
                    del structure[collectorNumber]
            for m2 in m2Cols:
                if m2 in colSegList:
                    del structure[collectorNumber]
        return structure, m1Cols, m2Cols

    
    def getColNumberGroup(self, projectId):
        sql = "select collector_number, group_concat(col_seg)\
                from calculations\
                where project_id = {}\
                group by collector_number".format(projectId)
        query = QSqlQuery(sql)
        structure = {}
        while query.next():
            structure[query.value(0)] = query.value(1).split(',')
        return structure
    
    def getM1Cols(self, projectId):
        sql = "select group_concat(m1_col_id)\
                from calculations\
                where m1_col_id != ''\
                and project_id = {}".format(projectId)
        query = QSqlQuery(sql)
        if query.first():
            return query.value(0).split(',')
    
    def getM2Cols(self, projectId):
        sql = "select group_concat(m2_col_id)\
                from calculations\
                where m2_col_id != ''\
                and project_id = {}".format(projectId)
        query = QSqlQuery(sql)
        if query.first():
            return [0] if query.value(0) == None else query.value(0).split(',')

    def getMaterialByDiameter(self, diameter, projectId):
        sql = "select name_es from materials m \
                left join pipes p \
                on m.id = p.material_id\
                left join parameters s \
                on p.criteria_id = s.project_criteria_id \
                left join projects pr \
                on s.id = pr.parameter_id \
                where p.diameter = {} and pr.id = {}".format(diameter, projectId)
        query = QSqlQuery(sql)
        if query.first():
            return '' if query.value(0) == None else query.value(0)

    def updateAuxDepthAdj(self, projectId):
        sql = "UPDATE calculations SET aux_depth_adjustment = (SELECT calc_depth_up FROM wl_adj WHERE wl_adj.id = calculations.id)\
               WHERE project_id = {}".format(projectId)
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            return query.lastError()
        return True
    
    def clearAuxDepthAdj(self, projectId):
        sql = "UPDATE calculations SET aux_depth_adjustment = NULL \
               WHERE project_id = {}".format(projectId)
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            return query.lastError()
        return True
    
    def clearDiameter(self, projectId):
        sql = "UPDATE calculations SET adopted_diameter = NULL \
               WHERE project_id = {}".format(projectId)
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            return query.lastError()
        return True
    
    def updateForceDepthDown(self, projectId):
        sql = "UPDATE calculations SET force_depth_down = (SELECT aux_h_imp_depth FROM wl_adj w WHERE w.calculation_id = calculations.id)\
               WHERE project_id = {}".format(projectId)
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            return query.lastError()
        return True

    @staticmethod
    def getSwmmSegments():
        """ Active project segments info (needed to create INP file) """
        
        sql = "select col_seg, extension, c_manning, inspection_id_up, inspection_id_down, \
              (adopted_diameter / 1000) as dn_meters, round(el_col_down - \
              (select el_col_up from calculations where col_seg = c.downstream_seg_id),2) as upstream_drop, \
              round(initial_flow_rate_qi,2) as q_i, round(prj_flow_rate_qgmax,2) as q_f from calculations c \
              LEFT JOIN projects pr ON c.project_id = pr.id\
                WHERE pr.active"
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            print(query.lastError())
            return False
        data = []
        rec = query.record()
        fields = [rec.fieldName(ix) for ix in range(rec.count())]
        while query.next():
            d = { f: query.value(rec.indexOf(f)) for f in fields}
            data.append(d)
        return data

    @staticmethod
    def getSwmmNodes():
        """ Returns active projects nodes with x,y coordenates """
        
        sql = "select inspection_id_up as node, el_col_up as elev, depth_up as depth, x_initial as x, y_initial as y \
            from calculations c1 LEFT JOIN projects pr ON c1.project_id = pr.id WHERE pr.active\
            UNION \
            select inspection_id_down as node, el_col_down as elev, depth_down as depth, x_final as x, y_final as y from calculations c2 \
            LEFT JOIN projects pr ON c2.project_id = pr.id WHERE pr.active \
            AND inspection_id_down not in \
            (select distinct inspection_id_up from calculations c3 LEFT JOIN projects pr ON c3.project_id = pr.id WHERE pr.active)"
        
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            print(query.lastError())
            return False
        data = []
        rec = query.record()
        fields = [rec.fieldName(ix) for ix in range(rec.count())]
        while query.next():
            d = { f: query.value(rec.indexOf(f)) for f in fields}
            data.append(d)
        return data

    @staticmethod
    def getActiveProfileData(colSeg):
        """ Returns segments data to plot profile """
        sql = "select collector_number, col_seg, \
            (select sum(extension) from calculations c1 where c1.collector_number = c.collector_number and c.id > id and pr.active) as x_initial,\
            (select sum(extension) from calculations c1 where c1.collector_number = c.collector_number and c.id >= id and pr.active) as x_final,\
            depth_up as y_initial,\
            depth_down as y_final,\
            x_initial as geom_x_initial,\
            y_initial as geom_y_initial,\
            x_final as geom_x_final,\
            y_final as geom_y_final,\
            previous_col_seg_id,\
            m1_col_id,\
            m2_col_id,\
            extension,\
            water_level_pipe_end as water_level,\
            inspection_type_up,\
            el_terr_up,\
            el_col_up,\
            adopted_diameter,\
            slopes_adopted_col,\
            downstream_seg_id as downSeg\
            from calculations c LEFT JOIN projects pr ON c.project_id = pr.id WHERE pr.active and col_seg = '{}'".format(colSeg)
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            print(query.lastError())
            return False
        data = {}        
        rec = query.record()
        key = 'collector_number'
        fields = [rec.fieldName(ix) for ix in range(rec.count())]
        while query.next():
            dict_key = query.value(rec.indexOf(key))
            d = { f: query.value(rec.indexOf(f)) for f in fields}
            if dict_key not in data.keys():
                data[dict_key] = []
            data[dict_key].append(d)
        return data

    @staticmethod
    def getDownstreamSeg(downSeg):
        sql = "select inspection_type_up, el_terr_up, el_col_up, depth_up as y_initial, extension\
        from calculations c LEFT JOIN projects pr ON c.project_id = pr.id WHERE pr.active and col_seg = '{}'".format(downSeg)
        query = QSqlQuery(sql)
        if query.first():
            data = query.record()
            return data
        return False

    @staticmethod
    def getTree(col_seg_att_name, features):
        feats = { f.attribute(col_seg_att_name): f for f in features}
        colSegs = list(feats.keys())
        data = Calculation.getColsegs(str(tuple(colSegs)))
        root = list(data.keys())
        relations = {}
        notInList = []
        for colSeg in colSegs:
            for d in data.values():
                c = d[0]
                if colSeg == c['previous_col_seg_id'] or colSeg == c['m1_col_id'] or colSeg == c['m2_col_id']:
                    if c['col_seg'] in root:
                        root.remove(c['col_seg'])
                        relations[colSeg] = c['col_seg']
                    else:
                        notInList.append(colSeg)
                        del feats[colSeg]
                        root.remove(colSeg)
        if len(root)>1:
            for r in root:
                if r not in relations:
                    notInList.append(r)
                    del feats[r]
                    root.remove(r)
        ordered = Calculation.orderColSegs(root[0], relations, {}, feats)
        return list(ordered.values()), notInList

    def orderColSegs(parent, list, aux, features):
        if (parent in list and list[parent] in list):
            aux[parent] = features[parent]
            return Calculation.orderColSegs(list[parent], list, aux, features)
        aux[parent]=features[parent]
        aux[list[parent]]=features[list[parent]]
        return aux

    @staticmethod
    def getColsegs(colSegs):
        sql = "SELECT c.id, collector_number, col_seg, previous_col_seg_id, m1_col_id, m2_col_id\
               FROM calculations c\
               LEFT JOIN projects p ON c.project_id = p.id  WHERE  p.active\
               and col_seg in {}".format(colSegs)
        query = QSqlQuery(sql)
        if query.lastError().isValid():
            print(query.lastError())
            return False
        data = {}
        rec = query.record()
        key = 'col_seg'
        fields = [rec.fieldName(ix) for ix in range(rec.count())]
        while query.next():
            dict_key = query.value(rec.indexOf(key))
            d = { f: query.value(rec.indexOf(f)) for f in fields}
            if dict_key not in data.keys():
                data[dict_key] = []
            data[dict_key].append(d)
        return data