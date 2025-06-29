"""
This class is responsible for storing all the information of the current state of the chess game.
Also responsible for the valid moves in the current state.
Also keeps a move log.
"""


class GameState():
    def __init__(self):
        #Game board that stores a 8x8 board
        #Each element is two characters, first character determines whether black or white - "b" or "w"
        #Second character determines the type of piece - R, N, B, Q, K or p
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.moveLog = []
        self.whiteToMove = True
        self.whiteKingLocation = (7,4)
        self.blackKingLocation = (0,4)
        self.inCheck = False
        self.pins = []
        self.checks = []
        self.checkMate = False
        self.staleMate = False

    #will not work for moves like en passant, castling and pawn promotion.
    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) #Store the move to the move log so that we can undo it later
        #update King's position
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)
        self.whiteToMove = not self.whiteToMove #switch turns

    #Undo move using key Z
    def undoMove(self):
        if len(self.moveLog) > 0: #there is atleast one move
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            #update King's position
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)
            self.whiteToMove = not self.whiteToMove
            self.checkMate = False
            self.staleMate = False

    #All moves considering the check
    def getValidMoves(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        if self.inCheck:
            if len(self.checks) == 1: #only 1 check, block check or move king
                moves = self.getAllPossibleMoves()
                #to block a check you must move a piece into one of the squares between enemy piece and king
                check = self.checks[0] #check information
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol] #enemy piece causing the check
                validSquares = [] #squares that pieces can move to
                #if knight, must capture the knight or move the king. other pieces can be blocked
                if pieceChecking[1] == "N":
                    validSquares = [(checkRow, checkCol)] #Knight's position
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2]*i, kingCol + check[3]*i) #check[2] and check[3] are the check directions
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: #once you get to piece and checks
                            break
                #get rid of any moves that don't block check or move king
                for i in range(len(moves) - 1, -1, -1): #go through the moves list backwards since we are removing from a list while iterating on it
                    if moves[i].pieceMoved[1] != 'K': #move doesn't move king so it must block or capture
                        if not (moves[i].endRow, moves[i].endCol) in validSquares: #move doesn't block OR capture piece
                            moves.remove(moves[i])
            else: #double check, king HAS to move
                self.getKingMoves(kingRow, kingCol, moves)
        else: #not in check so all moves are fine
            moves = self.getAllPossibleMoves()

        if len(moves) == 0:
            if self.inCheck:
                self.checkMate = True
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False
        return moves

    #All moves not taking check into consideration
    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    if piece == 'p':
                        self.getPawnMoves(r,c, moves)
                    elif piece == 'R':
                        self.getRookMoves(r,c, moves)
                    elif piece == 'B':
                        self.getBishopMoves(r,c, moves)
                    elif piece == 'N':
                        self.getKnightMoves(r,c, moves)
                    elif piece == 'Q':
                        self.getQueenMoves(r,c, moves)
                    elif piece == 'K':
                        self.getKingMoves(r,c, moves)
        return moves


#Get all the pawn moves for the pawn located at row r and col c and add those moves to list
    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove: #white pawn moves
            if r-1>=0:
                if self.board[r-1][c] == "--": #1 move ahead of pawn is valid or not
                    if not piecePinned or pinDirection == (-1, 0):
                        moves.append(Move((r, c), (r-1, c), self.board))
                        if r == 6 and self.board[r-2][c] == "--":
                            moves.append(Move((r, c), (r - 2, c), self.board))
                if c-1>=0 and self.board[r-1][c-1][0] == "b": #captures to pawn's left
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((r, c), (r-1, c-1), self.board))
                if c+1<=7 and self.board[r-1][c+1][0] == "b": #captures to pawn's right
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((r, c), (r-1, c+1), self.board))
        else: #black pawn moves
            if r+1<=7:
                if self.board[r+1][c] == "--": #1 move ahead of pawn is valid or not
                    if not piecePinned or pinDirection == (1, 0):
                        moves.append(Move((r, c), (r+1, c), self.board))
                        if r == 1 and self.board[r+2][c] == "--":
                            moves.append(Move((r, c), (r + 2, c), self.board))
                if c-1>=0 and self.board[r+1][c-1][0] == "w": #captures to pawn's left
                    if not piecePinned or pinDirection == (+1, -1):
                        moves.append(Move((r, c), (r+1, c-1), self.board))
                if c+1<=7 and self.board[r+1][c+1][0] == "w": #captures to pawn's right
                    if not piecePinned or pinDirection == (+1, +1):
                        moves.append(Move((r, c), (r+1, c+1), self.board))

