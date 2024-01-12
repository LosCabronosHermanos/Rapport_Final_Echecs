import pygame, asyncio,os , shutil
from PIL import Image, ImageChops, ImageFilter
import chess
import random
import numpy as np
from code_base_donnee import DataBaseHandler
from picamera2 import Picamera2
import RPi.GPIO as GPIO

camera = Picamera2()
camera_config = camera.create_still_configuration({"size":(1280,
720)})
camera.configure(camera_config)
camera.rotation = 180

camera.start()
button_pin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
def take_save_photo(index):
    return camera.capture_file(f"/home/adam/Desktop/FOLDER/Projet/coup_jouer/image_{index}.jpg")

def img_crop(index):
	img = Image.open(f"coup_jouer/image_{index}.jpg")
	largeur, hauteur = img.size
	image = img.crop((375,20, largeur-275,hauteur-80))
	return image
    
running = True
width, height = 700, 700
rows, cols = 8, 8
square_size = height // rows
screen = pygame.display.set_mode((width, height))
database_handler = DataBaseHandler()

board = chess.Board()

def creation_donne():
    try:
        os.mkdir("coup_jouer")
    except FileExistsError:
        shutil.rmtree("coup_jouer")
        os.mkdir("coup_jouer")
    
    database_handler.create_table()


def effacement_donne():
    os.remove("Database.db")
    shutil.rmtree("coup_jouer")
    shutil.rmtree("__pycache__")


def abs_path():
    return os.getcwd() 

# Charger et redimensionner les images des pièces d'échecs
# Blancs
R_b = pygame.transform.scale(pygame.image.load('pieces/blanc/rook_b.png'), (80, 80)) 
N_b = pygame.transform.scale(pygame.image.load('pieces/blanc/knight_b.png'), (80, 80)) 
B_b = pygame.transform.scale(pygame.image.load('pieces/blanc/bishop_b.png'), (80, 80)) 
P_b = pygame.transform.scale(pygame.image.load('pieces/blanc/pawn_b.png'), (80, 80)) 
K_b = pygame.transform.scale(pygame.image.load('pieces/blanc/king_b.png') , (80, 80))  
Q_b = pygame.transform.scale(pygame.image.load('pieces/blanc/queen_b.png') , (80, 80))  

# Noirs
R_n = pygame.transform.scale(pygame.image.load('pieces/noir/rook_n.png'), (80, 80)) 
N_n = pygame.transform.scale(pygame.image.load('pieces/noir/knight_n.png'), (80, 80)) 
B_n = pygame.transform.scale(pygame.image.load('pieces/noir/bishop_n.png'), (80, 80)) 
P_n = pygame.transform.scale(pygame.image.load('pieces/noir/pawn_n.png'), (80, 80)) 
K_n = pygame.transform.scale(pygame.image.load('pieces/noir/king_n.png')  , (80, 80)) 
Q_n = pygame.transform.scale(pygame.image.load('pieces/noir/queen_n.png') , (80, 80)) 


def draw( matrice_jeu ):
    """Fonction qui permet de draw le board d'echec"""
    for row in range(rows):
        for col in range(cols):
            color = (155, 103, 60) if (row + col) % 2 == 0 else (225, 198, 153)
            pygame.draw.rect(screen, color, (col * square_size, row * square_size, square_size, square_size))
            if matrice_jeu[row][col] != 0 :
                screen.blit(matrice_jeu[row][col], ((col * square_size)+3, (row * square_size)+7))

def translation_p(matrice_jeu,coord):
    """fonction qui actualise la matrice_jeu"""
    bouge = [0,R_n,N_n,B_n,K_n,Q_n,B_n,N_n,R_n,P_n] # Ensemble des pièces blanches ( que le joueur controlle)
    p1,p2 = coord
    if matrice_jeu[p1[0]][p1[1]] in bouge:
        matrice_jeu[p1[0]][p1[1]] = matrice_jeu[p2[0]][p2[1]]# on change la valeur de lacoordonnée d'arrivée de la pièce à celle de la pièce
        matrice_jeu[p2[0]][p2[1]] = 0 # le point de départ de la pièce est changé à 0
    return matrice_jeu

def matrice_en_rgb( diff ):
    """fonction qui transforme la matrice (vide normalement) en une matrice de meme dimension que 
    le board d'echec et mets les RGB correspondants a chaque case ((0,0,0) si c'est noir etc..) et qui la renvoie"""

    larg_image, haut_image = diff.size
    larg_carre = larg_image // 8
    haut_carre = haut_image // 8

    matrice = []
    for i in range(8):
        ligne_moy = []
        for j in range(8):
            # on designe les 4 coins de chaque carré du board avec x1,y1,x2,y2
            x1 = j * larg_carre
            y1 = i * haut_carre
            x2 = x1 + larg_carre
            y2 = y1 + haut_carre
            carre = diff.crop((x1, y1, x2, y2)) # coupe l'image en un carre de coins x1,y1,x2,y2
            moyenne = tuple(int(sum(val) / len(val)) for val in zip(*carre.getdata()))# tuple où chaque élément représente la moyenne des valeurs RGB pour chaque carré du board
            ligne_moy.append(moyenne)
        matrice.append(ligne_moy)
    return matrice  

def matrice_en_bool(matrice):
    mat = matrice.copy()
    for i in range(len(matrice)) :
        for j in range(len(matrice)):
            if any( x > 2 for x in matrice[i][j] ):
                mat[i][j] = True 
            else :
                mat[i][j] = False
    return mat


