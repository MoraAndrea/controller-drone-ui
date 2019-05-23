import logging
import threading
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfile, askdirectory

from controller.UserGuiResources.logger import ConsoleUiLogger, App
from controller.Utils.messaging.CommunicationDockerKubernetes.KubernetesManagerClass import KubernetesClass
from controller.config.config import Configuration
from controller.messaging_UI_controller import send_add_message_to_rabbit_or_runALL, send_del_message_to_rabbit


class Application(Frame):
    INTERIOR_BORDER = 5
    APP_PARAMETERS = {'VLC': [{'name':'video-BigBunny','path':'/home/Video/videoNoSound.mp4'}, {'name':'video-BigBunny1','path':'/home/Video/videoNoSound.mp4'}],'Other':[]}
    PathVideo = {"video-BigBunny":["/home/Video/videoNoSound.mp4"],"video-BigBunny1":["/home/Video/videoNoSound.mp4"]}

    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.apps = None
        self.parameters = None
        self.pods = None
        self.value_param = None
        self.value_app = None
        self.value_pods=[]
        self.btn_go = None
        self.btn_close = None
        self.btn_delete_pod=None
        self.text_file = None
        self.logger =None
        self.file = None
        self.podsRun =[]
        self.initUI()

    # create GUI
    def initUI(self):

        main_frame = Frame(self.main_win)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        main_frame.columnconfigure(5, weight=1)

        ### Apps ###
        list_item_values = self.APP_PARAMETERS.keys()   #["VLC", "one"]

        label_apps = Label(main_frame, text="Apps:")
        label_apps.grid(sticky=W, pady=(5, 0), padx=8)

        self.apps = Listbox(main_frame, width=25, height=10, bd=0,
                            highlightthickness=0, name='apps', exportselection=0)
        self.apps.grid(row=1, column=0, padx=self.INTERIOR_BORDER,
                       pady=self.INTERIOR_BORDER, sticky='nw')
        self.apps.bind('<<ListboxSelect>>', self.on_select_app)

        scroll_apps = Scrollbar(main_frame, command=self.apps.yview, orient=VERTICAL)
        scroll_apps.grid(row=1, column=1, sticky='nsew')
        scroll_apps.place(in_=self.apps, relx=1.0, relheight=1.0, bordermode=OUTSIDE)
        self.apps.configure(yscrollcommand=scroll_apps.set)

        self.apps.insert('end', *list_item_values)

        ### Parameters ####
        label_parameters = Label(main_frame, text="Parameters for app: ")
        label_parameters.grid(sticky=W, pady=(10, 0), padx=8)

        self.parameters = Listbox(main_frame, width=25, height=11, bd=0,
                                  highlightthickness=0, name="parameters", exportselection=0, state=DISABLED)
        self.parameters.grid(row=4, column=0, padx=self.INTERIOR_BORDER,
                             pady=self.INTERIOR_BORDER, sticky='sw')
        self.parameters.bind('<<ListboxSelect>>', self.on_select_param)

        scroll_parameters = Scrollbar(main_frame, command=self.parameters.yview,
                                      orient=VERTICAL)
        scroll_parameters.grid(row=4, column=1, sticky='nsew')
        scroll_parameters.place(in_=self.parameters, relx=1.0, relheight=1.0, bordermode=OUTSIDE)
        self.parameters.configure(yscrollcommand=scroll_parameters.set)

        ### Winner nodes ####
        label_winner = Label(main_frame, text="Winner Nodes:")
        label_winner.grid(row=0, column=4, sticky=W, pady=(5, 0), padx=43)

        nodes = Listbox(main_frame, width=40, height=10, bd=0,
                        highlightthickness=0, name='nodes')
        nodes.grid(row=1, column=4, padx=40,
                   pady=self.INTERIOR_BORDER, sticky='nw')

        scroll_nodes = Scrollbar(main_frame, command=nodes.yview,
                                 orient=VERTICAL)
        scroll_nodes.grid(row=0, column=5, sticky='nsew')
        scroll_nodes.place(in_=nodes, relx=1.0, relheight=1.0, bordermode=OUTSIDE)
        nodes.configure(yscrollcommand=scroll_nodes.set)

        ### buttons ####
        btn_browse = Button(main_frame, text="Browse", command=self.browse_file)
        btn_browse.grid(row=4, column=4, sticky=W + N, padx=(40, 0))
        self.btn_go = Button(main_frame, text="Run", state=DISABLED, command=self.run)
        self.btn_go.grid(row=4, column=4, sticky=W + N, padx=(40, 0), pady=(40, 0))
        self.btn_close = Button(main_frame, text="Close All", state=DISABLED, command=self.close)
        self.btn_close.grid(row=4, column=4, sticky=W + N, padx=(40, 0), pady=(80, 0))
        self.btn_delete_pod = Button(main_frame, text="Delete", state=DISABLED, command=self.delete_pods)
        self.btn_delete_pod.grid(row=4, column=4, sticky=W + N, padx=(40, 0), pady=(120, 0))
        self.btn_log = Button(main_frame, text="logger", state=NORMAL, command=self.run_logger)
        self.btn_log.grid(row=4, column=4, sticky=W + N, padx=(40, 0), pady=(160, 0))

        ### text chosen file or options ###
        self.text_file = Text(main_frame, width=30, height=3)
        self.text_file.grid(row=4, column=4, sticky=W + N, padx=(130, 0), pady=(0, 0))

        ### Present pods ###
        label_pods = Label(main_frame, text="Pods:")
        label_pods.grid(row=4, column=4, sticky=W+N, padx=(135, 0), pady=(60, 0))
        self.pods = Listbox(main_frame, width=30, height=7, bd=0,
                        highlightthickness=0,selectmode='multiple', name='pods')
        self.pods.grid(row=4, column=4, padx=(132, 0), pady=(80, 0), sticky=W + N)
        self.pods.bind('<<ListboxSelect>>', self.on_select_pods)
        scroll_pods = Scrollbar(main_frame, command=self.pods.yview,
                                 orient=VERTICAL)
        scroll_pods.grid(row=4, column=5, sticky='nsew')
        scroll_pods.place(in_=self.pods, relx=1.0, relheight=1.0, bordermode=OUTSIDE)
        self.pods.configure(yscrollcommand=scroll_pods.set)

        names=kubernetes.get_list_podsName_for_namespace(configuration.NAMESPACE)
        if names is not None:
            self.podsRun.append(names)
            self.pods.insert('end', *self.podsRun)


    def loggerApp(self):
        logging.basicConfig(level=logging.DEBUG)
        root = Toplevel(self.main_win)
        app = App(root)

    def run_logger(self):
        threadLogger = threading.Thread(name='loggerThread', target=self.loggerApp)
        threadLogger.start()

    # command when select a App
    def on_select_app(self, event):
        self.value_param = None
        self.text_file.delete('1.0', END)
        self.btn_go.config(state=DISABLED)

        w = event.widget
        print(w)
        index = int(self.apps.curselection()[0])
        self.value_app = self.apps.get(index)
        print('You selected item %d: "%s"' % (index, self.value_app))
        ConsoleUiLogger.submit_message('DEBUG', 'You selected item %d: "%s"' % (index, self.value_app))
        if self.value_app in self.APP_PARAMETERS and len(self.APP_PARAMETERS[self.value_app])>0:
            self.parameters.config(state=NORMAL)
            self.parameters.delete('0', END)
            # self.parameters.insert('end', *self.APP_PARAMETERS[self.value_app])
            for param in self.APP_PARAMETERS[self.value_app]:
                self.parameters.insert('end',param['name'])
            # self.enable_item(0)
        else:
            self.parameters.config(state=NORMAL)
            self.parameters.delete('0', END)
            self.text_file.insert('1.0', "No parameters")
            self.parameters.insert(END, "No parameters")
            self.parameters.config(state=DISABLED)
            # self.disable_item(0)

    # command when select a parameter
    def on_select_param(self, event):
        self.text_file.delete('1.0', END)
        param_event = event.widget
        print(param_event)
        index_param = int(self.parameters.curselection()[0])
        self.value_param = self.parameters.get(index_param)
        print('You selected item %d: "%s"' % (index_param, self.value_param))
        ConsoleUiLogger.submit_message('DEBUG', 'You selected item %d: "%s"' % (index_param, self.value_param))
        self.btn_go.config(state="normal")
        self.text_file.insert('1.0', self.value_app + " " + self.value_param)

    # command when select a pods
    def on_select_pods(self, event):
        pods_event = event.widget
        print(pods_event)
        index_pods = int(self.pods.curselection()[0])
        self.value_pods.append(self.pods.get(index_pods))
        print('You selected item %d: "%s"' % (index_pods, self.value_pods))
        ConsoleUiLogger.submit_message('DEBUG', 'You selected item %d: "%s"' % (index_pods, self.value_pods))
        self.btn_delete_pod.config(state="normal")

    # search file with request message
    def browse_file(self):
        self.file = askopenfile(mode='rb', title='Choose a Json file')
        if self.file != None:
            data = self.file.read()
            self.text_file.insert('1.0', self.file.name)
            ConsoleUiLogger.submit_message('INFO', "File chosen: "+self.file.name)
            self.file.close()
            # print("I got %d bytes from this file." % len(data))
            self.btn_go.config(state="normal")
        else:
            ConsoleUiLogger.submit_message('ERROR', "Error to load file!")

    # run request
    def run(self):
        self.text_file.delete('1.0', END)
        pods_info=None
        # =send_add_message_to_rabbit_or_runALL(self, self.file, self.value_app, self.value_param, self.PathVideo[self.value_param][0])
        if pods_info is False:
            self.text_file.delete('1.0', END)
            messagebox.showwarning("Warn", "Pod is already present")
            ConsoleUiLogger.submit_message('WARNING', "Pod is already present")
            return
        else:
            self.podsRun.append(pods_info)
            self.pods.insert('end', *self.podsRun)

        if self.podsRun is None:
            self.text_file.delete('1.0', END)
            messagebox.showerror("Error", "No request to send!!!")
            ConsoleUiLogger.submit_message('ERROR', "No request to send!!!")
        else:
            messagebox.showinfo("Info", "Request send...")
            self.btn_close.config(state=NORMAL)

    # delete all pod created for this app
    def close(self):
        self.text_file.delete('1.0', END)
        ConsoleUiLogger.submit_message('INFO',"I'm deleting pod with name:")
        result=None
            #send_del_message_to_rabbit(self, self.file, self.value_app, self.value_param)
        if result is False:
            ConsoleUiLogger.submit_message('WARNING', "Pod not found")
        else:
            ConsoleUiLogger.submit_message('INFO', "Cancellation message sent... ")

    def delete_pods(self):
        self.text_file.delete('1.0', END)
        for pod in self.value_pods:
            if kubernetes.delete_pod(pod, "test") is False:
                ConsoleUiLogger.submit_message('WARNING', "pod "+ pod+" not found")
            else:
                ConsoleUiLogger.submit_message('INFO', " --> "+pod)
                idx = self.pods.get(0, END).index(pod)
                self.pods.delete(idx)

    # NOT USED
    @staticmethod
    def select_folder():
        global folder_path
        filename = askdirectory()
        folder_path.set(filename)
        print(filename)

    # NOT USED
    def disable_item(self, index):
        self.parameters.itemconfig(index, fg="gray")
        self.parameters.bind("<<ListboxSelect>>",
                             lambda event, index=index: self.no_selection(event, index))

    # NOT USED
    def no_selection(self, event, index):
        if str(self.parameters.curselection()[0]) in str(index):
            self.parameters.selection_clear(index)

    def getText(self):
        return self.text_file

    def getLogger(self):
        return ConsoleUiLogger

if __name__ == "__main__":
    main_win = Tk()
    main_win.title("GUI DRONE")
    geo = main_win.geometry
    geo("610x450+400+400")
    main_win.minsize(610, 450)
    main_win.resizable(0, 0)
    img = PhotoImage(file='UserGuiResources/ico.png')
    main_win.tk.call('wm', 'iconphoto', main_win._w, img)

    configuration = Configuration("config/config.ini")
    kubernetes = KubernetesClass()

    app = Application(main_win)

    main_win.mainloop()
