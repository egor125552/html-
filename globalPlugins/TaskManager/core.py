# -*- coding: utf-8 -*-

import wx
from . import psutil
import ctypes
from .startup import StartupManagerDialog

class TaskManagerDialog(wx.Dialog):
    def __init__(self, parent):
        super(TaskManagerDialog, self).__init__(parent, title=_("Task Manager"), size=(500, 400))
        self.sort_col = 0
        self.sort_ascending = True
        self.InitUI()
        self.Centre()

    def InitUI(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.process_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.process_list.InsertColumn(0, _("Name"), width=200)
        self.process_list.InsertColumn(1, _("PID"), width=60)
        self.process_list.InsertColumn(2, _("CPU (%)"), width=70)
        self.process_list.InsertColumn(3, _("Memory (MB)"), width=100)
        main_sizer.Add(self.process_list, 1, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        refresh_button = wx.Button(panel, label=_("Refresh"))
        terminate_button = wx.Button(panel, label=_("Terminate Process"))
        terminate_all_button = wx.Button(panel, label=_("Terminate All..."))
        priority_button = wx.Button(panel, label=_("Set Priority"))
        startup_button = wx.Button(panel, label=_("Startup..."))
        close_button = wx.Button(panel, label=_("Close"))

        button_sizer.Add(refresh_button, 0, wx.ALL, 5)
        button_sizer.Add(terminate_button, 0, wx.ALL, 5)
        button_sizer.Add(terminate_all_button, 0, wx.ALL, 5)
        button_sizer.Add(priority_button, 0, wx.ALL, 5)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(startup_button, 0, wx.ALL, 5)
        button_sizer.Add(close_button, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)

        refresh_button.Bind(wx.EVT_BUTTON, self.OnRefresh)
        terminate_button.Bind(wx.EVT_BUTTON, self.OnTerminate)
        terminate_all_button.Bind(wx.EVT_BUTTON, self.OnTerminateAll)
        priority_button.Bind(wx.EVT_BUTTON, self.OnSetPriority)
        startup_button.Bind(wx.EVT_BUTTON, self.OnStartup)
        close_button.Bind(wx.EVT_BUTTON, self.OnClose)
        self.process_list.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)

        self.populate_process_list()

    def populate_process_list(self):
        self.process_list.DeleteAllItems()
        processes_data = get_processes()

        sort_keys = [
            lambda p: (p.get('name') or '').lower(),
            lambda p: p.get('pid', 0),
            lambda p: p.get('cpu_percent') or 0.0,
            lambda p: p.get('memory_info').rss if p.get('memory_info') else 0
        ]
        sort_key_func = sort_keys[self.sort_col]
        sorted_processes = sorted(processes_data, key=sort_key_func, reverse=not self.sort_ascending)

        for proc in sorted_processes:
            index = self.process_list.InsertItem(self.process_list.GetItemCount(), proc.get('name', 'N/A'))
            self.process_list.SetItem(index, 1, str(proc.get('pid', 0)))
            cpu_percent = proc.get('cpu_percent') or 0.0
            self.process_list.SetItem(index, 2, f"{cpu_percent:.1f}")
            mem_info = proc.get('memory_info')
            mem_mb = mem_info.rss / (1024 * 1024) if mem_info else 0
            self.process_list.SetItem(index, 3, f"{mem_mb:.2f}")
            self.process_list.SetItemData(index, proc.get('pid', 0))

    def OnRefresh(self, event):
        self.populate_process_list()

    def OnColClick(self, event):
        col = event.GetColumn()
        if self.sort_col == col:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_col = col
            self.sort_ascending = True
        self.populate_process_list()

    def OnTerminate(self, event):
        selected_item = self.process_list.GetFirstSelected()
        if selected_item == -1:
            wx.MessageBox(_("Please select a process to terminate."), _("Information"), wx.OK | wx.ICON_INFORMATION)
            return
        pid = self.process_list.GetItemData(selected_item)
        if terminate_process(pid):
            wx.MessageBox(_("Process terminated successfully."), _("Success"), wx.OK | wx.ICON_INFORMATION)
            self.populate_process_list()
        else:
            wx.MessageBox(_("Failed to terminate the process. It may have already been closed or you may not have sufficient permissions."), _("Error"), wx.OK | wx.ICON_ERROR)

    def OnSetPriority(self, event):
        selected_item = self.process_list.GetFirstSelected()
        if selected_item == -1:
            wx.MessageBox(_("Please select a process."), _("Information"), wx.OK | wx.ICON_INFORMATION)
            return
        pid = self.process_list.GetItemData(selected_item)
        menu = wx.Menu()
        priorities = {
            _("High"): psutil.HIGH_PRIORITY_CLASS,
            _("Above Normal"): psutil.ABOVE_NORMAL_PRIORITY_CLASS,
            _("Normal"): psutil.NORMAL_PRIORITY_CLASS,
            _("Below Normal"): psutil.BELOW_NORMAL_PRIORITY_CLASS,
            _("Low"): psutil.LOW_PRIORITY_CLASS,
        }
        for label, priority_val in priorities.items():
            menu_item = menu.Append(wx.ID_ANY, label)
            self.Bind(wx.EVT_MENU, lambda evt, p=pid, prio=priority_val: self.OnPrioritySelect(evt, p, prio), menu_item)
        self.PopupMenu(menu)
        menu.Destroy()

    def OnPrioritySelect(self, event, pid, priority):
        if change_process_priority(pid, priority):
            wx.MessageBox(_("Process priority changed successfully."), _("Success"), wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(_("Failed to change process priority. You may not have sufficient permissions."), _("Error"), wx.OK | wx.ICON_ERROR)

    def OnTerminateAll(self, event):
        dlg = wx.MessageDialog(
            self,
            _("This will attempt to terminate all non-critical processes running under your user account. Are you sure you want to continue?"),
            _("Confirm Termination"),
            wx.YES_NO | wx.ICON_WARNING
        )
        if dlg.ShowModal() == wx.ID_YES:
            count = terminate_all_user_processes()
            wx.MessageBox(
                _("{count} processes were terminated.").format(count=count),
                _("Operation Complete"),
                wx.OK | wx.ICON_INFORMATION
            )
            self.populate_process_list()
        dlg.Destroy()

    def OnStartup(self, event):
        dlg = StartupManagerDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnClose(self, event):
        self.Close()

def terminate_all_user_processes():
    """Terminates all non-critical processes for the current user."""
    current_user = psutil.Process().username()
    # Exclude critical processes to avoid system instability
    excluded_processes = {'nvda.exe', 'explorer.exe', 'csrss.exe', 'winlogon.exe', 'dwm.exe'}
    terminated_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['username'] == current_user and proc.info['name'].lower() not in excluded_processes:
                p = psutil.Process(proc.info['pid'])
                p.terminate()
                terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return terminated_count

def get_processes():
    """Returns a list of running processes."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def terminate_process(pid):
    """Terminates a process by its PID."""
    try:
        p = psutil.Process(pid)
        p.terminate()
        return True
    except psutil.NoSuchProcess:
        return False

def change_process_priority(pid, priority):
    """Changes the priority of a process."""
    try:
        p = psutil.Process(pid)
        p.nice(priority)
        return True
    except psutil.NoSuchProcess:
        return False