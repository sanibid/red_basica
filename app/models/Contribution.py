from PyQt5.QtCore import Qt, QCoreApplication, QT_TRANSLATE_NOOP
from PyQt5.QtSql import QSqlRelation, QSqlRelationalTableModel, QSqlTableModel, QSqlQuery
from PyQt5.QtGui import QColor

translate = QCoreApplication.translate

class Contribution(QSqlRelationalTableModel):
    
    def __init__(self, *args, **kwargs):
        super(Contribution, self).__init__(*args, **kwargs)
        self.setTable("contributions")
        self.select()
        # is important to use QT_TRANSLATE_NOOP and columns needs to be list () and not array [] 
        self.columns = (
            QT_TRANSLATE_NOOP("ContTbl", "col_seg"),
            QT_TRANSLATE_NOOP("ContTbl", "previous_col_seg_end"),
            QT_TRANSLATE_NOOP("ContTbl", "col_pipe_m1_end"),
            QT_TRANSLATE_NOOP("ContTbl", "col_pipe_m2_end"),
            QT_TRANSLATE_NOOP("ContTbl", "subtotal_up_seg_end"),
            QT_TRANSLATE_NOOP("ContTbl", "condominial_lines_end"),
            QT_TRANSLATE_NOOP("ContTbl", "linear_contr_seg_end"),
            QT_TRANSLATE_NOOP("ContTbl", "previous_col_seg_start"),
            QT_TRANSLATE_NOOP("ContTbl", "col_pipe_m1_start"),
            QT_TRANSLATE_NOOP("ContTbl", "col_pipe_m2_start"),
            QT_TRANSLATE_NOOP("ContTbl", "subtotal_up_seg_start"),
            QT_TRANSLATE_NOOP("ContTbl", "condominial_lines_start"),
            QT_TRANSLATE_NOOP("ContTbl", "linear_contr_seg_start"),
            QT_TRANSLATE_NOOP("ContTbl", "avg_flow_end"),
            QT_TRANSLATE_NOOP("ContTbl", "recur_flow_end"),
            QT_TRANSLATE_NOOP("ContTbl", "max_flow_end"),
            QT_TRANSLATE_NOOP("ContTbl", "avg_flow_start"),
            QT_TRANSLATE_NOOP("ContTbl", "recur_flow_start"),
            QT_TRANSLATE_NOOP("ContTbl", "max_flow_start"),
            QT_TRANSLATE_NOOP("ContTbl", "intake_prev_col"),
            QT_TRANSLATE_NOOP("ContTbl", "intake_col_m1"),
            QT_TRANSLATE_NOOP("ContTbl", "intake_col_m2"),
            QT_TRANSLATE_NOOP("ContTbl", "intake_seg"),
            QT_TRANSLATE_NOOP("ContTbl", "intake_accumulated")
        )
        self.hiddenColumns = ["id", "calculation_id", "created_at", "updated_at", "initial_segment"]

    
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
                return translate("ContTbl", self.record().fieldName(section))
        return super(Contribution, self).headerData(section, orientation, role)