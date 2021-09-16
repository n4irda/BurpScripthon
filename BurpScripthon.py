
import threading
import re
import time
import json
import importlib
import imp

from burp import IBurpExtender, ITab

from javax.swing import (
    JTable, JTextField, JPanel, JButton, JSeparator, JCheckBox,
    JScrollPane, JSplitPane, JLabel, JTabbedPane, BoxLayout, Box, BorderFactory
)

from javax.swing.table import DefaultTableModel
from java.awt import Color, Dimension
from java.awt.event import MouseAdapter
from java.lang import Math

from os.path import exists, abspath, isfile
from os import makedirs, environ
from os import name as os_name
from os import sep as SEP
from sys import path as import_path


EXTENDER_PATH = abspath(".")
MODULES_DIR = EXTENDER_PATH + "/modules"
import_path.append(MODULES_DIR)

WORK_DIR = environ["HOME"] + "/.BurpScripthon"
SCRIPTS_DIR = WORK_DIR + "/scripts"

if not exists(WORK_DIR):
    makedirs(SCRIPTS_DIR)
    makedirs(WORK_DIR + "/.tmp")

    with open(EXTENDER_PATH + '/scripts/example_1.py', 'rb') as src:
        with open(SCRIPTS_DIR + '/example_1.py', 'wb') as dst:
            dst.write(src.read())

import_path.append(SCRIPTS_DIR)


def handle_path(unix_path):
    if os_name == "window":
        return unix_path.replace("/", "\\")
    return unix_path


class TableMouseEvent(MouseAdapter):
    def __init__(self, extender):
        self._extender = extender
        self.row_selected = None

    def mouseReleased(self, evt):

        if evt.button == 1:
            row = self._extender.table.rowAtPoint(evt.getPoint())
            # col = self._extender.table.columnAtPoint(evt.getPoint())
            self.row_selected = int(self._extender.table.getValueAt(row, 0))
            self._extender.showScriptOut(self.row_selected)


class TextInput(JTextField):
    def __init__(self, *args, **kwargs):
        super(TextInput, self).__init__(*args, **kwargs)
        self.setMaximumSize(Dimension(10000, kwargs.get("height", 25)))


class Script(Box):

    active = False

    rexp = '.*'

    def _on_load(self, reload=False):
        if exists(SCRIPTS_DIR + '/' + self._s_name.text):
            self.tab_panel._import_script(self.id, self._s_name.text, reload)
            self.notification_label.text = " "
        else:
            self.notification_label.text = "File not exist."

    def state_handler(self, touch_event):
        if self.active: self.active = False
        else: self.active = True

        self.tab_panel.script_state_handler(self.id)

    def __init__(self, *args, **kwargs):
        super(Script, self).__init__(*args, **kwargs)
        self.tab_panel = kwargs.get("s_panel")
        self.id = kwargs.get("id")
        self.active = kwargs.get("active", False)

        # self.setLayout(BoxLayout(self, BoxLayout.PAGE_AXIS))
        self.setBorder(BorderFactory.createEmptyBorder(20, 10, 20, 10))

        self.load_btn = JButton('load')
        self.load_btn.addActionListener(lambda *x: self._on_load())

        self.rload_btn = JButton("reload")
        self.rload_btn.addActionListener(lambda *x: self._on_load(reload=True))

        self.remove_btn = JButton('Remove')
        self.remove_btn.setBackground(Color(255, 80, 80))
        self.remove_btn.addActionListener(
            lambda *x: self.tab_panel.remove_script(self.id)
        )

        self.active_btn = JCheckBox("Active", self.active)
        self.active_btn.addActionListener(lambda *x: self.state_handler(x[0]))

        self._s_name = JTextField(kwargs.get('name', ''))
        self._s_name.setMaximumSize(Dimension(300, 25))
        self._s_name.setPreferredSize(Dimension(300, 25))
        script_input = Box.createHorizontalBox()
        # script_input.setAlignmentX(0)
        l_label = JLabel('Script Name: ')
        l_label.setPreferredSize(Dimension(80, 25))
        script_input.add(l_label)
        script_input.add(self._s_name)
        script_input.add(self.active_btn)
        script_input.add(self.load_btn)
        script_input.add(self.rload_btn)
        script_input.add(self.remove_btn)
        script_input.add(Box.createHorizontalGlue())

        self.notification_label = JLabel(" ")
        self.notification_label.setForeground(Color.RED)
        notification_box = Box.createHorizontalBox()
        notification_box.add(Box.createHorizontalStrut(80))
        notification_box.add(self.notification_label)
        notification_box.add(Box.createHorizontalGlue())

        self.add(script_input)
        self.add(JSeparator())
        self.add(notification_box)

        # btn_box = Box.createHorizontalBox()
        # btn_box.add(self.remove_btn)
        # btn_box.add(Box.createHorizontalGlue())
        # self.add(btn_box)