def matrice_to_chess_coordinates(matrice_coords):
    """Convertit les coordonnes des pieces qui ont bouge trouvé avec coord_piece_change en les coordonnées d'échecs qui lui correspondent"""
    chess_files = "abcdefgh"
    chess_ranks = "87654321"

    # Récupérer les coordonnées de départ et d'arrivée
    start_coord = chess_files[matrice_coords[0][1]] + chess_ranks[matrice_coords[0][0]]
    end_coord = chess_files[matrice_coords[1][1]] + chess_ranks[matrice_coords[1][0]]

    chess_notation = end_coord +start_coord 

    return chess_notation

def chess_to_matrice_coordinates(chess_notation):
    """Convertit les coordonnées d'échecs en coordonnées de matrice_jeu"""
    chess_files = "abcdefgh"
    chess_ranks = "87654321"
    chess_notation = str(chess_notation)
    # Récupérer les coordonnées d'échecs
    end_coord = chess_notation[:2]
    start_coord = chess_notation[2:]

    # Convertir les coordonnées d'échecs en indices de matrice_jeu
    end_row = chess_ranks.index(end_coord[1])
    end_col = chess_files.index(end_coord[0])
    start_row = chess_ranks.index(start_coord[1])
    start_col = chess_files.index(start_coord[0])

    return [start_row, start_col], [end_row, end_col]



def coordonnees_deux_plus_grandes_valeurs(diff):
    matrice_rgb = matrice_en_rgb(diff)
    # Initialiser les coordonnées et les valeurs
    coord1, coord2 = None, None
    max_value1, max_value2 = 0,0
    # Parcourir la matrice RGB
    for i in range(len(matrice_rgb)):
        for j in range(len(matrice_rgb)):
            tuple_rgb = matrice_rgb[i][j]
            # Obtenir les deux plus grandes valeurs dans le tuple
            max_val = max(tuple_rgb)
            temp_tuple = [val for val in tuple_rgb if val != max_val]
            second_max_val = max(temp_tuple) if temp_tuple else max_val
            # Mettre à jour les coordonnées et les valeurs si nécessaire
            if max_val > max_value1:
                coord2 = coord1
                max_value2 = max_value1
                coord1 = [i, j]
                max_value1 = max_val
            elif max_val > max_value2:
                coord2 = [i, j]
                max_value2 = max_val
            elif second_max_val > max_value2:
                coord2 = [i, j]
                max_value2 = second_max_val
    print(coord1,coord2)        
    return coord1, coord2




# Boucle de jeu principale
def main():
    pygame.init()

    global running,index_image

    matrice_jeu = [[R_n, N_n, B_n, Q_n, K_n, B_n, N_n, R_n],
                   [P_n, P_n, P_n, P_n, P_n, P_n, P_n, P_n],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [P_b, P_b, P_b, P_b, P_b, P_b, P_b, P_b],
                   [R_b, N_b, B_b, Q_b, K_b, B_b, N_b, R_b]]

    index_image = 0

    take_save_photo(index_image)
    image_act = img_crop(index_image)

    creation_donne()

    while running:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False 
        if GPIO.input(button_pin) == GPIO.HIGH:   #---------------------------#
            save_file_bd = f"/coup_jouer/image_{index_image}.jpg" #------------------------ c'est surement ça qu'il faut changer
            save_file_static = f"/home/adam/Desktop/FOLDER/kutta/static/image_{index_image}.jpg"
            pygame.image.save(screen,save_file_static)
            database_handler.save_coup(abs_path()+save_file_bd)
            image_prec = image_act
            index_image += 1
            take_save_photo(index_image)#---------------------------#
            save_file_bd = f"coup_jouer/image_{index_image}.jpg"
            save_file_static = f"/home/adam/Desktop/FOLDER/kutta/static/image_{index_image}.jpg"
            image_act = img_crop(index_image)
            diff = ImageChops.subtract(image_prec, image_act)
            diff = diff.filter(ImageFilter.SHARPEN)

            coord = coordonnees_deux_plus_grandes_valeurs(diff)
            print(f"index_image : {index_image}")
            if index_image % 2 == 0:
                # Bot joue

                legal_moves = list(board.legal_moves)
                random_move = random.choice(legal_moves)
                print(f"le move du bot est :{random_move}")
                board.push(random_move)
                coup_noir = chess_to_matrice_coordinates(random_move)
                c1, c2 = coup_noir
                matrice_jeu[c1[0]][c1[1]] = matrice_jeu[c2[0]][c2[1]] # j'actualise la matrice jeu avec le coup du bot
                matrice_jeu[c2[0]][c2[1]] = 0

            else:
                # Joueur joue
                diff = ImageChops.subtract(image_prec, image_act)
                diff = diff.filter(ImageFilter.SHARPEN)
                changement = matrice_to_chess_coordinates(coordonnees_deux_plus_grandes_valeurs(diff))
                
                if chess.Move.from_uci(changement) in list(board.legal_moves):
                  
                    print(f"notre coup est : {changement}")
                    move = chess.Move.from_uci(changement)
                    board.push(move)
                    coord = coordonnees_deux_plus_grandes_valeurs(diff)
                    matrice_jeu = translation_p(matrice_jeu, coord)
                else:
                    
                    coord = coordonnees_deux_plus_grandes_valeurs(diff)
                    mon_tuple = coord
                    ma_liste = list(coord)
                    ma_liste[0] = mon_tuple[1]
                    ma_liste[1] = mon_tuple[0]
                    coord = tuple(ma_liste)
                    changement = matrice_to_chess_coordinates(coord)
                    print(f"notre coup est : {changement}")
                    move = chess.Move.from_uci(changement)
                    board.push(move)
                    print(matrice_en_rgb(diff))
                    matrice_jeu = translation_p(matrice_jeu, coord)
        # Mettre à jour l'affichage
        draw(matrice_jeu)
        pygame.display.update()

main()
print(database_handler.s())
