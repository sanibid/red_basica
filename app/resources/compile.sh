#!/bin/bash

#install dependencies: sudo apt install pyqt5-dev-tools

pyuic5 main_window.ui -o ../views/ui/MainWindowUi.py
pyuic5 edit_values_dialog.ui -o ../views/ui/EditValuesDialogUi.py
pyuic5 iterations.ui -o ../views/ui/IterationsDialogUi.py
pyuic5 project_dialog.ui -o ../views/ui/ProjectDialogUi.py
pyuic5 new_project_dialog.ui -o ../views/ui/NewProjectDialogUi.py
pyuic5 parameter_dialog.ui -o ../views/ui/ParameterDialogUi.py
pyuic5 export_layers_dialog.ui -o ../views/ui/ExportLayersDialogUi.py
pyuic5 flow_dialog.ui -o ../views/ui/FlowDialogUi.py
# pyrcc5 images/contributions.qrc -o ../views/ui/contributions_rc.py
sed -i 's/import\ contributions_rc/from\ .\ import\ contributions_rc/g' ../views/ui/ParameterDialogUi.py # diff between python 2.7 and 3.4
echo " "
echo "done!"