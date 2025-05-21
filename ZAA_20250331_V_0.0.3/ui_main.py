from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QMenuBar, QMenu, QAction
from PyQt5.QtGui import QPixmap
from ui_reaction_analysis import ReactionAnalysisApp
from TPD_analysis import TPD_core
from species_evolution_chasing import SpeciesEvolutionChaseWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Zacros-manually-down-0.1.0V")
        self.setGeometry(100, 100, 400, 400)
        
        # **创建主布局**
        main_layout = QVBoxLayout()
                
        # **创建菜单栏**
        self.menu_bar = QMenuBar(self)
        
        # **创建 File 菜单**
        file_menu = self.menu_bar.addMenu("File")
        open_action = QAction("Open", self)  # 创建一个 "Open" 选项
        open_action.triggered.connect(self.openFileDialog)
        file_menu.addAction(open_action)
        
        exit_action = QAction("Exit", self)  # 创建一个 "Exit" 选项
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        

        # **创建 Plot 菜单**
        plot_menu = self.menu_bar.addMenu("Manually-downscailing")
        plot_action = QAction("Show Plot", self)
        plot_action.triggered.connect(self.openSecondWindow)
        plot_menu.addAction(plot_action)

        # **创建 TPD 菜单**
        TPD_menu = self.menu_bar.addMenu("TPD-plotting")
        TPD_action = QAction("TPD-plotting", self)
        TPD_action.triggered.connect(self.openTPDWindow)
        TPD_menu.addAction(TPD_action)
        
        # **创建 Help 菜单**
        help_menu = self.menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_info)
        help_menu.addAction(about_action)
        label = QLabel(self)
        pixmap = QPixmap("MA.jpg")
        label.setPixmap(pixmap)
        main_layout.addWidget(label)
        self.label = QLabel("", self)
        main_layout.addWidget(self.label)
        # **添加菜单栏到布局**
        main_layout.setMenuBar(self.menu_bar)
        
        
        evolution_menu = self.menu_bar.addMenu("Species Evolution")
        evolution_action = QAction("Chase Evolution", self)
        evolution_action.triggered.connect(self.openSpeciesEvolutionWindow)
        evolution_menu.addAction(evolution_action)

        pattern_menu = self.menu_bar.addMenu("Pattern Design")
        pattern_action = QAction("Open Designer", self)
        pattern_action.triggered.connect(self.openPatternDesigner)
        pattern_menu.addAction(pattern_action)
        self.setLayout(main_layout)

    def openFileDialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.selected_folder = folder_path
            self.label.setText(f"已选择: {folder_path}")

    def show_about_info(self):
        """显示 About 信息"""
        self.label.setText("Zacros Acceleration Assistant v1.0\nCreated by Weitian and Yuhong")
    def openPatternDesigner(self):
        from pattern_design import PatternDesignWindow  # 确保你另一个文件名是 pattern_design.py
        self.pattern_window = PatternDesignWindow()
        self.pattern_window.show()    
    def openSecondWindow(self):
        if self.selected_folder:
            self.second_window = ReactionAnalysisApp(self.selected_folder)
            self.second_window.show()
        else:
            self.label.setText("请先选择一个文件夹！")
   
    def openSpeciesEvolutionWindow(self):
        if hasattr(self, 'selected_folder'):
            self.evolution_window = SpeciesEvolutionChaseWindow(self.selected_folder)
            self.evolution_window.show()
        else:
            self.label.setText("请先选择一个文件夹！")
            
    def openTPDWindow(self):
        if self.selected_folder:
            self.TPD_window = TPD_core(self.selected_folder)
            self.TPD_window.show()
        else:
            self.label.setText("请先选择一个文件夹！")