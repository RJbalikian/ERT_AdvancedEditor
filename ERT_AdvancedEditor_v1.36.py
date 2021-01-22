import math
import pandas as pd
import csv
import pathlib
import wx
import matplotlib
import matplotlib.pylab as pL
import matplotlib.pyplot as plt
import matplotlib.backends.backend_wxagg as wxagg
import re
import numpy as np
import scipy
import scipy.interpolate
import sys

#from mpl_toolkits.mplot3d import Axes3D
#import wx.lib.inspection as wxli

class ERTAPP(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, title='ERT Editing',pos=(100,100),size=(500,500))

    #Built from template here: https://wiki.wxpython.org/GridSizerTutorial
    #Set up Panels
        def setUpPanels(self):
            self.topPanel = wx.Panel(self, wx.ID_ANY,size = (1000,10),name='Top Panel')
            self.infoPanel = wx.Panel(self, wx.ID_ANY,size = (1000,50),name='Info Panel')
            self.chartPanel = wx.Panel(self, wx.ID_ANY,size = (1000,500),name='Chart Panel')
            self.bottomPanel= wx.Panel(self, wx.ID_ANY,size = (1000,130),name='Bottom Panel')
    #need to create more panels, see here: https://stackoverflow.com/questions/31286082/matplotlib-in-wxpython-with-multiple-panels

        def titleSetup(self):
            bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (4, 4))
            self.titleIco = wx.StaticBitmap(self.topPanel, wx.ID_ANY, bmp)
            self.title = wx.StaticText(self.topPanel, wx.ID_ANY, 'Advanced ERT Editing')

    #Declare inputs for first row
        def inputSetup(self):
            bmp = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_OTHER, (4, 4))
            self.inputOneIco = wx.StaticBitmap(self.topPanel, wx.ID_ANY, bmp)
            self.labelOne = wx.StaticText(self.topPanel, wx.ID_ANY, 'Input ERT Data')
            self.inputTxtOne = wx.TextCtrl(self.topPanel, wx.ID_ANY, '')
            self.inputTxtOne.SetHint('Enter data file path here')
            self.inputBrowseBtn = wx.Button(self.topPanel, wx.ID_ANY, 'Browse')
            self.Bind(wx.EVT_BUTTON, self.onBrowse, self.inputBrowseBtn)

            self.readInFileBtn = wx.Button(self.topPanel, wx.ID_ANY, 'Read Data')
            self.Bind(wx.EVT_BUTTON, self.onReadIn, self.readInFileBtn)

            self.inputDataType = wx.Choice(self.topPanel, id=wx.ID_ANY,choices=['.DAT (LS)','.TXT (LS)','.DAT (SAS)', '.VTK', '.XYZ'],name='.TXT (LS)')
            self.Bind(wx.EVT_CHOICE,self.onDataType,self.inputDataType)

            self.autoShiftBx = wx.CheckBox(self.topPanel,wx.ID_ANY, 'Auto Shift?')
            self.autoShiftBx.SetValue(True)

            #Row 3 item(s)
            self.TxtProfileName = wx.StaticText(self.infoPanel, wx.ID_ANY, 'Profile Name: ')
            self.TxtProfileRange = wx.StaticText(self.infoPanel, wx.ID_ANY, 'Profile Length: ')
            self.TxtDataPts = wx.StaticText(self.infoPanel, wx.ID_ANY, 'Data Points: ')
            self.TxtBlank = wx.StaticText(self.infoPanel, wx.ID_ANY, '')
            self.TxtBlank2 = wx.StaticText(self.infoPanel, wx.ID_ANY, '')
            self.TxtMinElectSpcng = wx.StaticText(self.infoPanel, wx.ID_ANY, 'Min. Electrode Spacing: ')
            self.TxtProjectName = wx.StaticText(self.infoPanel, wx.ID_ANY, 'Project Name: ')
            self.TxtArray = wx.StaticText(self.infoPanel, wx.ID_ANY, 'Array: ')

            self.msgProfileName = wx.StaticText(self.infoPanel, wx.ID_ANY, '')
            self.msgProfileRange = wx.StaticText(self.infoPanel, wx.ID_ANY, '')
            self.msgDataPts = wx.StaticText(self.infoPanel, wx.ID_ANY, '')

            self.msgMinElectSpcng = wx.StaticText(self.infoPanel, wx.ID_ANY, '')
            self.msgProjectName = wx.StaticText(self.infoPanel, wx.ID_ANY, '')
            self.msgArray = wx.StaticText(self.infoPanel, wx.ID_ANY, '')

    # DataViz Area item(s)
        def dataVizSetup(self):
            self.editSlider = wx.Slider(self.chartPanel, pos=(200,0), id=wx.ID_ANY, style=wx.SL_TOP | wx.SL_AUTOTICKS | wx.SL_LABELS, name='Edit Data')
            self.Bind(wx.EVT_SCROLL, self.onSliderEditEVENT, self.editSlider)

            self.dataVizMsg1 = wx.StaticText(self.chartPanel, wx.ID_ANY, '')
            self.dataVizMsg2 = wx.StaticText(self.chartPanel, wx.ID_ANY, '')
            self.dataVizInput = wx.TextCtrl(self.chartPanel, wx.ID_ANY, '')

            self.dataVizInputBtn = wx.Button(self.chartPanel, -1, "Use Value")
            self.dataVizInputBtn.Bind(wx.EVT_BUTTON, self.ONdataVizInput)

            self.saveEditsBtn = wx.Button(self.chartPanel, -1, "Save Edits")
            self.saveEditsBtn.Bind(wx.EVT_BUTTON, self.ONSaveEdits)
            self.saveEditsBtn.SetBackgroundColour((100,175,100))
            self.currentChart = 'Graph'

            self.editDataChoiceList = ['AppResist','Resistance','Electrode x-Dists','Variance','PctErr','PseudoX','PseudoZ']
            self.editDataChoiceBool = [False]*len(self.editDataChoiceList)
            self.editDataValues = []
            for i in self.editDataChoiceList:
                self.editDataValues.append([0,0])

            self.editDataType = wx.Choice(self.chartPanel, id=wx.ID_ANY,choices=self.editDataChoiceList,name='Edit Data')
            self.editDataType.Bind(wx.EVT_CHOICE, self.onSelectEditDataType)
            self.setEditToggleBtn = wx.ToggleButton(self.chartPanel,wx.ID_ANY,'Unused',size=(25,30))
            self.setEditToggleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onSetEditToggle)
            self.labelMinRem = wx.StaticText(self.chartPanel, wx.ID_ANY, 'Min.')
            self.inputTxtMinRem = wx.TextCtrl(self.chartPanel, wx.ID_ANY,style=wx.TE_PROCESS_ENTER, name='')
            self.inputTxtMinRem.Bind(wx.EVT_TEXT_ENTER, self.onEditDataValueChangeEvent)
            self.labelMaxRem = wx.StaticText(self.chartPanel, wx.ID_ANY,'Max.')
            self.inputTxtMaxRem = wx.TextCtrl(self.chartPanel, wx.ID_ANY,style=wx.TE_PROCESS_ENTER,name= '')
            self.inputTxtMaxRem.Bind(wx.EVT_TEXT_ENTER, self.onEditDataValueChangeEvent)
            self.editTypeToggleBtn = wx.ToggleButton(self.chartPanel,wx.ID_ANY,'Remove',size=(25,50))
            self.editTypeToggleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onEditTypeToggle)
            self.editLogicToggleBtn = wx.ToggleButton(self.chartPanel,wx.ID_ANY,'OR',size=(25,25))
            self.editLogicToggleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.onLogicToggle)
            self.removePtsBtn = wx.Button(self.chartPanel, -1, "Edit Points")
            self.removePtsBtn.Bind(wx.EVT_BUTTON, self.onRemovePts)

            self.electrodeToggleBtn = wx.ToggleButton(self.chartPanel,wx.ID_ANY,'On',size=(25,25))
            self.electrodeToggleBtn.Bind(wx.EVT_TOGGLEBUTTON, self.ONtoggle)

            self.GraphEditBtn = wx.Button(self.chartPanel, -1, "Graphic Editor", size=(100, 30))
            self.GraphEditBtn.Bind(wx.EVT_BUTTON, self.graphChartEvent)

            self.StatEditBtn = wx.Button(self.chartPanel, -1, "Statistical Editor", size=(100, 30))
            self.Bind(wx.EVT_BUTTON, self.statChartEvent, self.StatEditBtn)

            self.addGPSBtn = wx.Button(self.chartPanel, -1, "GPS Data", size=(100, 30))
            self.addGPSBtn.Bind(wx.EVT_BUTTON, self.GPSChartEvent)

            self.addTopoBtn = wx.Button(self.chartPanel, -1, "Topography Data", size=(100, 30))
            self.addTopoBtn.Bind(wx.EVT_BUTTON, self.topoChartEvent)

            self.reviewBtn = wx.Button(self.chartPanel, -1, "Review Edits", size=(100, 15))
            self.reviewBtn.Bind(wx.EVT_BUTTON, self.reviewEvent)

        def bottomAreaSetup(self):
            # Row 4 items
            self.reverseBx = wx.CheckBox(self.bottomPanel,wx.ID_ANY, 'Reverse Profile')
            self.labelGPSIN = wx.StaticText(self.bottomPanel, wx.ID_ANY, 'GPS Data')
            self.inputTxtGPS = wx.TextCtrl(self.bottomPanel, wx.ID_ANY, 'Enter GPS Filepath Here')
            self.inputGPSBtn = wx.Button(self.bottomPanel, wx.ID_ANY, 'Browse')
            self.Bind(wx.EVT_BUTTON, self.onGPSBrowse, self.inputGPSBtn)
            self.Bind(wx.EVT_CHECKBOX, self.onReverse, self.reverseBx)

            self.dataEditMsg = wx.StaticText(self.bottomPanel, wx.ID_ANY, '')

            self.labelTopoIN = wx.StaticText(self.bottomPanel, wx.ID_ANY, 'Topo Data')
            self.inputTxtTopo = wx.TextCtrl(self.bottomPanel, wx.ID_ANY, 'Enter Topo Filepath Here')
            self.inputTopoBtn = wx.Button(self.bottomPanel, wx.ID_ANY, 'Browse')
            self.includeTopoBx = wx.CheckBox(self.bottomPanel,wx.ID_ANY, 'Include Topography')
            self.Bind(wx.EVT_BUTTON, self.onTopoBrowse, self.inputTopoBtn)
            self.Bind(wx.EVT_CHECKBOX, self.onIncludeTopo, self.includeTopoBx)

            #Bottom Row items
            self.saveBtn = wx.Button(self.bottomPanel, wx.ID_ANY, 'Export and Save Data')
            self.cancelBtn = wx.Button(self.bottomPanel, wx.ID_ANY, 'Cancel')
            self.Bind(wx.EVT_BUTTON, self.onExport, self.saveBtn)
            self.Bind(wx.EVT_BUTTON, self.onCancel, self.cancelBtn)


            self.labelExport = wx.StaticText(self.bottomPanel, wx.ID_ANY, 'Export Data')
            self.exportTXT = wx.TextCtrl(self.bottomPanel, wx.ID_ANY, 'Enter Export Filepath Here')
            self.exportDataBtn = wx.Button(self.bottomPanel, wx.ID_ANY, 'Browse')
            self.Bind(wx.EVT_BUTTON, self.onExportBrowse, self.exportDataBtn)

    #Set up chart
        def chartSetup(self):
            self.chartSizer = wx.BoxSizer(wx.VERTICAL)

            self.figure = matplotlib.figure.Figure()
            self.canvas = wxagg.FigureCanvasWxAgg(self.chartPanel, -1, self.figure)

            self.axes = self.figure.add_subplot(111)
            self.axes.set_xlabel('X-Distance (m)')
            self.axes.set_ylabel('Depth (m)')

            self.toolbar = wxagg.NavigationToolbar2WxAgg(self.canvas)

        def sizersSetup(self):
            #Set up sizers
            self.baseSizer       = wx.BoxSizer(wx.VERTICAL)

            self.topSizer        = wx.BoxSizer(wx.VERTICAL)
            self.titleSizer      = wx.BoxSizer(wx.HORIZONTAL)
            self.inputSizer   = wx.BoxSizer(wx.HORIZONTAL)
            #self.readMsgSizer   = wx.BoxSizer(wx.HORIZONTAL)
            self.profileInfoSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.profileTxtSizer1 = wx.BoxSizer(wx.VERTICAL)
            self.profileTxtSizer2 = wx.BoxSizer(wx.VERTICAL)
            self.profileMsgSizer1 = wx.BoxSizer(wx.VERTICAL)
            self.profileMsgSizer2 = wx.BoxSizer(wx.VERTICAL)
            self.profileInfoSizer = wx.BoxSizer(wx.HORIZONTAL)

            self.ctrlSizer = wx.BoxSizer(wx.VERTICAL)
            self.chartSizer = wx.BoxSizer(wx.VERTICAL)
            self.dataVizSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.vizInfoSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.dataEditSizer = wx.BoxSizer(wx.HORIZONTAL)

            self.bottomSizer = wx.BoxSizer(wx.VERTICAL)
            self.GPSSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.TopoSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.botSizer = wx.BoxSizer(wx.HORIZONTAL)

        def addtoSizers(self):
            #Add items to sizers
            self.titleSizer.Add(self.title, 0, wx.ALIGN_CENTER)

            self.inputSizer.Add(self.labelOne, 1,wx.ALIGN_CENTER,5)
            self.inputSizer.Add(self.inputTxtOne, 8,wx.EXPAND,5)
            self.inputSizer.Add(self.inputBrowseBtn,1,wx.ALIGN_CENTER,5)
            self.inputSizer.Add(self.inputDataType,1,wx.ALIGN_CENTER,5)
            self.inputSizer.Add(self.readInFileBtn,1,wx.ALIGN_CENTER,5)
            self.inputSizer.Add(self.autoShiftBx, 1, wx.ALIGN_CENTER, 5)

            #self.readMsgSizer.Add(self.msgLabelOne, 0, wx.ALL,5)

            self.profileTxtSizer1.Add(self.TxtProfileName, 0, wx.ALIGN_LEFT,5)
            self.profileTxtSizer1.Add(self.TxtProfileRange, 0, wx.ALIGN_LEFT,5)
            self.profileTxtSizer1.Add(self.TxtDataPts, 0, wx.ALIGN_LEFT,5)
            self.profileTxtSizer2.Add(self.TxtMinElectSpcng, 0, wx.ALIGN_LEFT,5)
            self.profileTxtSizer2.Add(self.TxtArray, 0, wx.ALIGN_LEFT,5)
            self.profileTxtSizer2.Add(self.TxtProjectName, 0, wx.ALIGN_LEFT,5)

            self.profileMsgSizer1.Add(self.msgProfileName, 0, wx.ALIGN_LEFT,5)
            self.profileMsgSizer1.Add(self.msgProfileRange, 0, wx.ALIGN_LEFT,5)
            self.profileMsgSizer1.Add(self.msgDataPts, 0, wx.ALIGN_LEFT,5)
            self.profileMsgSizer2.Add(self.msgMinElectSpcng, 0, wx.ALIGN_LEFT,5)
            self.profileMsgSizer2.Add(self.msgArray, 0, wx.ALIGN_LEFT,5)
            self.profileMsgSizer2.Add(self.msgProjectName, 0, wx.ALIGN_LEFT,5)

            self.profileInfoSizer.Add(self.profileTxtSizer1, 1,wx.ALL,5)
            self.profileInfoSizer.Add(self.profileMsgSizer1,3,wx.ALL,5)
            self.profileInfoSizer.Add(self.profileTxtSizer2, 1, wx.ALL, 5)
            self.profileInfoSizer.Add(self.profileMsgSizer2, 3, wx.ALL, 5)

            self.topSizer.Add(self.titleSizer,1,wx.ALL,5)
            self.topSizer.Add(self.inputSizer, 2, wx.ALL, 5)
            #self.topSizer.Add(self.readMsgSizer, 1, wx.ALL, 5)

            self.vizInfoSizer.Add(self.dataVizMsg1,16,wx.ALL,5)
            self.vizInfoSizer.Add(self.dataVizMsg2, 24, wx.ALL, 5)
            self.vizInfoSizer.Add(self.electrodeToggleBtn,1,wx.ALL,5)
            self.vizInfoSizer.Add(self.dataVizInput, 1, wx.ALL, 5)
            self.vizInfoSizer.Add(self.dataVizInputBtn,3,wx.ALL,5)
            self.vizInfoSizer.Add(self.saveEditsBtn,3,wx.ALL,5)

            self.ctrlSizer.Add(self.GraphEditBtn, 2, wx.ALL, 5)
            self.ctrlSizer.Add(self.StatEditBtn, 2, wx.ALL, 5)
            self.ctrlSizer.Add(self.addGPSBtn, 2, wx.ALL, 5)
            self.ctrlSizer.Add(self.addTopoBtn, 2, wx.ALL, 5)
            self.ctrlSizer.Add(self.reviewBtn,1,wx.ALL,5)

            self.dataEditSizer.Add(self.editDataType,5, wx.ALL, 5)
            self.dataEditSizer.Add(self.setEditToggleBtn,2,wx.ALL,5)
            self.dataEditSizer.Add(self.labelMinRem, 2, wx.ALL, 5)
            self.dataEditSizer.Add(self.inputTxtMinRem, 3, wx.ALL, 5)
            self.dataEditSizer.Add(self.inputTxtMaxRem, 3, wx.ALL, 5)
            self.dataEditSizer.Add(self.labelMaxRem, 2, wx.ALL, 5)
            self.dataEditSizer.Add(self.editTypeToggleBtn,3,wx.ALL,5)
            self.dataEditSizer.Add(self.editLogicToggleBtn,2,wx.ALL,5)
            self.dataEditSizer.Add(self.removePtsBtn, 3, wx.ALL, 5)

            self.chartSizer.Add(self.vizInfoSizer, 1, wx.ALL, 5)
            self.chartSizer.Add(self.editSlider,1, wx.LEFT | wx.RIGHT | wx.EXPAND,94)
            self.chartSizer.Add(self.canvas, 12, wx.EXPAND)
            self.chartSizer.Add(self.toolbar, 1, wx.EXPAND)
            self.chartSizer.Add(self.dataEditSizer,1,wx.EXPAND)

            self.dataVizSizer.Add(self.ctrlSizer,1,wx.EXPAND)
            self.dataVizSizer.Add(self.chartSizer,6,wx.EXPAND)

            self.GPSSizer.Add(self.dataEditMsg, 2, wx.ALL, 5)
            self.GPSSizer.Add(self.reverseBx, 1, wx.ALL, 5)
            self.GPSSizer.Add(self.labelGPSIN, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            self.GPSSizer.Add(self.inputTxtGPS, 8, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            self.GPSSizer.Add(self.inputGPSBtn, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

            self.TopoSizer.Add(self.includeTopoBx, 2, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            self.TopoSizer.Add(self.labelTopoIN, 1, wx.ALIGN_CENTER_VERTICAL| wx.ALL, 5)
            self.TopoSizer.Add(self.inputTxtTopo, 8, wx.ALIGN_CENTER_VERTICAL| wx.ALL, 5)
            self.TopoSizer.Add(self.inputTopoBtn, 1, wx.ALIGN_CENTER_VERTICAL| wx.ALL, 5)

            self.botSizer.Add(self.labelExport, 1,  wx.ALL, 5)
            self.botSizer.Add(self.exportTXT,6, wx.ALL, 5)
            self.botSizer.Add(self.exportDataBtn,1, wx.ALL, 5)
            self.botSizer.Add(self.cancelBtn, 1,  wx.ALL, 5)
            self.botSizer.Add(self.saveBtn, 1,  wx.ALL, 5)
            #btnSizer.Add(saveEditsBtn,0,wx.ALL,5)

            self.bottomSizer.Add(self.GPSSizer,0, wx.ALIGN_RIGHT | wx.ALL, 5)
            self.bottomSizer.Add(self.TopoSizer,0, wx.ALIGN_RIGHT | wx.ALL, 5)
            self.bottomSizer.Add(self.botSizer,0, wx.ALIGN_RIGHT | wx.ALL, 5)

        def addtoPanels(self):

            self.topPanel.SetSizer(self.topSizer)
            self.infoPanel.SetSizer(self.profileInfoSizer)
            self.chartPanel.SetSizer(self.dataVizSizer)
            self.bottomPanel.SetSizer(self.bottomSizer)

            self.topPanel.Layout()

            self.baseSizer.Add(self.topPanel,1, wx.EXPAND,1)
            self.baseSizer.Add(self.infoPanel,1,wx.EXPAND,1)
            self.baseSizer.Add(self.chartPanel, 10, wx.EXPAND | wx.ALL, 5)
            self.baseSizer.Add(self.bottomPanel, 1, wx.EXPAND | wx.ALL, 1)

            self.SetSizer(self.baseSizer)
            self.SetSize(1100,950)

        def variableInfo(): #To see what the 'global' variables are
            pass
            #self.electxDataIN:  list of all electrode xdistances
            #self.xCols:    list with numbers of columns with x-values, from initial read-in table. varies with datatype
            #self.xData:    list with all x-values of data points
            #self.zData:    list with all z-values of data points (depth)
            #self.values:   list with all resist. values of data points
            #self.inputDataExt: extension of file read in, selected from initial drop-down (default = .dat (LS))
            #self.xDF   :   dataframe with only x-dist of electrodes, and all of them
            #self.dataHeaders: headers from original file read in, used for column names for dataframeIN
            #self.dataListIN: nested list that will be used to create dataframe, with all read-in data
            #self.dataframeIN: initial dataframe from data that is read in
            #self.df:       dataframe formatted for editing, but remaining static as initial input data
            #self.dataframeEDIT: dataframe that is manipulated during editing
            #self.electrodes: sorted list of all electrode xdistances
            #self.electrodesShifted: shifted, sorted list of all electrode xdistances
            #self.electState:list of booleans giving status of electrode (True = in use, False = edited out)
            #self.electrodeElevs: surface elevation values at each electrode
            #self.dataLengthIN: number of measurements in file/length of dataframes
            #self.dataframeEDITColHeaders
            #self.dataShifted: indicates whether data has been shifted

        setUpPanels(self)
        titleSetup(self)
        inputSetup(self)
        dataVizSetup(self)
        bottomAreaSetup(self)
        chartSetup(self)
        sizersSetup(self)
        addtoSizers(self)
        addtoPanels(self)

        #wxli.InspectionTool().Show(self)

#Initial Plot

    def nullFunction(self,event):
        pass

    def onBrowse(self,event):
        with wx.FileDialog(self,"Open Data File", style= wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.dataPath = pathlib.Path(fileDialog.GetPath())
            fName = str(self.dataPath.parent) + '\\' + self.dataPath.name
            self.inputDataExt = self.dataPath.suffix

            try:
                with open(self.dataPath,'r') as datafile:
                    self.inputTxtOne.SetValue(fName)
            except  IOError:
                wx.LogError("Cannot Open File")

        if self.inputDataExt.lower() == '.txt':
            self.inputDataExt = '.TXT (LS)'
            n = 1
        elif self.inputDataExt.lower() == '.dat':
            if self.dataPath.stem.startswith('lr'):
                self.inputDataExt = '.DAT (SAS)'
                n = 2
            else:
                self.inputDataExt = '.DAT (LS)'
                n = 0
        elif self.inputDataExt.lower() == '.vtk':
            self.inputDataExt = '.VTK'
            n=3
        elif self.inputDataExt.lower() == '.xyz':
            self.inputDataExt = '.XYZ'
            n=4
        else:
            wx.LogError("Cannot Open File")

        if self.inputDataExt == '.DAT (LS)' or self.inputDataExt == '.TXT (LS)':
            outPath = self.dataPath.stem.split('-')[0]
        else:
            outPath = self.dataPath.stem.split('.')[0]
            if outPath.startswith('lr'):
                outPath = outPath[2:]
        outPath = outPath +'_pyEdit.dat'

        if self.includeTopoBx.GetValue():
            outPath = outPath[:-4]
            outPath = outPath + "_topo.dat"

        self.exportTXT.SetValue(str(self.dataPath.with_name(outPath)))

        self.inputDataType.SetSelection(n)

        self.readInFileBtn.SetLabelText('Read Data')

    def onGPSBrowse(self,event):
        with wx.FileDialog(self,"Open GPS File", style= wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.GPSpath = pathlib.Path(fileDialog.GetPath())
            gpsFName = str(self.GPSpath.parent) + '\\' + self.GPSpath.name
            self.inputTxtGPS.SetValue(gpsFName)
        self.getGPSVals()

    def getGPSVals(self):
        with open(self.GPSpath) as GPSFile:
            data = csv.reader(GPSFile)

            self.gpsXData = []
            self.gpsYData = []
            self.gpsLabels = []
            for row in enumerate(data):
                if row[0] == 0:
                    pass #headerline
                else:
                    r = re.split('\t+', str(row[1][0]))

                    if row[0] == '':
                        pass
                    else:
                        self.gpsLabels.append(r[2])
                        self.gpsXData.append(float(r[3]))
                        self.gpsYData.append(float(r[4]))

    def onTopoBrowse(self,event):
        with wx.FileDialog(self,"Open Topo File", style= wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.topoPath = pathlib.Path(fileDialog.GetPath())
            topoFName = str(self.topoPath.parent) + '\\' + self.topoPath.name
            self.inputTxtTopo.SetValue(topoFName)
        self.includeTopoBx.SetValue(True)
        self.getTopoVals()
        self.topoText()

    def onIncludeTopo(self,event):
        self.topoText()

    def topoText(self):
        if self.includeTopoBx.GetValue() == True:
            #print('topo' not in self.exportTXT.GetValue())
            if 'topo' not in self.exportTXT.GetValue():
                #print("It's Not in")
                if len(self.exportTXT.GetValue())>0:
                    outPath = self.exportTXT.GetValue()
                    outPath = outPath[:int(len(outPath)-4)]
                    outPath = outPath + "_topo.dat"
                    self.exportTXT.SetValue(outPath)
        elif self.includeTopoBx.GetValue() == False:

            if '_topo' in self.exportTXT.GetValue():
                outPath = self.exportTXT.GetValue()
                #print(outPath)
                strInd = int(outPath.find("_topo"))
                strInd2 = strInd + 5
                outPath = outPath[:strInd]+outPath[strInd2:]
                self.exportTXT.SetValue(outPath)

    def onReverse(self,event):
        self.reverseText()

    def reverseText(self):
        if self.reverseBx.GetValue() == True:
            if '_rev' not in self.exportTXT.GetValue():

                if len(self.exportTXT.GetValue())>0:
                    outPath = self.exportTXT.GetValue()
                    outPath = outPath[:int(len(outPath)-4)]
                    outPath = outPath + "_rev.dat"
                    self.exportTXT.SetValue(outPath)
        elif self.reverseBx.GetValue() == False:

            if '_rev' in self.exportTXT.GetValue():
                outPath = self.exportTXT.GetValue()
                #print(outPath)
                strInd = int(outPath.find("_rev"))
                strInd2 = strInd + 4
                outPath = outPath[:strInd]+outPath[strInd2:]
                self.exportTXT.SetValue(outPath)

    def getTopoVals(self):
        with open(self.topoPath) as topoFile:
            data = csv.reader(topoFile)

            topoXData = []
            topoYData = []
            topoLabels = []
            for row in enumerate(data):
                if row[0] == 0:
                    pass
                else:
                    r = re.split('\t+', str(row[1][0]))
                    if r[0] == '':
                        pass
                    else:
                        topoLabels.append(r[0])
                        topoXData.append(float(r[1]))
                        topoYData.append(float(r[2]))

        self.topoDF = pd.DataFrame([topoXData, topoYData]).transpose()
        self.topoDF.columns = ["xDist", "Elev"]

    def onDataType(self,event):

        self.inputDataExt = self.inputDataType.GetString(self.inputDataType.GetSelection())

        if self.inputDataExt == '.DAT (LS)':
            self.headerlines = 8
        elif self.inputDataExt == '.DAT (SAS)':
            self.headerlines = 5
        elif self.inputDataExt == '.VTK':
            self.headerlines = 5 #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        elif self.inputDataExt == '.XYZ':
            self.header = 5 #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        elif self.inputDataExt =='':
            self.headerlines = 8
        else:
            if len(self.inputTxtOne.GetValue()) > 0:
                try:
                    with open(self.dataPath, 'r') as datafile:
                        filereader = csv.reader(datafile)
                        start = 0

                        for row in enumerate(filereader):
                            if start == 0:
                                if 'N\\tTime' in str(row[1]):
                                    start = 1
                                    self.headerlines = row[0]
                                else:
                                    continue
                            else:
                                continue
                except:
                    self.headerlines = -1
                    wx.LogError('Data File not selected')
            else:
                self.headerlines = -1

    def onReadIn(self, event):
        self.onDataType(self) #initialize number of headerlines to use
        self.dataHeader = []

        filepath = pathlib.Path(self.inputTxtOne.GetValue())
        self.ext = str(filepath.suffix)
        filename = str(filepath.stem)
        self.dataframeEDITColHeaders = ['MeasID','A(x)','A(z)','B(x)','B(z)','M(x)','M(z)','N(x)','N(z)', 'aVal', 'nFac','PseudoX','PseudoZ','Resistance','AppResist','Cycles','Variance','DataLevel','DtLvlMean','PctErr','Keep']

        if self.ext.lower() == '.dat':
            ###############Need to update to fit .txt data format
            dataLst = []
            self.dataLead = []
            self.dataTail = []
            with open(filepath) as dataFile:
                data = csv.reader(dataFile)

                if self.inputDataExt == '.DAT (SAS)':
                    self.dataHeaders = ['M(x)','aVal','nFac','AppResist']

                    i = 0
                    dataList=[]
                    for row in enumerate(data):
                        if row[0]>self.headerlines: #Read in actual data
                            if row[0] > self.headerlines + datalength: #Read in data tail
                                self.dataTail.append(row[1])
                            else:
                                #It sometimes reads the lines differently. Sometimes as a list (as it should) other times as a long string
                                if len(row[1]) < 4:
                                    #Entire row is read as string
                                    dataList.append(re.split(' +', row[1][0]))
                                else:
                                    #Row is read correctly as separate columns
                                    dataList.append(row[1])
                                i+=1

                        else:
                            if row[0] == 3: #Read in data length
                                datalength = float(row[1][0])

                            self.dataLead.append(row[1])#Create data lead variable for later use

                    datalengthIN = i
                    self.fileHeaderDict = {}
                    self.dataListIN = dataList #Formatted global nested list is created of data read in

                    project = self.dataLead[0][0]
                    array = self.dataLead[2][0]

                    if float(array) == 3:
                        array = "Dipole-Dipole"

                    msrmtType = 'Apparent Resistivity'
                    self.fileHeaderDict['Filename'] = filename
                    self.fileHeaderDict['Project'] = project
                    self.fileHeaderDict['minElectSpcng'] = round(float(self.dataLead[1][0]),2)
                    self.fileHeaderDict['Array'] = array
                    self.fileHeaderDict["Type of Measurement"] = msrmtType
                    self.fileHeaderDict['DataPts'] = self.dataLead[3][0]

                    self.dataframeIN = pd.DataFrame(self.dataListIN)

                    #Sometimes the data is read in with an extra column at the beginning. This fixes that.
                    if len(self.dataframeIN.columns) > 4:
                        del self.dataframeIN[0]
                        self.dataframeIN.reindex([0, 1, 2, 3], axis='columns')
                    self.dataframeIN = self.dataframeIN.astype(float)

                    self.dataframeIN.columns = self.dataHeaders

                    self.dataframeCols = [-2, -3, -4, -5, -6, 0, -7, -8, -9, 1, 2, -10, -11, -12, 3, -1, -1, -13, -14, -15,-16]  # neg val ind. colums that need to be calculated
                    self.dataframeEDIT = pd.DataFrame()
                    dataframelength = len(self.dataframeIN.index)
                    nullList = []
                    keepList = []
                    zeroList = []
                    for i in range(0, dataframelength):
                        nullList.append(-1)
                        zeroList.append(0.0)
                        keepList.append(True)

                    # Create dataframe that will be used in editing process (self.dataframeEDIT) one column at a time
                    for item in enumerate(self.dataframeEDITColHeaders):
                        if self.dataframeCols[
                            item[0]] > -1:  # Columns from dataframeIN that are directly read to dataframeEDIT
                            self.dataframeEDIT[item[1]] = self.dataframeIN.iloc[:, self.dataframeCols[item[0]]]
                            self.dataframeEDIT[item[1]] = self.dataframeEDIT[item[1]].astype(float)
                        elif self.dataframeCols[item[0]] == -1:  # Null list (can't calculate)
                            self.dataframeEDIT[item[1]] = nullList
                        elif self.dataframeCols[item[0]] == -2:  # Measure ID
                            for i in range(0, dataframelength):
                                self.dataframeEDIT.loc[i, item[1]] = i
                        elif self.dataframeCols[item[0]] == -3:  # A(x)
                            self.dataframeIN['A(x)'] = self.dataframeIN['M(x)'] + self.dataframeIN['aVal'] + (self.dataframeIN['aVal']*self.dataframeIN['nFac']) + self.dataframeIN['aVal']
                            self.dataframeEDIT['A(x)'] = self.dataframeIN['A(x)']
                        elif self.dataframeCols[item[0]] == -4:  # A(z)
                            self.dataframeEDIT[item[1]] = zeroList
                        elif self.dataframeCols[item[0]] == -5:  # B(x)
                            self.dataframeIN['B(x)'] = self.dataframeIN['M(x)'] + self.dataframeIN['aVal'] + (self.dataframeIN['aVal']*self.dataframeIN['nFac'])
                            self.dataframeEDIT['B(x)'] = self.dataframeIN['B(x)']
                        elif self.dataframeCols[item[0]] == -6:  # B(z)
                            self.dataframeEDIT[item[1]] = zeroList
                        #elif self.dataframeCols[item[0]] == -6:  # M(x)
                            #Reads in directly
                        elif self.dataframeCols[item[0]] == -7:  # M(z)
                            self.dataframeEDIT[item[1]] = zeroList
                        elif self.dataframeCols[item[0]] == -8:  #N(x)
                            self.dataframeIN['N(x)'] = self.dataframeIN['M(x)'] + self.dataframeIN['aVal']
                            self.dataframeEDIT['N(x)'] = self.dataframeIN['N(x)']
                        elif self.dataframeCols[item[0]] == -9:  # N(z)
                            self.dataframeEDIT[item[1]] = zeroList
                        elif self.dataframeCols[item[0]] == -10:  # PseudoX
                            self.dataframeEDIT['PseudoX'] = (((self.dataframeEDIT['A(x)'] + self.dataframeEDIT[
                                'B(x)']) / 2) + ((self.dataframeEDIT['M(x)'] + self.dataframeEDIT['N(x)']) / 2)) / 2
                        elif self.dataframeCols[item[0]] == -11:  # PseudoZ
                            n = self.dataframeEDIT['nFac']
                            a = self.dataframeEDIT['aVal']

                            self.dataframeEDIT['PseudoZ'] = round((((n ** 2) * -0.0018) + 0.2752 * n + 0.1483) * a, 1)
                        elif self.dataframeCols[item[0]] == -12:  #Resistance
                            PI = math.pi
                            n = self.dataframeEDIT['nFac']
                            a = self.dataframeEDIT['aVal']
                            appR = self.dataframeIN['AppResist']

                            if self.fileHeaderDict['Array'] == 'Dipole-Dipole':
                                self.dataframeEDIT['Resistance'] = appR/(PI * n * (n + 1) * (n + 2) * a)
                            else:
                                print(
                                    'Array is not Dipole-Dipole, but Dipole-Dipole k-factor used to calculate App. Resistivity')
                        elif self.dataframeCols[item[0]] == -13:  #DataLevel
                            self.dataframeEDIT['DataLevel'] = nullList
                            uniqueDepths = self.dataframeEDIT['PseudoZ'].unique()
                            uniqueDepths = list(set(uniqueDepths.flatten()))
                            self.dataLevels = len(uniqueDepths)
                            dataLength = len(self.dataframeEDIT['PseudoZ'])
                            for i in range(0, dataLength):
                                self.dataframeEDIT.loc[i, 'DataLevel'] = uniqueDepths.index(
                                    self.dataframeEDIT.loc[i, 'PseudoZ'])
                        elif self.dataframeCols[item[0]] == -14:  #DtLvlMean
                            for i in uniqueDepths:
                                df = self.dataframeEDIT[self.dataframeEDIT.iloc[:, 12] == i]
                                dtLvlMean = df['AppResist'].mean()
                                indexList = df.index.values.tolist()
                                for ind in indexList:
                                    self.dataframeEDIT.loc[ind, 'DtLvlMean'] = dtLvlMean
                        elif self.dataframeCols[item[0]] == -15:  #PctErr
                            self.dataframeEDIT['PctErr'] = (abs(
                                self.dataframeEDIT['DtLvlMean'] - self.dataframeEDIT['AppResist'])) / \
                                                           self.dataframeEDIT['DtLvlMean']
                        elif self.dataframeCols[item[0]] == -16:  #Keep
                            self.dataframeEDIT[item[1]] = keepList
                        else:
                                self.dataframeEDIT[item[1]] = nullList

                elif self.inputDataExt == '.DAT (LS)': # If it's .DAT (LS)
                    self.dataHeaders = ["NoElectrodes",'A(x)', 'A(z)', 'B(x)', 'B(z)', 'M(x)', 'M(z)', 'N(x)', 'N(z)', 'Resistance']
                    datalength=12
                    dataList = []
                    for row in enumerate(data):

                        if row[0]>int(self.headerlines) and row[0] <= float(self.headerlines + datalength):
                            strrow = str(row[1])
                            strrow = strrow[2:-2]

                            splitrow = strrow.split('\\t')

                            if len(splitrow) != 10:
                                newrow = []
                                for i in splitrow:
                                    val = i.strip()
                                    newrow.append(val)

                                    if len(newrow) < 9:
                                        newrow = re.split(' +',newrow[0])

                                    row = [float(i) for i in newrow]
                                dataList.append(row)
                            else:
                                dataList.append(splitrow)

                        elif row[0] <= int(self.headerlines):
                            if isinstance(row[1], list):
                                val = str(row[1])[2:-2]
                            else:
                                val = row[1]
                            self.dataLead.append(val)
                            if row[0] == 6:
                                datalength = float(row[1][0])
                        else:
                            self.dataTail.append(row[1])

                    self.dataListIN = dataList
                    self.fileHeaderDict = {}

                    project = self.dataLead[0]
                    dataFrmt = self.dataLead[2]
                    array = int(self.dataLead[3])
                    if array == 3:
                        array = "Dipole-Dipole"

                    msrmtType = str(self.dataLead[5])
                    if msrmtType.strip() == '0':
                        msrmtType = "Apparent Resistivity"
                    else:
                        msrmtType = 'Resistance'

                    self.fileHeaderDict['Filename'] = filename
                    self.fileHeaderDict['Project'] = project
                    self.fileHeaderDict['minElectSpcng'] = str(round(float(self.dataLead[1]),2))
                    self.fileHeaderDict['Array'] = array
                    self.fileHeaderDict["Type of Measurement"] = msrmtType
                    self.fileHeaderDict['DataPts'] = str(self.dataLead[6])
                    self.fileHeaderDict['DistType'] = str(self.dataLead[7])

                    self.dataframeIN = pd.DataFrame(self.dataListIN)
                    self.dataframeIN.columns = self.dataHeaders

                    self.dataframeCols = [-2, 1, 2, 3, 4, 5, 6, 7, 8, -3, -4, -5, -6, 9, -7, -1, -1, -8, -9, -10, -11]  # neg val ind. colums that need to be calculated
                    self.dataframeEDIT = pd.DataFrame()
                    dataframelength = len(self.dataframeIN.index)
                    nullList = []
                    keepList = []
                    for i in range(0, dataframelength):
                        nullList.append(-1)
                        keepList.append(True)

                    # Create dataframe that will be used in editing process (self.dataframeEDIT) one column at a time
                    for item in enumerate(self.dataframeEDITColHeaders):
                        if self.dataframeCols[item[0]] > -1: #Columns from dataframeIN that are directly read to dataframeEDIT
                            self.dataframeEDIT[item[1]] = self.dataframeIN.iloc[:, self.dataframeCols[item[0]]]
                            self.dataframeEDIT[item[1]] = self.dataframeEDIT[item[1]].astype(float)
                        elif self.dataframeCols[item[0]] == -1: #Null list (can't calculate)
                            self.dataframeEDIT[item[1]] = nullList
                        elif self.dataframeCols[item[0]] == -2:#Measure ID
                            for i in range(0,dataframelength):
                                self.dataframeEDIT.loc[i,item[1]] = i
                        elif self.dataframeCols[item[0]] == -3: #A spacing
                            self.dataframeEDIT[item[1]] = abs(self.dataframeEDIT['A(x)'] - self.dataframeEDIT['B(x)'])
                        elif self.dataframeCols[item[0]] == -4: #N-factor
                            self.dataframeEDIT[item[1]] = abs(self.dataframeEDIT['B(x)'] - self.dataframeEDIT['N(x)']) / self.dataframeEDIT['aVal']
                        elif self.dataframeCols[item[0]] == -5:#PseduoX
                            self.dataframeEDIT['PseudoX'] = (((self.dataframeEDIT['A(x)']+self.dataframeEDIT['B(x)'])/2)+((self.dataframeEDIT['M(x)']+self.dataframeEDIT['N(x)'])/2))/2
                        elif self.dataframeCols[item[0]] == -6: #PseduoZ
                            n = self.dataframeEDIT['nFac']
                            a = self.dataframeEDIT['aVal']
                            self.dataframeEDIT['PseudoZ'] = round((((n**2)*-0.0018)+0.2752*n+0.1483)*a,1)
                        elif self.dataframeCols[item[0]] == -7:#AppResistivity
                            PI = math.pi
                            n = self.dataframeEDIT['nFac']
                            a = self.dataframeEDIT['aVal']
                            R = self.dataframeEDIT['Resistance']

                            if self.fileHeaderDict['Array'] == 'Dipole-Dipole':
                                self.dataframeEDIT['AppResist'] = PI*n*(n+1)*(n+2)*a*R
                            else:
                                print('Array is not Dipole-Dipole, but Dipole-Dipole k-factor used to calculate App. Resistivity')

                        elif self.dataframeCols[item[0]] == -8:  #DataLevel
                            self.dataframeEDIT['DataLevel'] = nullList
                            uniqueDepths = self.dataframeEDIT['PseudoZ'].unique()
                            uniqueDepths = list(set(uniqueDepths.flatten()))
                            self.dataLevels = len(uniqueDepths)
                            dataLength = len(self.dataframeEDIT['PseudoZ'])
                            for i in range(0, dataLength):
                                self.dataframeEDIT.loc[i, 'DataLevel'] = uniqueDepths.index(self.dataframeEDIT.loc[i, 'PseudoZ'])
                        elif self.dataframeCols[item[0]] == -9:  # DtLvlMean
                            for i in uniqueDepths:
                                df = self.dataframeEDIT[self.dataframeEDIT.iloc[:, 12] == i]
                                dtLvlMean = df['AppResist'].mean()
                                indexList = df.index.values.tolist()
                                for ind in indexList:
                                    self.dataframeEDIT.loc[ind, 'DtLvlMean'] = dtLvlMean
                        elif self.dataframeCols[item[0]] == -10:  #PctErr
                            self.dataframeEDIT['PctErr'] = (abs(
                                self.dataframeEDIT['DtLvlMean'] - self.dataframeEDIT['AppResist'])) / \
                                                           self.dataframeEDIT['DtLvlMean']
                        elif self.dataframeCols[item[0]] == -11:  #Keep
                            self.dataframeEDIT[item[1]] = keepList
                        else:
                            self.dataframeEDIT[item[1]] = nullList

            self.readInFileBtn.SetLabelText("Reset Data")

        elif self.ext.lower() == '.txt':

            with open(filepath, 'r') as datafile:
                filereader = csv.reader(datafile)
                start = 0
                end = 0
                fileHeader = []
                data = []

                for row in enumerate(filereader):
                    if start == 0:

                        if row[0] <= 13:
                            fileHeader.append(row[1])
                            fileHeader[row[0]] = fileHeader[row[0]][:]

                        if 'N\\tTime' in str(row[1]):
                            start = 1
                            self.headerlines = row[0]
                            dataHdrTemp = str(row[1])
                            self.dataHeaders = dataHdrTemp[2:-2].split('\\t')
                            self.dataHeaders[1] = dataHdrTemp[1].strip()
                            self.fileHeaderDict = {}

                            for item in fileHeader:
                                if len(item) > 0:
                                    self.fileHeaderDict[str(item[0]).split(":", 1)[0]] = str(item[0]).split(":", 1)[1].strip()

                    elif start == 1 and end == 0:
                        if len(row[1]) > 0:
                            data.append(str(row[1])[2:-1].split('\\t'))
                        else:
                            end = 1
                    else:
                        continue

            self.dataListIN = data
            self.dataframeIN = pd.DataFrame(self.dataListIN)
            self.dataframeCols = [0, 6, 8, 9, 11, 12, 14, 15, 17, -2, -3, 18, 20, 26, 28, 29, 27, -4, -5, -6, -7] #neg val ind. colums that need to be calculated
            self.dataframeEDIT = pd.DataFrame()
            dataframelength = len(self.dataframeIN.index)
            nullList = []
            keepList = []
            for i in range(0, dataframelength):
                nullList.append(-1)
                keepList.append(True)

            # Create dataframe that will be used in editing process (self.dataframeEDIT) one column at a time
            for item in enumerate(self.dataframeEDITColHeaders):
                if self.dataframeCols[item[0]] > -1:
                    #print(item[1])
                    self.dataframeEDIT[item[1]] = self.dataframeIN.iloc[:, self.dataframeCols[item[0]]]
                    self.dataframeEDIT[item[1]] = self.dataframeEDIT[item[1]].astype(float)
                elif self.dataframeCols[item[0]] == -2:
                    self.dataframeEDIT[item[1]] = abs(self.dataframeEDIT['A(x)'] - self.dataframeEDIT['B(x)'])
                elif self.dataframeCols[item[0]] == -3:
                    self.dataframeEDIT[item[1]] = abs(self.dataframeEDIT['N(x)'] - self.dataframeEDIT['M(x)']) / self.dataframeEDIT['aVal']
                elif self.dataframeCols[item[0]] == -4:
                    self.dataframeEDIT['DataLevel'] = nullList
                    uniqueDepths = self.dataframeEDIT['PseudoZ'].unique()
                    uniqueDepths = list(set(uniqueDepths.flatten()))
                    self.dataLevels = len(uniqueDepths)
                    dataLength = len(self.dataframeEDIT['PseudoZ'])
                    for i in range(0, dataLength):
                        self.dataframeEDIT.loc[i, 'DataLevel'] = uniqueDepths.index(self.dataframeEDIT.loc[i, 'PseudoZ'])
                elif self.dataframeCols[item[0]] == -5:
                    for i in uniqueDepths:
                        df = self.dataframeEDIT[self.dataframeEDIT.iloc[:, 12] == i]
                        dtLvlMean = df['AppResist'].mean()
                        indexList = df.index.values.tolist()
                        for ind in indexList:
                            self.dataframeEDIT.loc[ind, 'DtLvlMean'] = dtLvlMean
                elif self.dataframeCols[item[0]] == -6:
                    self.dataframeEDIT['PctErr'] = (abs(self.dataframeEDIT['DtLvlMean'] - self.dataframeEDIT['AppResist'])) / self.dataframeEDIT['DtLvlMean']
                elif self.dataframeCols[item[0]] == -7:
                    self.dataframeEDIT[item[1]] = keepList
                else:
                    self.dataframeEDIT[item[1]] = nullList

            self.dataHeaders[1] = 'MeasTime'
            if len(self.dataHeaders) > 37:
                self.dataHeaders[37] = 'Extra'

            self.dataTail = [0,0,0,0,0,0,0]

            self.dataframeIN.columns = self.dataHeaders

            self.readInFileBtn.SetLabelText("Reset Data")

            self.fileHeaderDict['Filename'] = filename
            self.fileHeaderDict['Project'] = self.fileHeaderDict['Project name']
            self.fileHeaderDict['Array'] = self.fileHeaderDict['Protocol file'][21:-4]
            self.fileHeaderDict['minElectSpcng'] = self.fileHeaderDict['Smallest electrode spacing']
            self.fileHeaderDict['DataPts'] = len(self.dataframeIN)

            self.dataLead = []
            self.dataLead.append(self.fileHeaderDict['Project name'] + "  " + self.fileHeaderDict['Filename'])
            self.dataLead.append(self.fileHeaderDict['minElectSpcng'])
            self.dataLead.append('11') #General Array format
            self.dataLead.append(self.fileHeaderDict['Sub array code']) #tells what kind of array is used
            self.dataLead.append('Type of measurement (0=app.resistivity,1=resistance)')
            self.dataLead.append('0') #Col 26 in .txt (col 28 is app. resistivity)
            self.dataLead.append(self.fileHeaderDict['DataPts'])
            self.dataLead.append('2')
            self.dataLead.append('0')

        elif self.ext.lower() == '.vtk':
            with open(filepath, 'r') as datafile:
                filereader = csv.reader(datafile)
                startLocs = 0
                startData = 0
                startLocInd = 'POINTS'
                startDataInd = 'LOOKUP_TABLE'
                endLocs = 0
                endData = 0
                endLocInd = []
                endDataInd = []
                fileLead = []
                fileMid = []
                fileTail = []
                vtkdata = []
                vtklocs = []
                newrow = []
                xLocPts = []
                yLocPts = []
                zLocPts = []
                vPts = []

                for row in enumerate(filereader):
                    if startLocs == 0:
                        fileLead.append(row[1])
                        fileLead[row[0]] = fileLead[row[0]][:]
                        if startLocInd in str(row[1]):
                            startLocs = 1
                    elif startLocs == 1 and endLocs == 0:
                        if endLocInd == row[1]:
                            endLocs = 1
                        else:
                            newrow = re.split(' +', str(row[1][0]))
                            newrow = newrow[1:]
                            vtklocs.append(newrow)
                    elif startData == 0:
                        fileMid.append(row[1])
                        if startDataInd in str(row[1]):
                            startData = 1
                    elif startData == 1 and endData == 0:
                        if row[1] == endDataInd:
                            endData == 1
                        else:
                            newrow = re.split(' +', str(row[1][0]))
                            newrow = newrow[1:]
                            vtkdata.append(newrow)
                    else:
                        fileTail.append(row[1])
                        fileTail[row[0]] = fileTail[row[0]][:]

            xPtCols = [0,3,6,9]
            yPtCols = [1,4,7,10]
            zPtCols = [2,5,8,11]
            for r in vtklocs:
                Xs = 0.0
                for x in xPtCols:
                    Xs = Xs + float(r[x])
                xLocPts.append(Xs/4.0)

                Ys = 0.0
                for y in yPtCols:
                    Ys = Ys + float(r[y])
                yLocPts.append(Ys/4.0)

                Zs = 0.0
                for z in zPtCols:
                    Zs = Zs + float(r[z])
                zLocPts.append(Zs/4)

            for d in vtkdata:
                for i in d:
                    vPts.append(i)

            self.dataframeIN = pd.DataFrame([xLocPts, yLocPts, zLocPts, vPts]).transpose()
            self.dataframeIN.columns = ['X','Y','Z','Resistivity']
            print(self.dataframeIN)
            #Format vtk file

            self.fileHeaderDict = {}
            self.fileHeaderDict['Filename'] = filename
            self.fileHeaderDict['Project'] = 'NA'
            self.fileHeaderDict['Array'] = 'NA'
            self.fileHeaderDict['minElectSpcng'] = str(round(self.dataframeIN.loc[1,'X'] - self.dataframeIN.loc[0,'X'],1))
            self.fileHeaderDict['DataPts'] = len(self.dataframeIN)

        elif self.ext.lower() == '.xyz':#!!!!!!!!!!!!!!!!
            with open(filepath, 'r') as datafile:
                filereader = csv.reader(datafile)
                start = 0
                startIndicator = 'Elevation'
                end = 0
                endIndicator = '/'
                fileHeader = []
                data = []


                for row in enumerate(filereader):
                    if start == 0:
                        fileHeader.append(row[1])
                        fileHeader[row[0]] = fileHeader[row[0]][:]
                        if startIndicator in str(row[1]):
                            start = 1
                    elif start == 1 and end == 0:
                        if endIndicator in str(row[1]):
                            end = 1
                        else:
                            data.append(str(row[1])[2:-1].split('\\t'))
                    else:
                        continue

            ######format xyz input

        else:
            self.datVizMsg2.SetLabelText("Filepath Error. Must be .DAT, .TXT, .VTK, or .XYZ file")

        self.dataLengthIN = len(self.dataframeIN.iloc[:,0])

        self.read = 0
        self.generateXY()
        self.generateProfileInfo()
        self.graphChart()
        self.read = 1

    def generateXY(self):
        self.xCols = []
        aVals = []
        nFacs = []
        yCols = []
        valCols = []

        self.xData = []
        self.yData = []
        self.zData = []
        self.values = []


        if self.inputDataExt == '.DAT (SAS)' or self.inputDataExt == '.DAT (LS)' or self.inputDataExt == '.TXT (LS)':
            self.xCols = [11]
            self.electrodeCols = [1,3,5,7]
            aVals = 9
            nFacs = 10
            zCols = 12
            valCols = 14 #13 is resistance; 14 is app. resistivity

            if self.autoShiftBx.GetValue():
                startPt = []
                for c in self.electrodeCols:
                    startPt.append(float(self.dataframeEDIT.iloc[:,c].min()))
                startPt = min(startPt)

                if startPt != 0:
                    self.dataShifted = True
                    for c in self.electrodeCols:
                        for i in enumerate(self.dataframeEDIT.iloc[:,c]):
                            self.dataframeEDIT.iloc[i[0],c] = float(i[1]) - float(startPt)

                    if self.inputDataExt == '.DAT (LS)' or self.inputDataExt == '.TXT (LS)':
                        outPath = self.dataPath.stem.split('-')[0]
                    elif self.inputDataExt == '.DAT (SAS)':
                        outPath = self.dataPath.stem.split('.')[0]
                        if outPath.startswith('lr'):
                            outPath = outPath[2:]
                    outPath = outPath + '_shift_pyEdit.dat'
                    self.exportTXT.SetValue(str(self.dataPath.with_name(outPath)))
                else:
                    self.dataShifted = False


            if self.includeTopoBx.GetValue():
                outPath = self.exportTXT.GetValue()[:-4]
                outPath = outPath + "_topo.dat"
                self.exportTXT.SetValue(outPath)

            #Get all electrode xDistances
            self.electxDataIN = []
            for c in self.electrodeCols:
                for row in self.dataframeEDIT.iloc[:,c]:
                    self.electxDataIN.append(round(float(row),0))

            xDataIN = self.dataframeEDIT.iloc[:,self.xCols[0]].to_list()
            for item in xDataIN:
                self.xData.append(float(item))

            zDataIN = self.dataframeEDIT.iloc[:,zCols].to_list()
            for item in zDataIN:
                self.zData.append(float(item))

            valIN = self.dataframeEDIT.iloc[:,valCols].to_list()
            for item in valIN:
                self.values.append(float(item))

            xDistCols = ['B(x)', 'A(x)', 'N(x)', 'M(x)']

            xDF = pd.DataFrame(self.dataframeIN.loc[:,xDistCols[:]])
            xDF.columns = xDistCols
            xDF = xDF.astype(float)
            self.xDF = pd.DataFrame()

            self.xDF['A(x)'] = xDF['A(x)']
            self.xDF['B(x)'] = xDF['B(x)']
            self.xDF['M(x)'] = xDF['M(x)']
            self.xDF['N(x)'] = xDF['N(x)']

            xList = []
            for item in xDistCols:
                xDistList = self.dataframeIN.loc[:,item].to_list()

                for item in xDistList:
                    xList.append(float(item))

            #print(self.dataframeIN)

            minvals = self.xDF.min()
            self.minXDist = minvals.min()
            maxvals = self.xDF.max()
            self.maxXDist = maxvals.max()
            #self.minXDist = min(self.xData)
            #self.maxXDist = max(self.xData)
            self.minDepth = min(self.zData)
            self.maxDepth = max(self.zData)
            self.maxResist = max(self.values)

        elif self.inputDataExt == '.VTK':
            self.dataframeIN = self.dataframeIN.astype(float)
            for i in range(0,len(self.dataframeIN)):
                self.xData.append(self.dataframeIN.loc[i,'X'])
                self.yData.append(self.dataframeIN.loc[i,'Y'])
                self.zData.append(self.dataframeIN.loc[i,'Z'])
                self.values.append(self.dataframeIN.loc[i,"Resistivity"])

                self.minXDist = min(self.xData)
                self.maxXDist = max(self.xData)
                self.minDepth = min(self.zData)
                self.maxDepth = max(self.zData)
                self.maxResist = max(self.values)

        elif self.inputDataExt == '.XYZ':
            pass

        else:
            pass

        if self.zData[0] < 0:
            for i in enumerate(self.zData):
                self.zData[i[0]] = self.zData[i[0]]*-1

        self.maxDepth = max(self.zData)
        self.minResist = min(self.values)
        self.maxResist = max(self.values)
        self.fileHeaderDict['DataPts'] = len(self.dataframeIN)


        dt = []
        dt.append(self.xData)
        dt.append(self.zData)
        dt.append(self.values)
        cols = ['xDist', 'Depth', 'Value']

        df = pd.DataFrame(dt)
        df = df.transpose()
        df.columns = cols


        if self.inputDataExt =='.XYZ' or self.inputDataExt == '.VTK':
            for i in range(0,len(self.dataframeIN)):
                self.df = df.copy()
                self.df.loc[i,"DtLvlMean"] = 0.0
                self.df.loc[i,'PctErr'] = 0.0
                self.df.loc[i,'MeasID'] = i
                self.electxDataIN = self.xData
                self.electxDataIN = [float(i) for i in self.electxDataIN]
                self.electxDataIN = sorted(set(self.electxDataIN))
        else:
            pass

        xDataINList = []
        self.electrodes = []
        for i in self.electxDataIN:
            xDataINList.append(round(i,0))
        self.electrodes = sorted(xDataINList)
        self.electState = []
        for i in self.electrodes:
            self.electState.append(bool(i*0+1))

        print(self.electrodes)

        self.electrodesShifted = []
        if self.dataShifted:
            for e in self.electrodes:
                self.electrodesShifted.append(e-startPt)

        self.dataEditMsg.SetLabelText(str(len(self.dataframeEDIT)) + ' data pts')

    def generateProfileInfo(self):

        self.msgProfileName.SetLabelText(str(self.fileHeaderDict['Filename']))
        self.msgProfileRange.SetLabelText(str(round(self.minXDist,0)) + " - " + str(round(self.maxXDist,0)))
        self.msgDataPts.SetLabelText(str(self.fileHeaderDict['DataPts']))
        self.msgArray.SetLabelText(str(self.fileHeaderDict['Array']))

        self.msgProjectName.SetLabelText(str(self.fileHeaderDict['Project']))
        self.msgMinElectSpcng.SetLabelText(str(self.fileHeaderDict['minElectSpcng']))

        self.electrodeToggleBtn.SetValue(True)
        self.electrodeToggleBtn.SetBackgroundColour((0, 255, 0))
        self.sliderVal = self.editSlider.GetValue()
        self.dataVizMsg2.SetLabelText('Electrode at ' + str(self.sliderVal) + ' m')

    def graphChartEvent(self, event):
        self.graphChart()

    def graphChart(self):
        self.editSlider.Show()

        if self.currentChart != 'Graph':
            self.editSlider.SetValue(0)
        self.currentChart = 'Graph'

        self.dataVizMsg1.SetLabelText('Graphical Editing Interface')
        self.saveEditsBtn.Hide()
        self.dataVizInput.Show()
        self.dataVizInputBtn.Show()
        self.electrodeToggleBtn.Show()

        x = []
        z = []
        v = []
        pe = []
        n1 = []
        n2 = []

        KeepList = self.dataframeEDIT['Keep'].to_list()
        peList = self.dataframeEDIT['PctErr'].to_list()

        for i in enumerate(KeepList):
            if i[1]:
                x.append(self.dataframeEDIT.loc[i[0],'PseudoX'])
                z.append(self.dataframeEDIT.loc[i[0],'PseudoZ'])
                v.append(self.dataframeEDIT.loc[i[0],'AppResist'])
                pe.append(peList[i[0]])

        self.axes.clear()

        if 'scipy.interpolate' in sys.modules:
            self.makeColormesh(x,z,v, pe,n1,n2)
        else:
            ptSize = round(100/self.maxXDist*125,1)
            self.axes.scatter(x,z, c=v,edgecolors='black',s=ptSize, marker='h')

    def makeColormesh(self,x,z,v, pe,xOmit,zOmit):

        for i in enumerate(v):
            v[i[0]] = abs(float(i[1]))

        xi, zi = np.linspace(min(x), max(x), 300), np.linspace(min(z), max(z), 300)
        xi, zi = np.meshgrid(xi, zi)

        vi = scipy.interpolate.griddata((x, z), v, (xi, zi), method='linear')

        ptSize = round(100 / self.maxXDist * 35, 1)

        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        cmap = pL.cm.binary
        my_cmap = cmap(np.arange(cmap.N))
        my_cmap[:,-1] = np.linspace(0,1,cmap.N)
        #my_cmap = cmap(np.arange(pe))
        #my_cmap[:,-1] = np.linspace(0,1,pe)
        my_cmap = matplotlib.colors.ListedColormap(my_cmap)

        vmax = np.percentile(v, 98)
        vmin = np.percentile(v, 2)
        minx = min(x)
        maxx = max(x)
        minz = min(z)
        maxz = max(z)

        norm = matplotlib.colors.LogNorm(vmin = vmin, vmax = vmax)
        #im = self.axes.imshow(vi, vmin=vmin, vmax=vmax, origin='lower',
        im = self.axes.imshow(vi, origin='lower',
                    extent=[minx, maxx, minz, maxz],
                    aspect='auto',
                    cmap='nipy_spectral',
                    norm = norm,
                    interpolation='bilinear')
        self.figure.colorbar(im, orientation='horizontal')

        if self.currentChart == 'Graph':
            self.axes.scatter(x, z, c=pe, edgecolors=None, s=ptSize, marker='o', cmap=my_cmap)
            if abs(self.minDepth) < 10 :
                self.axes.set_ylim(self.maxDepth * 1.15, 0)
            else:
                depthrange = abs(self.maxDepth-self.minDepth)
                self.axes.set_ylim(self.minDepth-(depthrange*0.05), self.maxDepth + (depthrange*0.05))
            self.axes.set_xlabel('X-Distance (m)')
            self.axes.set_ylabel('Depth (m)')
            self.axes.xaxis.tick_top()

            self.editSlider.SetMax(int(self.maxXDist))
            self.editSlider.SetMin(int(self.minXDist))

            self.editSlider.SetTickFreq(5)

            self.canvas.draw()

        elif self.currentChart == 'Review':
            self.axes.scatter(xOmit, zOmit, c='black', s=ptSize/1.5, marker='x')
            if abs(self.minDepth) < 10 :
                self.axes.set_ylim(self.maxDepth * 1.15, 0)
            else:
                depthrange = abs(self.maxDepth - self.minDepth)
                self.axes.set_ylim(self.minDepth - (depthrange * 0.05), self.maxDepth + (depthrange * 0.05))
            self.axes.set_xlabel('X-Distance (m)')
            self.axes.set_ylabel('Elev/Depth (m)')
            self.axes.xaxis.tick_top()

        self.canvas.draw()



        #self.axes.scatter(x, z, c=pe, edgecolors='none', s=ptSize, marker='h', alpha=0.5, cmap='binary')

    def statChartEvent(self,event):
        self.statChart()

    def statChart(self):

        self.dataVizMsg1.SetLabelText('Statistical Editing Interface')
        self.dataVizMsg2.SetLabelText('Move slider to % err upper limit')

        self.currentChart = 'Stat'
        self.saveEditsBtn.Show()
        self.dataVizInput.Show()
        self.editSlider.Show()
        self.dataVizInputBtn.Show()
        self.electrodeToggleBtn.Hide()

        peIndex =  int(self.dataframeEDIT.columns.get_loc('PctErr'))

        KeepList = self.dataframeEDIT.loc[:,'Keep'].to_list()
        peList = self.dataframeEDIT.iloc[:,peIndex].to_list()

        pctErr = []
        for i in enumerate(KeepList):
            if i[1]:
                pctErr.append(float(peList[i[0]]) * 100)

        self.editSlider.SetMin(0)
        self.editSlider.SetMax(int(max(pctErr)))
        self.editSlider.SetValue(int(max(pctErr)))
        self.editSlider.SetTickFreq(1)

        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        self.axes.hist(pctErr, bins=30)
        self.axes.set_xlim(0, max(pctErr)*1.1)
        self.axes.xaxis.tick_bottom()

        self.canvas.draw()

    def GPSChartEvent(self,event):
        self.GPSChart()

    def GPSChart(self):
        self.editSlider.Hide()
        self.electrodeToggleBtn.Hide()
        self.dataVizInput.Hide()
        self.dataVizInputBtn.Hide()
        self.saveEditsBtn.Hide()

        self.currentChart = 'GPS'
        self.dataVizMsg1.SetLabelText('GPS Data Viewer')
        if len(self.GPSpath.stem) < 1:
            self.GPSpath = ''
        self.dataVizMsg2.SetLabelText(str(self.GPSpath.stem))

        self.getGPSVals()

        self.figure.clear()
        self.axes = self.figure.add_subplot(111)

        xRange = max(self.gpsXData) - min(self.gpsXData)
        yRange = max(self.gpsYData) - min(self.gpsYData)

        if xRange!=0:
            slope = abs(yRange/xRange)
        else:
            slope = 1000

        if slope < 1:
            if slope < 0.2:
                xFact = 0.2
                yFact = 5
            elif slope < 0.6:
                xFact = 0.2
                yFact = 3
            else:
                xFact = 0.2
                yFact = 1
        else:
            if slope > 4:
                xFact = 5
                yFact = 0.2
            elif slope > 2:
                xFact = 3
                yFact = 0.2
            else:
                xFact = 1
                yFact = 0.2

        lowXlim = min(self.gpsXData) - xFact*xRange
        upXlim = max(self.gpsXData) + xFact*xRange
        lowYlim = min(self.gpsYData) - yFact*yRange
        upYlim = max(self.gpsYData) + yFact*yRange


        tick_spacing = 100
        self.axes.scatter(self.gpsXData,self.gpsYData, s=20, marker='h')
        self.axes.plot(self.gpsXData, self.gpsYData)
        self.axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(tick_spacing))
        self.axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(tick_spacing))
        self.axes.ticklabel_format(axis='both',style='plain')
        self.axes.grid(which='major', axis='both',color=(0.8,0.8,0.8))
        self.axes.set_xlim(lowXlim,upXlim)
        self.axes.set_ylim(lowYlim,upYlim)
        self.axes.set_xlabel('UTM Easting')
        self.axes.set_ylabel('UTM Northing')
        self.axes.xaxis.tick_bottom()

        self.canvas.draw()

    def topoChartEvent(self,event):
        self.topoChart()

    def topoChart(self):
        self.editSlider.Hide()
        self.electrodeToggleBtn.Hide()
        self.dataVizInput.Hide()
        self.dataVizInputBtn.Hide()
        self.saveEditsBtn.Hide()

        self.currentChart = 'Topo'
        self.dataVizMsg1.SetLabelText('Topo Data Viewer')
        self.dataVizMsg2.SetLabelText(str(self.topoPath.stem))

        self.getTopoVals()

        self.figure.clear()
        self.axes = self.figure.add_subplot(111)

        #tick_spacing = 100
        self.axes.scatter(self.topoDF['xDist'],self.topoDF['Elev'], s=5, marker='h')
        self.axes.plot(self.topoDF['xDist'],self.topoDF['Elev'])
        self.axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(100))
        #self.axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(tick_spacing))
        self.axes.ticklabel_format(axis='both',style='plain')
        self.axes.grid(which='major', axis='both',color=(0.8,0.8,0.8))
        self.axes.set_xlim(0-max(self.topoDF['xDist'])*.2,max(self.topoDF['xDist'])*1.2)
        self.axes.set_ylim(min(self.topoDF['Elev'])*0.8,max(self.topoDF['Elev'])*1.2)
        self.axes.set_xlabel('X-Distance Along Profile (m)')
        self.axes.set_ylabel('Elevation Above MSL (m)')
        self.axes.xaxis.tick_bottom()

        self.canvas.draw()

    def onSliderEditEVENT(self,event):
        self.onSliderEdit()

    def onSliderEdit(self):
        self.sliderVal = float(self.editSlider.GetValue())
        if self.currentChart == 'Graph':

            if self.sliderVal in self.electrodes:

                self.electrodeToggleBtn.Show()

                toggleState = self.electState[int(self.electrodes.index(self.sliderVal))]
                self.electrodeToggleBtn.SetValue(toggleState)

                if toggleState == True:
                    self.dataVizMsg2.SetLabelText("Electrode at " + str(self.sliderVal) + " m is in use")
                    self.electrodeToggleBtn.SetLabelText('On')
                    self.electrodeToggleBtn.SetBackgroundColour((100, 255, 100))
                else:
                    self.electrodeToggleBtn.SetLabelText('Off')
                    self.electrodeToggleBtn.SetBackgroundColour((255, 100, 100))
                    self.dataVizMsg2.SetLabelText("Electrode at " + str(self.sliderVal) + " m is not in use")

            else:
                self.dataVizMsg2.SetLabelText('No Electrode at this x-location')
                self.electrodeToggleBtn.Hide()
        elif self.currentChart == 'Stat':

            currData = 0
            for i in self.dataframeEDIT["Keep"]:
                if i:
                    currData = currData + 1

            peIndex = self.dataframeEDIT.columns.get_loc('PctErr')
            dataCut = 0
            for r in enumerate(self.dataframeEDIT.iloc[:, peIndex]):
                if float(r[1]) >= float(self.sliderVal) / 100.0:
                    dataCut += 1

            self.dataVizMsg2.SetLabelText(str(self.sliderVal)+'% Err: '+str(dataCut) + ' points will be deleted ('+
                                          str(round(dataCut/currData*100,1))+'% of the current data).')
        else:
            self.dataVizMsg2.SetLabelText('Value: ' + str(self.sliderVal))

    def onEditTypeToggle(self, event):
        self.editTypeToggleState = self.editTypeToggleBtn.GetValue()
        if self.editTypeToggleState == True:
            self.editTypeToggleBtn.SetLabelText('Keep')
        elif self.editTypeToggleState == False:
            self.editTypeToggleBtn.SetLabelText('Remove')

    def onSelectEditDataType(self,event):
        choiceListInd = self.editDataType.GetSelection()
        colNumBase = [14, 13, [1, 3, 5, 7], 16, 19, 11, 12]

        self.setEditToggleState = self.editDataChoiceBool[choiceListInd]
        self.setEditToggleBtn.SetValue(self.setEditToggleState)
        if float(self.editDataValues[choiceListInd][0]) == 0 and float(self.editDataValues[choiceListInd][1]) == 0:
            #Set min value in box
            if type(colNumBase[choiceListInd]) is list:
                minVal = []
                for i in colNumBase[choiceListInd]:
                    minVal.append(self.dataframeEDIT[self.dataframeEDITColHeaders[i]].min())
                minVal = min(minVal)
            else:
                minVal = self.dataframeEDIT[self.editDataChoiceList[choiceListInd]].min()
            self.inputTxtMinRem.SetValue(str(minVal))

            # Set max value in box
            if type(colNumBase[choiceListInd]) is list:
                maxVal = []
                for i in colNumBase[choiceListInd]:
                    maxVal.append(self.dataframeEDIT[self.dataframeEDITColHeaders[i]].max())
                maxVal = max(maxVal)
            else:
                maxVal = self.dataframeEDIT[self.editDataChoiceList[choiceListInd]].max()
            self.inputTxtMaxRem.SetValue(str(maxVal))

        else:
            self.inputTxtMinRem.SetValue(str(self.editDataValues[choiceListInd][0]))
            self.inputTxtMaxRem.SetValue(str(self.editDataValues[choiceListInd][1]))
        if self.setEditToggleState:
            self.setEditToggleBtn.SetLabelText('Used')
        else:
            self.setEditToggleBtn.SetLabelText('Not Used')

    def onSetEditToggle(self,event):
        self.setEditToggleState = self.setEditToggleBtn.GetValue()
        choiceListInd = self.editDataType.GetSelection()

        if self.setEditToggleState == True:
            if self.editDataType.GetSelection() > -1:
                self.editDataChoiceBool[choiceListInd] = True
                self.setEditToggleBtn.SetLabelText('Used')
            else:
                self.setEditToggleState = False
                self.setEditToggleBtn.SetValue(False)
        elif self.setEditToggleState == False:
            if self.editDataType.GetSelection() > -1:
                self.editDataChoiceBool[choiceListInd] = False
            self.setEditToggleBtn.SetLabelText('Not Used')
        self.setEditDataValues()

    def onEditDataValueChangeEvent(self,event):
        self.setEditDataValues()

    def setEditDataValues(self):
        choiceListInd = self.editDataType.GetSelection()
        colNumBase = [14, 13, [1, 3, 5, 7], 16, 19, 11, 12]

        #Set Min Value Box
        if self.inputTxtMinRem.GetValue().isnumeric():
            self.editDataValues[choiceListInd][0] = float(self.inputTxtMinRem.GetValue())
        elif self.inputTxtMinRem.GetValue().lower() == 'min':
            if type(colNumBase[choiceListInd]) is list:
                minVal = []
                for i in colNumBase[choiceListInd]:
                    minVal.append(self.dataframeEDIT[self.dataframeEDITColHeaders[i]].min())
                minVal = min(minVal)
            else:
                minVal = self.dataframeEDIT[self.editDataChoiceList[choiceListInd]].min()
            self.inputTxtMinRem.SetValue(str(minVal))
            self.editDataValues[choiceListInd][0] = float(minVal)
        else:
            pass
            # self.editDataChoiceList = ['AppResist', 'Resistance', 'Electrode x-Dists', 'Variance', 'PctErr', 'PseudoX','PseudoZ']

        #Set Max Value Box
        if self.inputTxtMaxRem.GetValue().isnumeric():
            self.editDataValues[choiceListInd][1] = float(self.inputTxtMaxRem.GetValue())
        elif self.inputTxtMaxRem.GetValue().lower() == 'max':
            if type(colNumBase[choiceListInd]) is list:
                maxVal = []
                for i in colNumBase[choiceListInd]:
                    maxVal.append(self.dataframeEDIT[self.dataframeEDITColHeaders[i]].max())
                maxVal = max(maxVal)
            else:
                maxVal = self.dataframeEDIT[self.editDataChoiceList[choiceListInd]].max()
            self.inputTxtMaxRem.SetValue(str(maxVal))
            self.editDataValues[choiceListInd][1] = float(maxVal)
        else:
            pass

    def onLogicToggle(self, event):
        self.editLogicToggleState = self.editLogicToggleBtn.GetValue()
        if self.editLogicToggleState == True:
            self.editLogicToggleBtn.SetLabelText('AND')
        elif self.editLogicToggleState == False:
            self.editLogicToggleBtn.SetLabelText('OR')

    def onRemovePts(self,event):
        #self.editDataChoiceList = ['AppResist', 'Resistance', 'Electrode x-Dists', 'Variance', 'PctErr', 'PseudoX','PseudoZ']
        self.setEditDataValues()

        colNumBase = [14,13,[1,3,5,7],16,19,11,12]
        colNums = []
        for i in enumerate(colNumBase):
            if self.editDataChoiceBool[i[0]]:
                colNums.append(i[1])
        colNames = self.dataframeEDIT.columns

        if len(colNums) < 1:
            pass
        else:
            if self.editLogicToggleBtn.GetLabelText() == 'AND': #AND
                # Create list to hold items if they are to be acted on; starts all true, any false value makes false
                editList = []
                for k in range(0, self.dataLengthIN):
                    editList.append(1)
                index = -1

                for dTypeInUse in enumerate(self.editDataChoiceBool):
                    if dTypeInUse[1]:
                        for c in colNums:
                            if type(c) is list:
                                row = -1
                                for r in range(0, self.dataLengthIN):
                                    row = row + 1
                                    listBoolCt = 0
                                    for item in c:
                                        if self.dataframeEDIT.iloc[r,c] >= float(self.editDataValues[dTypeInUse[0]][0]) and self.dataframeEDIT.iloc[r,c] <= float(self.editDataValues[dTypeInUse[0]][1]):
                                            listBoolCt = listBoolCt + 1
                                    if listBoolCt == 0:
                                        editList[row] = 0

                            else: #if the columns are not a list of columns
                                #Iterate through each row in col c to see if it is in range
                                for r in self.dataframeEDIT[colNames[c]]:
                                    index = index + 1
                                    if r < float(self.editDataValues[i2][0]) and r > float(self.editDataValues[i2][1]):
                                        editList[index] = 0

            elif self.editLogicToggleBtn.GetLabelText() == 'OR': #OR
                for dTypeInUse in enumerate(self.editDataChoiceBool):
                    if dTypeInUse[1]:
                        for c in colNums:
                            if type(c) is list:
                                #Create editList if multiple columns involved
                                editList = []
                                for k in range(0, self.dataLengthIN):
                                    editList.append(0)

                                for item in c:
                                    row = -1
                                    for r in self.dataframeEDIT[colNames[item]]:
                                        if r >= float(self.editDataValues[dTypeInUse[0]][0]) and r <= float(self.editDataValues[dTypeInUse[0]][1]):
                                            if self.editTypeToggleBtn.GetLabelText() == 'Remove':
                                                self.dataframeEDIT.loc[row, 'Keep'] = False
                                            elif self.editTypeToggleBtn.GetLabelText() == 'Keep':
                                                self.dataframeEDIT.loc[row, 'Keep'] = True
                                            else:
                                                pass
                                        else:
                                            if self.editTypeToggleBtn.GetLabelText() == 'Keep':
                                                self.dataframeEDIT.loc[row, 'Keep'] = False

                            else:
                                row = -1
                                for r in self.dataframeEDIT[colNames[c]]:
                                    row = row + 1
                                    if r >= float(self.editDataValues[dTypeInUse[0]][0]) and r <= float(self.editDataValues[dTypeInUse[0]][1]):
                                        if self.editTypeToggleBtn.GetLabelText() == 'Remove':
                                            self.dataframeEDIT.loc[row, 'Keep'] = False
                                        elif self.editTypeToggleBtn.GetLabelText() == 'Keep':
                                            self.dataframeEDIT.loc[row, 'Keep'] = True
                                        else:
                                            pass
                                    else:
                                        if self.editTypeToggleBtn.GetLabelText() == 'Keep':
                                            self.dataframeEDIT.loc[row, 'Keep'] = False
            else:
                pass
            self.graphChart()

    def ONtoggle(self,event):
        self.ToggleState = self.electrodeToggleBtn.GetValue()
        self.sliderVal = self.editSlider.GetValue()


        if self.ToggleState == True:
            self.dataVizMsg2.SetLabelText("Electrode at "+ str(self.sliderVal) +" m is in use")
            self.electrodeToggleBtn.SetLabelText('On')
            self.electrodeToggleBtn.SetBackgroundColour((100,255,100))

            xCols = [0,1,2,3]
            keep=[]
            for c in xCols:
                for r in enumerate(self.xDF.iloc[:,c]):
                    if float(r[1]) == float(self.sliderVal):
                        keep.append(r[0])

            for i in self.dataframeEDIT.index:
                if i in keep:
                    self.dataframeEDIT.loc[[i],['Keep']] = True

            eIndex = int(self.electrodes.index(self.sliderVal))
            self.electState[eIndex] = True

        elif self.ToggleState == False:
            self.electrodeToggleBtn.SetLabelText('Off')
            self.electrodeToggleBtn.SetBackgroundColour((255,100,100))
            self.dataVizMsg2.SetLabelText("Electrode at " + str(self.sliderVal) + " m is not in use")

            xCols = [0,1,2,3]
            lose=[]
            for c in xCols:
                for r in enumerate(self.xDF.iloc[:,c]):
                    if float(r[1]) == float(self.sliderVal):
                        lose.append(r[0])

            for i in self.dataframeEDIT.index:
                if i in lose:
                    self.dataframeEDIT.loc[[i],['Keep']] = False

            #change self.electState to True
            eIndex = int(self.electrodes.index(self.sliderVal))
            self.electState[eIndex] = False

        else:
            self.dataVizMsg2.SetLabelText("uhh, this is wierd")

        dataRetained = 0
        for i in self.dataframeEDIT["Keep"]:
            if i:
                dataRetained = dataRetained + 1

        self.dataEditMsg.SetLabelText(str(dataRetained) + '/' + str(len(self.dataframeEDIT)) + 'pts (' + str(round(dataRetained/len(self.dataframeEDIT)*100,1)) + '%)')

        self.graphChart()

    def ONSaveEdits(self,event):

        if self.currentChart == 'Graph':
            #do nothing
            pass
        elif self.currentChart == 'Stat':
            #self.sliderVal = float(self.editSlider.GetValue())
            peIndex = self.dataframeEDIT.columns.get_loc('PctErr')
            lose = []

            for r in enumerate(self.dataframeEDIT.iloc[:, peIndex]):
                if float(r[1]) >= float(self.sliderVal)/100.0:
                    lose.append(r[0])

            kIndex = int(self.dataframeEDIT.columns.get_loc('Keep'))

            for i in self.dataframeEDIT.index:
                if i in lose:
                    self.dataframeEDIT.iloc[i, kIndex] = False

            dataRetained = 0
            for i in self.dataframeEDIT["Keep"]:
                if i:
                    dataRetained = dataRetained + 1

            self.dataEditMsg.SetLabelText(str(dataRetained) + '/' + str(len(self.dataframeEDIT)) + 'pts (' + str(
                round(dataRetained / len(self.dataframeEDIT) * 100, 1)) + '%)')

            self.statChart()
        else:
            pass

    def ONdataVizInput(self,event):
        if self.dataVizInput.GetValue().isnumeric():
            if float(self.dataVizInput.GetValue()) < float(self.editSlider.GetMin()) or float(self.dataVizInput.GetValue()) > float(self.editSlider.GetMax()):
                self.dataVizMsg2.SetValue('Error: Value must integer be between '+ str(self.editSlider.GetMin())+ ' and '+str(self.editSlider.GetMax()))
            else:
                self.editSlider.SetValue(int(self.dataVizInput.GetValue()))
                self.dataVizInput.SetValue('')
        else:
            self.dataVizInput.SetValue('Error: Value must be numeric')
        self.onSliderEdit()

    def reviewEvent(self,event):
        self.reviewChart()

    def reviewChart(self):
        self.editSlider.Hide()
        self.currentChart = 'Review'
        self.dataVizMsg1.SetLabelText('Review Edits')
        self.saveEditsBtn.Hide()
        self.electrodeToggleBtn.Hide()
        self.dataVizInput.Hide()
        self.dataVizInputBtn.Hide()

        x = []
        z = []
        v = []
        pe = []
        xOmit = []
        zOmit = []

        self.createExportDF()
        for i in enumerate(self.dataframeEDIT['Keep']):
            x.append(self.dataframeEDIT.loc[i[0], 'PseudoX'])
            z.append(self.dataframeEDIT.loc[i[0], 'PseudoZ'])
            v.append(self.dataframeEDIT.loc[i[0], 'AppResist'])

            if i[1]:
                pass
            else:
                xOmit.append(self.dataframeEDIT.loc[i[0],'PseudoX'])
                zOmit.append(self.dataframeEDIT.loc[i[0],'PseudoZ'])

        if 'scipy.interpolate' in sys.modules:
            self.makeColormesh(x,z,v,pe,xOmit,zOmit)
        else:
            ptSize = round(100/self.maxXDist*125,1)
            self.axes.scatter(x,z, c=v,edgecolors='black',s=ptSize, marker='h')

        #self.axes.scatter(x,z, c=v,s=ptSize, marker='h')
        #self.axes.scatter(xOmit,zOmit,c='black',s=ptSize-ptSize*0.333,marker = 'x')

        #minz = min(z)
        #maxz = max(z)
        #zspace = (maxz-minz)/10
        #self.axes.set_ylim(minz-zspace,maxz+zspace)
        #self.axes.set_xlabel('X-Distance (m)')
        #self.axes.set_ylabel('Elev/Depth (m)')
        #self.axes.xaxis.tick_top()

        #self.canvas.draw()
        #pass

    def getClosestElev(self):
        if len(self.inputTxtTopo.GetValue())>0 and 'Enter Topo Filepath Here' not in self.inputTxtTopo.GetValue():
            if self.topoDF['xDist'].max() > max(self.electrodes) or self.topoDF['xDist'].min() > min(self.electrodes):
                if self.topoDF['xDist'].max() > max(self.electrodes):
                    wx.LogError("File format error. Maximum topo X-Distance is greater than maximum electrode X-Distance.")
                else:
                    wx.LogError("File format error. Minimum topo X-Distance is less than minimum electrode X-Distance.")
            else:

                self.electrodeElevs = [[] for k in range(len(self.electrodes))]#blank list

                for x in enumerate(self.electrodes):

                    elecxDist = x[1]
                    elecIndex = x[0]

                    index = np.argmin(np.abs(np.array(self.topoDF['xDist']) - elecxDist))#finds index of closest elevation
                    nearestTopoxDist = self.topoDF.loc[index,'xDist']
                    nearestTopoElev = self.topoDF.loc[index,'Elev']

                    if nearestTopoxDist == x[1]:
                        self.electrodeElevs[elecIndex] = nearestTopoElev
                    elif nearestTopoxDist >= x[1]:
                        mapNum = nearestTopoxDist - self.electrodes[elecIndex]
                        mapDenom = nearestTopoxDist - self.topoDF.loc[index-1,'xDist']
                        mVal = float(mapNum/mapDenom)
                        self.electrodeElevs[elecIndex] = nearestTopoElev - (nearestTopoElev-self.topoDF.loc[index-1,'Elev'])*mVal
                    else:
                        mapNum = self.electrodes[elecIndex] - nearestTopoxDist
                        mapDenom = self.topoDF.loc[index+1,'xDist']-nearestTopoxDist
                        mVal = float(mapNum/mapDenom)
                        self.electrodeElevs[elecIndex] = nearestTopoElev + (nearestTopoElev-self.topoDF.loc[index-1,'Elev'])*mVal

                blankList = [[] for k in range(len(self.dataframeEDIT['Keep']))]  # blank list
                self.dataframeEDIT['SurfElevs'] = blankList

                elecXDistColNames = ['A(x)','B(x)','M(x)','N(x)']
                elecElevColNames =  ['A(z)','B(z)','M(z)','N(z)']
                elecXDistColNums = [1,3,5,7]

                for c in enumerate(elecXDistColNums):
                    for x in enumerate(self.dataframeEDIT[elecElevColNames[c[0]]]):

                        elecxDist = x[1]
                        elecIndex = x[0]

                        index = np.argmin(
                            np.abs(np.array(self.topoDF['xDist']) - elecxDist))  # finds index of closest elevation
                        nearestTopoxDist = self.topoDF.loc[index, 'xDist']
                        nearestTopoElev = self.topoDF.loc[index, 'Elev']

                        if nearestTopoxDist == x[1]:
                            self.dataframeEDIT.iloc[elecIndex,c[1]+1] = nearestTopoElev
                        elif nearestTopoxDist >= x[1]:
                            mapNum = nearestTopoxDist - self.dataframeEDIT.iloc[elecIndex,c[1]+1]
                            mapDenom = nearestTopoxDist - self.topoDF.loc[index - 1, 'xDist']
                            mVal = float(mapNum / mapDenom)
                            self.dataframeEDIT.iloc[elecIndex,c[1]+1] = nearestTopoElev - (
                                        nearestTopoElev - self.topoDF.loc[index - 1, 'Elev']) * mVal
                        else:
                            mapNum = self.dataframeEDIT.iloc[elecIndex,c[1]+1] - nearestTopoxDist
                            mapDenom = self.topoDF.loc[index + 1, 'xDist'] - nearestTopoxDist
                            mVal = float(mapNum / mapDenom)
                            self.dataframeEDIT.iloc[elecIndex,c[1]+1] = nearestTopoElev + (
                                        nearestTopoElev - self.topoDF.loc[index - 1, 'Elev']) * mVal

                    self.dataframeEDIT['PtElev'] = self.dataframeEDIT[elecElevColNames[c[0]]] - self.dataframeEDIT['PseudoZ']
        else:
            pass

        if self.inputDataExt == '.DAT (LS)':
            self.electrodeElevs = []

            for x in enumerate(self.electrodes): #Checks if there's already elevation data??
                found = 0
                for xc in self.electrodeCols:
                    if found == 0:
                        for i in enumerate(self.dataframeEDIT.iloc[:,xc]):
                            if round(float(x[1]),2) == round(float(i[1]),2):
                                zc = xc + 1
                                found = 1
                                elev = self.dataframeEDIT.iloc[i[0],zc]
                    elif found == 1:
                        self.electrodeElevs.append(float(elev))

        else:
            wx.LogError("No Topography Data Found")

    def onExportBrowse(self, event):
        with wx.FileDialog(self, "Select Export Filepath", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.exportPathname = pathlib.Path(fileDialog.GetPath())
            try:
                with open(self.exportPathname, 'r') as exportFile:
                    path = exportFile.name
                    self.exportTXT.SetValue(path)

            except  IOError:
                wx.LogError("Cannot Open File")

    def onExport(self, event):

        dataDF,keepLength = self.createExportDF()

        dataLeadDF = pd.DataFrame()
        dataTailDF = pd.DataFrame()

        #Create Data Lead
        dataLeadDF[0] = self.dataLead

        if self.inputDataExt == '.DAT (SAS)':
            dataLeadList = []
            dataLeadList.append(self.dataLead[0][0])
            dataLeadList.append(self.dataLead[1][0])
            dataLeadList.append(11)
            dataLeadList.append(self.dataLead[2][0])
            dataLeadList.append('Type of measurement (0=app.resistivity,1=resistance)')
            dataLeadList.append(0)
            dataLeadList.append(keepLength)
            dataLeadList.append(2)
            dataLeadList.append(0)

            dataLeadDF = pd.DataFrame(dataLeadList)
        else:
            dataLeadDF.iloc[4,0] = 'Type of measurement (0=app.resistivity,1=resistance)'
            dataLeadDF.iloc[6,0] = str(int(keepLength))

        for c in range(1, 10):
            dataLeadDF[int(c)] = [None, None, None, None, None, None, None, None, None]

        #Create Data Tail
        for c in range(0, 10):
            if c < 1:
                dataTailDF[int(c)] = [0,     0,     0,    0,   0,    0,    0]
            else:
                dataTailDF[int(c)] = [None, None, None, None, None, None, None]

        #print(dataLeadDF)
        #print(dataDF)
        #print(dataTailDF)

        DFList = [dataLeadDF, dataDF, dataTailDF]

        self.exportDataframe = pd.concat(DFList, ignore_index=True, axis=0)

        self.exportDataframe.to_csv(self.exportTXT.GetValue(), sep="\t", index=False, header=False)

    def createExportDF(self):
        dataDF = pd.DataFrame(columns=["NoElectrodes",'A(x)', 'A(z)', 'B(x)', 'B(z)', 'M(x)', 'M(z)', 'N(x)', 'N(z)', 'Resistance'])

        tempList = []
        noneList = []
        keepRows = []
        for i in enumerate(self.dataframeEDIT["Keep"]):
            if i[1]:
                keepRows.append(i[0])
                tempList.append(4)#number of electrodes
                noneList.append(None)
        dataDF['NoElectrodes'] = tempList #Add number of electrodes to first column
        keepLength = len(keepRows)

        if self.inputDataExt == '.TXT (LS)' or self.inputDataExt == '.DAT (LS)' or self.inputDataExt == '.DAT (SAS)' :
            cols = [7,5,1,3]
            valCol = 14 #14 app resistivity; 13 is Resistance
            zCols = [8, 6, 2, 4]

        #Add electrode XDistances to dataDF
        j=0
        for c in cols:
            for r in enumerate(keepRows):
                dataDF.iloc[int(r[0]), int(c)] = round(float(self.xDF.iloc[int(r[1]),int(j)]),2)
            j+=1

        #Run getClosestElev() if data has elevations and is .DAT (LS) style or if includeTopoBx checkbox is marked
        if self.includeTopoBx.GetValue() or (float(self.dataframeEDIT.iloc[0,self.xCols[0]+1]) > 0.0 and self.inputDataExt == '.DAT (LS)'):
            self.getClosestElev()
        else:
            self.electrodeElevs = []
            for i in self.electrodes:
                self.electrodeElevs.append(0.00)

        #if self.includeTopoBx.GetValue():
        #    if self.dataframeEDIT.loc[:,'PseudoZ'].sum(axis = 0) > 0:
        #        self.dataframeEDIT['PtElev'] = self.dataframeEDIT['SurfElevs'] - self.dataframeEDIT['Depth']
        #    else:
        #        self.dataframeEDIT['PtElevs'] = self.dataframeEDIT['SurfElevs'] + self.dataframeEDIT['Depth']
        #else:
        #    self.dataframeEDIT['SurfElevs'] = zeroList
        #    self.dataframeEDIT['PtElevs'] = self.dataframeEDIT['SurfElevs'] - self.dataframeEDIT['Depth']

        j = 0
        zeroList = [0 for k in range(len(self.dataframeEDIT['Keep']))]  # blank list
        if self.dataShifted:
            electrodes = self.electrodesShifted
        else:
            electrodes = self.electrodes

        print(electrodes)
        print(self.electrodes)
        print(self.electrodesShifted)

        print(self.electrodeElevs)
        print(dataDF)

        for r in enumerate(self.dataframeEDIT["Keep"]):

            if r[1]:
                dataDF.loc[int(j),int(9)] = self.dataframeEDIT.iloc[int(r[0]),int(valCol)]
                for z in zCols:
                    i = electrodes.index(float(dataDF.iloc[j,z-1]))
                    dataDF.iloc[j,z] = round(self.electrodeElevs[i],2)
                j+=1


        if self.reverseBx.GetValue() == True:
            xDistCols = [1, 3, 5, 7]

            for i in xDistCols:
                dataDF[i] = self.maxXDist-dataDF[i]

        return dataDF, keepLength

    def onCancel(self, event):
        self.closeProgram()

    def closeProgram(self):
        self.Close()

# Run the program
if __name__ == '__main__':
    app = wx.App()
    frame = ERTAPP().Show()
    app.MainLoop()
