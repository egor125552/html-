# -*- coding: utf-8 -*-

import globalPluginHandler
from scriptHandler import script
import gui
import wx
from .core import TaskManagerDialog

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self.taskManagerDialog = None

    def showTaskManager(self):
        if not self.taskManagerDialog:
            self.taskManagerDialog = TaskManagerDialog(gui.mainFrame)
        self.taskManagerDialog.Show()
        self.taskManagerDialog.Raise()

    @script(
        description=_("Shows the Task Manager"),
        gesture="kb:NVDA+shift+t"
    )
    def script_showTaskManager(self, gesture):
        wx.CallAfter(self.showTaskManager)

    def terminate(self):
        if self.taskManagerDialog:
            self.taskManagerDialog.Destroy()
        super(GlobalPlugin, self).terminate()