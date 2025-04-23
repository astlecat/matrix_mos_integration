try:
    import PyQt6.QtWidgets as QT
    import PyQt6.QtCore as QTCORE
    import PyQt6.QtGui as QTGUI
except ImportError:
    print('Using PyQt5. Everything might not work as expected')
    import PyQt5.QtWidgets as QT
    import PyQt5.QtCore as QTCORE
    import PyQt5.QtGui as QTGUI

import db
import main as mainfunctions
from main import ConfigManager
import sys
from random import randint


Filters = 'Filters'
manager: ConfigManager = None

def clearlayout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()

    layout.update()

#"ID",
#    "First_Name",
#    "Second_Name",
#    "Third_Name",
#    "Grade_Didgit",
#    "Grade_Letter",
#    "Phone_Number",
#    "Matrix_Login",
#    "Access_tier"


#"ID",
#    "Room_ID",
#    "Grade_Didgits",
#    "Grade_Letter",
#    "Room_Type"



class ConfirmAction(QT.QDialog):

    def __init__(self, parent=None, message="Are you sure"):
        super(ConfirmAction, self).__init__(parent)

        self.setWindowTitle("Confirm action")

        self.label = QT.QLabel(message)
        self.cancelbutton = QT.QPushButton("Cancel")
        self.okbutton = QT.QPushButton("Ok")

        layout = QT.QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 2)

        layout.addWidget(self.okbutton, 1, 0)
        layout.addWidget(self.cancelbutton, 1, 1)

        self.setLayout(layout)

        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton.clicked.connect(self.reject)
        self.rejected.connect(self.Cancel)
        self.accepted.connect(self.Ok)

    def Ok(self):
        self.setResult(1)

    def Cancel(self):
        self.setResult(-1)

class PromotionDialog(QT.QDialog):

    def __init__(self, parent=None):
        super(PromotionDialog, self).__init__(parent)

        self.setWindowTitle("Promote Users")

        self.label = QT.QLabel("Select Access Tier.")
        self.combo = QT.QComboBox()
        self.combo.addItem("Student", 1)
        self.combo.addItem("Moderator", 2)
        self.combo.addItem("Admin", 3)
        self.combo.addItem("Custom", 4)
        self.combo.currentIndexChanged.connect(self.ComboChanged)
        self.spin = QT.QSpinBox()
        self.spin.setMinimum(0)
        self.spin.setMaximum(100)
        self.spin.setHidden(True)
        self.spinlabel = QT.QLabel("Custom Access Tier : ")
        self.spinlabel.setHidden(True)
        self.cancelbutton = QT.QPushButton("Cancel")
        self.okbutton = QT.QPushButton("Ok")

        layout = QT.QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 2)

        layout.addWidget(self.combo, 1, 0, 1, 2)
        layout.addWidget(self.spin, 2, 1, 1, 1)
        layout.addWidget(self.spinlabel, 2, 0, 1, 1)

        layout.addWidget(self.cancelbutton, 3, 1)
        layout.addWidget(self.okbutton, 3, 0)

        self.setLayout(layout)

        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton.clicked.connect(self.reject)
        self.rejected.connect(self.Cancel)
        self.accepted.connect(self.Ok)

    def ComboChanged(self):
        self.combo.currentData()
        if self.combo.currentData() == 4:
            self.spin.setHidden(False)
            self.spinlabel.setHidden(False)
        else:
            self.spin.setHidden(True)
            self.spinlabel.setHidden(True)

    def Ok(self):

        dlg = ConfirmAction(self,"Are you sure you want to promote these users in selected chats?")
        dlg.exec()

        if dlg.result() == 1:
            if self.combo.currentData() == 4:
                self.setResult(int(self.spin.text()))
            elif self.combo.currentData() == 3:
                self.setResult(100)
            elif self.combo.currentData() == 2:
                self.setResult(50)
            elif self.combo.currentData() == 1:
                self.setResult(0)
        else:
            self.reject()

    def Cancel(self):
        self.setResult(-1)

