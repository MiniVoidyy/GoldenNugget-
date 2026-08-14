#!/usr/bin/env python3
"""Add resetDropdown widget to the UI file."""

with open('src/qt/mainwindow.ui', 'r') as f:
    content = f.read()

# Find the titleBar widget end
idx = content.find('<widget class="QToolButton" name="titleBar">')
if idx == -1:
    print('Could not find titleBar')
    exit(1)

# Find the closing </item> for the titleBar's item
# The structure is: <item> -> <widget class="QToolButton" name="titleBar"> ... </widget> </item>
titlebar_start = content.find('<item>', content.find('<item>', content.find('<item>', content.find('<item>', content.find('<item>', idx)))))
if titlebar_start == -1:
    print('Could not find titleBar item start')
    exit(1)

item_end = content.find('</item>', content.find('<item>', content.find('<item>', content.find('<item>', content.find('<item>', idx)))))
if titlebar_start == -1:
    print('Could not find titleBar item end')
    exit(1)

# Actually, let's find the </item> that closes the titleBar's item
item_start = content.find('<item>', idx)
item_end = content.find('</item>', item_start)
print(f'item_start: {item_start}, item_end: {item_end}')

# The structure is nested items. Let's find the correct one.
# Look for the titleBar widget specifically
titlebar_widget_start = content.find('<widget class="QToolButton" name="titleBar">', idx)
if titlebar_widget_start == -1:
    print('Could not find titleBar widget')
    exit(1)

# Find the item that contains this widget
item_start = content.rfind('<item>', 0, titlebar_widget_start)
item_end = content.find('</item>', titlebar_widget_start)

print(f'item_start: {item_start}, item_end: {item_end}')

# Insert after the titleBar's item
new_widget = '''
        <item>
         <widget class="QComboBox" name="resetDropdown">
          <property name="minimumSize">
           <size>
            <width>140</width>
            <height>32</height>
           </size>
          </property>
          <property name="maximumSize">
           <size>
            <width>140</width>
            <height>32</height>
           </size>
          </property>
          <property name="styleSheet">
           <string notr="true">QComboBox {
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
}
</string>
          </property>
          <property name="placeholderText">
           <string notr="true">Reset...</string>
          </property>
          <item>
           <property name="text">
            <string notr="true">Reset Tweaks</string>
           </property>
          </item>
          <item>
           <property name="text">
            <string notr="true">Reset PosterBoard</string>
           </property>
          </item>
          <item>
           <property name="text">
            <string notr="true">Reset All</string>
           </property>
          </item>
         </widget>
        </item>
'''

# Insert after the titleBar's item
item_end_tag = '</item>'
item_end_pos = content.find(item_end_tag, content.find('<widget class="QToolButton" name="titleBar">'))
if item_end_pos != -1:
    item_end_pos += len(item_end_tag)
    new_content = content[:item_end_pos] + new_widget + content[item_end_pos:]
    with open('src/qt/mainwindow.ui', 'w') as f:
        f.write(new_content)
    print('Added resetDropdown widget')
else:
    print('Could not find insertion point')

print('Done')