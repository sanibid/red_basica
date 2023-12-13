<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="1" simplifyDrawingTol="1" styleCategories="AllStyleCategories" readOnly="0" simplifyDrawingHints="0" minScale="1e+08" version="3.4.2-Madeira" hasScaleBasedVisibilityFlag="0" simplifyMaxScale="1" maxScale="0" simplifyLocal="1" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 forceraster="0" type="RuleRenderer" symbollevels="0" enableorderby="0">
    <rules key="{71662cd5-4900-4a3d-b956-35dd66b26875}">
      <rule symbol="0" key="{aa50985e-1069-4a35-9b95-e20759ccedeb}" filter="&quot;QE_IP&quot; is NULL and  &quot;QE_FP&quot;  is NULL"/>
      <rule symbol="1" key="{889bd533-f0e2-449d-bd28-e1deff809d43}" filter=" &quot;QE_IP&quot; &lt;> 'NULL' or  &quot;QE_FP&quot; &lt;>'NULL' "/>
      <rule symbol="2" key="{c4f2bc48-a786-437c-8a83-3eef2286b43a}" filter=" &quot;QE_IP&quot; &lt;> 'NULL' and  &quot;QE_FP&quot; &lt;>'NULL'"/>
    </rules>
    <symbols>
      <symbol clip_to_extent="1" name="0" alpha="1" type="marker">
        <layer enabled="1" locked="0" class="SimpleMarker" pass="0">
          <prop v="0" k="angle"/>
          <prop v="255,255,255,204" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="255,173,173,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.4" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MapUnit" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="12" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MapUnit" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" name="1" alpha="1" type="marker">
        <layer enabled="1" locked="0" class="SimpleMarker" pass="0">
          <prop v="0" k="angle"/>
          <prop v="255,255,255,204" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="70,182,5,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.4" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MapUnit" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="12" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MapUnit" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" name="2" alpha="1" type="marker">
        <layer enabled="1" locked="0" class="SimpleMarker" pass="0">
          <prop v="0" k="angle"/>
          <prop v="255,255,255,204" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="40,104,3,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.4" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MapUnit" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="12" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MapUnit" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontStrikeout="0" blendMode="6" fontUnderline="0" fieldName="ID_QE" fontCapitals="0" fontLetterSpacing="0" fontWeight="25" fontSizeUnit="MapUnit" isExpression="0" fontItalic="0" namedStyle="Regular" textOpacity="1" fontWordSpacing="0" fontFamily="Calibri Light" useSubstitutions="0" fontSize="7.5" textColor="71,71,71,255" previewBkgrdColor="#ffffff" multilineHeight="1">
        <text-buffer bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferDraw="0" bufferSize="1" bufferBlendMode="0" bufferJoinStyle="64" bufferSizeUnits="MM" bufferOpacity="1" bufferColor="255,255,255,255" bufferNoFill="0"/>
        <background shapeRadiiY="0" shapeRotation="0" shapeBorderWidthUnit="MM" shapeRadiiUnit="MM" shapeDraw="0" shapeSVGFile="" shapeOffsetX="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeBlendMode="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255" shapeRotationType="0" shapeOffsetY="0" shapeOpacity="1" shapeRadiiX="0" shapeType="0" shapeSizeUnit="MM" shapeBorderWidth="0" shapeOffsetUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSizeX="0" shapeBorderColor="128,128,128,255" shapeJoinStyle="64" shapeSizeType="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeSizeY="0"/>
        <shadow shadowOffsetAngle="135" shadowRadiusAlphaOnly="0" shadowOpacity="0.7" shadowUnder="0" shadowOffsetGlobal="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetUnit="MM" shadowDraw="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowBlendMode="6" shadowRadius="1.5" shadowScale="100" shadowOffsetDist="1" shadowColor="0,0,0,255" shadowRadiusUnit="MM"/>
        <substitutions/>
      </text-style>
      <text-format addDirectionSymbol="0" formatNumbers="0" autoWrapLength="0" plussign="0" decimals="3" reverseDirectionSymbol="0" placeDirectionSymbol="0" leftDirectionSymbol="&lt;" wrapChar="" useMaxLineLengthForAutoWrap="1" multilineAlign="0" rightDirectionSymbol=">"/>
      <placement rotationAngle="0" distMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceUnits="MM" offsetType="0" centroidInside="0" placement="1" yOffset="0" maxCurvedCharAngleOut="-20" priority="5" fitInPolygonOnly="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleIn="20" preserveRotation="1" repeatDistance="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" placementFlags="10" quadOffset="4" xOffset="0" distUnits="MM" offsetUnits="MapUnit" dist="0" centroidWhole="0"/>
      <rendering labelPerPart="0" scaleMax="10000000" fontLimitPixelSize="1" maxNumLabels="2000" obstacle="1" scaleMin="1" obstacleFactor="0" obstacleType="0" drawLabels="1" displayAll="0" mergeLines="0" minFeatureSize="0" scaleVisibility="0" fontMaxPixelSize="10000" upsidedownLabels="0" fontMinPixelSize="3" limitNumLabels="0" zIndex="0"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties"/>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <customproperties>
    <property key="dualview/previewExpressions" value="ID_QE"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Pie">
    <DiagramCategory opacity="1" width="15" penColor="#000000" diagramOrientation="Up" sizeType="MM" sizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" scaleDependency="Area" lineSizeScale="3x:0,0,0,0,0,0" minScaleDenominator="0" penWidth="0" enabled="0" scaleBasedVisibility="0" height="15" barWidth="5" rotationOffset="0" lineSizeType="MM" maxScaleDenominator="1e+08" penAlpha="255" labelPlacementMethod="XHeight" backgroundColor="#ffffff" minimumSize="0">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute field="" color="#000000" label=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings zIndex="0" showAll="1" placement="0" dist="0" linePlacementFlags="2" obstacle="0" priority="0">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties" type="Map">
          <Option name="positionX" type="Map">
            <Option name="active" type="bool" value="true"/>
            <Option name="field" type="QString" value="ID_QE"/>
            <Option name="type" type="int" value="2"/>
          </Option>
          <Option name="positionY" type="Map">
            <Option name="active" type="bool" value="true"/>
            <Option name="field" type="QString" value="ID_QE"/>
            <Option name="type" type="int" value="2"/>
          </Option>
          <Option name="show" type="Map">
            <Option name="active" type="bool" value="true"/>
            <Option name="field" type="QString" value="ID_QE"/>
            <Option name="type" type="int" value="2"/>
          </Option>
        </Option>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="ID_QE">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="QString" value="0"/>
            <Option name="UseHtml" type="QString" value="0"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="QE_FP">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="QString" value="0"/>
            <Option name="UseHtml" type="QString" value="0"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="QE_IP">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="QString" value="0"/>
            <Option name="UseHtml" type="QString" value="0"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="t1">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="QString" value="0"/>
            <Option name="UseHtml" type="QString" value="0"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="ID_QE" index="0" name=""/>
    <alias field="QE_FP" index="1" name=""/>
    <alias field="QE_IP" index="2" name=""/>
    <alias field="t1" index="3" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="ID_QE" expression="" applyOnUpdate="0"/>
    <default field="QE_FP" expression="" applyOnUpdate="0"/>
    <default field="QE_IP" expression="" applyOnUpdate="0"/>
    <default field="t1" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint constraints="0" field="ID_QE" notnull_strength="0" exp_strength="0" unique_strength="0"/>
    <constraint constraints="0" field="QE_FP" notnull_strength="0" exp_strength="0" unique_strength="0"/>
    <constraint constraints="0" field="QE_IP" notnull_strength="0" exp_strength="0" unique_strength="0"/>
    <constraint constraints="0" field="t1" notnull_strength="0" exp_strength="0" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="ID_QE" exp="" desc=""/>
    <constraint field="QE_FP" exp="" desc=""/>
    <constraint field="QE_IP" exp="" desc=""/>
    <constraint field="t1" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="&quot;ID_QE&quot;">
    <columns>
      <column name="ID_QE" width="-1" type="field" hidden="0"/>
      <column name="QE_FP" width="-1" type="field" hidden="0"/>
      <column name="QE_IP" width="-1" type="field" hidden="0"/>
      <column width="-1" type="actions" hidden="1"/>
      <column name="t1" width="-1" type="field" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1">D:/_ARQUIVOS_P/BID - Cap Haitien/_Produto04e05 - Projetos Pilotos/saniBID RedBasica - Cap Haitien - Pilotos/_Cap Haitien - Detalhe_Ramais</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>D:/_ARQUIVOS_P/BID - Cap Haitien/_Produto04e05 - Projetos Pilotos/saniBID RedBasica - Cap Haitien - Pilotos/_Cap Haitien - Detalhe_Ramais</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- codificação: utf-8 -*-
"""
Os formulários do QGIS podem ter uma função Python que é chamada quando
o formulário
 é aberto.

QGIS forms can have a Python function that is called when the form is
opened.

Use esta função para adicionar lógica extra aos seus formulários.

Entre com o nome da função no campo "Python Init function".
Un exemplo a seguir:
"""
a partir de PyQt4.QtGui importe QWidget

def my_form_open(diálogo, camada, feição):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>2</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="ID_QE" editable="1"/>
    <field name="QE_FP" editable="1"/>
    <field name="QE_IP" editable="1"/>
    <field name="t1" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="ID_QE" labelOnTop="0"/>
    <field name="QE_FP" labelOnTop="0"/>
    <field name="QE_IP" labelOnTop="0"/>
    <field name="t1" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>ID_QE</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