class SettingsPanel(Box):

    def _on_save(self):
        dst = self._s_session_input.text
        if exists(SEP.join(dst.split(SEP)[:-1])):
            self.__scripthon_inst.session.session_file = self._s_label.text = dst
            self.__scripthon_inst.session.save()
            self._session_notification.text = " "
        else:
            self._session_notification.text = "Path for that file does not exist"

    def _on_load(self):
        src = self._l_session_input.text
        if exists(src) and isfile(src):
            self.__scripthon_inst.session.session_file = self._s_label.text = src
            self.__scripthon_inst.load_session()
            self._session_notification.text = " "
        else:
            self._session_notification.text = "File is not a BurpScripthon session."

    def _on_f_apply(self):
        _f = self.__scripthon_inst.session.data["settings"]["filter"]
        _f["ID"] = self._re_field_id.text
        _f["METHOD"] = self._re_field_method.text
        _f["URL"] = self._re_field_url.text
        _f["STATE"] = self._re_field_status.text
        self.__scripthon_inst._reload_table()

    def _on_f_cancel(self):
        _f = self.__scripthon_inst.session.data["settings"]["filter"]
        self._re_field_id.text = _f["ID"]
        self._re_field_method.text = _f["METHOD"]
        self._re_field_url.text = _f["URL"]
        self._re_field_status.text = _f["STATE"]

    def __init__(self, *args, **kwargs):
        super(SettingsPanel, self).__init__(*args, **kwargs)

        self.__scripthon_inst = kwargs.get("scripthon")

        self.rexp = self.__scripthon_inst.session.data["settings"]["filter"]

        self.setBorder(BorderFactory.createEmptyBorder(20, 10, 20, 10))

        # Session actions.
        self._btn_load = JButton("load")
        self._btn_load.addActionListener(lambda *x: self._on_load())

        self._btn_save = JButton("save")
        self._btn_save.addActionListener(lambda *x: self._on_save())

        self._s_label = JLabel(self.__scripthon_inst.session.session_file)
        self._s_label.setPreferredSize(Dimension(200, 30))
        session_info = Box.createHorizontalBox()
        c_label = JLabel("currect session: ")
        c_label.setPreferredSize(Dimension(85, 30))
        session_info.add(c_label)
        session_info.add(Box.createHorizontalGlue())
        session_info.add(self._s_label)
        session_info.add(Box.createHorizontalGlue())

        load_session_box = Box.createHorizontalBox()
        l_label = JLabel("Load session from: ")
        l_label.setPreferredSize(Dimension(85, 30))
        self._l_session_input = TextInput()
        self._l_session_input.setPreferredSize(Dimension(200, 30))
        load_session_box.add(l_label)
        load_session_box.add(self._l_session_input)
        load_session_box.add(self._btn_load)

        save_session_box = Box.createHorizontalBox()
        s_label = JLabel("Save session to: ")
        s_label.setPreferredSize(Dimension(85, 30))
        self._s_session_input = TextInput()
        self._s_session_input.setPreferredSize(Dimension(200, 30))
        save_session_box.add(s_label)
        save_session_box.add(self._s_session_input)
        save_session_box.add(self._btn_save)

        self._session_notification = JLabel("Test")
        self._session_notification.setForeground(Color.RED)
        notification_box = Box.createHorizontalBox()
        notification_box.add(Box.createHorizontalGlue())
        notification_box.add(self._session_notification)
        notification_box.add(Box.createHorizontalGlue())

        self.add(session_info)
        self.add(Box.createRigidArea(Dimension(15, 15)))
        self.add(load_session_box)
        self.add(save_session_box)
        self.add(notification_box)
        self.add(Box.createRigidArea(Dimension(15, 15)))
        sp = JSeparator()
        sp.setMaximumSize(Dimension(10000, 30))
        self.add(sp)
        self.add(Box.createRigidArea(Dimension(15, 15)))

        # filter actions.
        self.add(JLabel("Filter by regular expression."))
        self.add(Box.createRigidArea(Dimension(15, 10)))

        self._re_field_id = TextInput()
        self._re_field_method = TextInput()
        self._re_field_url = TextInput()
        self._re_field_status = TextInput()
        self._on_f_cancel()

        input_1 = Box.createHorizontalBox()
        label_1 = JLabel('ID')
        label_1.setPreferredSize(Dimension(50, 30))
        input_1.add(label_1)
        input_1.add(self._re_field_id)

        input_2 = Box.createHorizontalBox()
        label_2 = JLabel("METHOD")
        label_2.setPreferredSize(Dimension(50, 30))
        input_2.add(label_2)
        input_2.add(self._re_field_method)

        input_3 = Box.createHorizontalBox()
        label_3 = JLabel("URL")
        label_3.setPreferredSize(Dimension(50, 30))
        input_3.add(label_3)
        input_3.add(self._re_field_url)

        input_4 = Box.createHorizontalBox()
        label_4 = JLabel("STATE")
        label_4.setPreferredSize(Dimension(50, 30))
        input_4.add(label_4)
        input_4.add(self._re_field_status)

        self.add(input_1)
        self.add(input_2)
        self.add(input_3)
        self.add(input_4)

        self._f_btn_apply = JButton("apply")
        self._f_btn_apply.addActionListener(lambda *x: self._on_f_apply())

        self._f_btn_cancel = JButton("cancel")
        self._f_btn_cancel.addActionListener(lambda *x: self._on_f_cancel())

        fbtns_box = Box.createHorizontalBox()
        fbtns_box.add(Box.createHorizontalGlue())
        fbtns_box.add(self._f_btn_apply)
        fbtns_box.add(self._f_btn_cancel)

        self.add(Box.createRigidArea(Dimension(15, 10)))
        self.add(fbtns_box)

        self.clear_btn = JButton('clear table')
        self.clear_btn.setBackground(Color(255, 80, 80))
        self.clear_btn.addActionListener(
            lambda *x: self.__scripthon_inst._clear_table()
        )
        sp = JSeparator()
        sp.setMaximumSize(Dimension(10000, 30))
        self.add(sp)
        cbox = Box.createHorizontalBox()
        cbox.add(self.clear_btn)
        cbox.add(Box.createHorizontalGlue())
        self.add(cbox)
        # self.clear_btn.setAli


