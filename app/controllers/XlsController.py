import os
from PyQt5.QtCore import QObject, QLocale
from ..models.Project import Project
from ..models.Parameter import Parameter
from ..models.Criteria import Criteria
from ..models.Calculation import Calculation
from ..lib.xlrd import open_workbook
from ..lib.xlwt import easyxf
from ..lib.xlutils.copy import copy

class XlsController(QObject):
        
    def __init__(self):
        super().__init__()    
        locale = QLocale().name()
        lang = locale[0:2] if locale[0:2] in ('en','es','pt') else 'en'     
        self.template_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'xls', 'export_tpl_{}.xls'.format(lang.upper()))                

        self.centerStyle = easyxf("pattern: pattern solid, fore_color white; font: color black; align: vert centre, horiz center")
        self.projectStyle = easyxf("font: bold on; borders: top_color white, bottom_color white, right_color white, left_color white,\
                                    left thin, right thin, top thin, bottom thin;\
                                    pattern: pattern solid, fore_color white; font: color black; align: vert centre, horiz left ")   
        self.borderStyle = easyxf("borders: top_color black, bottom_color black, right_color black, left_color black,\
                                    left thin, right thin, top thin, bottom thin;\
                                    pattern: pattern solid, fore_color white; font: color black, height 160; align: vert centre, horiz center")
        self.negativeStyle = easyxf("borders: top_color black, bottom_color black, right_color black, left_color black,\
                                    left thin, right thin, top thin, bottom thin;\
                                    pattern: pattern solid, fore_color white; font: color red, height 160; align: vert centre, horiz center")       
        self.qeMaxStyle = easyxf("borders: right_color black,right thin;\
                                pattern: pattern solid, fore_color white; font: color black; align: vert centre, horiz center")  

        self.projectCol = 2
        self.paramCol1 = 9
        self.paramCol2 = 13
        self.paramCol3 = 17
        self.slopesCol = 20
        self.qeRefMedCol = 28
        self.qeRefMaxCol = 29
        self.qeRow = 5
        self.tableStartRow = 14        

    def getData(self):
        #Project data
        projModel = Project()        
        projModel.setFilter('active = 1')
        projModel.select()
        proj = projModel.record(0)
        
        #Parameters
        paramsModel = Parameter()
        paramsModel.setFilter('id = {}'.format(proj.value('parameter_id')))
        paramsModel.select()
        params = paramsModel.record(0)
        
        #Criteria
        critModel = Criteria()
        critModel.setFilter('id = {}'.format(params.value('project_criteria_id')))
        critModel.select()
        crit = critModel.record(0)

        #Calculations
        calcModel = Calculation()
        calcModel.setFilter('project_id = {}'.format(proj.value('id')))
        calcModel.select()

        data = {
                'project': proj,
                'parameters': params,
                'criterias': crit,
                'calculations': calcModel
        }
        return data


    def createFile(self, filename):        
        tpl = open_workbook(self.template_path, formatting_info=True)
        wb = copy(tpl)
        data = self.getData()
        proj = data['project']
        params = data['parameters']
        crit = data['criterias']
        calc = data['calculations']

        sheet = wb.get_sheet(0)
        sheet.write(3,self.projectCol, proj.value('city'), self.projectStyle)
        sheet.write(4,self.projectCol, proj.value('name'), self.projectStyle)
        sheet.write(5,self.projectCol, proj.value('microsystem'), self.projectStyle)
        sheet.write(6,self.projectCol, proj.value('author'), self.projectStyle)
        sheet.write(7,self.projectCol, proj.value('date'), self.projectStyle)

        sheet.write(3, self.paramCol1, params.value('final_population'), self.borderStyle)
        sheet.write(4, self.paramCol1, params.value('beginning_population'), self.borderStyle)
        sheet.write(5, self.paramCol1, crit.value('water_consumption_pc'), self.borderStyle)
        sheet.write(6, self.paramCol1, params.value('occupancy_rate_start'), self.borderStyle)
        sheet.write(7, self.paramCol1, crit.value('k1_daily'), self.borderStyle)
        sheet.write(8, self.paramCol1, crit.value('k2_hourly'), self.borderStyle)

        sheet.write(3, self.paramCol2, crit.value('coefficient_return_c'), self.borderStyle)
        sheet.write(4, self.paramCol2, crit.value('intake_rate'), self.borderStyle)
        sheet.write(5, self.paramCol2, '{} %'.format(crit.value('max_water_level')), self.borderStyle)
        sheet.write(6, self.paramCol2, crit.value('flow_min_qmin'), self.borderStyle)
        sheet.write(7, self.paramCol2, crit.value('avg_tractive_force_min'), self.borderStyle)
        sheet.write(8, self.paramCol2, crit.value('min_diameter'), self.borderStyle)
        
        sheet.write(4, self.paramCol3, params.value('sewer_contribution_rate_end'), self.borderStyle)
        sheet.write(5, self.paramCol3, params.value('sewer_contribution_rate_start'), self.borderStyle)
        sheet.write(7, self.paramCol3, crit.value('cover_min_street'), self.borderStyle)
        sheet.write(8, self.paramCol3, crit.value('cover_min_sidewalks_gs'), self.borderStyle)

        sheet.write(5, self.slopesCol, crit.value('diameter_up_150'), self.borderStyle)
        sheet.write(6, self.slopesCol, crit.value('diameter_up_200'), self.borderStyle)
        sheet.write(7, self.slopesCol, crit.value('from_diameter_250'), self.borderStyle)

        sheet.write(self.qeRow, self.qeRefMedCol, '{} l/dia'.format(round(params.value('qe_reference_med'),4)), self.centerStyle)
        sheet.write(self.qeRow, self.qeRefMaxCol, '{} l/s'.format(round(params.value('qe_reference_max'),4)), self.qeMaxStyle)

        coeffRetC = crit.value('coefficient_return_c')
        watConsEnd = crit.value('water_consumption_pc_end')
        occRateEnd = params.value('occupancy_rate_end')
        qeReferenceMedEnd = (watConsEnd * occRateEnd * coeffRetC)
        k1Dly = crit.value('k1_daily')
        k2Hrly = crit.value('k2_hourly')
        qeReferenceMaxEnd = (watConsEnd *  occRateEnd * coeffRetC * k1Dly * k2Hrly) / 86400

        sheet.write(self.qeRow+1, self.qeRefMedCol, '{} l/dia'.format(round(qeReferenceMedEnd,4)), self.centerStyle)
        sheet.write(self.qeRow+1, self.qeRefMaxCol, '{} l/s'.format(round(qeReferenceMaxEnd, 4)), self.qeMaxStyle)

        sheet.write(self.qeRow+2, self.qeRefMedCol, '{} l/dia'.format(round(qeReferenceMedEnd*1000),4), self.centerStyle)
        sheet.write(self.qeRow+2, self.qeRefMaxCol, '{} l/s'.format(round(qeReferenceMaxEnd*1000), 4), self.qeMaxStyle)

        # Calc Table
        columns = ('col_seg', 'extension','previous_col_seg_id' ,'m1_col_id' ,'m2_col_id' ,'block_others_id' ,'qty_final_qe' , 
                    'qty_initial_qe', 'intake_in_seg' , 'total_flow_rate_end', 'total_flow_rate_start','el_terr_up' , 'el_terr_down',  
                    'el_col_up', 'el_col_down', 'depth_up' , 'depth_down',
                    'slopes_terr' , 'slopes_adopted_col','adopted_diameter' , 'c_manning',
                    'qmax', 'water_level_verification' , 'critical_velocity', 'velocity',
                    'recurrent_design_flow_qr', 'self_clean_water_level', 'tractive_force',
                    'inspection_type_up' , 'inspection_type_down', 'observations')

        currentRow = self.tableStartRow        
        for i in range(calc.rowCount()):
            rec = calc.record(i)
            qmax = max(rec.value('prj_flow_rate_qgmax'), rec.value('initial_flow_rate_qi'))
            water_level_verification = max(rec.value('water_level_y'), rec.value('water_level_y_start'))
            critical_velocity = max(rec.value('critical_velocity'), rec.value('initial_critical_velocity'))
            velocity = max(rec.value('velocity'), rec.value('initial_velocity'))

            recurrent_design_flow_qr = min(rec.value('initial_rec_des_flow_qfr'), rec.value('rec_des_flow_qfr'))
            self_clean_water_level = min(rec.value('water_level_y'), rec.value('water_level_y_start'))
            tractive_force = min(rec.value('tractive_force_start'), rec.value('tractive_force'))
            for c in range(len(columns)):
                col = columns[c]                
                value = rec.value(col)

                if col == 'qmax':
                    value = qmax
                elif col == 'water_level_verification':
                    value = water_level_verification
                elif col == 'critical_velocity':
                    value = critical_velocity
                elif col == 'velocity':
                    value = velocity
                elif col == 'recurrent_design_flow_qr':
                    value = recurrent_design_flow_qr
                elif col == 'self_clean_water_level':
                    value = self_clean_water_level
                elif col == 'tractive_force':
                    value = tractive_force
                if not value:
                   value = ''
                else:
                    style = self.negativeStyle if type(value) not in [str] and value < 0 else self.borderStyle
                sheet.write(currentRow, (c+1) , value, style)
            currentRow += 1            

        wb.save(filename)
          