class AddUserDialog(QT.QDialog):

    def __init__(self, parent=None):
        super(AddUserDialog, self).__init__(parent)

        self.setWindowTitle("Register New Users")

        self.label = QT.QLabel("Input User Information.")
        self.okbutton = QT.QPushButton("Ok")
        self.cancelbutton = QT.QPushButton("Cancel")

        self.nameedit = QT.QLineEdit("name")
        self.surnameedit = QT.QLineEdit("surname")
        self.patronicedit = QT.QLineEdit("patronic")
        self.gradeedit = QT.QSpinBox()
        self.gradeedit.setMaximum(11)
        self.gradeedit.setMinimum(1)
        self.letteredit = QT.QLineEdit("A")
        self.letteredit.textChanged.connect(self.LetterEditEdited)
        self.phoneedit = QT.QLineEdit("+7999888777")
        self.phoneedit.textChanged.connect(self.PhoneEditEdited)
        self.loginedit = QT.QLineEdit("login")
        self.passwordedit = QT.QLineEdit("password")
        self.statusedit = QT.QSpinBox()
        self.statusedit.setMinimum(0)
        self.statusedit.setMaximum(100)

        layout = QT.QGridLayout()
        layout.addWidget(self.label, 0, 0)
        layout.addWidget(QT.QLabel("Name : "), 1, 0,)
        layout.addWidget(self.nameedit, 1, 1, 1, 2)
        layout.addWidget(QT.QLabel("Surname : "), 2, 0)
        layout.addWidget(self.surnameedit, 2, 1, 1, 2)
        layout.addWidget(QT.QLabel("Patronic : "), 3, 0)
        layout.addWidget(self.patronicedit, 3, 1, 1, 2)
        layout.addWidget(QT.QLabel("Grade : "), 4, 0)
        layout.addWidget(self.gradeedit, 4, 1)
        layout.addWidget(self.letteredit, 4, 2)
        layout.addWidget(QT.QLabel("Phone : "), 5, 0)
        layout.addWidget(self.phoneedit, 5, 1, 1, 2)
        layout.addWidget(QT.QLabel("Login : "), 6, 0)
        layout.addWidget(self.loginedit, 6, 1, 1, 2)
        layout.addWidget(QT.QLabel("Password : "), 7, 0)
        layout.addWidget(self.passwordedit, 7, 1, 1, 2)
        layout.addWidget(QT.QLabel("Access Tier : "), 8, 0)
        layout.addWidget(self.statusedit, 8, 1, 1, 2)

        layout.addWidget(self.cancelbutton, 10, 2)
        layout.addWidget(self.okbutton, 10, 1)

        self.setLayout(layout)

        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton.clicked.connect(self.reject)
        self.rejected.connect(self.Cancel)
        self.accepted.connect(self.Ok)

    def Ok(self):

        dlg = ConfirmAction(self,"Are you sure you want to create this user?")
        dlg.exec()

        if dlg.result() == 1:
            mainfunctions.bot_add_user(self.nameedit.text(),self.surnameedit.text(),self.patronicedit.text(),self.gradeedit.text(),self.letteredit.text(),self.phoneedit.text(),self.loginedit.text(),self.statusedit.text(),self.passwordedit.text())
        else:
            self.reject()

    def Cancel(self):
        self.setResult(-1)

    def LetterEditEdited(self):
        text = self.letteredit.text().upper()

        text2 = ""
        for x in text:
            if not x in ' 012345679()[]-+=!@#$%&?/\\{};:<>.,|"\'':
                text2 += x

        if len(text2) > 1:
            text2 = text2[-1]

        self.letteredit.setText(text2)

    def PhoneEditEdited(self):
        text = self.phoneedit.text().upper()

        text2 = ""
        for i, x in enumerate(text):
            if x in "0123456789" or i == 0 and x == "+":
                text2 += x

        self.phoneedit.setText(text2)

