from PyQt5.QtSql import QSqlTableModel, QSqlQuery, QSqlDatabase
from PyQt5.QtCore import Qt

class Criteria(QSqlTableModel):

    def __init__(self, *args, **kwargs):
        super(Criteria, self).__init__(*args, **kwargs)
        self.setTable("project_criterias")
        self.setSort(self.fieldIndex('id'), Qt.AscendingOrder)
        self.select()

    # @staticmethod
    # def copyPipesFromTo(_from, _to):
    #     query = QSqlQuery()
    #     query.prepare("INSERT INTO pipes \
    #                     (criteria_id, diameter, material_id, manning_suggested, manning_adopted)\
    #                     select :to, diameter, material_id, manning_suggested, manning_adopted from pipes\
    #                     where criteria_id = :from")
    #     query.bindValue(":to", _to)
    #     query.bindValue(":from", _from)
    #     query.exec_()


    def getValueBy(self, column):
        query = QSqlQuery("SELECT pc."+column+"\
            FROM project_criterias pc\
            LEFT JOIN parameters pa ON pa.project_criteria_id = pc.id\
            LEFT JOIN projects pr ON pr.parameter_id = pa.id\
            WHERE pr.active")
        if query.first():
            return query.value(0)
        else:
            return 0

    def insertData(self, data):
        query = QSqlQuery()
        query.prepare("INSERT INTO project_criterias (name, water_consumption_pc, water_consumption_pc_end, k1_daily, k2_hourly, coefficient_return_c, intake_rate,\
                avg_tractive_force_min, flow_min_qmin, water_surface_max, max_water_level, min_diameter, diameter_up_150, diameter_up_200,\
                from_diameter_250, cover_min_street, cover_min_sidewalks_gs, type_preferred_head_col, max_drop, bottom_ib_mh,\
                created_at, updated_at) VALUES (:name, :water_consumption_pc, :water_consumption_pc_end, :k1_daily, :k2_hourly, :coefficient_return_c, :intake_rate,\
                :avg_tractive_force_min, :flow_min_qmin, :water_surface_max, :max_water_level, :min_diameter, :diameter_up_150, :diameter_up_200,\
                :from_diameter_250, :cover_min_street, :cover_min_sidewalks_gs, :type_preferred_head_col, :max_drop, :bottom_ib_mh,\
                :created_at, :updated_at)")

        query.bindValue(":name", data[0])
        query.bindValue(":water_consumption_pc", data[1])
        query.bindValue(":water_consumption_pc_end", data[2])
        query.bindValue(":k1_daily", data[3])
        query.bindValue(":k2_hourly", data[4])
        query.bindValue(":coefficient_return_c", data[5])
        query.bindValue(":intake_rate", data[6])
        query.bindValue(":avg_tractive_force_min", data[7])
        query.bindValue(":flow_min_qmin", data[8])
        query.bindValue(":water_surface_max", data[9])
        query.bindValue(":max_water_level", data[10])
        query.bindValue(":min_diameter", data[11])
        query.bindValue(":diameter_up_150", data[12])
        query.bindValue(":diameter_up_200", data[13])
        query.bindValue(":from_diameter_250", data[14])
        query.bindValue(":cover_min_street", data[15])
        query.bindValue(":cover_min_sidewalks_gs", data[16])
        query.bindValue(":type_preferred_head_col", data[17])
        query.bindValue(":max_drop", data[18])
        query.bindValue(":bottom_ib_mh", data[19])
        query.bindValue(":created_at", data[20])
        query.bindValue(":updated_at", data[21])

        if query.exec():
            inserted_id = query.lastInsertId()
            return inserted_id
        else:
            print("Error inserting data:", query.lastError().text())
            return False

    @staticmethod
    def openExternalDatabase(file, sql_query):
        db = QSqlDatabase.addDatabase("QSQLITE", "db2")
        db.setDatabaseName(file)
        if db.open():
            query = QSqlQuery(db=db)
            query.exec_(sql_query)
            values_list = []
            while query.next():
                values = [query.value(i) for i in range(query.record().count())]
                values_list.append(values)
            db.close()
        return values_list

    @staticmethod
    def getProfileList(file):
        sql = "SELECT id, name FROM project_criterias where id > 1"
        values = Criteria.openExternalDatabase(file, sql)
        return values

    @staticmethod
    def getProfileData(file, id):
        criteria_sql =  'SELECT name, water_consumption_pc, water_consumption_pc_end, k1_daily, k2_hourly, coefficient_return_c, intake_rate,\
                avg_tractive_force_min, flow_min_qmin, water_surface_max, max_water_level, min_diameter, diameter_up_150, diameter_up_200,\
                from_diameter_250, cover_min_street, cover_min_sidewalks_gs, type_preferred_head_col, max_drop, bottom_ib_mh,\
                created_at, updated_at\
            FROM project_criterias\
            WHERE id = {}'.format(id)
        criteria = Criteria.openExternalDatabase(file, criteria_sql)

        pipes_sql = "SELECT criteria_id, diameter, material_id, manning_suggested, manning_adopted, created_at, updated_at\
                FROM pipes\
                WHERE criteria_id = {}".format(id)
        pipes = Criteria.openExternalDatabase(file, pipes_sql)

        insp_devices_sql = "SELECT criteria_id, type_en, type_es ,type_pt, max_depth, max_diameter_suggested, created_at, updated_at\
                            FROM inspection_devices\
                            WHERE criteria_id = {}".format(id)

        insp_devices = Criteria.openExternalDatabase(file ,insp_devices_sql)

        return criteria[0], pipes, insp_devices