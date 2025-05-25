# title: Pyxel Bubbles
# author: ttrkaya
# desc: A Pyxel mouse click game example
# site: https://github.com/kitao/pyxel
# license: MIT
# version: 1.0

import pyxel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
import uuid
from datetime import datetime
import json
from cryptography.fernet import Fernet


SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256
LARGEUR = 10
HAUTEUR = 10
CONNECTION_STRING_ENCRYPYTED = b'gAAAAABoMuUjupVxMAs6tqDJI18NwojjeZN88HVFGDtp5n02NJk_je6CtA3V_2fcPMGRvHq66FGU5KZGsTMpDNWlZ5bVMNUIr5vYXLDkM8gw2FxUZV1RLbcFySgKSHO8RosvFvb5bBnJ8NXAQL1NATGOK44PnxiXOBBCzkksWrdF4sMFL4rcpXRMrJOVoL9zfxhr0gaRIhA9gInHjPx5fEkDyBjbU_ya1dNwlIh5GEqed773z4zr9yQEiCj8uVQzZBBdd3J_w1ca'

Base = declarative_base()
class Game(Base):
    __tablename__ = "mine_games"
    game_id = Column(String(36), primary_key=True, default=lambda : str(uuid.uuid4()))
    created = Column(DateTime, default=datetime.now())
    lastmodified = Column(DateTime, default=datetime.now())
    data = Column(JSON)
    mort = Column(Boolean, default=False)
    victoire = Column(Boolean, default=False)


class Terrain:
    def __init__(self, width : int, height : int, grid = None):
        self.width = width
        self.height = height
        if grid != None:
            self.grid = grid
        else:
            self.grid = [[Tuile(i, j) for j in range(height)] for i in range(width)]

        for i in range(width):
            for j in range(height):
                compteur = 0
                if i > 0 and j > 0 and self.grid[i-1][j-1].y_a_une_mine:
                    compteur = compteur + 1
                if i > 0 and self.grid[i-1][j].y_a_une_mine:
                    compteur = compteur + 1
                if i > 0 and j < height - 1 and self.grid[i-1][j+1].y_a_une_mine:
                    compteur = compteur + 1
                if j > 0 and self.grid[i][j-1].y_a_une_mine:
                    compteur = compteur + 1
                if j < height - 1 and self.grid[i][j+1].y_a_une_mine:
                    compteur = compteur + 1
                if i < width - 1 and j > 0 and self.grid[i+1][j-1].y_a_une_mine:
                    compteur = compteur + 1
                if i < width - 1 and self.grid[i+1][j].y_a_une_mine:
                    compteur = compteur + 1
                if i < width - 1 and j < height - 1 and self.grid[i+1][j+1].y_a_une_mine:
                    compteur = compteur + 1
                self.grid[i][j].compteur = compteur

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "grid": [
                [tuile.to_dict() for tuile in row]
                for row in self.grid
            ]
        }
    
    def is_victoire(self):
        for i in range(self.width):
            for j in range(self.height):
                tuile = self.grid[i][j]
                if not tuile.touchee and not tuile.y_a_une_mine:
                    return False
        return True    
    
    @classmethod
    def from_dict(cls, data):
        w = data["width"]
        h = data["height"]
        g = [
            [Tuile.from_dict(tuile) for tuile in row] 
            for row in data["grid"]]
        t = cls(w, h, g)
        return t