class AddRoomDialog(QT.QDialog):

    def __init__(self, parent=None):
        super(AddRoomDialog, self).__init__(parent)

        self.setWindowTitle("Create New Rooms")
        self.label = QT.QLabel("Input Room Information.")

        self.okbutton = QT.QPushButton("Ok")
        self.cancelbutton = QT.QPushButton("Cancel")

        self.nameedit = QT.QLineEdit("room name")
        self.gradeedit = QT.QLineEdit("1")
        self.gradeedit.textEdited.connect(self.GradeEditEdited)
        self.letteredit = QT.QLineEdit("А")
        self.letteredit.textEdited.connect(self.LetterEditEdited)
        self.roomtypecombo = QT.QComboBox()
        self.roomtypecombo.addItem("Parents",db.RoomType.PARENTS)
        self.roomtypecombo.addItem("Parents + Teachers", db.RoomType.PARENTS_TEACHER)
        self.roomtypecombo.addItem("Students", db.RoomType.STUDENTS)
        self.roomtypecombo.addItem("Students + Teachers", db.RoomType.STUDENTS_TEACHER)

        layout = QT.QGridLayout()
        layout.addWidget(self.label, 0, 0)
        layout.addWidget(QT.QLabel("Name : "), 1, 0)
        layout.addWidget(self.nameedit, 1, 1, 1, 2)
        layout.addWidget(QT.QLabel("Grade : "), 2, 0)
        layout.addWidget(self.gradeedit, 2, 1)
        layout.addWidget(self.letteredit, 2, 2)
        layout.addWidget(QT.QLabel("Room Type : "), 3, 0)
        layout.addWidget(self.roomtypecombo, 3, 1, 1, 2)

        layout.addWidget(self.cancelbutton, 4, 2)
        layout.addWidget(self.okbutton, 4, 1)

        self.setLayout(layout)

        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton.clicked.connect(self.reject)
        self.rejected.connect(self.Cancel)
        self.accepted.connect(self.Ok)

    def LetterEditEdited(self):
        text = self.letteredit.text().upper()

        text2 = ""
        for x in text:
            if not x in ' 012345679()[]-+=!@#$%&?/\\{};:<>.,|"' + "'":
                text2 += x

        self.letteredit.setText(text2)

    def GradeEditEdited(self):
        text = self.gradeedit.text().replace(" ",",")

        text2 = ""
        for x in text:
            if x in ',0123456789':
                text2 += x

        while ",," in text2:
            text2 = text2.replace(",,",",")


        ls = text2.split(",")

        if ls[-1] != "" and len(ls[-1]) > 2:
            part1 = ls[-1][0:2]
            part2 = ls[-1][3:-1]
            ls[-1] = part1
            ls.append(part2)

        ls2 = []
        for x in ls:
            if x != "" and int(x) < 1:
                ls2.append("1")
            elif x != "" and int(x) > 11:
                ls2.append("11")
            else:
                ls2.append(x)



        self.gradeedit.setText(",".join(ls2))

    def Ok(self):

        dlg = ConfirmAction(self,"Are you sure you want to create this room?")
        dlg.exec()


        if dlg.result() == 1:
            mainfunctions.bot_create_room(self.nameedit.text(),",".join(reversed(list(set(self.gradeedit.text().split(","))))),self.letteredit.text(),self.roomtypecombo.currentData())
        else:
            self.reject()

    def Cancel(self):
        self.setResult(-1)



