"""
This is our main driver file. It is responsible for handling user input and displaying the current GameState object.
"""

import pygame as p
from Chess import ChessEngine
import math

p.init()
checkAlert = p.font.SysFont("Arial", 26, True).render("!", True, p.Color("red"))
WIDTH = HEIGHT = 512
DIMENSION = 8 #Dimension of chess board = 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
checkMateFont = p.font.SysFont("Arial", 42, True, False)
invalidOverlay = p.image.load("images/crossed out.png")
invalidOverlay = p.transform.scale(invalidOverlay, (SQ_SIZE, SQ_SIZE))
"""
Load images will initialise a global dictionary of images, and will be called exactly once in the code
"""

def loadImages():
    pieces = ['wR', 'wN', 'wB', 'wQ', 'wK', 'wp', 'bR', 'bN', 'bQ', 'bK', 'bp', 'bB']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load('images/' + piece + '.png'), (SQ_SIZE, SQ_SIZE))
    #Note now we can access any of the images by just referring to the IMAGES dictionary and the correct index.

"""
The main driver for our code, this will handle user input and also update the graphics.
"""
def main():
    frameCount = 0
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False #flag variable for when a valid move is made
    loadImages() #only once
    running = True
    sqSelected = ()
    player_clicks = []
    captureSq = []
    moveSq = []
    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
            elif not gs.checkMate and not gs.staleMate and event.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos() #(x,y) of mouse
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                #If player clicks on the same square twice, undo the move.
                if sqSelected == (row, col):
                    sqSelected = ()
                    player_clicks = []
                    captureSq = []
                    moveSq = []
                else:
                    sqSelected = (row, col)
                    player_clicks.append(sqSelected)
                    if len(player_clicks) == 2:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True

                        if not moveMade and move.pieceCaptured[0] == move.pieceMoved[0]:
                            sqSelected = (move.endRow, move.endCol)
                            player_clicks = [sqSelected]
                        else:
                            sqSelected = ()  # resetting
                            player_clicks = []
                            captureSq = []
                            moveSq = []

                    if len(player_clicks) == 1:
                        selectedPiece = gs.board[sqSelected[0]][sqSelected[1]]
                        if selectedPiece == "--" or (gs.whiteToMove and selectedPiece[0] == "b") or (not gs.whiteToMove and selectedPiece[0] == "w"):
                            sqSelected = ()
                            player_clicks = []
                        else:
                            captureSq = []
                            moveSq = []
                            for move in validMoves:
                                if move.startRow == sqSelected[0] and move.startCol == sqSelected[1]:
                                    if (gs.whiteToMove and move.pieceCaptured[0] == "b") or (not gs.whiteToMove and move.pieceCaptured[0] == "w"):
                                        captureSq.append((move.endRow, move.endCol))
                                    elif move.pieceCaptured == "--":
                                        moveSq.append((move.endRow, move.endCol))

            elif event.type == p.KEYDOWN:
                if event.key == p.K_z: #user pressed Z key
                    gs.undoMove()
                    moveMade = True
                    sqSelected = ()
                    player_clicks = []
                    captureSq = []
                    moveSq = []

        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False

        clock.tick(MAX_FPS)
        p.display.flip()
        drawGameState(screen, gs, captureSq, moveSq, sqSelected, frameCount, validMoves)
        if gs.checkMate:
            text = "Black wins by checkmate!" if gs.whiteToMove else "White wins by checkmate!"
            drawText(screen, text)
        elif gs.staleMate:
            drawText(screen, "Stalemate")

        frameCount += 1

def drawGameState(screen, gs, captureSq, moveSq, sqSelected, frameCount, validMoves):
    drawBoard(screen, captureSq, moveSq) #draws the squares on the board
    drawPieces(screen, gs.board, sqSelected,frameCount) #draws the pieces on the board
    drawCheckIndicator(screen, gs)
    drawInvalidMoveOverlay(screen, gs, validMoves, sqSelected)

#Draws the squares on the board
def drawBoard(screen, captureSq, moveSq):
    colours = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            if (r,c) in captureSq:
                colour = p.Color("red")
            elif (r,c) in moveSq:
                colour = p.Color("blue")
            else:
                colour = colours[((r+c)%2)]
            p.draw.rect(screen, colour, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            p.draw.rect(screen, colour, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE), 100)

#Draws the pieces on the board (Doing it separately for easy reuse)
def drawPieces(screen, board, sqSelected, frameCount):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                if sqSelected == (r, c):
                    # Bounce selected piece
                    amplitude = 5  # pixels
                    speed = 0.1
                    offset = amplitude * math.sin(speed * frameCount)
                    screen.blit(IMAGES[piece], (c * SQ_SIZE, r * SQ_SIZE - offset))
                else:
                    screen.blit(IMAGES[piece], (c * SQ_SIZE, r * SQ_SIZE))

def drawInvalidMoveOverlay(screen, gs, validMoves, sqSelected):
    if sqSelected == ():
        return

    r, c = sqSelected
    piece = gs.board[r][c]

    if piece == "--" or (piece[0] == 'w' and not gs.whiteToMove) or (piece[0] == 'b' and gs.whiteToMove):
        return  # Don't show overlay if invalid piece is selected

    # Get all possible moves for this piece (ignoring checks)
    pseudoMoves = []
    if piece[1] == 'p':
        gs.getPawnMoves(r, c, pseudoMoves)
    elif piece[1] == 'R':
        gs.getRookMoves(r, c, pseudoMoves)
    elif piece[1] == 'B':
        gs.getBishopMoves(r, c, pseudoMoves)
    elif piece[1] == 'N':
        gs.getKnightMoves(r, c, pseudoMoves)
    elif piece[1] == 'Q':
        gs.getQueenMoves(r, c, pseudoMoves)
    elif piece[1] == 'K':
        sameTeam = "w" if gs.whiteToMove else "b"
        for m in range(-1, 2):
            for n in range(-1, 2):
                if m == 0 and n == 0:
                    continue  # skip the square the king is on
                i, j = r + m, c + n
                if 0 <= i < 8 and 0 <= j < 8:
                    if gs.board[i][j] == "--" or gs.board[i][j][0] != sameTeam:
                        pseudoMoves.append(ChessEngine.Move((r, c), (i, j), gs.board))

    # Find which of these were filtered out due to checks/pins
    legalMoves = [m for m in validMoves if m.startRow == r and m.startCol == c]
    invalidMoves = [m for m in pseudoMoves if m not in legalMoves]

    for move in invalidMoves:
        row, col = move.endRow, move.endCol
        screen.blit(invalidOverlay, (col * SQ_SIZE, row * SQ_SIZE))



def drawCheckIndicator(screen, gs):
    if gs.inCheck:
        # Determine king’s position based on which side is in check
        kingRow, kingCol = gs.whiteKingLocation if gs.whiteToMove else gs.blackKingLocation
        # Coordinates to place the exclamation mark on the square
        x = kingCol * SQ_SIZE + SQ_SIZE - 20  # top-right corner
        y = kingRow * SQ_SIZE + 5
        screen.blit(checkAlert, (x, y))


def drawText(screen, text):
    font = p.font.SysFont("Arial", 42, True, True)
    textObject = font.render(text, 0, p.Color('Black'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH//2 - textObject.get_width()//2,
                                                         HEIGHT//2 - textObject.get_height()//2)
    screen.blit(textObject, textLocation)

if __name__ == '__main__':
    main()