class Tuile:
    def __init__(self, x, y):
        self.y_a_une_mine = pyxel.rndi(0, 10) <= 1
        self.x = x
        self.y = y
        self.touchee =  False
        self.marquee =  False
        self.largeur = 10
        self.hauteur = 10
        self.couleur = 9
        self.xx = self.x * self.largeur
        self.yy = self.y * self.hauteur
        self.compteur = 0

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "y_a_une_mine": self.y_a_une_mine,
            "touchee": self.touchee,
            "marquee": self.marquee
        }
    
    @classmethod
    def from_dict(cls, data):
        x = data["x"]
        y = data["y"]
        t = cls(x, y)
        t.y_a_une_mine = data["y_a_une_mine"]
        if data["touchee"]:
            t.touche()
        if "marquee" in data and data["marquee"]:
            t.marque()
        return t
    
    def draw(self):
        pyxel.rect(self.xx, self.yy, self.largeur, self.hauteur, 2)
        pyxel.rect(self.xx + 1, self.yy + 1, self.largeur - 1, self.hauteur - 1, self.couleur)
        if self.touchee and not self.y_a_une_mine:
            pyxel.text(self.xx + 2, self.yy + 2, str(self.compteur), col=0)

    def touche(self):
        self.touchee = True
        if self.y_a_une_mine:
            self.couleur = 8
        else:
            self.couleur = 7
        return self.y_a_une_mine
    
    def marque(self):
        if self.touchee:
            return
        if not self.marquee:
            self.marquee = True
            self.couleur = 11
        else:
            self.marquee = False
            self.couleur = 9    

    def a_touche(self, x, y):
        if self.xx < x and x < self.xx + self.largeur:
            if self.yy < y and y < self.yy + self.hauteur:
                return True
        return False


class App:
    def __init__(self):

        # crypto
        cv = b'DomvRFXaUuXdRpHU-CMq2zUKVIQ0sD0NZyWHbqmK0Ms='
        cipher = Fernet(cv)
        connection_string = cipher.decrypt(CONNECTION_STRING_ENCRYPYTED).decode()

        # set the seed for random generation
        now = datetime.now()
        ts = int(now.timestamp())
        pyxel.rseed(ts)

        self.termine = False
        engine = create_engine(connection_string)
        Session = sessionmaker(bind=engine)

        Base.metadata.create_all(engine)

        self.session = Session()

        self.game = self.session.query(Game).filter(Game.mort != True).filter(Game.victoire != True).order_by(desc(Game.created)).first()
        if self.game:
            data = self.game.data
            self.terrain = Terrain.from_dict(json.loads(data))
        else:
            self.terrain = Terrain(LARGEUR, HAUTEUR)
            self.game = Game()
            self.session.add(self.game)

        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Mines", capture_scale=1)
        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    def update(self):

        if pyxel.btnp(pyxel.KEY_Q):
            if not self.termine:
                self.game.data = json.dumps(self.terrain.to_dict())
                self.game.lastmodified = datetime.now()
                self.session.commit()

            pyxel.quit()

        if not self.termine:

            if self.terrain.is_victoire():
                # on gagne...
                self.game.data = json.dumps(self.terrain.to_dict())
                self.game.mort = False
                self.game.victoire = True
                self.game.lastmodified = datetime.now()
                self.session.commit()
                self.termine = True
                

            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) or pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
                tuile_courante = None
                xx = pyxel.mouse_x
                yy = pyxel.mouse_y
                for ligne in self.terrain.grid:
                    for tuile in ligne:
                        if tuile.a_touche(xx, yy):
                            tuile_courante = tuile
                            break
                    if tuile_courante:
                        break

                if tuile_courante:
                    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                        mine = tuile.touche()
                        if mine:
                            # on meurt...
                            self.game.data = json.dumps(self.terrain.to_dict())
                            self.game.mort = True
                            self.game.victoire = False
                            self.game.lastmodified = datetime.now()
                            self.session.commit()
                            self.termine = True
                            

                    else:
                        tuile.marque()

    def draw(self):
        pyxel.cls(0)

        if self.game.victoire:
            # dessine la victoire
            pyxel.text(96, 50, "victoire", pyxel.frame_count % 15 + 1)
        elif self.game.mort:
            # dessine la mort
            pyxel.text(96, 50, "mort", 8)
        else:
            # boucle du jeu
            for ligne in self.terrain.grid:
                for tuile in ligne:
                    tuile.draw()

App()
