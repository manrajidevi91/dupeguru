# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""
Sidebar Window for dupeGuru - Modern main window with sidebar navigation.

This module provides the SidebarWindow class which implements
a modern main window design with a left sidebar for navigation
and a main content area for pages.
"""

from PyQt5.QtCore import Qt, QRect, pyqtSlot, QEvent
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QMenu,
    QMenuBar,
    QLabel,
    QFrame,
    QSpacerItem,
    QFileDialog,
    QApplication,
)
from PyQt5.QtGui import QFont

from hscommon.trans import trget
from qt.util import move_to_screen_center, create_actions
from core.app import AppMode
from qt.navigation_rail import NavigationRail
from qt.directories_dialog import DirectoriesDialog
from qt.result_window import ResultWindow
from qt.ignore_list_dialog import IgnoreListDialog
from qt.exclude_list_dialog import ExcludeListDialog
tr = trget("ui")


class WelcomeView(QWidget):
    """Empty-state landing page for the main content area."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.message = QLabel(tr("Add folders and press START SCAN to begin"))
        self.message.setStyleSheet("color: #71717a; font-size: 16px; font-weight: 400;")
        layout.addWidget(self.message)


class SidebarWindow(QMainWindow):
    """Modern main application window with sidebar navigation.
    
    This window implements a navigation rail (sidebar) on the left
    and a stacked widget for content pages on the right, following
    modern UI design patterns.
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(None, **kwargs)
        self.app = app
        self.pages = {}
        self.menubar = None
        self.menuList = set()
        self.last_index = -1
        self.previous_widget_actions = set()
        
        self._setup_ui()
        self._setup_actions()
        self._setup_menu()
        self.app.willSavePrefs.connect(self.appWillSavePrefs)
        
        # Connect theme changes
        if hasattr(self.app, 'theme_manager'):
            self.app.theme_manager.themeChanged.connect(self.apply_theme)
    
    def _setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle(self.app.NAME)
        self.resize(1240, 800)
        
        # Central widget with vertical layout to include Footer
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.root_layout = QVBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        
        # Content Row (Sidebar + Content Stack)
        self.content_row = QWidget()
        self.content_layout = QHBoxLayout(self.content_row)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Create navigation rail (sidebar)
        self.navigation_rail = NavigationRail(self.content_row)
        self.navigation_rail.setObjectName("NavigationRail")
        self.navigation_rail.modeChanged.connect(self._on_mode_changed)
        self.navigation_rail.addFolderClicked.connect(self._on_add_folder_clicked)
        self.navigation_rail.removeFolderClicked.connect(self._on_remove_folder_clicked)
        self.navigation_rail.changeFolderClicked.connect(self._on_change_folder_clicked)
        self.navigation_rail.startScanClicked.connect(self._on_start_scan_clicked)
        self.navigation_rail.scanTypeChanged.connect(self._on_scan_type_changed)
        self.navigation_rail.thresholdChanged.connect(self._on_threshold_changed)
        
        self.content_layout.addWidget(self.navigation_rail)
        
        # Create content area with stacked widget
        self.content_stack = QStackedWidget(self.content_row)
        self.content_layout.addWidget(self.content_stack)
        
        self.root_layout.addWidget(self.content_row)
        
        # 5. Global Footer Bar
        self.footer_bar = QFrame()
        self.footer_bar.setObjectName("FooterBar")
        self.footer_bar.setFixedHeight(28)
        footer_layout = QHBoxLayout(self.footer_bar)
        footer_layout.setContentsMargins(16, 0, 16, 0)
        
        self.status_label = QLabel(tr("Ready"))
        self.status_label.setStyleSheet("color: #a3c9ff; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        footer_layout.addWidget(self.status_label)
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #71717a; font-size: 11px;")
        footer_layout.addWidget(self.stats_label)
        
        footer_layout.addStretch()
        
        doc_link = QLabel(tr("Documentation"))
        doc_link.setStyleSheet("color: #71717a; font-size: 11px;")
        footer_layout.addWidget(doc_link)
        
        sep = QFrame()
        sep.setFixedSize(1, 10)
        sep.setStyleSheet("background: #27272a;")
        footer_layout.addWidget(sep)
        
        privacy_link = QLabel(tr("Privacy Policy"))
        privacy_link.setStyleSheet("color: #71717a; font-size: 11px;")
        footer_layout.addWidget(privacy_link)
        
        self.root_layout.addWidget(self.footer_bar)
        
        # Restore geometry
        self.restore_geometry()
        
        # Setup navigation state
        self._sync_sidebar_state()
    
    def _sync_sidebar_state(self):
        """Sync sidebar UI with application state."""
        # Sync Application Mode
        mode_map = {AppMode.STANDARD: "standard", AppMode.MUSIC: "music", AppMode.PICTURE: "picture"}
        current_mode = self.app.model.app_mode
        self.navigation_rail.set_mode(mode_map.get(current_mode, "standard"))
        
        # Sync Folders
        self._update_sidebar_folders()
        
        # Sync Scan Type
        scan_options = self.app.model.SCANNER_CLASS.get_scan_options()
        scan_type_labels = [so.label for so in scan_options]
        SCAN_TYPE_ORDER = [so.scan_type for so in scan_options]
        selected_scan_type = self.app.prefs.get_scan_type(self.app.model.app_mode)
        current_type_idx = SCAN_TYPE_ORDER.index(selected_scan_type)
        self.navigation_rail.update_scan_types(scan_type_labels, current_type_idx)
        
        # Sync Threshold
        self.navigation_rail.set_threshold(self.app.prefs.filter_hardness)

    def _update_sidebar_folders(self):
        """Update the folder list in the sidebar."""
        folders = [str(f) for f in self.app.model.directories]
        self.navigation_rail.update_folders(folders)

    def _on_mode_changed(self, mode_name):
        mode_map = {"standard": AppMode.STANDARD, "music": AppMode.MUSIC, "picture": AppMode.PICTURE}
        self.app.model.app_mode = mode_map.get(mode_name, AppMode.STANDARD)
        # Update scan types list as they change with mode
        scan_options = self.app.model.SCANNER_CLASS.get_scan_options()
        scan_type_labels = [so.label for so in scan_options]
        SCAN_TYPE_ORDER = [so.scan_type for so in scan_options]
        selected_scan_type = self.app.prefs.get_scan_type(self.app.model.app_mode)
        current_type_idx = SCAN_TYPE_ORDER.index(selected_scan_type)
        self.navigation_rail.update_scan_types(scan_type_labels, current_type_idx)

    def _on_add_folder_clicked(self):
        flags = QFileDialog.ShowDirsOnly
        parent = QApplication.activeWindow()
        directory = QFileDialog.getExistingDirectory(parent, tr("Select Directory"), "", flags)
        if directory:
            self.app.model.add_directory(directory)
            self._update_sidebar_folders()

    def _on_remove_folder_clicked(self, path):
        # Use index-based deletion as Directories doesn't have remove_directory
        dirs = self.app.model.directories
        for i in range(len(dirs)):
            if str(dirs[i]) == path:
                del dirs[i]
                self.app.model.notify("directories_changed")
                break
        self._update_sidebar_folders()

    def _on_change_folder_clicked(self, old_path):
        flags = QFileDialog.ShowDirsOnly
        parent = QApplication.activeWindow()
        new_directory = QFileDialog.getExistingDirectory(parent, tr("Select Directory"), old_path, flags)
        if new_directory:
            # First remove the old one (using index-based deletion)
            dirs = self.app.model.directories
            for i in range(len(dirs)):
                if str(dirs[i]) == old_path:
                    del dirs[i]
                    break
            # Then add the new one
            self.app.model.add_directory(new_directory)
            self._update_sidebar_folders()

    def _on_start_scan_clicked(self):
        self.app.actionStartScanning.trigger()

    def _on_scan_type_changed(self, index):
        scan_options = self.app.model.SCANNER_CLASS.get_scan_options()
        if 0 <= index < len(scan_options):
            self.app.prefs.set_scan_type(self.app.model.app_mode, scan_options[index].scan_type)
            self.app._update_options()

    def _on_threshold_changed(self, value):
        self.app.prefs.filter_hardness = value
        self.app._update_options()
    
    def _setup_actions(self):
        """Setup window actions."""
        # (name, shortcut, icon, desc, func)
        ACTIONS = [
            (
                "actionToggleSidebar",
                "",
                "",
                tr("Show sidebar"),
                self.toggle_sidebar,
            ),
        ]
        create_actions(ACTIONS, self)
        self.actionToggleSidebar.setCheckable(True)
        self.actionToggleSidebar.setChecked(True)
    
    def _setup_menu(self):
        """Setup the menubar."""
        self.menubar = self.menuBar()
        self.menubar.setGeometry(QRect(0, 0, 100, 22))
        
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setTitle(tr("File"))
        self.menuMark = QMenu(self.menubar)
        self.menuMark.setTitle(tr("Mark"))
        self.menuActions = QMenu(self.menubar)
        self.menuActions.setTitle(tr("Actions"))
        self.menuColumns = QMenu(self.menubar)
        self.menuColumns.setTitle(tr("Columns"))
        self.menuView = QMenu(self.menubar)
        self.menuView.setTitle(tr("View"))
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setTitle(tr("Help"))
        
        self.menuView.addAction(self.actionToggleSidebar)
        self.menuView.addSeparator()
        
        self.menuList.add(self.menuFile)
        self.menuList.add(self.menuMark)
        self.menuList.add(self.menuActions)
        self.menuList.add(self.menuColumns)
        self.menuList.add(self.menuView)
        self.menuList.add(self.menuHelp)
    
    def create_page(self, cls, **kwargs):
        """Create a page widget.
        
        Args:
            cls: Page class name or widget class
            **kwargs: Additional arguments for page creation
        
        Returns:
            Created page widget
        """
        app = kwargs.get("app", self.app)
        page = None
        
        if cls == "DirectoriesDialog":
            page = DirectoriesDialog(app)
        elif cls == "ResultWindow":
            parent = kwargs.get("parent", self)
            page = ResultWindow(parent, app)
        elif cls == "IgnoreListDialog":
            parent = kwargs.get("parent", self)
            model = kwargs.get("model")
            page = IgnoreListDialog(parent, model)
            page.accepted.connect(self.on_dialog_accepted)
        elif cls == "ExcludeListDialog":
            app = kwargs.get("app", app)
            parent = kwargs.get("parent", self)
            model = kwargs.get("model")
            page = ExcludeListDialog(app, parent, model)
            page.accepted.connect(self.on_dialog_accepted)
        elif cls == "Dashboard" or cls == "WelcomeView":
            page = WelcomeView(self)
        elif isinstance(cls, type):
            # If it's a class, instantiate it
            page = cls(**kwargs)
        
        if page:
            page_name = cls if isinstance(cls, str) else cls.__name__
            self.pages[page_name] = page
            self.content_stack.addWidget(page)
        
        return page
    
    def add_page(self, page, page_name):
        """Add an existing page to the content stack.
        
        Args:
            page: Page widget
            page_name: Unique name for the page
        """
        self.pages[page_name] = page
        self.content_stack.addWidget(page)
    
    def navigate_to(self, page_name):
        """Navigate to a page by name.
        
        Args:
            page_name: Name of the page to navigate to
        """
        if page_name in self.pages:
            widget = self.pages[page_name]
            index = self.content_stack.indexOf(widget)
            if index >= 0:
                self.content_stack.setCurrentIndex(index)
                self.update_menu_bar(index)
    
    def show_page(self, page):
        """Show a specific page widget.
        
        Args:
            page: Page widget to show
        """
        index = self.content_stack.indexOf(page)
        if index >= 0:
            self.content_stack.setCurrentIndex(index)
            self.update_menu_bar(index)
    
    def index_of_widget(self, widget):
        """Get the index of a widget in the content stack.
        
        Args:
            widget: Widget to find
        
        Returns:
            Index of the widget, or -1 if not found
        """
        return self.content_stack.indexOf(widget)
    
    def get_current_index(self):
        """Get the current page index."""
        return self.content_stack.currentIndex()
    
    def get_widget_at_index(self, index):
        """Get the widget at a specific index.
        
        Args:
            index: Index to get widget from
        
        Returns:
            Widget at the index, or None if index is invalid
        """
        return self.content_stack.widget(index)
    
    def get_count(self):
        """Get the number of pages."""
        return self.content_stack.count()
    
    def update_menu_bar(self, page_index=-1):
        """Update menu bar based on current page.
        
        Args:
            page_index: Index of the current page (-1 for current)
        """
        if page_index < 0:
            return
        
        current_index = self.get_current_index()
        active_widget = self.get_widget_at_index(current_index)
        
        if not active_widget:
            return
        
        if self.last_index < 0:
            self.last_index = current_index
            if hasattr(active_widget, 'specific_actions'):
                self.previous_widget_actions = active_widget.specific_actions
            return
        
        page_type = type(active_widget).__name__
        
        # Update menu enabled states
        for menu in self.menuList:
            if menu in (self.menuColumns, self.menuActions, self.menuMark):
                if not isinstance(active_widget, ResultWindow):
                    menu.setEnabled(False)
                    continue
                else:
                    menu.setEnabled(True)
            
            for action in menu.actions():
                if hasattr(active_widget, 'specific_actions'):
                    if action not in active_widget.specific_actions:
                        if action in self.previous_widget_actions:
                            action.setEnabled(False)
                        continue
                action.setEnabled(True)
        
        # Update specific action states
        self.app.directories_dialog.actionShowResultsWindow.setEnabled(
            False if page_type == "ResultWindow" else self.app.resultWindow is not None
        )
        self.app.actionIgnoreList.setEnabled(
            True if self.app.ignoreListDialog is not None and page_type != "IgnoreListDialog" else False
        )
        self.app.actionDirectoriesWindow.setEnabled(False if page_type == "DirectoriesDialog" else True)
        self.app.actionExcludeList.setEnabled(
            True if self.app.excludeListDialog is not None and page_type != "ExcludeListDialog" else False
        )
        
        if hasattr(active_widget, 'specific_actions'):
            self.previous_widget_actions = active_widget.specific_actions
        self.last_index = current_index
    
    def restore_geometry(self):
        """Restore window geometry from preferences."""
        if self.app.prefs.mainWindowRect is not None:
            self.setGeometry(self.app.prefs.mainWindowRect)
        if self.app.prefs.mainWindowIsMaximized:
            self.showMaximized()
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        visible = self.navigation_rail.isVisible()
        self.navigation_rail.setVisible(not visible)
        self.actionToggleSidebar.setChecked(not visible)
    
    def apply_theme(self):
        """Apply theme changes to the window."""
        # Apply theme to navigation rail
        self.navigation_rail.apply_theme()
        
        # Apply theme to all pages
        for page_name, page in self.pages.items():
            if hasattr(page, 'apply_theme'):
                page.apply_theme()
    
    def on_dialog_accepted(self):
        """Handle dialog accepted signal (remove from stack)."""
        widget = self.sender()
        if widget:
            index = self.index_of_widget(widget)
            if index >= 0:
                self.content_stack.removeWidget(widget)
    
    def appWillSavePrefs(self):
        """Handle application will save preferences signal."""
        prefs = self.app.prefs
        prefs.mainWindowIsMaximized = self.isMaximized()
        if not self.isMaximized():
            prefs.mainWindowRect = self.geometry()
    
    def showEvent(self, event):
        """Handle show event."""
        if not self.isMaximized():
            move_to_screen_center(self)
        super().showEvent(event)
    
    def changeEvent(self, event):
        """Handle change event."""
        if event.type() == QEvent.WindowStateChange and not self.isMaximized():
            move_to_screen_center(self)
        super().changeEvent(event)
    
    def closeEvent(self, close_event):
        """Handle close event."""
        # Force closing of widgets in reverse order
        for index in range(self.get_count() - 1, -1, -1):
            widget = self.get_widget_at_index(index)
            if hasattr(widget, 'closeEvent'):
                widget.closeEvent(close_event)
        self.appWillSavePrefs()