from PyQt5.QtSql import QSqlTableModel, QSqlRelationalTableModel, QSqlRelation, QSqlQuery
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