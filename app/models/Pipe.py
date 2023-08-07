from PyQt5.QtSql import QSqlTableModel, QSqlRelationalTableModel, QSqlQuery
from PyQt5.QtCore import Qt

class Pipe(QSqlRelationalTableModel):

    def __init__(self, *args, **kwargs):
        super(Pipe, self).__init__(*args, **kwargs)
        self.setTable("pipes")
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.setSort(self.fieldIndex('diameter'), Qt.AscendingOrder)
        #headers
        self.setHeaderData(self.fieldIndex("diameter"), Qt.Horizontal, "DN(mm)")
        self.setHeaderData(self.fieldIndex("material_id"), Qt.Horizontal, "Material")
        self.setHeaderData(self.fieldIndex("manning_suggested"), Qt.Horizontal, "C. Manning n sugerido")
        self.setHeaderData(self.fieldIndex("manning_adopted"), Qt.Horizontal, "C. Manning n adoptado")
        self.select()

    def getValueBy(self, column, where=None):
        sql = "SELECT p.{}\
            FROM pipes p\
            LEFT JOIN parameters pa on pa.project_criteria_id = p.criteria_id\
            WHERE pa.id in (SELECT parameter_id FROM projects where active)".format(column)
        if where != None:
            sql = sql + " AND {}".format(where)
        query = QSqlQuery(sql)
        if query.first():
            return query.value(0)
        else:
            return 0

    def insertPipes(self, criteria_id, data):
        for pipe in data:
            query = QSqlQuery()
            query.prepare("INSERT INTO pipes (criteria_id, diameter, material_id, manning_suggested, manning_adopted, created_at, updated_at) VALUES \
                    (:criteria_id, :diameter, :material_id, :manning_suggested, :manning_adopted, :created_at, :updated_at)")
            query.bindValue(":criteria_id", criteria_id)
            query.bindValue(":diameter", pipe[1])
            query.bindValue(":material_id", pipe[2])
            query.bindValue(":manning_suggested", pipe[3])
            query.bindValue(":manning_adopted", pipe[4])
            query.bindValue(":created_at", pipe[5])
            query.bindValue(":updated_at", pipe[6])

            if not query.exec():
                print("Error inserting data:", query.lastError().text())
                return False

    def getMinDiameter(self, diameter):
        #TODO check if is (min) or (min and equal)
        sql = "SELECT min(diameter)\
            FROM pipes\
            WHERE {} < diameter".format(diameter)
        query = QSqlQuery(sql)
        if query.first():
            return query.value(0)
        else:
            return 0