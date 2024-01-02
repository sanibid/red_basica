from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication
from ..models.Calculation import Calculation
from ..models.Parameter import Parameter
from ..models.Project import Project
from ..models.Criteria import Criteria
from ..models.Contribution import Contribution
from ..models.WaterLevelAdj import WaterLevelAdj
from ..models.Pipe import Pipe
from ..models.InspectionDevice import InspectionDevice
from .DataController import DataController
import time
import traceback
import math
translate = QCoreApplication.translate

class CalculationController(QObject):
    
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, str)
    progress = pyqtSignal(float)
    info = pyqtSignal(str)
    message = pyqtSignal(str)

    def __init__(self, projectId=None):
        QObject.__init__(self)
        self.projectId = projectId
        self.model = Calculation()
        self.parameterModel = Parameter()
        self.critModel = Criteria()
        self.contModel = Contribution()
        self.projModel = Project()
        self.wlAdj = WaterLevelAdj()
        self.pipe = Pipe()
        self.inspectionoDevice = InspectionDevice() 

    def importData(self, only_selected_features=False):
        success = True
        projectId = self.projectId
        try:
            # we dont check if is firstTime anymore
            start_time = time.time()
            if success:
                self.progress.emit(25)
                self.projModel.setSrid(projectId)
                success = self.uploadCalculations(projectId, only_selected_features)
                print("Total time execution to calculations:--- %s seconds ---" % (time.time() - start_time))

            if success:
                success = self.updateParameters()
                self.progress.emit(50)

            if success:
                success = self.updateContributions(projectId)
                self.progress.emit(75)

            if success:
                success = self.calcAfter(projectId)
                self.progress.emit(90)
                print("Total time execution to upload:--- %s seconds ---" % (time.time() - start_time))

            if success:
                self.progress.emit(100)
            
        except Exception as e:
            self.error.emit(e, traceback.format_exc())

        self.finished.emit(success)
    

    def exportData(self, projectId):
        """ Get segments data back from db in order to insert into qgis layer """
        
        calMod = Calculation()
        calMod.setFilter('project_id = {}'.format(projectId))
        calMod.select()
        while calMod.canFetchMore():
            calMod.fetchMore()
        critModel = Criteria()
        max_drop = critModel.getValueBy('max_drop')
        
        segments = {}
        nodes = {}
        for i in range(calMod.rowCount()):
            rec = calMod.record(i)
            col_seg = rec.value('col_seg')
            col_down = rec.value('el_col_down')
            col_up = calMod.getValueBy('el_col_up', 'previous_col_seg_id = "{}"'.format(col_seg))
            
            # SEGMENTS
            if col_up == 0:
                #check m1
                col_up = calMod.getValueBy('el_col_up', 'm1_col_id = "{}"'.format(col_seg))
                if col_up == 0:
                    col_up = calMod.getValueBy('el_col_up', 'm2_col_id = "{}"'.format(col_seg))
            upstream_drop = round(col_down - col_up, 6) if col_up > 0 else 0 #TODO:check this
            
            segment = {
                'ID_TRM_(N)': col_seg,
                'h_col_p2': round(rec.value('depth_down'), 2),
                'h_col_p1': round(rec.value('depth_up'), 2),
                'h_tap_p2': round(rec.value('covering_down'), 2),
                'h_tap_p1': round(rec.value('covering_up'), 2),
                'S': round(rec.value('slopes_adopted_col'), 5),
                'DN': rec.value('adopted_diameter'),
                'Mat_col': calMod.getMaterialByDiameter(rec.value('adopted_diameter'), projectId),
                'Caida_p2': (upstream_drop > 0.005 and ((upstream_drop < max_drop and ("D",) or ("TC",))[0],) or ("",))[0],
                'Caida_p2_h': round(upstream_drop, 2),
                'n': rec.value('c_manning'),
                'Qmed_i': round(rec.value('total_flow_rate_start'), 2),
                'Qmed_f': round(rec.value('total_flow_rate_end'), 2),
                'Qmax_i': round(rec.value('initial_flow_rate_qi'), 2),
                'Qmax_f': round(rec.value('prj_flow_rate_qgmax'), 2),
                'yn_i': round(rec.value('water_level_y_start'), 2),
                'yn_f': round(rec.value('water_level_y'), 2),
                'yrel_i': round(rec.value('water_level_pipe_start'), 2),
                'yrel_f': round(rec.value('water_level_pipe_end'), 2),
                'Trativa_i': round(rec.value('tractive_force_start'),2),
                'Trativa_f': round(rec.value('tractive_force'),2),
                'V_i': round(rec.value('initial_velocity'),2),
                'V_f': round(rec.value('velocity'), 2),
                'Vc_f': round(rec.value('critical_velocity'), 2),
                'Vc_i': round(rec.value('initial_critical_velocity'), 2),
                'Qr_i': round(rec.value('initial_rec_des_flow_qfr'), 2),
                'Qr_f': round(rec.value('rec_des_flow_qfr'), 2),
            }
            segments[col_seg] = segment

            # NODES
            node_id = rec.value('inspection_id_up') #should be equal to col_seg, right?
            node = {
                'Id_NODO_(n)': node_id,
                'Nodo_tipo': rec.value('inspection_type_up'),
                'CF_nodo': round(rec.value('el_col_up'), 2),
                'h_nodo_NT': round(rec.value('depth_up'), 2),
                'h_nodo_tp': '',
                'CItrd_nodo': round(rec.value('el_top_gen_up'), 2),
                'Tap_nodo': round(rec.value('covering_up'), 2)
            }
            nodes[col_seg] = node

        # Get final nodes
        for i in range(calMod.rowCount()):
            rec = calMod.record(i)
            node_id = rec.value('inspection_id_down')
            if node_id not in nodes.keys():
                node = {
                    'Id_NODO_(n)':node_id,
                    'Nodo_tipo':rec.value('inspection_type_down'),
                    'CF_nodo':round(rec.value('el_col_down'), 2),
                    'h_nodo_NT':round(rec.value('depth_down'), 2),
                    'h_nodo_tp':'',
                    'CItrd_nodo':round(rec.value('el_top_gen_down'), 2),
                    'Tap_nodo':round(rec.value('covering_down'), 2)
                }
                nodes[node_id] = node

        return {'segments':segments,'nodes':nodes}


    def uploadCalculations(self, projectId, only_selected_features=False):
        try:
            clear = self.model.clearProjectRows(projectId) #clears contributions and wla also
            data = DataController().getJsonData(only_selected_features)
            if clear and data:
                msg = translate("Calculation", "Uploading")
                print(msg)
                self.info.emit(msg)
                for row in data:
                    self.model.select()
                    rec = self.model.record()
                    rec.setValue('project_id',projectId)
                    rec.setValue('initial_segment',row['AUX_TRM_I'])
                    rec.setValue('final_segment',row['AUX_TRM_F'])
                    rec.setValue('collector_number',row['ID_COL'])
                    rec.setValue('col_seg',row['ID_TRM_(N)'])
                    rec.setValue('extension',row['L'])
                    rec.setValue('previous_col_seg_id',row['TRM_(N-1)_A'])
                    rec.setValue('m1_col_id',row['TRM_(N-1)_B'])
                    rec.setValue('m2_col_id',row['TRM_(N-1)_C'])
                    if not row['ID_UC'] == 'NULL':
                        rec.setValue('block_others_id',row['ID_UC'])
                    qeFp = row['QE_FP'] if 'QE_FP' in row else row['QEF']
                    rec.setValue('qty_final_qe', qeFp)
                    qeIp = row['QE_IP'] if 'QE_IP' in row else row['QEI']
                    rec.setValue('qty_initial_qe', qeIp)
                    qconcf =  row['QConcF'] if 'QConcF' in row else None
                    rec.setValue('conc_flow_qcf', qconcf)
                    qconci =  row['QConcI'] if 'QConcI' in row else None
                    rec.setValue('conc_flow_qci', qconci)
                    intake_in_seg = round(self.critModel.getValueBy('intake_rate') * self.strToFloat(row['L'])/1000, 6)
                    rec.setValue('intake_in_seg', intake_in_seg)
                    if not row['AUX_POS'] == 'NULL':
                        rec.setValue('col_pipe_position',row['AUX_POS'])
                    if not row['AUX_PROF_I'] == 'NULL':
                        rec.setValue('aux_prof_i',row['AUX_PROF_I'])
                    rec.setValue('el_terr_up',row['COTA_I'])
                    rec.setValue('el_terr_down',row['COTA_F'])
                    slopesTerr = 0 if (float(row['L']) == 0 or row['ID_COL'] == None) else round((float(row['COTA_I']) - float(row['COTA_F'])) / float(row['L']), 4)
                    rec.setValue('slopes_terr',slopesTerr)
                    rec.setValue('inspection_id_up',row['NODO_I'])
                    rec.setValue('inspection_id_down',row['NODO_F'])
                    rec.setValue('downstream_seg_id',row['TRM_(N+1)'])
                    rec.setValue('x_initial',row['X_I'])
                    rec.setValue('y_initial',row['Y_I'])
                    rec.setValue('x_final',row['X_F'])
                    rec.setValue('y_final',row['Y_F'])
                    rowCount = self.model.rowCount()
                    if (self.model.insertRecord(rowCount,rec)):
                        cRec = self.contModel.record()
                        cRec.setValue('calculation_id', self.model.query().lastInsertId())
                        condominial_lines_end = self.strToFloat(qeFp) * self.paramVal('occupancy_rate_end') * self.critVal('water_consumption_pc') * self.critVal('coefficient_return_c') / 86400
                        cRec.setValue('condominial_lines_end', condominial_lines_end)
                        cRec.setValue('initial_segment',row['AUX_TRM_I'])
                        cRec.setValue('col_seg',row['ID_TRM_(N)'])
                        condominial_lines_start = self.strToFloat(qeIp) * self.paramVal('occupancy_rate_start') * self.critVal('water_consumption_pc') * self.critVal('coefficient_return_c') / 86400
                        cRec.setValue('condominial_lines_start', condominial_lines_start)
                        cRow = self.contModel.rowCount()
                        self.contModel.insertRecord(cRow, cRec)

                        wlRec = self.wlAdj.record()
                        wlRec.setValue('calculation_id', self.model.query().lastInsertId())
                        wlRec.setValue('col_seg',row['ID_TRM_(N)'])
                        wlRec.setValue('initial_segment',row['AUX_TRM_I'])
                        wlRec.setValue('previous_col_seg_end',row['TRM_(N-1)_A'])
                        wlRec.setValue('m1_col_id',row['TRM_(N-1)_B'])
                        wlRec.setValue('m2_col_id',row['TRM_(N-1)_C'])
                        wlRow = self.wlAdj.rowCount()
                        self.wlAdj.insertRecord(wlRow, wlRec)
                return True
            else:
                self.info.emit(translate("Calculation", "ERROR:Selected patch(es)  have repeated names"))
                return False
        
        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        return False

    # When the calculations have been loaded, the missing parameters are generated
    def updateParameters(self):
        msg = translate("Calculation", "Updating Parameters")
        self.info.emit(msg)
        print(msg)
        paramModel = Parameter()
        paramModel.select()
        try:
            row = 0
            id = self.projModel.getActiveProjectParameter()
            paramModel.setFilter('id = {}'.format(id))
            paramModel.select()
            contributionSewage = paramModel.getValueBy('contribution_sewage')
            sewerContEnd = self.avgLinearContributionRate(0) if contributionSewage > 0 else 0
            sewerContStart = self.avgLinearContributionRate(1) if contributionSewage > 0 else 0
            paramModel.setData(paramModel.index(row, paramModel.fieldIndex('point_flows_end')), self.model.getQtyFinalQeSum())
            paramModel.setData(paramModel.index(row, paramModel.fieldIndex("point_flows_start")), self.model.getQtyInitialQeSum())
            paramModel.setData(paramModel.index(row, paramModel.fieldIndex("sewer_contribution_rate_end")), round(sewerContEnd, 13))
            paramModel.setData(paramModel.index(row, paramModel.fieldIndex("sewer_contribution_rate_start")), round(sewerContStart,13))
            paramModel.setData(paramModel.index(row, paramModel.fieldIndex("sewer_system_length")), round(self.model.getExtensionSum(),5))
            paramModel.updateRowInTable(row, paramModel.record(row))
            return True
        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        return False

    def updateContributions(self, projectId):
        msg = translate("Calculation", "Updating Contributions")
        self.info.emit(msg)
        print(msg)
        try:
            if projectId:
                self.model.setFilter('project_id = {} and initial_segment = 1'.format(projectId))
                for i in range(self.model.rowCount()):
                    self.model.select()
                    colSeg = self.model.record(i).value('col_seg')
                    if self.model.record(i).value('total_flow_rate_end') == None:
                        self.recursiveContributions(projectId, colSeg)
                    if self.model.record(i).value('aux_depth_adjustment') == None: #TODO check if is the only way to know if is calculated
                        self.waterLevelAdjustments(projectId, colSeg)
                return True
            else:
                raise Exception("projectId is required to update contributions")
        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        return False

    def recursiveContributions(self, projectId, colSeg, recalculate=False, m1List=[], m2List=[]):
        calMod = Calculation()
        conMod = Contribution()
        
        splitCol = colSeg.split('-')
        conMod.setFilter('calculation_id in (select id from calculations where project_id = {}) and col_seg like "{}-%" ORDER BY initial_segment DESC'.format(projectId, splitCol[0]))
        calMod.setFilter('project_id = {} and col_seg like "{}-%" ORDER BY initial_segment DESC'.format(projectId, splitCol[0]))
        
        calMod.select()
        conMod.select()
        while calMod.canFetchMore():
                calMod.fetchMore()
        while conMod.canFetchMore():
            conMod.fetchMore()
        for i in range(conMod.rowCount()):
            calMod.select()
            conMod.select()
            calc = calMod.record(i)
            con = conMod.record(i)
            m1End = m1Start = m2End = m2Start = 0
            if recalculate:
                if calc.value('m1_col_id') in m1List:
                    self.recursiveContributions(projectId, calc.value('m1_col_id'), True, m1List, m2List)
                    calMod.select()
                    m1End = calMod.getAvgFlowEndByColSeg(calc.value('m1_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m1_end')), m1End)
                    m1Start = calMod.getAvgFlowStartByColSeg(calc.value('m1_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m1_start')), m1Start)
                else:
                    m1End = calMod.getAvgFlowEndByColSeg(calc.value('m1_col_id'))
                    m1Start = calMod.getAvgFlowStartByColSeg(calc.value('m1_col_id'))
            else:
                if calc.value('m1_col_id'):
                    self.recursiveContributions(projectId, calc.value('m1_col_id'))
                    calMod.select()
                    m1End = calMod.getAvgFlowEndByColSeg(calc.value('m1_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m1_end')), m1End)
                    m1Start = calMod.getAvgFlowStartByColSeg(calc.value('m1_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m1_start')), m1Start)

            if recalculate:
                if calc.value('m2_col_id') in m2List:
                    self.recursiveContributions(projectId, calc.value('m2_col_id'), True, m1List, m2List)
                    calMod.select()
                    m2End = calMod.getAvgFlowEndByColSeg(calc.value('m2_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m2_end')), m2End)
                    m2Start = calMod.getAvgFlowStartByColSeg(calc.value('m2_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m2_start')), m2Start)
                else:
                    m2End = calMod.getAvgFlowEndByColSeg(calc.value('m2_col_id'))
                    m2Start = calMod.getAvgFlowStartByColSeg(calc.value('m2_col_id'))
            else:
                if calc.value('m2_col_id'):
                    self.recursiveContributions(projectId, calc.value('m2_col_id'))
                    calMod.select()
                    m2End = calMod.getAvgFlowEndByColSeg(calc.value('m2_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m2_end')), m2End)
                    m2Start = calMod.getAvgFlowStartByColSeg(calc.value('m2_col_id'))
                    conMod.setData(conMod.index(i, conMod.fieldIndex('col_pipe_m2_start')), m2Start)

            prevEnd = calMod.getAvgFlowEndByColSeg(calc.value('previous_col_seg_id'))
            conMod.setData(conMod.index(i, conMod.fieldIndex('previous_col_seg_end')), prevEnd)
            prevStart = calMod.getAvgFlowStartByColSeg(calc.value('previous_col_seg_id'))
            conMod.setData(conMod.index(i, conMod.fieldIndex('previous_col_seg_start')), prevStart)
            subtotalUpSegEnd = prevEnd + m1End + m2End
            conMod.setData(conMod.index(i, conMod.fieldIndex('subtotal_up_seg_end')), subtotalUpSegEnd)
            subtotalUpSegStart = prevStart + m1Start + m2Start
            conMod.setData(conMod.index(i, conMod.fieldIndex('subtotal_up_seg_start')), subtotalUpSegStart)
            ext = calMod.getValueBy('extension', 'col_seg = "{}"'.format(con.value('col_seg')))
            endLinear = self.getEndLinearContInSeg(ext)
            conMod.setData(conMod.index(i, conMod.fieldIndex('linear_contr_seg_end')), endLinear)
            startLinear = self.getStartLinearContInSeg(ext)
            conMod.setData(conMod.index(i, conMod.fieldIndex('linear_contr_seg_start')), startLinear)
            if conMod.updateRowInTable(i, conMod.record(i)):
                concFlowFinal = calMod.record(i).value('conc_flow_qcf') if calMod.record(i).value('conc_flow_qcf') != None else 0
                avgFlowEnd = round((subtotalUpSegEnd + con.value('condominial_lines_end')+ concFlowFinal + endLinear), 6)
                conMod.setData(conMod.index(i, conMod.fieldIndex('avg_flow_end')), avgFlowEnd)
                calMod.setData(calMod.index(i, calMod.fieldIndex('total_flow_rate_end')), avgFlowEnd)
                concFlowStart = calMod.record(i).value('conc_flow_qci') if calMod.record(i).value('conc_flow_qci') != None else 0
                avgFlowStart = round((subtotalUpSegStart + con.value('condominial_lines_start') + concFlowStart + startLinear), 6)
                conMod.setData(conMod.index(i, conMod.fieldIndex('avg_flow_start')), avgFlowStart)
                calMod.setData(calMod.index(i, calMod.fieldIndex('total_flow_rate_start')), avgFlowStart)

                adoptedDiameterInserted = calMod.getValueBy('adopted_diameter', 'col_seg = "{}"'.format(calc.value('col_seg')))
                if adoptedDiameterInserted == None:
                    adoptedDiameter = self.critVal('min_diameter') if calc.value('initial_segment') == 1 else calMod.getValueBy('adopted_diameter', 'col_seg = "{}"'.format(calc.value('previous_col_seg_id')))
                else:
                    adoptedDiameter = adoptedDiameterInserted
                calMod.setData(calMod.index(i, calMod.fieldIndex('adopted_diameter')), adoptedDiameter)
                slopesMinAccepted = 0 if calc.value('extension') == 0 else self.slopesMinAcceptedCalc(adoptedDiameter)
                if calc.value('slopes_min_modified') != True:
                    calMod.setData(calMod.index(i, calMod.fieldIndex('slopes_min_accepted_col')), slopesMinAccepted)
                cManning = 0 if (calc.value('extension') == 0 or calc.value('collector_number') == 0) else self.pipe.getValueBy('manning_adopted',"diameter ='{}'".format(adoptedDiameter))
                calMod.setData(calMod.index(i, calMod.fieldIndex('c_manning')), cManning)
                intakePrevCol = conMod.getIntakeBySegment(calc.value('previous_col_seg_id'))
                conMod.setData(conMod.index(i, conMod.fieldIndex('intake_prev_col')), intakePrevCol)
                intakeColM1 = conMod.getIntakeBySegment(calc.value('m1_col_id'))
                conMod.setData(conMod.index(i, conMod.fieldIndex('intake_col_m1')), intakeColM1)
                intakeColM2 = conMod.getIntakeBySegment(calc.value('m2_col_id'))
                conMod.setData(conMod.index(i, conMod.fieldIndex('intake_col_m2')), intakeColM2)
                intakeInSeg = calc.value('intake_in_seg')
                intakeAccumulated = intakePrevCol + intakeColM1 + intakeColM2 + intakeInSeg
                conMod.setData(conMod.index(i, conMod.fieldIndex('intake_accumulated')), intakeAccumulated)
                recurFlowEnd = (avgFlowEnd * self.critVal('k2_hourly')) + intakeAccumulated
                conMod.setData(conMod.index(i, conMod.fieldIndex('recur_flow_end')), recurFlowEnd)
                maxFlowEnd = (avgFlowEnd * self.critVal('k1_daily') * self.critVal('k2_hourly')) + intakeAccumulated
                conMod.setData(conMod.index(i, conMod.fieldIndex('max_flow_end')), maxFlowEnd)
                prjFlowRateQmax = self.getDesignFlow(calc.value('collector_number'), maxFlowEnd)
                calMod.setData(calMod.index(i, calMod.fieldIndex('prj_flow_rate_qgmax')), prjFlowRateQmax)
                recurFlowStart = (avgFlowStart * self.critVal('k2_hourly')) + intakeAccumulated
                conMod.setData(conMod.index(i, conMod.fieldIndex('recur_flow_start')), recurFlowStart)
                maxFlowStart = (avgFlowStart * self.critVal('k1_daily') * self.critVal('k2_hourly')) + intakeAccumulated
                conMod.setData(conMod.index(i, conMod.fieldIndex('max_flow_start')), maxFlowStart)
                initialFlowRateQi = self.getDesignFlow(calc.value('collector_number'), maxFlowStart)
                calMod.setData(calMod.index(i, calMod.fieldIndex('initial_flow_rate_qi')), initialFlowRateQi)

                recDesFlowQfr = self.getDesignFlow(calc.value('collector_number'), recurFlowEnd)
                calMod.setData(calMod.index(i, calMod.fieldIndex('rec_des_flow_qfr')), recDesFlowQfr)
                initRecDesFlowQfr = self.getDesignFlow(calc.value('collector_number'), recurFlowStart)
                calMod.setData(calMod.index(i, calMod.fieldIndex('initial_rec_des_flow_qfr')), initRecDesFlowQfr)

                calMod.updateRowInTable(i, calMod.record(i))
                conMod.updateRowInTable(i, conMod.record(i))

    def getDesignFlow(self, colNo, flow):
        if (colNo == None or flow == 0):
            return 0
        flowMinQmin = self.critVal('flow_min_qmin')
        if (flow < flowMinQmin):
            return flowMinQmin
        return flow

    # $Parametros.$L$24 || Getting Maximum Flow l/s
    def getMaximumFlow(self):
        return round(self.parameterModel.getValueBy('qe_reference_max'), 10)

    # $Parametros.$L$38 or$ Parametros.$L$40 || Average Linear Contribution Rate (l/s.km) start boolean
    def avgLinearContributionRate(self, start):
        extensionSum = self.model.getExtensionSum()
        if extensionSum == 0:
            return 0
        population = self.parameterModel.getValueBy('beginning_population') if start == 1 else self.parameterModel.getValueBy('final_population')
        waterCosumption = self.critModel.getValueBy('water_consumption_pc') if start == 1 else self.critModel.getValueBy('water_consumption_pc_end')
        coefRetC = self.critModel.getValueBy('coefficient_return_c')
        return round((((population * waterCosumption * coefRetC) / 86400) / extensionSum) * 1000, 13)

    # $A1.$B$1
    def getContributionAux(self, extension):
        contributionSewage = self.parameterModel.getValueBy('contribution_sewage')
        return 0 if (contributionSewage == 0 or extension == 0 ) else 1

    # $A1.$M$1 || Condominial Lines and Others START (l/s)
    def getCondominialLinesStart(self, qeIp):
        qeIp = self.strToFloat(qeIp)
        return round(qeIp * self.getMaximumFlow() / self.critModel.getValueBy('k1_daily'), 6)

    # $A1.$H$1 END-Linear Contribution in Segment (l/s)
    def getEndLinearContInSeg(self, ext):
        if ext == 0:
            return 0
        else:
            return ((self.getContributionAux(ext) * self.paramVal('sewer_contribution_rate_end') * ext) / 1000)

    # $A1.$N$1 START-Linear Contribution in Segment (l/s)
    def getStartLinearContInSeg(self, ext):
        if ext == 0:
            return 0
        else:
            return ((self.getContributionAux(ext) * self.paramVal('sewer_contribution_rate_start') * ext) / 1000)

    #TODO check if is universal and ask what happen btw 200 and 250s
    def slopesMinAcceptedCalc(self, adoptedDiameter):
        if (adoptedDiameter <= 150):
            return self.critModel.getValueBy('diameter_up_150')
        if (adoptedDiameter <= 200):
            return  self.critModel.getValueBy('diameter_up_200')
        if (adoptedDiameter >= 250):
            return  self.critModel.getValueBy('from_diameter_250')

    def critVal(self, field):
        return self.critModel.getValueBy(field)

    def paramVal(self, field):
        return self.parameterModel.getValueBy(field)

    def getNaDiffNeeded(self, amtSegNa, inspDevCoverNa, naDeeper):
        if (amtSegNa == 0 or (inspDevCoverNa - naDeeper) < 0.00000001):
            return 0
        if (inspDevCoverNa - naDeeper) < self.critVal('min_step_ib_mh'):
            return self.round_up(self.critVal('min_step_ib_mh'), 2)
        return self.round_up(inspDevCoverNa - naDeeper, 2)

    @staticmethod
    def strToFloat(str):
        return float(str) if len(str) > 0 else 0

    def getFunc(self, function, ext, colNo, a, b, c, d):
        if ext == 0 or colNo == 0:
            return 0

        calMod = Calculation()

        map = {
            'laminaabs': calMod.laminaabs,
            'laminarel': calMod.laminarel,
            'tenstrat': calMod.tenstrat,
            'velocrit': calMod.velocrit,
            'velocid': calMod.velocid
        }

        selected_function = map.get(function)
        if selected_function is not None:
            return selected_function(a, b, c, d)
        else:
            return 0

    def waterLevelAdjustments(self, projectId, colSeg, recalculate=False, m1List=[], m2List=[], action = ''):
        calMod = Calculation()
        wlMod = WaterLevelAdj()

        splitCol = colSeg.split('-')
        wlMod.setFilter('calculation_id in (select id from calculations where project_id = {}) and col_seg like "{}-%" ORDER BY initial_segment DESC'.format(projectId, splitCol[0]))
        calMod.setFilter('project_id = {} and col_seg like "{}-%" ORDER BY initial_segment DESC'.format(projectId, splitCol[0]))

        wlMod.select()
        calMod.select()

        while calMod.canFetchMore():
            calMod.fetchMore()
        while wlMod.canFetchMore():
            wlMod.fetchMore()

        for i in range(wlMod.rowCount()):
            wlMod.select()
            calMod.select()
            calc = calMod.record(i)
            wl = wlMod.record(i)

            m1ColDepth = m2ColDepth = m1ColCov = m2ColCov = m1ColUp = m2ColUp = m1ColNa = m2ColNa = 0
            if recalculate:
                if wl.value('m1_col_id') in m1List and len(wl.value('m1_col_id')) > 0:
                    self.waterLevelAdjustments(projectId, wl.value('m1_col_id'), True, m1List, m2List)
                    m1ColDepth = wlMod.getValueBy('down_end_h',"w.col_seg ='{}'".format(wl.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_depth')), m1ColDepth)
                    m1ColCov = wlMod.getValueBy('down_end_cov',"w.col_seg ='{}'".format(wl.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_cov')), m1ColCov)
                    m1ColUp = calMod.getValueBy('el_col_down',"col_seg = '{}'".format(calc.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_up')), m1ColUp)
                    m1ColNa = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_na')), m1ColNa)
                else:
                    m1ColDepth = wlMod.getValueBy('down_end_h',"w.col_seg ='{}'".format(wl.value('m1_col_id')))
                    m1ColCov = wlMod.getValueBy('down_end_cov',"w.col_seg ='{}'".format(wl.value('m1_col_id')))
                    m1ColUp = calMod.getValueBy('el_col_down',"col_seg = '{}'".format(calc.value('m1_col_id')))
                    m1ColNa = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('m1_col_id')))
            else:
                if len(wl.value('m1_col_id')) > 0:
                    self.waterLevelAdjustments(projectId, wl.value('m1_col_id'))
                    m1ColDepth = wlMod.getValueBy('down_end_h',"w.col_seg ='{}'".format(wl.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_depth')), m1ColDepth)
                    m1ColCov = wlMod.getValueBy('down_end_cov',"w.col_seg ='{}'".format(wl.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_cov')), m1ColCov)
                    m1ColUp = calMod.getValueBy('el_col_down',"col_seg = '{}'".format(calc.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_up')), m1ColUp)
                    m1ColNa = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('m1_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m1_col_na')), m1ColNa)

            if recalculate:
                if wl.value('m2_col_id') in m2List and len(wl.value('m2_col_id')) > 0:
                    self.waterLevelAdjustments(projectId, wl.value('m2_col_id'), True, m1List, m2List)
                    m2ColDepth = wlMod.getValueBy('down_end_h',"w.col_seg ='{}'".format(wl.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_depth')), m2ColDepth)
                    m2ColCov = wlMod.getValueBy('down_end_cov',"w.col_seg ='{}'".format(wl.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_cov')), m2ColCov)
                    m2ColUp = calMod.getValueBy('el_col_down',"col_seg = '{}'".format(calc.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_up')), m2ColUp)
                    m2ColNa = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_na')), m2ColNa)
                else:
                    m2ColDepth = wlMod.getValueBy('down_end_h',"w.col_seg ='{}'".format(wl.value('m2_col_id')))
                    m2ColCov = wlMod.getValueBy('down_end_cov',"w.col_seg ='{}'".format(wl.value('m2_col_id')))
                    m2ColUp = calMod.getValueBy('el_col_down',"col_seg = '{}'".format(calc.value('m2_col_id')))
                    m2ColNa = wlMod.getValueBy('down_side_seg',"col_seg = '{}'".format(calc.value('m2_col_id')))
            else:
                if len(wl.value('m2_col_id')) > 0:
                    self.waterLevelAdjustments(projectId, wl.value('m2_col_id'))
                    m2ColDepth = wlMod.getValueBy('down_end_h',"w.col_seg ='{}'".format(wl.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_depth')), m2ColDepth)
                    m2ColCov = wlMod.getValueBy('down_end_cov',"w.col_seg ='{}'".format(wl.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_cov')), m2ColCov)
                    m2ColUp = calMod.getValueBy('el_col_down',"col_seg = '{}'".format(calc.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_up')), m2ColUp)
                    m2ColNa = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('m2_col_id')))
                    wlMod.setData(wlMod.index(i, wlMod.fieldIndex('m2_col_na')), m2ColNa)

            extension = calc.value('extension')
            prjFlowRateQGMax = calc.value('prj_flow_rate_qgmax')
            colNo = calc.value('collector_number')
            cManning = calc.value('c_manning')
            initialFlowRateQi = calc.value('initial_flow_rate_qi')
            initialRecDesFlowQfr = calc.value('initial_rec_des_flow_qfr')

            prevDepthDown = calMod.getValueBy('depth_down',"col_seg = '{}'".format(calc.value('previous_col_seg_id')))
            amtSegDepth = prevDepthDown if (calc.value('initial_segment') != 1 and extension > 0) else 0
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('amt_seg_depth')), amtSegDepth)
            greaterDepth = max(m1ColDepth, m2ColDepth, amtSegDepth)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('greater_depth')), greaterDepth)
            depthUp = self.calcDepthUp(calc, wl, greaterDepth)
            calMod.setData(calMod.index(i, calMod.fieldIndex('depth_up')), depthUp)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('insp_dev_h_out')), depthUp)
            if recalculate == False and action == 'adjustNA':
                wlMod.setData(wlMod.index(i, wlMod.fieldIndex('imp_depth_up')), None)
                calMod.setData(calMod.index(i, calMod.fieldIndex('aux_depth_adjustment')), None)
            adoptedDiameter = calc.value('adopted_diameter')
            coveringUp = depthUp - adoptedDiameter / 1000
            calMod.setData(calMod.index(i, calMod.fieldIndex('covering_up')), coveringUp)
            elColUp = (calc.value('el_terr_up') - depthUp) if (extension != 0 or colNo != 0) else 0
            calMod.setData(calMod.index(i, calMod.fieldIndex('el_col_up')), elColUp)

            depthDown = self.calcDepthDown(calc, wl, elColUp)
            coveringDown = round(depthDown, 8) - adoptedDiameter/1000
            calMod.setData(calMod.index(i, calMod.fieldIndex('covering_down')), coveringDown)
            calMod.setData(calMod.index(i, calMod.fieldIndex('depth_down')), round(depthDown, 8))

            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('down_end_h')), round(depthDown,6))

            elColDown = (calc.value('el_terr_down') - depthDown) if (extension != 0 or colNo != 0) else 0
            calMod.setData(calMod.index(i, calMod.fieldIndex('el_col_down')), round(elColDown, 8))
            elTopGenUp =  (calc.value('el_terr_up') - coveringUp) if (extension != 0 or colNo != 0) else 0
            calMod.setData(calMod.index(i, calMod.fieldIndex('el_top_gen_up')), elTopGenUp)
            elTopGenDown =  (calc.value('el_terr_down') - coveringDown) if (extension != 0 or colNo != 0) else 0
            calMod.setData(calMod.index(i, calMod.fieldIndex('el_top_gen_down')), elTopGenDown)
            slopesAdoptedCol = (elTopGenUp - elTopGenDown) / extension if (extension != 0 or colNo != 0) else 0
            calMod.setData(calMod.index(i, calMod.fieldIndex('slopes_adopted_col')), round(slopesAdoptedCol, 6))
            dn1mm = calMod.dn1mm(max(prjFlowRateQGMax, initialFlowRateQi), round(slopesAdoptedCol, 6), cManning, self.critVal('max_water_level'))
            diam1 = self.critVal('min_diameter') if dn1mm < self.critVal('min_diameter') else self.pipe.getMinDiameter(dn1mm)
            calMod.setData(calMod.index(i, calMod.fieldIndex('suggested_diameter')), diam1)
            waterLevelY = self.getFunc('laminaabs', extension, colNo, prjFlowRateQGMax, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('water_level_y')), round(waterLevelY, 4))
            waterLevelPipeEnd = self.getFunc('laminarel', extension, colNo, prjFlowRateQGMax,adoptedDiameter, slopesAdoptedCol, cManning )
            calMod.setData(calMod.index(i, calMod.fieldIndex('water_level_pipe_end')), round(waterLevelPipeEnd, 4)*100)

            tractiveForce = self.getFunc('tenstrat', extension, colNo, calc.value('rec_des_flow_qfr'),adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('tractive_force')), round(tractiveForce, 4))
            criticalVelocity = self.getFunc('velocrit', extension, colNo, prjFlowRateQGMax, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('critical_velocity')), round(criticalVelocity, 4))
            velocity = self.getFunc('velocid', extension, colNo, prjFlowRateQGMax, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('velocity')), round(velocity, 2))

            waterLevelYStart = self.getFunc('laminaabs', extension, colNo, initialFlowRateQi, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('water_level_y_start')), round(waterLevelYStart, 4))
            waterLevelPipeStart = self.getFunc('laminarel', extension, colNo, initialFlowRateQi, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('water_level_pipe_start')), round(waterLevelPipeStart, 4) * 100)
            tractiveForceStart = self.getFunc('tenstrat', extension, colNo, initialRecDesFlowQfr, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('tractive_force_start')), round(tractiveForceStart, 4))
            criticalVelocityStart = self.getFunc('velocrit', extension, colNo, initialFlowRateQi, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('initial_critical_velocity')), round(criticalVelocityStart, 4))
            velocityStart = self.getFunc('velocid', extension, colNo, initialFlowRateQi, adoptedDiameter, slopesAdoptedCol, cManning)
            calMod.setData(calMod.index(i, calMod.fieldIndex('initial_velocity')), round(velocityStart, 4))

            prevCoveringDown = calMod.getValueBy('covering_down',"col_seg = '{}'".format(calc.value('previous_col_seg_id')))
            amtSegCov = prevCoveringDown if (calc.value('initial_segment') != 1 and extension > 0) else 0
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('amt_seg_cov')), amtSegCov)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('insp_dev_cov_out')), round(coveringUp, 6))
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('down_end_cov')), round(coveringDown, 6))
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('greater_cov')), max(m1ColCov, m2ColCov, amtSegCov))
            forceDepthUp = 0 if calc.value('force_depth_up')==None else calc.value('force_depth_up')
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('force_depth')), forceDepthUp)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('aux_ini')), calc.value('initial_segment'))

            elColDownPrevious = calMod.getValueBy('el_col_down',"col_seg = '{}'".format(calc.value('previous_col_seg_id')))
            amtSegUp = 0 if elColDownPrevious == None else elColDownPrevious
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('amt_seg_up')), amtSegUp)
            lowestUp = 0 if amtSegUp == 0 and m1ColUp == 0 and m2ColUp == 0 else min(i for i in [amtSegUp, m1ColUp, m2ColUp] if i != 0)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('lowest_up')), lowestUp)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('insp_dev_cov_up')), elColUp)
            upDiffNeeded = 0 if amtSegUp == 0 else round(elColUp - lowestUp + self.critModel.getValueBy('bottom_ib_mh'), 6) if elColUp - lowestUp > (self.critModel.getValueBy('bottom_ib_mh') * (-1)) else 0
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('up_diff_needed')), upDiffNeeded)
            upstreamSideSeg = 0 if calc.value('extension') == 0  else elColUp + max(waterLevelY, waterLevelYStart)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('up_side_seg')), round(upstreamSideSeg, 6))
            downstreamSideSeg = 0 if calc.value('extension') == 0 else elColDown + max(waterLevelY, waterLevelYStart) #$A3.I15
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('down_side_seg')), round(downstreamSideSeg, 6))
            downSidePrev = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('previous_col_seg_id')))
            amtSegNa = 0 if downSidePrev == None else 0 if wlMod.isError(downSidePrev) else downSidePrev
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('amt_seg_na')), amtSegNa)
            m1ColNa = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('m1_col_id')))
            m2ColNa = wlMod.getValueBy('down_side_seg',"w.col_seg = '{}'".format(calc.value('m2_col_id')))
            naDeeper = 0 if amtSegNa == 0 and m1ColNa == 0 and m2ColNa == 0 else min(i for i in [amtSegNa, m1ColNa, m2ColNa] if i != 0)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('na_deeper')), naDeeper)
            upstreamSideSeg = 0 if wlMod.isError(upstreamSideSeg) == True else round(upstreamSideSeg, 6)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('insp_dev_cov_na')), upstreamSideSeg)
            naDiffNeeded = self.getNaDiffNeeded(amtSegNa, upstreamSideSeg, naDeeper)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('na_diff_needed')), naDiffNeeded)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('calc_depth_up')), round(depthUp + naDiffNeeded, 2))
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('dn_est_need')), diam1)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('dn_ad')), adoptedDiameter)
            dnAdPrevCol = wlMod.getValueBy('dn_ad',"w.col_seg = '{}'".format(calc.value('previous_col_seg_id')))
            dnAdM1Col = wlMod.getValueBy('dn_ad',"w.col_seg = '{}'".format(calc.value('m1_col_id')))
            dnAdM2Col = wlMod.getValueBy('dn_ad',"w.col_seg = '{}'".format(calc.value('m2_col_id')))
            dnCalcMax = diam1 if calc.value('initial_segment') == 1 else max(diam1, dnAdPrevCol, dnAdM1Col, dnAdM2Col)
            wlMod.setData(wlMod.index(i, wlMod.fieldIndex('dn_calc_max')), dnCalcMax)
            inspectionTypeUp = "TL" if (calc.value('initial_segment') == 1 and self.critVal('simplified_tl_seg') == 1) else self.inspectionoDevice.getInspectionTypeUp(depthUp, adoptedDiameter)
            calMod.setData(calMod.index(i, calMod.fieldIndex('inspection_type_up')), inspectionTypeUp)
            calMod.updateRowInTable(i, calMod.record(i))
            wlMod.updateRowInTable(i, wlMod.record(i))

    def calcAfter(self, projectId):
        msg = translate("Calculation", "Updating water level adjustments")
        self.info.emit(msg)
        try:
            calMod = Calculation()
            wlMod = WaterLevelAdj()
            
            calMod.setFilter('project_id = {}'.format(projectId))  
            wlMod.setFilter("calculation_id in (select id from calculations where project_id = {})".format(projectId))

            calMod.select()
            wlMod.select()

            while wlMod.canFetchMore():
                wlMod.fetchMore()
            while calMod.canFetchMore():
                calMod.fetchMore()
            
            for i in range(calMod.rowCount()):
                calMod.select()
                wlMod.select()
                calc = calMod.record(i)
                wl = wlMod.record(i)
                
                inspectionTypeUp = calMod.getValueBy('inspection_type_up',"col_seg ='{}'".format(calc.value('downstream_seg_id')))
                insTypeDown = inspectionTypeUp if inspectionTypeUp != 0 and inspectionTypeUp != None else calc.value('inspection_type_up')
                calMod.setData(calMod.index(i, calMod.fieldIndex('inspection_type_down')), insTypeDown)
                impDepthUp = wlMod.getValueBy('greater_depth',"previous_col_seg_end ='{}'".format(calc.value('col_seg')))
                greaterDepthPrev = wlMod.getValueBy('greater_depth',"w.previous_col_seg_end ='{}'".format(calc.value('col_seg')))
                greaterDepthPrev = 0 if greaterDepthPrev == None else greaterDepthPrev
                greaterDepthM1 = wlMod.getValueBy('greater_depth',"w.m1_col_id ='{}'".format(calc.value('col_seg')))
                greaterDepthM1 = 0 if greaterDepthM1 == None else greaterDepthM1
                greaterDepthM2 = wlMod.getValueBy('greater_depth',"w.m2_col_id ='{}'".format(calc.value('col_seg')))
                greaterDepthM2 = 0 if greaterDepthM2 == None else greaterDepthM2
                greaterDepthAux = greaterDepthPrev + greaterDepthM1 + greaterDepthM2
                auxImpDepthUp = None if greaterDepthAux == 0 else greaterDepthAux
                wlMod.setData(wlMod.index(i, wlMod.fieldIndex('aux_imp_depth_up')), auxImpDepthUp)
                downEnd = wlMod.getValueBy('down_end_h',"w.col_seg ='{}'".format(calc.value('col_seg')))
                auxHImpDepth = None if auxImpDepthUp == None else  None if (auxImpDepthUp - downEnd) == 0 else round(auxImpDepthUp, 2)
                wlMod.setData(wlMod.index(i, wlMod.fieldIndex('aux_h_imp_depth')), auxHImpDepth)
                calMod.updateRowInTable(i, calMod.record(i))
                wlMod.updateRowInTable(i, wlMod.record(i))
            return True
        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        return False

    # $RedBasica.$V$15
    def calcDepthUp(self, calc, wl, greaterDepth):
        if (calc.value('initial_segment') == 1):
            if (calc.value('force_depth_up') == None):
                if (calc.value('col_pipe_position') == 1):
                    return self.critModel.getValueBy('cover_min_sidewalks_gs') + calc.value('adopted_diameter') / 1000
                else:
                    return self.critModel.getValueBy('cover_min_street') + calc.value('adopted_diameter') / 1000
            else:
                return calc.value('force_depth_up')
        else:
            bottomIbMh = self.critModel.getValueBy('bottom_ib_mh')
            if (calc.value('force_depth_up') == None):
                x = (self.critModel.getValueBy('cover_min_sidewalks_gs') + bottomIbMh + (calc.value('adopted_diameter')/1000)) if calc.value('col_pipe_position') == 1 else (self.critModel.getValueBy('cover_min_street') + bottomIbMh + (calc.value('adopted_diameter')/1000))
                return max((greaterDepth + bottomIbMh), calc.value('aux_depth_adjustment'), x)
            else:
                auxDepthAdj = 0 if calc.value('aux_depth_adjustment') == None else calc.value('aux_depth_adjustment')
                return max((greaterDepth + bottomIbMh), calc.value('force_depth_up'), auxDepthAdj)
    
    # $RedBasica.$W$15 depth_down
    def calcDepthDown(self, calc, wl, elColUp):
        extension = calc.value('extension')
        if extension == 0:
            return 0
        else:
            forceDepthDown = calc.value('force_depth_down')
            y = 0 if forceDepthDown == None else forceDepthDown
            elTerrDown = calc.value('el_terr_down')
            slopesMinAccepted = calc.value('slopes_min_accepted_col')
            a = elTerrDown - (elColUp - slopesMinAccepted * extension)
            if  y >= 0:
                if (forceDepthDown == None):
                    coverMinSidewalks = self.critModel.getValueBy('cover_min_sidewalks_gs')
                    coverMinStreet = self.critModel.getValueBy('cover_min_street')
                    adoptedDiameter = calc.value('adopted_diameter')
                    b = coverMinSidewalks + adoptedDiameter / 1000 if calc.value('col_pipe_position') == 1 else coverMinStreet + adoptedDiameter / 1000
                    return max(a,b)
                else:
                    return max(a, forceDepthDown)
            else:
                if (forceDepthDown == None):
                    return a
                else:
                    return max(a, forceDepthDown)
    
    def calculateDN(self, projectId, growing=False):
        success = False
        try:
            msg = translate("Calculation", "Calculating DN")
            self.info.emit(msg)
            self.progress.emit(10)
            print(msg)
            start_time = time.time()
            calMod = Calculation()
            calMod.setFilter('project_id = {}'.format(projectId))
            calMod.select()
            if growing == True:
                wlMod = WaterLevelAdj()
                wlMod.setFilter("calculation_id in (select id from calculations where project_id = {})".format(projectId))
                wlMod.select()
                while wlMod.canFetchMore():
                    wlMod.fetchMore()
            listRows = {}
            m1ColList = m2ColList = []
            
            self.progress.emit(10)

            while calMod.canFetchMore():
                calMod.fetchMore()

            for i in range(calMod.rowCount()):
                if growing == True:
                    wl = wlMod.record(i)
                calc = calMod.record(i)
                if growing == False and calc.value('adopted_diameter') != calc.value('suggested_diameter'):
                    calMod.setData(calMod.index(i, calMod.fieldIndex('adopted_diameter')), calc.value('suggested_diameter'))
                    if calMod.updateRowInTable(i, calMod.record(i)):
                        listRows[calc.value('collector_number')] = calc.value('col_seg')
                        m1 = calMod.getValueBy('m1_col_id','m1_col_id= "{}"'.format(calc.value('col_seg')))
                        if m1 != None:
                            m1ColList.append(m1)
                        m2 = calMod.getValueBy('m2_col_id','m2_col_id= "{}"'.format(calc.value('col_seg')))
                        if m2 != None:
                            m2ColList.append(m2)
                    calMod.select()

                if growing == True and calc.value('adopted_diameter') != wl.value('dn_calc_max'):
                    calMod.setData(calMod.index(i, calMod.fieldIndex('adopted_diameter')), wl.value('dn_calc_max'))
                    if calMod.updateRowInTable(i, calMod.record(i)):
                        listRows[calc.value('collector_number')] = calc.value('col_seg')
                        m1 = calMod.getValueBy('m1_col_id','m1_col_id= "{}"'.format(calc.value('col_seg')))
                        if m1 != None:
                            m1ColList.append(m1)
                        m2 = calMod.getValueBy('m2_col_id','m2_col_id= "{}"'.format(calc.value('col_seg')))
                        if m2 != None:
                            m2ColList.append(m2)
                    wlMod.select()
                    calMod.select()
            
            self.progress.emit(60)

            for key, colSeg in listRows.items():
                self.recursiveContributions(projectId, colSeg, True, m1ColList, m2ColList)
                self.waterLevelAdjustments(projectId, colSeg, True, m1ColList, m2ColList)
            
            self.progress.emit(90)

            self.calcAfter(projectId)
            
            success = True
            self.progress.emit(100)
            self.info.emit(translate("Calculation", "Done."))
            print("Total time execution to Calculate DN:--- %s seconds ---" % (time.time() - start_time))
        except Exception as e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(success)
    
    def calculateGrowDN(self, projectId):
        success = False
        try:
            msg = translate("Calculation", "Calculating Growing DN")
            self.info.emit(msg)
            self.progress.emit(10)
            print(msg)
            start_time = time.time()
            self.growDN(projectId)
            calMod = Calculation()
            listRows, m1ColList, m2ColList = calMod.getCompleteStructure(projectId)
            for key, colSegList in listRows.items():
                self.recursiveContributions(projectId, colSegList[0], True, m1ColList, m2ColList)
                self.waterLevelAdjustments(projectId, colSegList[0], True, m1ColList, m2ColList)
            self.calcAfter(projectId)
            self.progress.emit(90)
            success = True
            self.progress.emit(100)
            self.info.emit(translate("Calculation", "Done."))
            print("Total time execution to Calculate DN:--- %s seconds ---" % (time.time() - start_time))
        except Exception as e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(success)

    def growDN(self, projectId, iterationNo=0):
        calMod = Calculation()
        calMod.setFilter('project_id = {}'.format(projectId))
        calMod.select()
        wlMod = WaterLevelAdj()
        wlMod.setFilter("calculation_id in (select id from calculations where project_id = {})".format(projectId))
        wlMod.select()
        while wlMod.canFetchMore():
            wlMod.fetchMore()

        listRows = {}
        m1ColList = m2ColList = []

        self.progress.emit(10)

        while calMod.canFetchMore():
            calMod.fetchMore()

        for i in range(calMod.rowCount()):
            calc = calMod.record(i)
            prevCalc = calMod.record(i-1)
            wl = wlMod.record(i)
            adoptedDiameter = calc.value('adopted_diameter')
            prevAdoptedDiameter = prevCalc.value('adopted_diameter')
            initialSegment = calc.value('initial_segment')
            dnCalcMax = wl.value('dn_calc_max')
            if initialSegment == 1 or dnCalcMax > prevAdoptedDiameter:
                calMod.setData(calMod.index(i, calMod.fieldIndex('adopted_diameter')), dnCalcMax)
            else:
                calMod.setData(calMod.index(i, calMod.fieldIndex('adopted_diameter')), prevAdoptedDiameter)
            if  adoptedDiameter != dnCalcMax:
                if calMod.updateRowInTable(i, calMod.record(i)):
                    listRows[calc.value('collector_number')] = calc.value('col_seg')
                    m1 = calMod.getValueBy('m1_col_id','m1_col_id = "{}"'.format(calc.value('col_seg')))
                    if m1 != None:
                        m1ColList.append(m1)
                    m2 = calMod.getValueBy('m2_col_id','m2_col_id = "{}"'.format(calc.value('col_seg')))
                    if m2 != None:
                        m2ColList.append(m2)
            calMod.select()
        self.progress.emit(60)
        for key, colSeg in listRows.items():
            self.recursiveContributions(projectId, colSeg, True, m1ColList, m2ColList)
            self.waterLevelAdjustments(projectId, colSeg, True, m1ColList, m2ColList)
        maxWaterLvl = self.critModel.getValueBy('max_water_level')
        compare = calMod.getValueBy('col_seg',
                                    'water_level_pipe_end > {} OR water_level_pipe_start > {}'
                                    .format(maxWaterLvl, maxWaterLvl))

        self.calcAfter(projectId)

        if (iterationNo <= 15):
            iterationNo = iterationNo + 1
            if (compare):
                return self.growDN(projectId, iterationNo)
            else:
                """"""
                for i in range(calMod.rowCount()):
                    calc = calMod.record(i)
                    adoptedDiam = calc.value('adopted_diameter')
                    prevColSeg = calc.value('previous_col_seg_id')
                    m1 = calc.value('m1_col_id')
                    m2 = calc.value('m2_col_id')
                    check = self.checkNoLargerUpDiam(adoptedDiam, prevColSeg, m1, m2)
                    if check:
                        self.growDN(projectId, iterationNo)

    def checkNoLargerUpDiam(self, currentVal, prevColSeg, m1, m2):
        compare = self.model.getValueBy('col_seg',
                                        '(col_seg = "{}" OR col_seg = "{}" OR col_seg = "{}")\
                                        AND adopted_diameter > {}'
                                        .format(prevColSeg, m1, m2, currentVal))
        if compare != 0:
            return True
        return False



    # TODO filter by projectId
    def updateVal(self, projectId, colSeg):
        success = False
        try:
            msg = translate("Calculation", "Updating col-seg {}".format(colSeg))
            print(msg)
            self.info.emit(msg)
            self.progress.emit(10)
            start_time = time.time()
            calMod = Calculation()

            m1ColList = m2ColList = []
            colSeg, m1ColList, m2ColList = self.getFirstSegRelated(colSeg, [], [])

            self.progress.emit(30)
            self.info.emit(translate("Calculation", "Updating contributions"))
            self.recursiveContributions(projectId, colSeg, True, m1ColList, m2ColList) 

            self.progress.emit(60)
            self.info.emit(translate("Calculation", "Updating water level Adjustments"))
            self.waterLevelAdjustments(projectId, colSeg, True, m1ColList, m2ColList)

            self.progress.emit(90)
            self.info.emit(translate("Calculation", "Running calcAfter"))
            self.calcAfter(projectId)

            self.progress.emit(100)
            success = True
            self.info.emit(translate("Calculation", "Done."))

            print("Total time execution to Update Value:--- %s seconds ---" % (time.time() - start_time))
        except Exception as e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(success)
    
    def getFirstSegRelated(self, colSeg, m1=[], m2=[]):
        #Check if the modified cell is m1 in another segment. The function will finish when don't detect related segment 
        calMod = Calculation()

        collectorNumber = calMod.getValueBy('collector_number','col_seg= "{}" GROUP BY collector_number'.format(colSeg))
        m1Related = calMod.getValueBy('col_seg','m1_col_id LIKE "{}-%"'.format(collectorNumber))
        m1Col = calMod.getValueBy('m1_col_id','m1_col_id LIKE "{}-%"'.format(collectorNumber))
        m2Related = calMod.getValueBy('col_seg','m2_col_id LIKE "{}-%"'.format(collectorNumber))
        m2Col = calMod.getValueBy('m2_col_id','m2_col_id LIKE "{}-%"'.format(collectorNumber))

        if m1Related == 0 and m2Related == 0:
            return colSeg, m1, m2
        if m1Related != 0:
            m1.append(m1Col)
            return self.getFirstSegRelated(m1Related, m1, m2)
        if m2Related != 0:
            m2.append(m2Col)
            return self.getFirstSegRelated(m2Related, m1, m2)

    def updateValues(self, projectId, colSegs):
        success = False
        try:
            start_time = time.time()
            for colSeg in colSegs:
                msg = translate("Calculation", "Updating col-seg {}".format(colSeg))
                print(msg)
                self.info.emit(msg)
                self.progress.emit(10)
                calMod = Calculation()
                m1ColList = m2ColList = []
                colSeg, m1ColList, m2ColList = self.getFirstSegRelated(colSeg,[],[])

                self.progress.emit(30)
                self.info.emit(translate("Calculation", "Updating contributions"))
                self.recursiveContributions(projectId, colSeg, True, m1ColList, m2ColList)

                self.progress.emit(60)
                self.info.emit(translate("Calculation", "Updating water level Adjustments"))
                self.waterLevelAdjustments(projectId, colSeg, True, m1ColList, m2ColList)

                self.progress.emit(90)
                self.info.emit(translate("Calculation", "Running calcAfter"))
                self.calcAfter(projectId)

                self.progress.emit(100)
                success = True
                self.info.emit(translate("Calculation", "Done."))

            print("Total time execution to Update Value:--- %s seconds ---" % (time.time() - start_time))
        except Exception as e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(success)

    def calculateMinExc(self, projectId):
        success = False
        try:
            msg = translate("Calculation", "Calculating Min Excavation")
            self.info.emit(msg)
            self.progress.emit(10)
            print(msg)
            start_time = time.time()
            calMod = Calculation()
            calMod.setFilter('project_id = {}'.format(projectId))
            calMod.select()
            while calMod.canFetchMore():
                calMod.fetchMore()
            listRows = {}
            m1ColList = m2ColList = []
            self.progress.emit(10)
            for i in range(calMod.rowCount()):
                calc = calMod.record(i)
                if  calc.value('force_depth_down') != None:
                    calMod.setData(calMod.index(i, calMod.fieldIndex('force_depth_down')), None)
                    calMod.updateRowInTable(i, calMod.record(i))
                    listRows[calc.value('collector_number')] = calc.value('col_seg')
                    m1 = calMod.getValueBy('m1_col_id','m1_col_id= "{}"'.format(calc.value('col_seg')))
                    if m1 != None:
                        m1ColList.append(m1)
                    m2 = calMod.getValueBy('m2_col_id','m2_col_id= "{}"'.format(calc.value('col_seg')))
                    if m2 != None:
                        m2ColList.append(m2)
                calMod.select()
            self.progress.emit(60)
            for key, colSeg in listRows.items():
                self.recursiveContributions(projectId, colSeg, True, m1ColList, m2ColList)
                self.waterLevelAdjustments(projectId, colSeg, True, m1ColList, m2ColList)
            self.progress.emit(90)
            self.calcAfter(projectId)
            success = True
            self.progress.emit(100)
            self.info.emit(translate("Calculation", "Done."))
            print("Total time execution to Calculate Minimal Excavation:--- %s seconds ---" % (time.time() - start_time))
        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(success)

    def calculateMinSlope(self, projectId):
        success = False
        try:
            msg = translate("Calculation", "Calculating Min Slope")
            self.info.emit(msg)
            self.progress.emit(10)
            print(msg)
            start_time = time.time()
            calMod = Calculation()
            listRows = {}
            m1ColList = m2ColList = []
            self.progress.emit(10)
            calMod.updateForceDepthDown(projectId)
            listRows, m1ColList, m2ColList = calMod.getCompleteStructure(projectId)
            self.progress.emit(60)
            for key, colSegList in listRows.items():
                self.recursiveContributions(projectId, colSegList[0], True, m1ColList, m2ColList)
                self.waterLevelAdjustments(projectId, colSegList[0], True, m1ColList, m2ColList)
            self.progress.emit(90)
            self.calcAfter(projectId)
            success = True
            self.progress.emit(100)
            self.info.emit(translate("Calculation", "Done."))
            print("Total time execution to Calculate Minimal Slope:--- %s seconds ---" % (time.time() - start_time))
        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(success)

    def adjustNA(self, projectId, iterationMax):
        success = False
        try:
            self.resetWaterLevel(projectId, False)
            self.message.emit('')
            msg = translate("Calculation", "Adjusting NA")
            self.info.emit(msg)
            self.progress.emit(10)
            print(msg)
            start_time = time.time()
            calMod = Calculation()
            calMod.setFilter('project_id = {}'.format(projectId))
            calMod.select()
            wlMod = WaterLevelAdj()
            wlMod.setFilter("calculation_id in (select id from calculations where project_id = {})".format(projectId))
            wlMod.select()
            self.progress.emit(10)
            progress = 10
            check_time = time.time()
            count = 0
            while count != iterationMax and wlMod.getMaxNaDiffNeeded() != 0:
                listRows = {}
                m1ColList = m2ColList = []
                wlMod.updateImpDepthUp(projectId)
                calMod.updateAuxDepthAdj(projectId)
                listRows, m1ColList, m2ColList = calMod.getCompleteStructure(projectId)
                for key, colSegList in listRows.items():
                    self.recursiveContributions(projectId, colSegList[0], True, m1ColList, m2ColList)
                    self.waterLevelAdjustments(projectId, colSegList[0], True, m1ColList, m2ColList, 'adjustNA')
                progress = progress + 10 if progress <= 90 else 90
                self.calcAfter(projectId)
                count += 1
                self.progress.emit(progress)
            success = True
            self.progress.emit(100)
            self.info.emit(translate("Calculation", "Done."))
            print("Total time execution to Adjust NA:--- %s seconds ---" % (time.time() - start_time))
        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        if (wlMod.getMaxNaDiffNeeded() != 0):
                self.message.emit(translate("Calculation", "Warning: There are still sections where adjustments are needed. Repeat the operation increasing the number of maximum iterations."))
                return self.finished.emit({'success':success, 'message':True})
        return self.finished.emit({'success':success, 'message':False})
    
    def round_up(self, n, decimals=0):
        multiplier = 10 ** decimals 
        return math.ceil(n * multiplier) / multiplier

    def resetWaterLevel(self, projectId, finish = True):
        success = False
        try:
            msg = translate("Calculation", "Reseting Water Level")
            self.info.emit(msg)
            self.progress.emit(10)
            print(msg)
            start_time = time.time()
            calMod = Calculation()
            wlMod = WaterLevelAdj()
            calMod.clearAuxDepthAdj(projectId)
            wlMod.clearImpDepthUp(projectId)
            self.progress.emit(40)
            listRows, m1ColList, m2ColList = calMod.getCompleteStructure(projectId)
            for key, colSegList in listRows.items():
                    self.recursiveContributions(projectId, colSegList[0], True, m1ColList, m2ColList)
                    self.waterLevelAdjustments(projectId, colSegList[0], True, m1ColList, m2ColList)
            self.calcAfter(projectId)
            success = True
            self.progress.emit(100)
            self.info.emit(translate("Calculation", "Done."))
            print("Total time execution to Reset Water Level:--- %s seconds ---" % (time.time() - start_time))

        except Exception as e:
            self.error.emit(e, traceback.format_exc())

        if (finish == True):
            self.finished.emit(success)
    
    def clearDiameters(self, projectId):
        success = False
        try:
            msg = translate("Calculation", "Resetting Diameters")
            self.info.emit(msg)
            self.progress.emit(10)
            print(msg)
            start_time = time.time()
            calMod = Calculation()
            wlMod = WaterLevelAdj()
            calMod.clearDiameter(projectId)
            self.progress.emit(40)
            listRows, m1ColList, m2ColList = calMod.getCompleteStructure(projectId)
            for key, colSegList in listRows.items():
                    self.recursiveContributions(projectId, colSegList[0], True, m1ColList, m2ColList)
                    self.waterLevelAdjustments(projectId, colSegList[0], True, m1ColList, m2ColList)
            self.calcAfter(projectId)
            success = True
            self.progress.emit(100)
            self.info.emit(translate("Calculation", "Done."))
            print("Total time execution to Reset Diameters:--- %s seconds ---" % (time.time() - start_time))

        except Exception as e:
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(success)