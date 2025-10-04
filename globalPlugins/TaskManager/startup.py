# -*- coding: utf-8 -*-

import wx
import winreg
import os
import shutil

DISABLED_PREFIX = "DISABLED_"
DISABLED_FOLDER_NAME = "disabled_startup_items"

class StartupManagerDialog(wx.Dialog):
    def __init__(self, parent):
        super(StartupManagerDialog, self).__init__(parent, title=_("Startup Manager"), size=(700, 500))
        self.InitUI()
        self.Centre()

    def InitUI(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.startup_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.startup_list.InsertColumn(0, _("Name"), width=200)
        self.startup_list.InsertColumn(1, _("Command"), width=300)
        self.startup_list.InsertColumn(2, _("Location"), width=120)
        self.startup_list.InsertColumn(3, _("Enabled"), width=80)
        main_sizer.Add(self.startup_list, 1, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        enable_button = wx.Button(panel, label=_("Enable"))
        disable_button = wx.Button(panel, label=_("Disable"))
        close_button = wx.Button(panel, label=_("Close"))

        button_sizer.Add(enable_button, 0, wx.ALL, 5)
        button_sizer.Add(disable_button, 0, wx.ALL, 5)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(close_button, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)

        enable_button.Bind(wx.EVT_BUTTON, self.OnEnable)
        disable_button.Bind(wx.EVT_BUTTON, self.OnDisable)
        close_button.Bind(wx.EVT_BUTTON, lambda e: self.Close())

        self.populate_list()

    def populate_list(self):
        self.startup_list.DeleteAllItems()
        self.items = get_startup_items()
        for i, item in enumerate(self.items):
            index = self.startup_list.InsertItem(i, item['display_name'])
            self.startup_list.SetItem(index, 1, item['command'])
            self.startup_list.SetItem(index, 2, item['location_name'])
            self.startup_list.SetItem(index, 3, str(item['enabled']))
            self.startup_list.SetItemData(index, i)

    def OnEnable(self, event):
        self.toggle_item_status(enable=True)

    def OnDisable(self, event):
        self.toggle_item_status(enable=False)

    def toggle_item_status(self, enable):
        selected_index = self.startup_list.GetFirstSelected()
        if selected_index == -1:
            wx.MessageBox(_("Please select an item."), _("Information"), wx.OK | wx.ICON_INFORMATION)
            return

        item_index = self.startup_list.GetItemData(selected_index)
        item = self.items[item_index]

        if item['enabled'] == enable:
            return

        success = False
        if item['type'] == 'reg':
            success = toggle_registry_item(item, enable)
        elif item['type'] == 'folder':
            success = toggle_folder_item(item, enable)

        if success:
            self.populate_list()
        else:
            wx.MessageBox(_("Failed to change item status. Please check permissions."), _("Error"), wx.OK | wx.ICON_ERROR)

def get_startup_items():
    items = []
    reg_locations = [
        ("HKCU Run", winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ("HKLM Run", winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ]
    folder_locations = {
        "User Startup": os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup'),
        "Common Startup": os.path.join(os.getenv('PROGRAMDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup'),
    }

    for name, hkey, path in reg_locations:
        items.extend(read_from_registry(name, hkey, path))

    for name, path in folder_locations.items():
        items.extend(read_from_folder(name, path))

    return items

def read_from_registry(location_name, hkey, path):
    items = []
    try:
        with winreg.OpenKey(hkey, path) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    enabled = not name.startswith(DISABLED_PREFIX)
                    display_name = name[len(DISABLED_PREFIX):] if not enabled else name
                    items.append({
                        "type": "reg", "name": name, "display_name": display_name, "command": value,
                        "location_name": location_name, "enabled": enabled, "hkey": hkey, "path": path
                    })
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass
    return items

def read_from_folder(location_name, path):
    items = []
    # Enabled items
    if os.path.isdir(path):
        for filename in os.listdir(path):
            if filename.lower() == DISABLED_FOLDER_NAME:
                continue
            full_path = os.path.join(path, filename)
            items.append({
                "type": "folder", "name": filename, "display_name": filename, "command": full_path,
                "location_name": location_name, "enabled": True, "path": full_path
            })
    # Disabled items
    disabled_path = os.path.join(path, DISABLED_FOLDER_NAME)
    if os.path.isdir(disabled_path):
        for filename in os.listdir(disabled_path):
            full_path = os.path.join(disabled_path, filename)
            items.append({
                "type": "folder", "name": filename, "display_name": filename, "command": full_path,
                "location_name": location_name, "enabled": False, "path": full_path
            })
    return items

def toggle_registry_item(item, enable):
    try:
        with winreg.OpenKey(item['hkey'], item['path'], 0, winreg.KEY_ALL_ACCESS) as key:
            value, reg_type = winreg.QueryValueEx(key, item['name'])
            winreg.DeleteValue(key, item['name'])

            new_name = item['display_name'] if enable else DISABLED_PREFIX + item['display_name']
            winreg.SetValueEx(key, new_name, 0, reg_type, value)
        return True
    except (FileNotFoundError, OSError):
        return False

def toggle_folder_item(item, enable):
    try:
        src_path = item['path']
        base_folder = os.path.dirname(src_path)

        if not enable: # Disabling
            dest_folder = os.path.join(base_folder, DISABLED_FOLDER_NAME)
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            shutil.move(src_path, os.path.join(dest_folder, item['name']))
        else: # Enabling
            dest_folder = os.path.dirname(base_folder) # Move to parent folder
            shutil.move(src_path, os.path.join(dest_folder, item['name']))
        return True
    except (OSError, shutil.Error):
        return False