from tkinter import *
import serial

BLOCK_NUM_H = 10  # ブロックの数（横方向)
BLOCK_NUM_V = 10  # ブロックの数（縦方向）
BLOCK_WIGTH = 60  # ブロックの幅
BLOCK_HEIGHT = 20  # ブロックの高さ
COLOR_BLOCK_1 = "blue"  # ブロックの色
COLOR_BLOCK_2 = "red"  # ブロックの色

HEIGHT_SPACE = 300  # 縦方向の空きスペース

CANVAS_WIDTH = 600
CANVAS_HEIGHT = 400

BAR_WIDTH = 200  # パドルの幅
BAR_HEIGHT = 20  # パドルの高さ
BAR_Y_POSITION = 390  # パドルの下方向からの位置
COLOR_BAR = "green"  # パドルの色

RADIUS_BALL = 10  # ボールの半径
COLOR_BALL = "yellow"  # ボールの色
NUM_BALL = 2  # ボールの数

UPDATE_TIME = 20  # 更新間隔（ms）


# シリアルポートの初期化（Arduinoの接続されているポートに応じて変更）
ser = serial.Serial('COM4', 9600)

class Block:
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.x1 = x
        self.y1 = y
        self.x2 = x + BLOCK_WIGTH
        self.y2 = y + BLOCK_HEIGHT
        self.color = color
        self.id = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill=self.color, width=0)

    def hit_check(self, ball):
        return (self.x1 <= ball.x <= self.x2) and (self.y1 <= ball.y <= self.y2) # return bool

class Ball:
    def __init__(self, canvas, x = 350, y = 250):
        self.canvas = canvas
        self.x = x
        self.y = y

        #Direction x ?
        self.dirx = -15
        self.diry = -15
        self.r = RADIUS_BALL
        self.id = canvas.create_oval(self.x - self.r, self.y - self.r, self.x + self.r, self.y + self.r, fill = COLOR_BALL)

    def move(self):
        # ボールの座標を更新
        self.x += self.dirx
        self.y += self.diry
        # キャンバス上のボールの位置を更新
        self.canvas.coords(self.id, self.x - self.r, self.y - self.r, self.x + self.r, self.y + self.r)

    def check_collision(self):
        # Check for wall collisions
        if self.x <= 0 or self.x >= CANVAS_WIDTH:
            self.dirx *= -1
        if self.y <= 0:
            self.diry *= -1
        if self.y >= CANVAS_HEIGHT:
            self.is_gameover = True
            print("Game Over! Score:", self.point)
        
        # Check for bar collision
        if self.bar.y <= self.ball.y + self.ball.r <= self.bar.y + 10 and self.bar.x <= self.ball.x <= self.bar.x + self.bar.width:
            self.ball.diry *= -1

        # Check for block collisions
        for block in self.blocks[:]:
            if block.hit_check(self.ball):
                self.blocks.remove(block)
                self.canvas.delete(block.id)
                self.ball.diry *= -1
                self.point += 10
                break
            
class Bar:
    def __init__(self, canvas, init_x = 0):
        self.canvas = canvas
        self.x = init_x
        self.y = BAR_Y_POSITION
        self.width = BAR_WIDTH
        self.id = canvas.create_rectangle(self.x, self.y, self.x + self.width, self.y + BAR_HEIGHT, fill = COLOR_BAR)

    def move(self, x):
        self.x = x
        self.canvas.coords(self.id, self.x, self.y, self.x + self.width, self.y + BAR_HEIGHT)

class BlockBreaker:
    def __init__(self, master):
        self.master = master
        self.canvas = Canvas(master, width = CANVAS_WIDTH, height = CANVAS_HEIGHT)
        self.canvas.pack()

        # self.master.bind('<Motion>', self.motion)

        self.master.bind('<Button-1>', self.click)

        self.setup_game()

    def setup_game(self):
        self.blocks = [Block(self.canvas, ix * BLOCK_WIGTH, iy * BLOCK_HEIGHT, COLOR_BLOCK_1 if (iy + ix) % 2 == 0 else COLOR_BLOCK_2) 
                        for iy in range(BLOCK_NUM_V) for ix in range(BLOCK_NUM_H)]
        # self.ball = [Ball(self.canvas) for i in range(NUM_BALL)]
        self.ball = Ball(self.canvas)
        self.bar = Bar(self.canvas)
        self.is_gameover = False
        self.point = 0
        self.game_loop()

    def reset_game(self):
        # キャンバス上のオブジェクトをすべて削除
        self.canvas.delete("all")
        # ゲームの状態を初期化
        self.setup_game()

    def click(self, event):
        if self.is_gameover:
            self.reset_game()

    def game_loop(self):
        if not self.is_gameover:
            self.ball.move()
            self.motion()
            self.check_collision()
            self.canvas.after(50, self.game_loop)

    def check_collision(self):
        # Check for wall collisions
        if self.ball.x <= RADIUS_BALL or self.ball.x >= CANVAS_WIDTH - RADIUS_BALL:
            self.ball.dirx *= -1
        if self.ball.y <= 0:
            self.ball.diry *= -1
        if self.ball.y >= CANVAS_HEIGHT - RADIUS_BALL:
            self.is_gameover = True
            print("Game Over! Score:", self.point)
        
        # Check for bar collision
        if self.bar.y <= self.ball.y + self.ball.r <= self.bar.y + 10 and self.bar.x <= self.ball.x <= self.bar.x + self.bar.width:
            self.ball.diry *= -1

        # Check for block collisions
        for block in self.blocks[:]:
            if block.hit_check(self.ball):
                self.blocks.remove(block)
                self.canvas.delete(block.id)
                self.ball.diry *= -1
                self.point += 10
                break

    def motion(self):
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            pot_value = int(line)
            # 可変抵抗の値を画面の幅にマッピング
            mapped_value = self.map_value(pot_value, 0, 1023, 0, self.canvas.winfo_width() - self.bar.width)
            self.bar.move(mapped_value)

    @staticmethod
    def map_value(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
            
root = Tk()
app = BlockBreaker(root)
root.mainloop()
