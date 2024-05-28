# tetris algorithm

from random import randrange as rand
import pygame
import sys
import socket
import threading
import pickle

# The configuration
config = {
    'cell_size': 20,
    'cols': 10,
    'rows': 16,
    'delay': 750,
    'maxfps': 30
}

colors = [
    (0, 0, 0),
    (255, 0, 0),
    (0, 150, 0),
    (0, 0, 255),
    (255, 120, 0),
    (255, 255, 0),
    (180, 0, 255),
    (0, 220, 220)
]

# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],

    [[0, 2, 2],
     [2, 2, 0]],

    [[3, 3, 0],
     [0, 3, 3]],

    [[4, 0, 0],
     [4, 4, 4]],

    [[0, 0, 5],
     [5, 5, 5]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]


def rotate_clockwise(shape):
    return [[shape[y][x]
             for y in range(len(shape))]
            for x in range(len(shape[0]) - 1, -1, -1)]


def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[cy + off_y][cx + off_x]:
                    return True
            except IndexError:
                return True
    return False


def remove_row(board, row):
    del board[row]
    return [[0 for i in range(config['cols'])]] + board


def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy + off_y - 1][cx + off_x] += val
    return mat1


def new_board():
    board = [[0 for x in range(config['cols'])]
             for y in range(config['rows'])]
    board += [[1 for x in range(config['cols'])]]
    return board


class TetrisApp(object):
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(250, 25)
        self.width = config['cell_size'] * config['cols'] + 150  # 추가된 너비
        self.height = config['cell_size'] * config['rows']

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        self.init_game()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("220.149.128.100", 4307))

        # 서버에 연결

        receive_thread = threading.Thread(target=self.receive_data)
        receive_thread.start()

    def send_message(self, message):  # server에 message를 보냄
        try:
            if str(type(message)) != "<class 'str'>":
                message = str(message)
            self.client_socket.send(message.encode())
        except socket.error as e:
            print("Error sending message:", e)

    def receive_data(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break

                received_data = data.decode('utf-8')
                print(received_data)
                if 'score' in received_data:
                    score = received_data.split(":")
                    print("Received score from server:", score[1])
                    # 여기에 서버로부터 받은 점수를 화면에 표시하는 로직을 추가
                    self.display_other_score(score[1])
                    self.other_score = score[1]
                elif 'over' in received_data:
                    game_over = received_data.split(" ")
                    print("Received game over status from server:", game_over[0], game_over[1])
                    print("You Win")
                    self.center_msg("You Win!!")
                    self.gameover = True
                    pygame.display.update()
                    sys.exit()
            except Exception as e:
                print("Error receiving data:", e)
                break

    # 서버로부터 받은 점수를 화면에 표시하는 함수
    def display_other_score(self, score):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.width - 150, 90))

    def new_stone(self):
        self.stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(config['cols'] / 2 - len(self.stone[0]) / 2)
        self.stone_y = 0

        if check_collision(self.board,
                           self.stone,
                           (self.stone_x, self.stone_y)):
            self.gameover = True

    def init_game(self):
        self.board = new_board()
        self.new_stone()
        self.score = 0
        self.other_score = 0

    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image = pygame.font.Font(
                pygame.font.get_default_font(), 12).render(
                line, False, (255, 255, 255), (0, 0, 0))

            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2

            self.screen.blit(msg_image, (
                self.width // 2 - msgim_center_x,
                self.height // 2 - msgim_center_y + i * 22))

    def draw_matrix(self, matrix, offset):
        off_x, off_y = offset
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    pygame.draw.rect(
                        self.screen,
                        colors[val],
                        pygame.Rect(
                            (off_x + x) *
                            config['cell_size'],
                            (off_y + y) *
                            config['cell_size'],
                            config['cell_size'],
                            config['cell_size']), 0)

    def move(self, delta_x):
        if not self.gameover and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > config['cols'] - len(self.stone[0]):
                new_x = config['cols'] - len(self.stone[0])
            if not check_collision(self.board,
                                   self.stone,
                                   (new_x, self.stone_y)):
                self.stone_x = new_x

    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()

    def drop(self):
        if not self.gameover and not self.paused:
            self.stone_y += 1
            if check_collision(self.board,
                               self.stone,
                               (self.stone_x, self.stone_y)):
                self.board = join_matrixes(
                    self.board,
                    self.stone,
                    (self.stone_x, self.stone_y))
                self.new_stone()
                while True:
                    for i, row in enumerate(self.board[:-1]):
                        if 0 not in row:
                            self.board = remove_row(
                                self.board, i)
                            self.score += 10
                            # 서버에 현재 게임 상태 전송
                            self.send_message("score:" + str(self.score))
                            break
                    else:
                        break

    def rotate_stone(self):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(self.board,
                                   new_stone,
                                   (self.stone_x, self.stone_y)):
                self.stone = new_stone

    def toggle_pause(self):
        self.paused = not self.paused

    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False

    def run(self):
        key_actions = {
            'ESCAPE': self.quit,
            'LEFT': lambda: self.move(-1),
            'RIGHT': lambda: self.move(+1),
            'DOWN': self.drop,
            'UP': self.rotate_stone,
            'p': self.toggle_pause,
            'SPACE': self.start_game
        }

        self.gameover = False
        self.paused = False
        pygame.time.set_timer(pygame.USEREVENT + 1, config['delay'])
        dont_burn_my_cpu = pygame.time.Clock()
        while 1:
            self.screen.fill((0, 0, 0))
            if self.gameover:
                self.center_msg(f"""Game Over! You loss
                                 Your Score: {self.score}
                                Press space to continue""")
                self.send_message("game over")
                break
            else:
                if self.paused:
                    self.center_msg("Paused")
                else:
                    self.draw_matrix(self.board, (0, 0))
                    self.draw_matrix(self.stone,
                                     (self.stone_x,
                                      self.stone_y))
                    font = pygame.font.Font(None, 24)
                    score_text = font.render(f"my Score: {self.score}", True, (255, 255, 255))
                    self.screen.blit(score_text, (self.width - 150, 10))  # 옆에 새로운 칸에 표시
                    score_text = font.render(f"other Score: {self.other_score}", True, (255, 255, 255))
                    self.screen.blit(score_text, (self.width - 150, 120))

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.drop()
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in key_actions:
                        if event.key == eval("pygame.K_"
                                             + key):
                            key_actions[key]()

            dont_burn_my_cpu.tick(config['maxfps'])


if __name__ == '__main__':
    App = TetrisApp()
    App.run()