class ScriptPanel(JPanel):

    scripts = []

    # hold scripts imported as keys.
    imports = {}

    def _on_ptab_scripts(self, *args):
        # sid = self._ptab_scripts.getTitleAt(self._ptab_scripts.getSelectedIndex())
        sid = self._scripthon_inst._tableMouseEvent.row_selected
        if sid:
            self._scripthon_inst.showScriptOut(sid)

    def __init__(self, extender, scripthon_inst, *args, **kwargs):
        super(ScriptPanel, self).__init__(*args, **kwargs)

        self._scripthon_inst = scripthon_inst

        self.setLayout(BoxLayout(self, BoxLayout.PAGE_AXIS))
        self._ptab_scripts = JTabbedPane()
        self._ptab_scripts.setMaximumSize(Dimension(10000, 100))
        self._ptab_scripts.addChangeListener(self._on_ptab_scripts)
        self._ptab_out = JTabbedPane()

        self.add_script_btn = JButton('+')
        self.add_script_btn.setMaximumSize(Dimension(5, 5))
        self.add_script_btn.addActionListener(self.add_script)

        self._ptab_scripts.addTab("...", JPanel())
        self._ptab_scripts.setTabComponentAt(len(self.scripts), self.add_script_btn)

        self.load_scripts(self._scripthon_inst.session.data["scripts"])

        self._script_out = extender._callbacks.createTextEditor()
        self._script_out.setEditable(False)

        self._log = extender._callbacks.createTextEditor()
        # self._log.setEditable(False)

        self._error_log = extender._callbacks.createTextEditor()
        self._error_log.setEditable(False)

        self._setting = SettingsPanel(BoxLayout.PAGE_AXIS, scripthon=scripthon_inst)

        self._ptab_out.addTab("Script Out", self._script_out.getComponent())
        self._ptab_out.addTab("Log", self._log.getComponent())
        self._ptab_out.addTab("Errors", self._error_log.getComponent())
        self._ptab_out.addTab("Setting", self._setting)

        self.add(self._ptab_scripts)
        self.add(self._ptab_out)

    # used to: import python script
    # arguments:
    #   s_id: (int) id of script.
    #   s_name: (str) name of script.
    def _import_script(self, s_id, s_name, reload=False):
        if exists(SCRIPTS_DIR + '/' + s_name) and s_name[-3:] == ".py":
            try:
                if reload:
                    self.imports[s_id] = imp.reload(self.imports[s_id])
                else:
                    self.imports[s_id] = importlib.import_module(
                        s_name.split('.py')[0]
                    )
            except ImportError as e:
                self._error_log.text += str(e) + "\n"

    # used to: load scripts of a session.
    # arguments:
    #   scripts: A list of lists, every list represent data of a script, like
    #           [ script_id, script_object, script_path, script_state]
    def load_scripts(self, scripts):
        if len(self.scripts) > 0:
            indexes = list(range(1, len(self.scripts) + 1))
            indexes.reverse()
            for i in indexes:
                self._ptab_scripts.removeTabAt(i)

            self.scripts = []

        for i in scripts:
            script_inst = Script(
                BoxLayout.PAGE_AXIS, s_panel=self, id=i[0], active=i[3], name=i[2]
            )
            # script_inst = Script(self, i[0], active=i[3], name=i[2])
            self.scripts.append([i[0], script_inst, i[2], i[3]])

            self._import_script(i[0], i[2])

            self._ptab_scripts.addTab(str(i[0]), script_inst)

        self._ptab_scripts.setSelectedComponent(
            self._ptab_scripts.getComponentAt(len(self.scripts))
        )

    def add_script(self, *args):
        if len(self.scripts) > 0:
            script_id = self.scripts[-1][0] + 1
        else:
            script_id = 1

        sd = [script_id, "None", " ", False]
        self.scripts.append([
            sd[0],
            Script(BoxLayout.PAGE_AXIS, s_panel=self, id=sd[0], active=sd[3]),
            sd[2],
            sd[3]]
        )
        self._ptab_scripts.addTab(
            str(script_id), self.scripts[-1][1]
        )
        self._ptab_scripts.setSelectedComponent(
            self._ptab_scripts.getComponentAt(len(self.scripts))
        )
        self._scripthon_inst.session.data["scripts"].append(sd)

    def remove_script(self, script_id):
        session_data = self._scripthon_inst.session.data
        for i in self.scripts:
            if i[0] == script_id:
                self._ptab_scripts.removeTabAt(self.scripts.index(i) + 1)
                s_id = self.scripts.index(i)
                session_data["scripts"].pop(s_id)
                session_data["scripts_out"].pop(s_id)
                self.scripts.remove(i)
                return True

    def script_state_handler(self, script_id):
        session_scripts = self._scripthon_inst.session.data["scripts"]
        for i in self.scripts:
            if i[0] == script_id:
                session_scripts[self.scripts.index(i)][3] = i[3] = i[1].active
                return


