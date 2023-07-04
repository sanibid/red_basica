import os
import json
import time
from qgis.core import QgsProject
from PyQt5.QtSql import QSqlDatabase,QSqlQuery

class Store():
    def __init__(self):
        self.setup()
        self.initialize()

    def setup(self):
        project = QgsProject.instance()
        project_path = project.fileName()
        project_directory = os.path.dirname(project_path)
        db_directory = os.path.join(project_directory, 'db')
        if not os.path.exists(db_directory):
            os.makedirs(db_directory)
        file_path = os.path.join(project_directory, 'db', 'sanihub.db')
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(file_path)

    def initialize(self):
        start_time = time.time()
        if self.db.open():
            print("open DB success")
            if not self.db.tables():
                print( "No tables found")
                self.createTables()
                self.importCountries()
                self.importMaterials()
                self.importCriterias()
                self.importInspectionDevices()
                self.importPipes()
                self.db.close()
            else:
                print("Tables already exist")                
        else:
            print("Error openind database")
        print("Total time execution to initialize: --- %s seconds ---" % (time.time() - start_time))

    def createTables(self):
        print("Creating Tables ...")
        query = QSqlQuery()
        query.exec("PRAGMA journal_mode=wal;")        
        query.exec_("CREATE TABLE IF NOT EXISTS countries\
            (id integer primary key autoincrement,\
            name_en text unique not null,\
            name_es text unique not null,\
            name_pt text unique not null,\
            iso2 text)")

        query.exec_("CREATE TABLE IF NOT EXISTS materials\
            (id integer primary key autoincrement,\
            name_en text,\
            name_es text,\
            name_pt text,\
            min_diameter double precision,\
            max_diameter double precision,\
            manning_roughness_c double precision,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP)")
            

        query.exec_("CREATE TABLE IF NOT EXISTS project_criterias\
            (id integer primary key autoincrement,\
            name text unique not null,\
            water_consumption_pc double precision,\
            k1_daily double precision,\
            k2_hourly double precision,\
            coefficient_return_c double precision,\
            intake_rate double precision,\
            avg_tractive_force_min double precision,\
            flow_min_qmin double precision,\
            water_surface_max double precision,\
            max_water_level double precision,\
            min_diameter double precision,\
            diameter_up_150 double precision,\
            diameter_up_200 double precision,\
            from_diameter_250 double precision,\
            cover_min_street double precision,\
            cover_min_sidewalks_gs double precision,\
            type_preferred_head_col text,\
            max_drop double precision,\
            bottom_ib_mh double precision,\
            parent_project_id integer, \
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP, \
            FOREIGN KEY(parent_project_id) REFERENCES projects(id) ON DELETE CASCADE)")

        query.exec_("CREATE TRIGGER projects_criterias_trigger AFTER UPDATE ON project_criterias\
        BEGIN\
            UPDATE project_criterias SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")

        query.exec_("CREATE TABLE IF NOT EXISTS parameters\
            (id integer primary key autoincrement,\
            project_criteria_id integer,\
            layer_name text,\
            final_population integer,\
            beginning_population integer,\
            occupancy_rate_start double precision,\
            occupancy_rate_end double precision,\
            residences_end integer,\
            residences_start integer,\
            connections_end integer,\
            connections_start integer,\
            point_flows_end double precision,\
            point_flows_start double precision,\
            qe_reference_max double precision,\
            qe_reference_med double precision,\
            contribution_sewage boolean,\
            sewer_contribution_rate_end double precision,\
            sewer_contribution_rate_start double precision,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            FOREIGN KEY(project_criteria_id) REFERENCES project_criterias(id) ON DELETE CASCADE)")

        query.exec_("CREATE TRIGGER parameters_trigger AFTER UPDATE ON parameters\
        BEGIN\
            UPDATE parameters SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")    

        query.exec_("CREATE TABLE IF NOT EXISTS projects\
            (id integer primary key autoincrement,\
            parameter_id integer,\
            name text unique not null,\
            country_id integer,\
            city text,\
            microsystem text,\
            author text,\
            active boolean,\
            date date,\
            srid integer,\
            server_id integer,\
            default_view boolean,\
            depth_min_view boolean,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            FOREIGN KEY(parameter_id) REFERENCES parameters(id) ON DELETE CASCADE,\
            FOREIGN KEY(country_id) REFERENCES countries(id))")        

        query.exec_("CREATE TRIGGER projects_trigger AFTER UPDATE ON projects\
            BEGIN\
                UPDATE projects SET updated_at = datetime('now') WHERE id = NEW.id;\
            END;")
     
        query.exec_("CREATE TABLE IF NOT EXISTS pipes\
            (id integer primary key autoincrement,\
            criteria_id integer,\
            diameter double precision,\
            material_id integer,\
            manning_suggested double precision,\
            manning_adopted double precision,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            FOREIGN KEY(material_id) REFERENCES materials(id),\
            FOREIGN KEY(criteria_id) REFERENCES project_criterias(id) ON DELETE CASCADE)")

        query.exec_("CREATE TRIGGER pipes_trigger AFTER UPDATE ON pipes\
        BEGIN\
            UPDATE pipes SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")

        query.exec_("CREATE TABLE IF NOT EXISTS inspection_devices\
            (id integer primary key autoincrement,\
            criteria_id integer,\
            type_en text,\
            type_es text,\
            type_pt text,\
            max_depth double precision,\
            max_diameter_suggested double precision,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            FOREIGN KEY(criteria_id) REFERENCES project_criterias(id) ON DELETE CASCADE)")

        query.exec_("CREATE TRIGGER devices_trigger AFTER UPDATE ON inspection_devices\
        BEGIN\
            UPDATE inspection_devices SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")
        
        query.exec_("CREATE TABLE IF NOT EXISTS calculations\
            (id integer primary key autoincrement,\
            project_id integer,\
            layer_name text,\
            initial_segment boolean,\
            final_segment boolean,\
            collector_number text,\
            col_seg text,\
            extension double precision,\
            previous_col_seg_id text,\
            m1_col_id text,\
            m2_col_id text,\
            block_others_id text,\
            qty_final_qe integer,\
            qty_initial_qe integer,\
            intake_in_seg double precision,\
            total_flow_rate_end double precision,\
            total_flow_rate_start double precision,\
            col_pipe_position integer,\
            aux_prof_i text,\
            force_depth_up double precision,\
            aux_depth_adjustment double precision,\
            covering_up double precision,\
            covering_down double precision,\
            depth_up double precision,\
            depth_down double precision,\
            force_depth_down double precision,\
            el_terr_up double precision,\
            el_terr_down double precision,\
            el_col_up double precision,\
            el_col_down double precision,\
            el_top_gen_up double precision,\
            el_top_gen_down double precision,\
            slopes_terr double precision,\
            slopes_min_accepted_col double precision,\
            slopes_adopted_col double precision,\
            suggested_diameter double precision,\
            adopted_diameter double precision,\
            c_manning double precision,\
            prj_flow_rate_qgmax double precision,\
            water_level_y double precision,\
            water_level_pipe_end double precision,\
            tractive_force double precision,\
            critical_velocity double precision,\
            velocity double precision,\
            initial_flow_rate_qi double precision,\
            water_level_y_start double precision,\
            water_level_pipe_start double precision,\
            tractive_force_start double precision,\
            inspection_id_up text,\
            inspection_type_up text,\
            inspection_id_down text,\
            inspection_type_down text,\
            downstream_seg_id text,\
            x_initial double precision,\
            y_initial double precision,\
            x_final double precision,\
            y_final double precision,\
            observations text,\
            slopes_min_modified boolean,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE)")

        query.exec_("CREATE TRIGGER calculations_insert_trigger AFTER INSERT ON calculations\
        BEGIN\
            UPDATE calculations SET created_at = datetime('now') WHERE id = NEW.id;\
        END;")

        query.exec_("CREATE TRIGGER calculations_trigger AFTER UPDATE ON calculations\
        BEGIN\
            UPDATE calculations SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")
        
        query.exec_("CREATE TABLE IF NOT EXISTS contributions\
            (id integer primary key autoincrement,\
            calculation_id integer,\
            initial_segment boolean,\
            col_seg text,\
            previous_col_seg_end double precision,\
            col_pipe_m1_end double precision,\
            col_pipe_m2_end double precision,\
            subtotal_up_seg_end double precision,\
            condominial_lines_end double precision,\
            linear_contr_seg_end double precision,\
            previous_col_seg_start double precision,\
            col_pipe_m1_start double precision,\
            col_pipe_m2_start double precision,\
            subtotal_up_seg_start double precision,\
            condominial_lines_start double precision,\
            linear_contr_seg_start double precision,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            FOREIGN KEY(calculation_id) REFERENCES calculations(id) ON DELETE CASCADE)")

        query.exec_("CREATE TRIGGER contributions_insert_trigger AFTER INSERT ON contributions\
        BEGIN\
            UPDATE contributions SET created_at = datetime('now') WHERE id = NEW.id;\
        END;")

        query.exec_("CREATE TRIGGER contributions_trigger AFTER UPDATE ON contributions\
        BEGIN\
            UPDATE contributions SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")

        query.exec_("CREATE TABLE IF NOT EXISTS wl_adj\
            (id integer primary key autoincrement,\
            calculation_id integer,\
            initial_segment boolean,\
            col_seg character varying,\
            previous_col_seg_end character varying,\
            m1_col_id character varying,\
            m2_col_id character varying,\
            amt_seg_depth double precision,\
            m1_col_depth double precision,\
            m2_col_depth double precision,\
            greater_depth double precision,\
            insp_dev_h_out double precision,\
            down_end_h double precision,\
            amt_seg_cov double precision,\
            m1_col_cov double precision,\
            m2_col_cov double precision,\
            greater_cov double precision,\
            insp_dev_cov_out double precision,\
            down_end_cov double precision,\
            amt_seg_up double precision,\
            m1_col_up double precision,\
            m2_col_up double precision,\
            lowest_up double precision,\
            insp_dev_cov_up double precision,\
            up_diff_needed double precision,\
            amt_seg_na double precision,\
            m1_col_na double precision,\
            m2_col_na double precision,\
            na_deeper double precision,\
            insp_dev_cov_na double precision,\
            na_diff_needed double precision,\
            force_depth double precision,\
            calc_depth_up double precision,\
            imp_depth_up double precision,\
            aux_imp_depth_up double precision,\
            aux_h_imp_depth double precision,\
            aux_ini double precision,\
            dn_est_need double precision,\
            dn_ad double precision,\
            dn_calc_max double precision,\
            up_side_seg double precision,\
            down_side_seg double precision,\
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP,\
            FOREIGN KEY(calculation_id) REFERENCES calculations(id) ON DELETE CASCADE)")
        
        query.exec_("CREATE TRIGGER wl_adj_insert_trigger AFTER INSERT ON wl_adj\
        BEGIN\
            UPDATE wl_adj SET created_at = datetime('now') WHERE id = NEW.id;\
        END;")

        query.exec_("CREATE TRIGGER wl_adj_trigger AFTER UPDATE ON wl_adj\
        BEGIN\
            UPDATE wl_adj SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")

        query.exec_("CREATE TRIGGER projects_trigger AFTER UPDATE ON projects\
        BEGIN\
            UPDATE projects SET updated_at = datetime('now') WHERE id = NEW.id;\
        END;")
          

    def importCountries(self):
        print("Inserting Countries.")
        query = QSqlQuery()
        filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'countries.json')
        with open(filename) as json_file:
            countries = json.load(json_file)
        values = ''
        for p in countries:
            values += "('"+p['name_en']+"','"+p['name_es']+"','"+p['name_pt']+"','"+p['iso2']+"'),"
        execQuery = "INSERT INTO countries (name_en, name_es, name_pt, iso2) VALUES "+ values[:-1] + ";"
        query.exec_('BEGIN TRANSACTION;')
        query.exec_(execQuery)
        query.exec_('COMMIT;')
        print("Finalizing Country table")

    def importMaterials(self):
        print("Inserting Materials.")
        query = QSqlQuery()
        filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'materials.json')
        with open(filename) as json_file:
            materials = json.load(json_file)
        values = ''
        for p in materials:
            values += "('"+p['name_en']+"','"+p['name_es']+"','"+p['name_pt']+"','"+str(p['min_diameter'])+"','"+str(p['max_diameter'])+"',\
                        '"+str(p['manning_roughness_c'])+"', datetime('now'), datetime('now')),"
        execQuery = "INSERT INTO materials (name_en, name_es, name_pt, min_diameter, max_diameter,\
                        manning_roughness_c, created_at, updated_at) VALUES "+ values[:-1] + ";"
        query.exec_('BEGIN TRANSACTION;')
        query.exec_(execQuery)
        query.exec_('COMMIT;')
        print("Finalizing Materials table")

    def importInspectionDevices(self):
        print("Inserting Inspection Devices.")
        query = QSqlQuery()
        filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'inspection-devices.json')
        with open(filename) as json_file:
            inspection_devices = json.load(json_file)
        values = ''
        for p in inspection_devices:
            values += "('"+str(p['criteria_id'])+"','"+p['type_en']+"','"+p['type_es']+"','"+p['type_pt']+"','"+str(p['max_depth'])+"',\
                        '"+str(p['max_diameter_suggested'])+"', datetime('now'), datetime('now')),"
        execQuery = "INSERT INTO inspection_devices (criteria_id, type_en, type_es, type_pt, max_depth,  max_diameter_suggested, created_at, updated_at) VALUES "+ values[:-1] + ";"
        query.exec_('BEGIN TRANSACTION;')
        query.exec_(execQuery)
        query.exec_('COMMIT;')
        print("Finalizing Inspection Devices table")
    
    def importPipes(self):
        print("Inserting Pipes.")
        query = QSqlQuery()
        filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'pipes.json')
        with open(filename) as json_file:
            pipes = json.load(json_file)
        values = ''
        for p in pipes:
            values += "('"+str(p['criteria_id'])+"','"+str(p['diameter'])+"','"+str(p['material_id'])+"','"+str(p['manning_suggested'])+"','"+str(p['manning_adopted'])+"',\
                        datetime('now'), datetime('now')),"
        execQuery = "INSERT INTO pipes (criteria_id, diameter, material_id, manning_suggested, manning_adopted, created_at, updated_at) VALUES "+ values[:-1] + ";"
        query.exec_('BEGIN TRANSACTION;')
        query.exec_(execQuery)
        query.exec_('COMMIT;')
        print("Finalizing Pipes table")

    def importCriterias(self):
        print("Inserting SANIHUB Criterias.")
        query = QSqlQuery()
        filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'criterias.json')
        with open(filename) as json_file:
            criterias = json.load(json_file)
        values = ''
        for p in criterias:
            values += "('"+p['name']+"','"+p['water_consumption_pc']+"','"+p['k1_daily']+"','"+p['k2_hourly']+"','"+p['coefficient_return_c']+"',\
                '"+p['intake_rate']+"','"+p['avg_tractive_force_min']+"','"+p['flow_min_qmin']+"','"+p['water_surface_max']+"','"+p['max_water_level']+"',\
                '"+p['min_diameter']+"','"+p['diameter_up_150']+"','"+p['diameter_up_200']+"','"+p['from_diameter_250']+"','"+p['cover_min_street']+"',\
                '"+p['cover_min_sidewalks_gs']+"','"+p['type_preferred_head_col']+"','"+p['max_drop']+"','"+p['bottom_ib_mh']+"', datetime('now'), datetime('now')),"

        execQuery = "INSERT INTO project_criterias (name, water_consumption_pc, k1_daily, k2_hourly, coefficient_return_c, intake_rate, \
            avg_tractive_force_min, flow_min_qmin, water_surface_max, max_water_level, min_diameter, diameter_up_150, diameter_up_200, \
            from_diameter_250, cover_min_street, cover_min_sidewalks_gs, type_preferred_head_col, max_drop, bottom_ib_mh, \
            created_at, updated_at) VALUES "+ values[:-1] + ";"

        query.exec_('BEGIN TRANSACTION;')
        query.exec_(execQuery)
        query.exec_('COMMIT;')
        print("Finalizing Project_Criterias table")

    def getDB(self):
        return self.db