class Window(QT.QWidget):
    def __init__(self):
        super().__init__()

        self.chatlist = db.get_rooms()

        self.userlist = mainfunctions.bot_get_all_members()

        self.setWindowTitle("Matrix server manager - GUI mode")
        self.setMaximumSize(1500,2000)


        tabs = QT.QTabWidget()

        mainlayout = QT.QGridLayout()
        mainlayout.setAlignment(QTCORE.Qt.AlignmentFlag.AlignTop)

        self.setLayout(mainlayout)


        # First Tab


        self.userfilterarea = QT.QWidget()

        self.uservisible = self.userlist.copy()

        self.usersearchparamswidget = QT.QWidget()
        self.usersearchparamslayout = QT.QGridLayout()
        self.usersearchparamslayout.setAlignment(QTCORE.Qt.AlignmentFlag.AlignTop)
        self.usersearchparamswidget.setLayout(self.usersearchparamslayout)

        self.usersearchbar = QT.QLineEdit()
        self.usersearchbar.setMinimumSize(300, 30)
        self.usersearchbar.setMaximumSize(99999, 30)
        self.usersearchbar.textEdited.connect(self.SearchUsers)

        # User Filters

        self.usersonlyfromchatscheckmark = QT.QCheckBox()
        self.usersonlyfromchatscheckmark.setText("Only from selected chats")
        self.usersonlyfromchatscheckmark.clicked.connect(self.SearchUsers)

        self.userselectallvisible = QT.QPushButton()
        self.userselectallvisible.setText("Select All Users")
        self.userselectallvisible.clicked.connect(self.SelectAllUsers)



        self.usersearchparamslayout.addWidget(self.usersearchbar, 0, 0, 1, 2)
        self.usersearchparamslayout.addWidget(self.usersonlyfromchatscheckmark, 1, 0, 1, 1)
        self.usersearchparamslayout.addWidget(self.userselectallvisible, 1, 1, 1, 1)

        self.useritemlist = QT.QListWidget()
        self.useritemlist.setSizePolicy(QT.QSizePolicy.Policy.Fixed, QT.QSizePolicy.Policy.Expanding)
        self.useritemlist.setMinimumSize(300, 200)
        self.useritemlist.setMaximumSize(99999, 99999)
        self.useritemlist.setVerticalScrollBarPolicy(QTCORE.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.useritemlist.setHorizontalScrollBarPolicy(QTCORE.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.useritemlist.setSelectionMode(QT.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.useritemlist.itemSelectionChanged.connect(self.SearchChats)






        self.userpromotebutton = QT.QPushButton()
        self.userpromotebutton.setText("Promote Selection in Chats")
        self.userpromotebutton.clicked.connect(self.PromoteSelectedUsersInSelectedChats)

        self.userinvitebutton = QT.QPushButton()
        self.userinvitebutton.setText("Invite Selection to Chats")
        self.userinvitebutton.clicked.connect(self.InviteSelectedUsersToSelectedChats)

        self.userkickbutton = QT.QPushButton()
        self.userkickbutton.setText("Kick Selection from Chats")
        self.userkickbutton.clicked.connect(self.KickSelectedUsersFromSelectedChats)

        self.useraddbutton = QT.QPushButton()
        self.useraddbutton.setText("Register user")
        self.useraddbutton.clicked.connect(self.RegisterNewUser)

        self.roomaddbutton = QT.QPushButton()
        self.roomaddbutton.setText("Create room")
        self.roomaddbutton.clicked.connect(self.CreateNewRoom)

        self.generatebutton = QT.QPushButton()
        self.generatebutton.setText("Generate Rooms")
        self.generatebutton.clicked.connect(self.GenerateRooms)

        self.UpdateUsers()


        self.chatvisible = self.chatlist.copy()

        self.chatsearchparamswidget = QT.QWidget()
        self.chatsearchparamslayout = QT.QGridLayout()
        self.chatsearchparamslayout.setAlignment(QTCORE.Qt.AlignmentFlag.AlignTop)
        self.chatsearchparamswidget.setLayout(self.chatsearchparamslayout)

        self.chatsearchbar = QT.QLineEdit()
        self.chatsearchbar.setMinimumSize(300, 30)
        self.chatsearchbar.setMaximumSize(99999, 30)
        self.chatsearchbar.textEdited.connect(self.SearchChats)

        # Chat Filters
        self.chatsonlywithuserscheckmark = QT.QCheckBox()
        self.chatsonlywithuserscheckmark.setText("Only with selected users")
        self.chatsonlywithuserscheckmark.clicked.connect(self.SearchChats)

        self.chatselectallvisible = QT.QPushButton()
        self.chatselectallvisible.setText("Select All Chats")
        self.chatselectallvisible.clicked.connect(self.SelectAllChats)

        self.chatsearchparamslayout.addWidget(self.chatsearchbar, 0, 0, 1, 2)
        self.chatsearchparamslayout.addWidget(self.chatsonlywithuserscheckmark, 1, 0, 1, 1)
        self.chatsearchparamslayout.addWidget(self.chatselectallvisible, 1, 1, 1, 1)



        self.chatitemlist = QT.QListWidget()
        self.chatitemlist.setSizePolicy(QT.QSizePolicy.Policy.Fixed, QT.QSizePolicy.Policy.Expanding)
        self.chatitemlist.setMinimumSize(300, 200)
        self.chatitemlist.setMaximumSize(99999, 99999)
        self.chatitemlist.setVerticalScrollBarPolicy(QTCORE.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.chatitemlist.setHorizontalScrollBarPolicy(QTCORE.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chatitemlist.setSelectionMode(QT.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.chatitemlist.itemSelectionChanged.connect(self.SearchUsers)

        self.UpdateChats()

        mainlayout.addWidget(self.usersearchparamswidget, 0, 0, 1, 2)
        mainlayout.addWidget(self.chatsearchparamswidget, 0, 2, 1, 2)
        mainlayout.addWidget(self.useritemlist, 1, 0, 1, 2)
        mainlayout.addWidget(self.chatitemlist, 1, 2, 1, 2)
        mainlayout.addWidget(self.userpromotebutton, 2, 0, 1, 1)
        mainlayout.addWidget(self.userinvitebutton, 2, 1, 1, 1)
        mainlayout.addWidget(self.userkickbutton, 2, 2, 1, 1)
        mainlayout.addWidget(self.useraddbutton, 3, 0, 1, 2)
        mainlayout.addWidget(self.roomaddbutton, 3, 2, 1, 2)
        mainlayout.addWidget(self.generatebutton, 4, 0, 1, 4)



    def UpdateUsers(self):

        self.useritemlist.clear()
        self.userlist = db.get_students()

        for user in self.userlist:
            name = f'{user["ID"]} {user["Second_Name"]} {user["First_Name"]} {user["Third_Name"]} {user["Grade_Didgit"]}{user["Grade_Letter"]}:  {user["Matrix_Login"]}'
            self.useritemlist.addItem(QT.QListWidgetItem(name))

            # {"ID":1,"First_Name":"Иван","Second_Name":"Иванов","Third_Name":"Иванович","Grade_Didgit":"9","Grade_Letter":"А","Phone_Number":"88005553535","Matrix_Login":"@massivenerd1","Access_tier":"student"}

        self.update()

    def SearchUsers(self):

        searchstring = self.usersearchbar.text().lower()

        if self.chatsonlywithuserscheckmark.isChecked() and self.usersonlyfromchatscheckmark.isChecked():
            self.chatsonlywithuserscheckmark.click()
            self.chatsonlywithuserscheckmark.update()

        leusers = []
        if self.usersonlyfromchatscheckmark.isChecked():
            for x in self.chatitemlist.selectedItems():
                leusers.extend(mainfunctions.get_room_members(':'.join(x.text().split(":")[1:]).strip()))


        for i in range(self.useritemlist.count()):
            self.useritemlist.item(i).setHidden(False)

        for i, user in enumerate(self.userlist):
            user_string = ' '.join([a.lower() for a in map(str, user.values())])
            if not searchstring in user_string:
                self.useritemlist.item(i).setHidden(True)

            if self.usersonlyfromchatscheckmark.isChecked() and not user["Matrix_Login"] in leusers:
                self.useritemlist.item(i).setHidden(True)

    def SelectAllUsers(self):

        self.useritemlist.selectAll()


    def UpdateChats(self):

        self.chatitemlist.clear()
        self.chatlist = db.get_rooms()

        for chat in self.chatlist:
            name = f'{chat["Grade_Didgits"]} {chat["Grade_Letter"]} {chat["Room_Type"]}:  {chat["Room_ID"]}'
            self.chatitemlist.addItem(QT.QListWidgetItem(name))

            # {"ID":1,"Room_ID":1111,"Grade_Didgits":"1","Grade_Letter":"AAA","Room_Type":"Adminroom"}

        self.update()

    def SearchChats(self):

        searchstring = self.chatsearchbar.text().lower()

        if self.chatsonlywithuserscheckmark.isChecked() and self.usersonlyfromchatscheckmark.isChecked():
            self.usersonlyfromchatscheckmark.click()
            self.usersonlyfromchatscheckmark.update()

        lechats = []

        if self.chatsonlywithuserscheckmark.isChecked() and self.chatitemlist.count() > 0:

            for x in [self.chatitemlist.item(x) for x in range(self.chatitemlist.count())]:
                ls = mainfunctions.get_room_members(':'.join(x.text().split(":")[1:]).strip())

                for y in self.useritemlist.selectedItems():
                    if ':'.join(y.text().split(":")[1:]).strip() in ls:
                        lechats.append(':'.join(x.text().split(":")[1:]).strip())

        for i in range(self.chatitemlist.count()):
            self.chatitemlist.item(i).setHidden(False)

        for i, chat in enumerate(self.chatlist):
            chat_string = ' '.join([a.lower() for a in map(str, chat.values())])
            if not searchstring in chat_string:
                self.chatitemlist.item(i).setHidden(True)

            if self.chatsonlywithuserscheckmark.isChecked() and not chat["Room_ID"] in lechats:
                self.chatitemlist.item(i).setHidden(True)

    def SelectAllChats(self):

        self.chatitemlist.selectAll()

    def RegisterNewUser(self):
        dlg = AddUserDialog(self)
        dlg.exec()
        self.UpdateUsers()

    def CreateNewRoom(self):
        dlg = AddRoomDialog(self)
        dlg.exec()
        self.UpdateChats()

    def InviteSelectedUsersToSelectedChats(self):

        dlg = ConfirmAction(self, "Are you sure you want to invite these users to selected chats?")
        dlg.exec()

        if dlg.result() == 1:

            for x in self.chatitemlist.selectedItems():
                RoomID = ':'.join(x.text().split(":")[1:]).strip()
                for y in self.useritemlist.selectedItems():
                    UserID = ':'.join(y.text().split(":")[1:]).strip()
                    mainfunctions.invite_user(UserID,RoomID,"Management Order")

    def KickSelectedUsersFromSelectedChats(self):

        dlg = ConfirmAction(self, "Are you sure you want to kick these users from selected chats?")
        dlg.exec()

        if dlg.result() == 1:

            for x in self.chatitemlist.selectedItems():
                RoomID = ':'.join(x.text().split(":")[1:]).strip()
                for y in self.useritemlist.selectedItems():
                    UserID = ':'.join(y.text().split(":")[1:]).strip()
                    mainfunctions.kick_user(UserID,RoomID,"Management Order")

    def PromoteSelectedUsersInSelectedChats(self):

        dlg = PromotionDialog(self)
        dlg.exec()


        if dlg.result() != -1:

            for x in self.chatitemlist.selectedItems():
                RoomID = ':'.join(x.text().split(":")[1:]).strip()
                for y in self.useritemlist.selectedItems():
                    UserID = ':'.join(y.text().split(":")[1:]).strip()
                    PossibleUsers = mainfunctions.get_room_members(RoomID)
                    if UserID in PossibleUsers:
                        mainfunctions.change_user_power_level(UserID, RoomID, dlg.result())

    def GenerateRooms(self):
        dlg = ConfirmAction(self, "Are you sure you want to generate new rooms?")
        dlg.exec()

        if dlg.result() != -1:
            mainfunctions.generate_rooms()






def main(manager1: ConfigManager):
    global manager
    manager = manager1
    mainfunctions.manager = manager
    app = QT.QApplication(sys.argv)

    window = Window()
    window.show()

    app.exec()