class TableModel(DefaultTableModel):

    def isCellEditable(self, *args):
        return False


class Session:

    data = {}

    def default(self):
        self.data = {
            # keys are ids of requests/responses, and values the data (list) for its.
            "table": {},

            "scripts": [],

            "scripts_out": {},

            "log": "",

            "settings": {
                "session_file": "",

                "filter": {
                    "ID": " ",
                    "METHOD": " ",
                    "URL": " ",
                    "STATE": " "
                }
            }
        }

    def setScriptOut(self, script_id, item_id, out):
        script_id = str(script_id)
        item_id = str(item_id)

        if not self.data["scripts_out"].get(script_id):
            self.data["scripts_out"][script_id] = {item_id: out}

        elif not self.data["scripts_out"][script_id].get(item_id):
            self.data["scripts_out"][script_id][item_id] = out + "\r\n"

        else: self.data["scripts_out"][script_id][item_id] += out

    def getScriptOut(self, script_id, item_id):
        script_id = str(script_id)
        item_id = str(item_id)

        try:
            return self.data["scripts_out"][script_id].get(item_id, " ")
        except KeyError:
            return " "

    def save(self):
        with open(self.session_file, 'wb') as fp:
            json.dump(self.data, fp)

    def load(self):
        with open(self.session_file, 'rb') as fp:
            self.data = json.load(fp)

    def __init__(self):
        self.session_file = handle_path(WORK_DIR + "/.tmp/tempsession.json")
        self.default()
        self.data["scripts"] = [[1, "None", "example_1.py", True]]


