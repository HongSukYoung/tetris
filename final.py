import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
from tetrisfinal import *
import socket
import random

class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("게임 방")
        self.add = random.gauss(0,1)
        self.nickname = ''
        self.room = [[], []]
        self.nickroom = [[],[]]
        self.myroom = -99

        # 왼쪽 프레임
        left_frame = tk.Frame(master)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.text_area = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=80, height=24)
        self.text_area.pack()

        self.message_entry = tk.Entry(left_frame, width=70)
        self.message_entry.pack()



        # 오른쪽 프레임
        right_frame = tk.Frame(master)
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        self.nick_entry = tk.Entry(right_frame, width = 50)
        self.nick_entry.pack()

        self.send_button = tk.Button(right_frame, text="닉네임 변경", command=self.nick_change, width = 50, height = 3)
        self.send_button.pack(pady =5)

        self.room_entry = tk.Entry(right_frame, width = 50)
        self.room_entry.pack()

        self.send_button = tk.Button(right_frame, text="입장", command=self.enter_room, width = 50, height = 3)
        self.send_button.pack(pady =5)

        self.start_game_button = tk.Button(right_frame, text="게임시작", command=self.start_game,width = 50, height = 3)
        self.start_game_button.pack(pady =5)

        self.send_button = tk.Button(right_frame, text="전송", command=self.send_message, width = 50, height = 3)
        self.send_button.pack(pady =5)

        self.exit_button = tk.Button(right_frame, text="종료", command=self.exit_chat, width = 50, height = 3)
        self.exit_button.pack(pady =5)

        # 창 크기 및 위치 설정
        window_width = 1000
        window_height = 600
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        master.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

        # 새로운 쓰레드에서 서버로부터의 메시지 수신을 처리
        receive_thread = Thread(target=self.receive_messages)
        receive_thread.start()

    def connect_to_server(self):
        try:
            self.client_socket.connect(('220.149.128.100', 4307))
        except Exception as e:
            print(f"서버 연결 오류: {e}")
            self.master.destroy()

    def receive_messages(self):
        while True:
            try:
                response = self.client_socket.recv(1024).decode()
                if not response:
                    break
                other_add, func, msg = response.split(":")
                if func == 'a':
                    self.a_fun(float(other_add),int(msg))
                elif func == 'b':
                    self.b_fun(float(other_add))
                elif func == 'd':
                    self.d_fun(float(other_add),str(msg))
                elif func == 'e':
                    self.e_fun(float(other_add),str(msg))
            except Exception as e:
                print(f"메시지 수신 오류: {e}")
                break

    def enter_room(self):
        room_number = self.room_entry.get()
        self.myroom = room_number
        self.client_socket.send(f"{self.add}:a:{room_number}".encode())
    
    def start_game(self):
        self.client_socket.send(f"{self.add}:b:0".encode())
        App = TetrisApp()
        App.run()

    def send_message(self):
        message = self.message_entry.get()
        full_message = f"{self.add}:d:{message}"
        self.client_socket.send(full_message.encode())
        if self.nickname != '':
            self.text_area.insert(tk.END, f"{self.nickname}:{message}\n")
        else :
            self.text_area.insert(tk.END, f"나:{message}\n")
    
    def nick_change(self):
        new_nick = self.nick_entry.get()
        self.nickname = new_nick
        full_nick = f"{self.add}:e:{self.nickname}"
        self.client_socket.send(full_nick.encode())

    def a_fun(self,add,rm):
        for sublist in self.room:
            if add in sublist:
                sublist.remove(add)
        self.room[rm].append(add)

    def b_fun(self,add):
        idx = int(self.myroom)
        if add in self.room[idx]:
            App = TetrisApp()
            App.run()

    def d_fun(self,add,msg):
        idx = int(self.myroom)
        if add in self.room[idx]:
            if add in self.nickroom[0]:

                for jdx, dress in enumerate(self.nickroom[0]):
                    if dress == add:
                        self.text_area.insert(tk.END, f"{self.nickroom[1][jdx]}:{msg}\n")
                        break
            else:
                self.text_area.insert(tk.END, f"{add}:{msg}\n")
    
    def e_fun(self,add, nn):
        if add in self.nickroom[0]:
            for i, dres in enumerate(self.nickroom[0]):
                if dres == add:
                    for j in range(2):
                        self.nickroom[j].pop(i)
                    break

        self.nickroom[0].append(add)
        self.nickroom[1].append(nn)

    def exit_chat(self):
        self.client_socket.close()
        self.master.destroy()


def main():
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
