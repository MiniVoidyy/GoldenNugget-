#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse('src/qt/mainwindow.ui')
root = tree.getroot()

# Build parent map
parent_map = {c: p for p in root.iter() for c in p}

# 1. Fix home page - change GoldenNugget label font to Unbounded
for widget in root.iter('widget'):
    if widget.get('name') == 'label_2':
        for prop in widget.findall('property'):
            if prop.get('name') == 'font':
                font = prop.find('font')
                if font is not None:
                    family = font.find('family')
                    if family is not None:
                        family.text = 'Unbounded'
                    weight = font.find('weight')
                    if weight is not None:
                        weight.text = '700'
                break

# 2. Fix posterboardLbl text to "PosterBoard" and font
for widget in root.iter('widget'):
    if widget.get('name') == 'posterboardLbl':
        for prop in widget.findall('property'):
            if prop.get('name') == 'text':
                prop.text = 'PosterBoard'
            elif prop.get('name') == 'font':
                font = prop.find('font')
                if font is not None:
                    family = font.find('family')
                    if family is not None:
                        family.text = 'Unbounded'
                    weight = font.find('weight')
                    if weight is not None:
                        weight.text = '600'
                break

# 3. Add Reset dropdown after titleBar
# Find the titleBar widget
titlebar_widget = None
for widget in root.iter('widget'):
    if widget.get('name') == 'titleBar':
        titlebar_widget = widget
        break

if titlebar_widget is not None:
    # Find the item that contains titleBar
    parent_item = None
    for elem in root.iter():
        if elem.tag == 'item' and elem.find('widget') is not None and elem.find('widget').get('name') == 'titleBar':
            parent_item = elem
            break
    
    if parent_item is not None:
        # Find the parent layout
        layout = parent_map.get(parent_item)
        if layout is not None and layout.tag == 'layout':
            # Find the index of the titleBar item
            items = list(layout)
            title_index = -1
            for i, item in enumerate(items):
                if item.find('widget') is not None and item.find('widget').get('name') == 'titleBar':
                    title_index = i
                    break
                
                if title_index >= 0:
                    # Create new item for reset dropdown
                    new_item = ET.SubElement(layout, 'item')
                    reset_combo = ET.SubElement(new_item, 'widget', {
                        'class': 'QComboBox',
                        'name': 'resetDropdown'
                    })
                    ET.SubElement(reset_combo, 'property', {'name': 'minimumSize'}).text = '140x32'
                    ET.SubElement(reset_combo, 'property', {'name': 'maximumSize'}).text = '140x32'
                    
                    style_prop = ET.SubElement(reset_combo, 'property', {'name': 'styleSheet'})
                    style_prop.text = """QComboBox {
	background-color: transparent;
	border: none;
	color: #8E8E93;
	font-size: 13px;
	padding-left: 8px;
	border-radius: 8px;
}
QComboBox:hover {
	background-color: #2C2C2E;
}
QComboBox::drop-down {
	image: url(:/icon/caret-down-fill.svg);
	icon-size: 14px;
	width: 20px;
	border: none;
}
QComboBox QAbstractItemView {
	background-color: #1C1C1E;
	border: 1px solid #3A3A3C;
	border-radius: 8px;
	selection-background-color: #007AFF;
	padding: 4px;
	outline: none;
}
QComboBox QAbstractItemView::item {
	padding: 8px 12px;
	min-height: 32px;
}"""
                    
                    ET.SubElement(reset_combo, 'property', {'name': 'placeholderText'}).text = 'Reset...'
                    
                    for text in ['Reset Tweaks', 'Reset PosterBoard', 'Reset All']:
                        item_elem = ET.SubElement(reset_combo, 'item')
                        ET.SubElement(item_elem, 'property', {'name': 'text'}).text = text
                    
                    # Insert after titleBar
                    items = list(layout)
                    title_index = -1
                    for i, item in enumerate(items):
                        if item.find('widget') is not None and item.find('widget').get('name') == 'titleBar':
                            title_index = i
                            break
                    if title_index >= 0:
                        # Rebuild layout children
                        children = list(layout)
                        layout[:] = children[:title_index+1] + [new_item] + children[title_index+1:]

tree.write('src/qt/mainwindow.ui', encoding='utf-8', xml_declaration=True)
print('Done')