class BurpScripthon:
    session = Session()

    _ids_map = {}

    # True while session is active
    active = True

    def proxy_listener(self, isRequest, interceptdProxyMessage):
        httpMsg = interceptdProxyMessage.getMessageInfo()
        ss = self.session
        rid = str(interceptdProxyMessage.messageReference)

        if isRequest:
            dt = self.bHelpers.analyzeRequest(httpMsg)
            t_rid = len(ss.data["table"]) + 1
            ss.data["table"][rid] = [t_rid, dt.getMethod(), str(dt.getUrl())]

            # process request with scripts
            for script in self.script_panel.scripts:
                if script[3]:
                    s_id = script[0]
                    try:
                        rs = self.script_panel.imports[s_id].request(httpMsg, self)
                        if rs:
                            ss.setScriptOut(s_id, rid, rs)
                    except KeyError:
                        pass
        else:
            try:
                ss.data["table"][rid].append(self.bHelpers.analyzeResponse(
                    httpMsg.getResponse()).getStatusCode()
                )
            except KeyError:
                return

            # add item to table
            self.add_tItem(ss.data["table"][rid])

            # process response with scripts
            for script in self.script_panel.scripts:
                if script[3]:
                    s_id = script[0]
                    try:
                        rs = self.script_panel.imports[s_id].response(httpMsg, self)
                        if rs:
                            ss.setScriptOut(s_id, rid, rs)
                    except KeyError:
                        pass

    def extender_state_listener(self, *args):
        self.active = False
        self.session.save()

    def showScriptOut(self, rid):
        sp = self.script_panel._ptab_scripts
        if sp.selectedIndex > 0:
            script_id = sp.selectedIndex
            self.script_panel._script_out.text = self.session.getScriptOut(
                script_id, rid
            )

    # used to: check if row pass the filter rules.
    # return: True if pass, else False
    def _is_row_visible(self, row):
        rexps = self.session.data["settings"]["filter"]
        for k in row.keys():
            if not rexps[k].startswith(" ") and not re.match(rexps[k], str(row[k])):
                return False

        return True

    def add_tItem(self, tItem):
        row = {
            "ID": tItem[0],
            "METHOD": tItem[1],
            "URL": tItem[2],
            "STATE": tItem[3]
        }
        if self._is_row_visible(row):
            self.table.getModel().addRow(tItem)

    def _reload_table(self):
        indexes = list(range(self.table.getModel().getRowCount()))
        indexes.reverse()
        for i in indexes:
            self.table.getModel().removeRow(i)

        items = [int(i) for i in self.session.data["table"].keys()]
        items.sort()
        for i in items:
            item = self.session.data["table"][str(i)]
            if len(item) == 4:  # has a response status
                self.add_tItem(item)

    def load_session(self):
        self.session.default()
        self.session.load()

        self.script_panel.load_scripts(self.session.data["scripts"])
        self.script_panel._log.text = self.session.data["log"]
        self.script_panel._setting._on_f_cancel()

        self._reload_table()

    def _clear_table(self, *args):
        self.session.data["table"] = {}
        self.session.data["scripts_out"] = {}
        self._reload_table()

    def log(self, _s):
        _ss = self.bHelpers.bytesToString(self.script_panel._log.text) + _s + "\n"
        self.session.data["log"] = _ss
        self.script_panel._log.text = _ss

    def _saveSessionThread(self):
        while True:
            self.session.save()
            for i in range(60):
                if not self.active: return
                time.sleep(0.5)

    def __init__(self, extender):
        self._extender = extender
        self.bHelpers = extender._helpers
        self.e_callbacks = extender._callbacks

        self._tableMouseEvent = TableMouseEvent(self)
        self.table = JTable(TableModel(["ID", "METHOD", "URL", "STATE"], 0))
        self.table.addMouseListener(self._tableMouseEvent)
        self.table.getColumnModel().getColumn(0).setPreferredWidth(300)
        tWidth = self.table.getPreferredSize().width
        self.table.getColumn("ID").setPreferredWidth(80)
        self.table.getColumn("METHOD").setPreferredWidth(100)
        self.table.getColumn("URL").setPreferredWidth(Math.round(tWidth / 50 * 130))
        self.table.getColumn("STATE").setPreferredWidth(70)

        self._table_scroll = JScrollPane(self.table)

        # self._split = JSplitPane(JSplitPane.HORIZONTAL_SPLIT)
        self._split = JSplitPane(JSplitPane.VERTICAL_SPLIT)
        self._split.setDividerSize(5)
        self._split.setDividerLocation(tWidth)
        # self._split.setLeftComponent(self._table_scroll)
        self._split.setTopComponent(self._table_scroll)

        self.script_panel = ScriptPanel(extender, self)

        self._split.setRightComponent(self.script_panel)

        # extender.registerHttpListener(self.http_listener)
        extender._callbacks.registerProxyListener(self.proxy_listener)
        extender._callbacks.registerExtensionStateListener(
            self.extender_state_listener
        )

        threading.Thread(target=self._saveSessionThread).start()


class BurpScripthonTab(ITab):
    def __init__(self, extender):
        self._extender = extender
        self.ui = BurpScripthon(extender)

    # return caption that should appear on the custom tab.
    def getTabCaption(self):
        return "BurpScripthon"

    # return the component that should be used as contents of the custom tab when.
    def getUiComponent(self):
        return self.ui._split


class BurpExtender(IBurpExtender):

    def registerExtenderCallbacks(self, callbacks):

        self._callbacks = callbacks

        self._helpers = callbacks.getHelpers()

        callbacks.setExtensionName("BurpScripthon")

        callbacks.addSuiteTab(BurpScripthonTab(self))
