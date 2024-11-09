from PIL import Image
import os, signal
import customtkinter
from PIL import Image, ImageTk
import cv2
import torch
import json
from ultralytics import solutions
from tkinter.filedialog import askopenfile
import ntpath

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("840x600")
        self.title("TrafficBeam")
        self.minsize(1280, 720)
        self.configure(fg_color='#1B2838')

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x_cordinate = int((screen_width/2) - (1280/2))
        y_cordinate = int((screen_height/2) - (720/2))

        self.geometry("{}x{}+{}+{}".format(1280, 720, x_cordinate, y_cordinate))


        # create 1x2 grid system
        self.grid_rowconfigure((0), weight=0)
        self.grid_rowconfigure((1), weight=1)
        self.grid_columnconfigure((0,1,2,3), weight=1)

        # declare variables 

        self.routeTxt = ""
        self.isCarDetecting = customtkinter.BooleanVar(value=True)
        self.isTruckDetecting = customtkinter.BooleanVar(value=True)
        self.isMotorcycleDetecting = customtkinter.BooleanVar()

        self.isCarCounting = customtkinter.BooleanVar(value=True)
        self.isTruckCounting = customtkinter.BooleanVar(value=True)
        self.isMotorcycleCounting = customtkinter.BooleanVar()

        # Configuração do vídeo e do contador de objetos
        self.cap = cv2.VideoCapture("cars.mp4")
        assert self.cap.isOpened(), "Error reading video file"
        self.w, self.h, fps = (int(self.cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Define pontos da região
        self.region_points = [(0, 0), (self.w, 0), (self.w, self.h), (0, self.h)]
        self.counter = solutions.ObjectCounter(
            show=False,  # False para exibir diretamente no Tkinter
            region=self.region_points,
            model="yolo11n.pt",
            classes=[2, 3, 7],  # classes para Carros, Motos e Caminhões
            device=self.device.index,
            show_in=False,
            show_out=False,
        )

        # Dimensões desejadas para exibição do vídeo
        self.desired_width, self.desired_height = 1140, 720

        # add frame to app

        #NavBar Frame
        self.navBarFrame = customtkinter.CTkFrame(self, height=100, fg_color="#1B2838", corner_radius=0)
        self.navBarFrame.grid(row=0, column=0, columnspan=4, padx=0, ipady=0, sticky="ew")
        self.navBarFrame.grid_rowconfigure((0), weight=0)
        self.navBarFrame.grid_columnconfigure((0), weight=0)
        self.navBarFrame.grid_columnconfigure((1), weight=1)

        self.sideTitleFrame = customtkinter.CTkFrame(self.navBarFrame, width=226, fg_color="#1B2838", corner_radius=0)
        self.sideTitleFrame.grid(row=0, column=0, columnspan=1, padx=50, ipady=0, sticky="nsew")

        self.titleFrame = customtkinter.CTkFrame(self.navBarFrame, fg_color="#23364E", corner_radius=0)
        self.titleFrame.grid(row=0, column=1, columnspan=1, padx=0, pady=0, sticky="nsew")

        #Main Frame
        self.mainFrame = customtkinter.CTkFrame(self, fg_color="#171D25", bg_color="#171D25")
        self.mainFrame.grid(row=1, column=0, columnspan=2, ipadx=0, ipady=10, sticky="nsew")
        self.mainFrame.grid_rowconfigure(0, weight=1)

        #Side Menu
        self.sideFrame = customtkinter.CTkFrame(self, fg_color="#1B2838", bg_color="#1B2838")
        self.sideFrame.grid(row=1, column=2, columnspan=2, padx=0, pady=10, sticky="nsew")
        self.sideFrame.grid_columnconfigure(0, weight=1)
        self.sideFrame.grid_columnconfigure(1, weight=0)

    #Title Frame Widgets
        self.mainTitleLabel = customtkinter.CTkLabel(self.sideTitleFrame, text="TrafficBeam", font=("YU Gothic UI Semibold", 22, "bold"), bg_color="#1B2838", text_color="#E0E1E2")
        self.mainTitleLabel.grid(row=0, column=0, columnspan=1, padx=20, pady=10)

        self.videoSourceLabel = customtkinter.CTkLabel(self.titleFrame, text="Video ► cars.mp4", font=("YU Gothic UI Semibold", 15, "bold"), bg_color="#23364E", text_color="#E0E1E2")
        self.videoSourceLabel.grid(row=0, column=0, columnspan=1, padx=20, pady=10)

        # backImage = customtkinter.CTkImage(light_image=Image.open('Assets/Images/BackBtnIcon.png'), size=(32, 32)) # WidthxHeight]
        # self.backBtn = customtkinter.CTkButton(self.titleFrame, text="", width=32, height=32, fg_color="#2B2B2B").place(x=5, y=5)

    #Main Frame Widgets
        #Video Source
        self.videoFrame = customtkinter.CTkFrame(self.mainFrame, fg_color="#171D25", bg_color="#171D25")
        self.videoFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.videoFrame.grid_rowconfigure(0, weight=1)
        self.videoFrame.grid_columnconfigure(0, weight=1)
        self.videoLabel = customtkinter.CTkLabel(self.videoFrame, bg_color="#1c1e26", text="")
        self.videoLabel.grid(row=0, column=0, padx=20, sticky="nsew")

        # Begin Video Update
        self.update_video()

        self.protocol("WM_DELETE_WINDOW", self.Shutdown) # <-- adding the protocol to check when its closed

    #Side Frame Widgets
        # Detection

        customtkinter.CTkLabel(self.sideFrame, text="Configuration", bg_color="#1B2838", font=("YU Gothic UI Semibold", 20, "bold"), text_color="#E0E1E2").grid(row=0, column=0, columnspan=2, pady=5, sticky="nsew")
        customtkinter.CTkLabel(self.sideFrame, text="Detection", bg_color="#1B2838", font=("YU Gothic UI Semibold", 18, "bold"), text_color="#E0E1E2").grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")

        customtkinter.CTkLabel(self.sideFrame, text="Cars", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=2, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.carDetectionCheckBox = customtkinter.CTkCheckBox(self.sideFrame, text="", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2", variable=self.isCarDetecting)
        self.carDetectionCheckBox.grid(row=2, column=1, columnspan=1, padx=0, pady=2, sticky="e")

        customtkinter.CTkLabel(self.sideFrame, text="Trucks", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=3, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.truckDetectionCheckBox = customtkinter.CTkCheckBox(self.sideFrame, text="", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2", variable=self.isTruckDetecting)
        self.truckDetectionCheckBox.grid(row=3, column=1, columnspan=1, padx=0, pady=2, sticky="e")

        customtkinter.CTkLabel(self.sideFrame, text="Motorcycles", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=4, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.motorcycleDetectionCheckBox = customtkinter.CTkCheckBox(self.sideFrame, text="", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2", variable=self.isMotorcycleDetecting)
        self.motorcycleDetectionCheckBox.grid(row=4, column=1, columnspan=1, padx=0, pady=2, sticky="e")

            #Line
        customtkinter.CTkLabel(self.sideFrame, text="", bg_color="#0E3B74", height=1, font=("YU Gothic UI Semibold", 2, "bold")).grid(row=5, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Counter

        customtkinter.CTkLabel(self.sideFrame, text="Counter", bg_color="#1B2838", font=("YU Gothic UI Semibold", 18, "bold"), text_color="#E0E1E2").grid(row=6, column=0, columnspan=2, pady=5, sticky="nsew")

        customtkinter.CTkLabel(self.sideFrame, text="Cars", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=7, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.carCounterCheckBox = customtkinter.CTkCheckBox(self.sideFrame, text="", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2", variable=self.isCarCounting)
        self.carCounterCheckBox.grid(row=7, column=1, columnspan=1, padx=0, pady=2, sticky="e")

        customtkinter.CTkLabel(self.sideFrame, text="Trucks", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=8, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.truckCounterCheckBox = customtkinter.CTkCheckBox(self.sideFrame, text="", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2", variable=self.isTruckCounting)
        self.truckCounterCheckBox.grid(row=8, column=1, columnspan=1, padx=0, pady=2, sticky="e")

        customtkinter.CTkLabel(self.sideFrame, text="Motorcycles", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=9, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.motorcycleCounterCheckBox = customtkinter.CTkCheckBox(self.sideFrame, text="", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2", variable=self.isMotorcycleCounting)
        self.motorcycleCounterCheckBox.grid(row=9, column=1, columnspan=1, padx=0, pady=2, sticky="e")

            #Line
        customtkinter.CTkLabel(self.sideFrame, text="", bg_color="#0E3B74", height=1, font=("YU Gothic UI Semibold", 2, "bold")).grid(row=10, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Results

        customtkinter.CTkLabel(self.sideFrame, text="Results", bg_color="#1B2838", font=("YU Gothic UI Semibold", 20, "bold"), text_color="#E0E1E2").grid(row=11, column=0, columnspan=2, pady=5, sticky="nsew")
        customtkinter.CTkLabel(self.sideFrame, text="Detected Vehicles", bg_color="#1B2838", font=("YU Gothic UI Semibold", 18, "bold"), text_color="#E0E1E2").grid(row=12, column=0, columnspan=2, pady=5, sticky="nsew")

        customtkinter.CTkLabel(self.sideFrame, text="Cars: ", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=13, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.carTotalLabel = customtkinter.CTkLabel(self.sideFrame, text="0", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2")
        self.carTotalLabel.grid(row=13, column=1, columnspan=1, padx=40, pady=2, sticky="e")

        customtkinter.CTkLabel(self.sideFrame, text="Trucks: ", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=14, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.truckTotalLabel = customtkinter.CTkLabel(self.sideFrame, text="0", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2")
        self.truckTotalLabel.grid(row=14, column=1, columnspan=1, padx=40, pady=2, sticky="e")

        customtkinter.CTkLabel(self.sideFrame, text="Motorcycles: ", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=15, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.motorcycleTotalLabel = customtkinter.CTkLabel(self.sideFrame, text="0", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2")
        self.motorcycleTotalLabel.grid(row=15, column=1, columnspan=1, padx=40, pady=2, sticky="e")

        customtkinter.CTkLabel(self.sideFrame, text="Total: ", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2").grid(row=16, column=0, columnspan=1, padx=30, pady=2, sticky="w")

        self.totalLabel = customtkinter.CTkLabel(self.sideFrame, text="0", bg_color="#1B2838", font=("YU Gothic UI Semibold", 16, "bold"), text_color="#E0E1E2")
        self.totalLabel.grid(row=16, column=1, columnspan=1, padx=40, pady=2, sticky="e")

            #Line
        customtkinter.CTkLabel(self.sideFrame, text="", bg_color="#0E3B74", height=1, font=("YU Gothic UI Semibold", 2, "bold")).grid(row=17, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

            #Side Frame Buttons
        self.paramBtn = customtkinter.CTkButton(self.sideFrame, text="Apply & Track", fg_color="#13488B", bg_color="#13488B", text_color="#E0E1E2", font=("YU Gothic UI Semibold", 16, "bold"), command=self.SetParameters)
        self.paramBtn.grid(row=18, column=0, columnspan=1, padx=(10,5), pady=10, sticky="nsew")
        self.paramBtn = customtkinter.CTkButton(self.sideFrame, text="Upload Video", fg_color="#13488B", bg_color="#13488B", text_color="#E0E1E2", font=("YU Gothic UI Semibold", 16, "bold"), command=self.UploadVideo)
        self.paramBtn.grid(row=18, column=1, columnspan=1, padx=(5,10), pady=10, sticky="nsew")


    # add methods to app

    # Function to Update video
    def update_video(self):
        self.success, frame = self.cap.read()

        global cars_count, truck_count, total_count
        cars_count = 0
        truck_count = 0
        motorcycle_count = 0
        total_count = 0

        jString = str(self.counter.classwise_counts)
        jString = jString.replace("'", '"')
        result = json.loads(jString)
        if(result.get('car') != None):
            if(self.isCarCounting.get()):
                cars_count = (result['car']['IN'] + result['car']['OUT'])
        if(result.get('truck') != None):
            if(self.isTruckCounting.get()):
                truck_count = (result['truck']['IN'] + result['truck']['OUT'])
        if(result.get('motorcycle') != None):
            if(self.isMotorcycleCounting.get()):
                truck_count = (result['motorcycle']['IN'] + result['motorcycle']['OUT'])
        total_count = cars_count + truck_count + motorcycle_count

        try:
            self.carTotalLabel
        except:
            None
        else:
            self.carTotalLabel.configure(text=str(cars_count))

        try:
            self.truckTotalLabel
        except:
            None
        else:
            self.truckTotalLabel.configure(text=str(truck_count))

        try:
            self.motorcycleTotalLabel
        except:
            None
        else:
            self.motorcycleTotalLabel.configure(text=str(motorcycle_count))
            
        try:
            self.totalLabel
        except:
            None
        else:
            self.totalLabel.configure(text=str(total_count))

        if not self.success:
            print("Fim do vídeo ou erro ao capturar quadro.")
            self.cap.release()
            return

        # Processamento de contagem de objetos
        processed_frame = self.counter.count(frame)

        # Redimensiona o quadro para o tamanho desejado
        processed_frame = cv2.resize(processed_frame, (self.desired_width, self.desired_height))

        # Conversão para formato adequado ao Tkinter
        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(processed_frame)
        imgtk = ImageTk.PhotoImage(image=img)

        # Atualiza o rótulo de vídeo
        self.videoLabel.configure(image=imgtk)

        # Atualiza a interface a cada 30 ms
        self.videoLabel.after(30, self.update_video)

    def UploadVideo(self):
        self.videoPath = askopenfile()
        self.cap.release()
        self.cap = cv2.VideoCapture(self.videoPath.name)
        assert self.cap.isOpened(), "Error reading video file"
        self.w, self.h, fps = (int(self.cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
        self.videoSourceLabel.configure(text="Video ► "+ntpath.basename(self.videoPath.name))
        if not self.success:
            self.update_video()
        self.SetParameters()

    def SetParameters(self):

        selectedClasses = []


        if(self.isCarDetecting.get()):
            selectedClasses.append(2)
        if(self.isMotorcycleDetecting.get()):
            selectedClasses.append(3)
        if(self.isTruckDetecting.get()):
            selectedClasses.append(7)

        self.counter = solutions.ObjectCounter(
            show=False,  # False para exibir diretamente no Tkinter
            region=self.region_points,
            model="yolo11n.pt",
            classes=[selectedClasses],  # classes para Carros, Motos e Caminhões
            device=self.device.index,
            show_in=False,
            show_out=False,
            verbose=False,
        )

    def Close(self, window):
        app.deiconify()
        window.withdraw()

    def Shutdown(self):
        app.destroy()

app = App()
app.mainloop()