# Get all the Rook moves for the rook located at row r and col c and add those moves to list
    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q': #can't remove queen from pin on rook moves, only remove it on bishop moves
                    self.pins.remove(self.pins[i])
                break
        opposingTeam = "b" if self.whiteToMove else "w"
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right

        for d in directions:
            i, j = r + d[0], c + d[1]
            while 0 <= i < 8 and 0 <= j < 8:
                if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                    currentSquare = self.board[i][j]
                    if currentSquare == "--":
                        moves.append(Move((r, c), (i, j), self.board))
                    elif currentSquare[0] == opposingTeam:
                        moves.append(Move((r, c), (i, j), self.board))
                        break  # Can't move past captured piece
                    else:
                        break  # Blocked by own piece
                i += d[0]
                j += d[1]

    # Get all the Bishop moves for the bishop located at row r and col c and add those moves to list
    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        opposingTeam = "b" if self.whiteToMove else "w"
        directions = [(-1, -1), (-1, +1), (+1, +1), (+1, -1)]  # Diagonal directions

        for d in directions:
            i, j = r + d[0], c + d[1]
            while 0 <= i < 8 and 0 <= j < 8:
                if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                    currentSquare = self.board[i][j]
                    if currentSquare == "--":
                        moves.append(Move((r, c), (i, j), self.board))
                    elif currentSquare[0] == opposingTeam:
                        moves.append(Move((r, c), (i, j), self.board))
                        break
                    else:
                        break
                i += d[0]
                j += d[1]

# Get all the Knight moves for the knight located at row r and col c and add those moves to list
    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        opposingTeam = "b" if self.whiteToMove else "w"
        directions = [(-2, -1), (-2, +1), (-1, -2), (-1, +2), (+1, -2), (+1, +2), (+2, -1), (+2, +1)]  # Knight L directions

        for d in directions:
            i, j = r + d[0], c + d[1]
            if 0<=i<8 and 0<=j<8:
                if not piecePinned:
                    if self.board[i][j] == "--" or self.board[i][j][0] == opposingTeam:
                        moves.append(Move((r, c), (i, j), self.board))

# Get all the Queen moves for the queen located at row r and col c and add those moves to list
    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

# Get all the King moves for the king located at row r and col c and add those moves to list
    def getKingMoves(self, r, c, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor: #not an ally piece (empty or enemy piece)
                    #place king on end square and check for checks
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    #place king back on original location
                    if allyColor == "w":
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)


    """
    Returns if the player is in check, a list of pins and a list of checks
    """

    def checkForPinsAndChecks(self):
        pins = [] #squares where the allied pinned piece is and direction pinned from
        checks = [] #squares where enemy is applying a check
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        #check outward from king for pins and checks, keep track of all pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1) )
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = () #reset possible pins
            for i in range(1, 8):
                endRow = startRow + d[0]*i
                endCol = startCol + d[1]*i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == (): #1st allied piece could be pinned
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else: #2nd allied piece so no pin and stop checking in this direction
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        """
                        5 possibilities here in this conditional:
                        1. orthogonally away from king and piece is a rook
                        2. diagonally away from king and piece is a bishop
                        3. 1 square away diagonally from king and piece is a pawn
                        4. any direction and piece is a Queen
                        5. any direction 1 square away and piece is a king (this is necessary to prevent a king from moving to a square controlled by another king)
                        """
                        if (0<=j<=3 and type == 'R') or (4 <= j <= 7 and type == 'B') or (i == 1 and type == 'p' and ((enemyColor == 'w' and 6<=j<=7) or (enemyColor == 'b' and 4<=j<=5))) or \
                                (type == 'Q') or (i==1 and type == 'K'):
                            if possiblePin == (): #no piece blocking, so check
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                            else: #piece blocking so pin
                                pins.append(possiblePin)
                                break
                        else: #enemy piece not applying check
                            break
                else: #off board
                    break
        #now check for knight attacks
        knightMoves = ((-2, -1), (-2, 1), (-1,-2), (-1, 2), (1, -2), (1,2), (2, -1), (2,1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N': #enemy knight attacking king
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks




class Move():

    #Mapping rows and cols to standard chess notations. example - a8 is black rook
    ranksToRows = { "1": 7, "2" : 6, "3" : 5, "4" : 4, "5" : 3, "6" : 2, "7" : 1, "8": 0}
    rowsToRanks = {v:k for k,v in ranksToRows.items()}
    filesToCols = { "a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v:k for k,v in filesToCols.items()}
    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol


    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID

    def getChessNotation(self):
        return self.pieceMoved + self.getRankFiles(self.endRow, self.endCol)

    def getRankFiles(self, row, col):
        return self.colsToFiles[col] + self.rowsToRanks[row]